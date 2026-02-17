#!/bin/bash
# Pre-Delinquency Engine - Instance Setup Script
# Run this script on the EC2 instance after SSH'ing in

set -e

echo "🔧 Setting up Pre-Delinquency Engine on EC2 Instance"
echo "=============================================================="
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq
echo "   ✅ System updated"
echo ""

# Install Docker
echo "🐳 Installing Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker already installed"
else
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    rm get-docker.sh
    echo "   ✅ Docker installed"
fi
echo ""

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "   ✅ Docker Compose already installed"
else
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "   ✅ Docker Compose installed"
fi
echo ""

# Install Git
echo "📦 Installing Git..."
sudo apt-get install -y git
echo "   ✅ Git installed"
echo ""

# Install Python and pip
echo "🐍 Installing Python..."
sudo apt-get install -y python3-pip python3-venv
echo "   ✅ Python installed"
echo ""

# Clone repository
echo "📥 Cloning repository..."
if [ -d "pre-delinquency-engine" ]; then
    echo "   Repository already exists, pulling latest changes..."
    cd pre-delinquency-engine
    git pull
    cd ..
else
    # You'll need to replace this with your actual repository URL
    echo "   ⚠️  Please enter your repository URL:"
    read -p "   Repository URL: " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "   Using default repository structure..."
        mkdir -p pre-delinquency-engine
        cd pre-delinquency-engine
        
        # Create basic structure
        mkdir -p src/data_generation src/feature_engineering src/models src/serving src/streaming
        mkdir -p data/models/quick
        mkdir -p sql
        
        echo "   ⚠️  You'll need to copy your project files to this directory"
        cd ..
    else
        git clone $REPO_URL pre-delinquency-engine
    fi
fi
echo "   ✅ Repository ready"
echo ""

# Navigate to project directory
cd pre-delinquency-engine

# Create optimized docker-compose for t3.micro
echo "🐳 Creating optimized Docker Compose configuration..."
cat > docker-compose.prod.yml << 'EOF'
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
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 256M
        reservations:
          memory: 128M
  
  redis:
    image: redis:7-alpine
    container_name: delinquency_redis
    command: redis-server --appendonly yes --requirepass redis123 --maxmemory 128mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.1'
          memory: 128M
  
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: delinquency_zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
      ZOOKEEPER_SERVER_ID: 1
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.1'
          memory: 128M
  
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: delinquency_kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_LOG_RETENTION_HOURS: 24
      KAFKA_HEAP_OPTS: "-Xmx256M -Xms128M"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.2'
          memory: 384M
  
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    container_name: delinquency_api
    ports:
      - "8000:8000"
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
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 256M
  
  dashboard:
    build:
      context: .
      dockerfile: docker/Dockerfile.dashboard
    container_name: delinquency_dashboard
    ports:
      - "8501:8501"
    environment:
      API_URL: http://api:8000
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/bank_data
    depends_on:
      - api
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.15'
          memory: 256M

volumes:
  postgres_data:
  redis_data:
EOF

echo "   ✅ Docker Compose configuration created"
echo ""

# Create .env file
echo "⚙️  Creating environment configuration..."
cat > .env << 'EOF'
DATABASE_URL=postgresql://admin:admin123@localhost:5432/bank_data
REDIS_URL=redis://:redis123@localhost:6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
ENVIRONMENT=production
EOF
echo "   ✅ Environment configuration created"
echo ""

# Start Docker service
echo "🐳 Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
echo "   ✅ Docker service started"
echo ""

# Build and start services
echo "🚀 Building and starting services (this will take 5-10 minutes)..."
echo "   This is a good time to grab a coffee ☕"
echo ""

# Pull images first to show progress
docker-compose -f docker-compose.prod.yml pull

# Build custom images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

echo "   ✅ Services started"
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo "=============================================================="
echo "✅ Setup Complete!"
echo "=============================================================="
echo ""
echo "📍 Your application is now running at:"
echo "   API:       http://$PUBLIC_IP:8000"
echo "   API Docs:  http://$PUBLIC_IP:8000/docs"
echo "   Dashboard: http://$PUBLIC_IP:8501"
echo ""
echo "📝 Next Steps:"
echo "   1. Initialize database and generate data:"
echo "      bash deployment/free-tier/3-initialize-data.sh"
echo ""
echo "   2. Start streaming pipeline:"
echo "      bash deployment/free-tier/4-start-pipeline.sh"
echo ""
echo "💡 Useful Commands:"
echo "   View logs:     docker-compose -f docker-compose.prod.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.prod.yml down"
echo "   Restart:       docker-compose -f docker-compose.prod.yml restart"
echo ""
