#!/bin/bash
# Pre-Delinquency Engine - Complete GCP Deployment Script
# This script does EVERYTHING: creates VM, installs dependencies, deploys app
# Run from your LOCAL machine in the pre-delinquency-engine directory

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-pre-delinquency-demo}"
ZONE="us-central1-a"
INSTANCE_NAME="delinquency-engine"
MACHINE_TYPE="e2-medium"  # 2 vCPU, 4GB RAM - Free tier eligible

echo "🚀 Pre-Delinquency Engine - Complete GCP Deployment"
echo "=============================================================="
echo "Project: $PROJECT_ID"
echo "Zone: $ZONE"
echo "Instance: $INSTANCE_NAME"
echo "=============================================================="
echo ""

# Step 1: Set project
echo "📋 Step 1: Setting GCP project..."
gcloud config set project $PROJECT_ID
echo "   ✅ Project set"
echo ""

# Step 2: Enable required APIs
echo "🔧 Step 2: Enabling required APIs..."
gcloud services enable compute.googleapis.com
echo "   ✅ APIs enabled"
echo ""

# Step 3: Create firewall rules
echo "🔥 Step 3: Creating firewall rules..."
if ! gcloud compute firewall-rules describe allow-delinquency-ports &>/dev/null; then
    gcloud compute firewall-rules create allow-delinquency-ports \
        --allow tcp:8000,tcp:8501,tcp:22 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow access to API, Dashboard, and SSH"
    echo "   ✅ Firewall rules created"
else
    echo "   ✅ Firewall rules already exist"
fi
echo ""

# Step 4: Create VM instance
echo "💻 Step 4: Creating VM instance..."
if gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE &>/dev/null; then
    echo "   ⚠️  Instance already exists, using existing instance"
else
    gcloud compute instances create $INSTANCE_NAME \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=30GB \
        --boot-disk-type=pd-standard \
        --tags=http-server,https-server \
        --metadata=startup-script='#!/bin/bash
# This runs on first boot
apt-get update
apt-get install -y docker.io docker-compose git python3-pip
usermod -aG docker $USER
systemctl enable docker
systemctl start docker
'
    echo "   ✅ Instance created"
    echo "   ⏳ Waiting 60 seconds for instance to boot..."
    sleep 60
fi
echo ""

# Step 5: Get instance IP
echo "🌐 Step 5: Getting instance IP..."
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "   Instance IP: $EXTERNAL_IP"
echo ""

# Step 6: Wait for SSH to be ready
echo "⏳ Step 6: Waiting for SSH to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="echo 'SSH ready'" &>/dev/null; then
        echo "   ✅ SSH is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES - waiting..."
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ SSH failed to become ready"
    exit 1
fi
echo ""

# Step 7: Copy project files to VM
echo "📦 Step 7: Copying project files to VM..."
gcloud compute scp --recurse --zone=$ZONE \
    ./src \
    ./docker \
    ./dashboard \
    ./sql \
    ./requirements.txt \
    ./docker-compose.yml \
    $INSTANCE_NAME:~/
echo "   ✅ Files copied"
echo ""

# Step 8: Create production docker-compose on VM
echo "🐳 Step 8: Setting up Docker configuration..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
cat > ~/docker-compose.prod.yml << 'EOFCOMPOSE'
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    container_name: delinquency_db
    environment:
      POSTGRES_DB: bank_data
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
    ports:
      - '5432:5432'
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
  
  redis:
    image: redis:7-alpine
    container_name: delinquency_redis
    command: redis-server --appendonly yes --requirepass redis123
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data
    restart: unless-stopped
  
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: delinquency_zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    restart: unless-stopped
  
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: delinquency_kafka
    depends_on:
      - zookeeper
    ports:
      - '9092:9092'
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
    restart: unless-stopped
  
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    container_name: delinquency_api
    ports:
      - '8000:8000'
    environment:
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/bank_data
      REDIS_URL: redis://:redis123@redis:6379
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      ENVIRONMENT: production
    depends_on:
      - postgres
      - redis
      - kafka
    restart: unless-stopped
  
  dashboard:
    build:
      context: .
      dockerfile: docker/Dockerfile.dashboard
    container_name: delinquency_dashboard
    ports:
      - '8501:8501'
    environment:
      API_URL: http://api:8000
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/bank_data
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
EOFCOMPOSE
"
echo "   ✅ Docker configuration created"
echo ""

# Step 9: Install Docker and dependencies on VM
echo "🔧 Step 9: Installing Docker and dependencies..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    sudo apt-get update -qq
    sudo apt-get install -y docker.io docker-compose git python3-pip
    sudo usermod -aG docker \$USER
    sudo systemctl enable docker
    sudo systemctl start docker
"
echo "   ✅ Dependencies installed"
echo ""

# Step 10: Build and start services
echo "🚀 Step 10: Building and starting services (this takes 5-10 minutes)..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    cd ~
    sudo docker-compose -f docker-compose.prod.yml pull
    sudo docker-compose -f docker-compose.prod.yml build
    sudo docker-compose -f docker-compose.prod.yml up -d
"
echo "   ✅ Services started"
echo ""

# Step 11: Wait for services to be ready
echo "⏳ Step 11: Waiting for services to be ready..."
sleep 45
echo "   ✅ Services should be ready"
echo ""

# Step 12: Initialize database and generate data
echo "📊 Step 12: Initializing database and generating data..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    # Wait for PostgreSQL
    echo 'Waiting for PostgreSQL...'
    for i in {1..30}; do
        if sudo docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U admin &>/dev/null; then
            echo 'PostgreSQL ready'
            break
        fi
        sleep 2
    done
    
    # Initialize database
    echo 'Initializing database schema...'
    sudo docker-compose -f docker-compose.prod.yml exec -T api python -m src.data_generation.check_db
    
    # Create Kafka topics
    echo 'Creating Kafka topics...'
    sudo docker-compose -f docker-compose.prod.yml exec -T api python -m src.streaming.setup_topics
    
    # Generate data
    echo 'Generating synthetic data...'
    sudo docker-compose -f docker-compose.prod.yml exec -T api python -m src.data_generation.synthetic_data
    
    # Train model
    echo 'Training ML model...'
    sudo docker-compose -f docker-compose.prod.yml exec -T api python -m src.models.quick_train
    
    echo 'Data initialization complete!'
"
echo "   ✅ Database initialized and data generated"
echo ""

# Step 13: Verify deployment
echo "🔍 Step 13: Verifying deployment..."
sleep 5
if curl -s http://$EXTERNAL_IP:8000/health | grep -q "healthy"; then
    echo "   ✅ API is responding"
else
    echo "   ⚠️  API may still be starting up"
fi
echo ""

# Final output
echo "=============================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=============================================================="
echo ""
echo "📍 Your application is running at:"
echo "   API:       http://$EXTERNAL_IP:8000"
echo "   API Docs:  http://$EXTERNAL_IP:8000/docs"
echo "   Dashboard: http://$EXTERNAL_IP:8501"
echo ""
echo "🔧 Useful commands:"
echo "   SSH into instance:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "   View logs:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo docker-compose -f docker-compose.prod.yml logs -f'"
echo ""
echo "   Stop services:"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo docker-compose -f docker-compose.prod.yml down'"
echo ""
echo "   Delete instance (cleanup):"
echo "   gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "💡 Test your API:"
echo "   curl http://$EXTERNAL_IP:8000/health"
echo "   curl http://$EXTERNAL_IP:8000/stats"
echo ""
