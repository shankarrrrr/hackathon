# PHASE 7: AWS DEPLOYMENT - FREE TIER OPTIMIZED

> **AWS deployment guide optimized for Free Tier and minimal costs**  
> Includes both Free Tier configuration and ultra-low-cost alternatives

## AWS Free Tier Reality Check

### ❌ Services NOT in Free Tier (Expensive)

| Service | Free Tier | Why Not Free | Monthly Cost |
|---------|-----------|--------------|--------------|
| **Amazon MSK** | ❌ No free tier | Managed Kafka is expensive | $150+ |
| **ElastiCache** | ❌ No free tier | Managed Redis costs money | $15-40 |
| **NAT Gateway** | ❌ No free tier | $0.045/hour per AZ | $33-100 |
| **Application Load Balancer** | ❌ No free tier | $0.0225/hour + data | $16-25 |

### ✅ Services WITH Free Tier (Limited)

| Service | Free Tier | Limits | After Free Tier |
|---------|-----------|--------|-----------------|
| **EC2** | ✅ 750 hours/month | t2.micro or t3.micro only | $8-15/month |
| **RDS** | ✅ 750 hours/month | db.t2.micro, 20GB storage | $15-30/month |
| **S3** | ✅ 5GB storage | 20,000 GET, 2,000 PUT | $0.023/GB |
| **CloudWatch** | ✅ 10 metrics | 5GB logs, 1M API requests | Varies |
| **Lambda** | ✅ 1M requests | 400,000 GB-seconds | $0.20/1M requests |
| **ECS Fargate** | ❌ No free tier | Pay per vCPU/GB-hour | $30-300/month |

### 💰 Realistic Costs

**Minimum Production Setup**: $200-300/month  
**Free Tier Optimized**: $50-100/month (first 12 months)  
**After Free Tier Expires**: $150-250/month

---

## Strategy 1: Free Tier Optimized (Recommended for Demo/Learning)

This approach maximizes AWS Free Tier usage and minimizes costs for the first 12 months.

### Architecture Changes

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTERNET GATEWAY                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EC2 INSTANCE (t3.micro)                       │
│                    Public Subnet - FREE TIER                     │
├─────────────────────────────────────────────────────────────────┤
│  • Nginx Reverse Proxy                                           │
│  • Docker Compose (all services)                                 │
│  • API (FastAPI)                                                 │
│  • Dashboard (Streamlit)                                         │
│  • Kafka (single broker)                                         │
│  • PostgreSQL (containerized)                                    │
│  • Redis (containerized)                                         │
│  • All Workers                                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AMAZON S3 (5GB FREE)                          │
│  • ML Models                                                     │
│  • Backups                                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Cost Breakdown (Free Tier)

| Service | Configuration | Free Tier | Cost |
|---------|--------------|-----------|------|
| **EC2** | t3.micro (1 vCPU, 1GB RAM) | 750 hours/month | **$0** (first 12 months) |
| **EBS** | 30GB gp3 volume | 30GB free | **$0** (first 12 months) |
| **S3** | 5GB storage | 5GB free | **$0** |
| **Data Transfer** | 100GB out | 100GB free | **$0** (first 12 months) |
| **CloudWatch** | Basic monitoring | 10 metrics free | **$0** |
| **Elastic IP** | 1 IP (while attached) | 1 free | **$0** |
| **Total** | | | **$0/month** (first year) |

**After 12 months**: ~$10-15/month

### Deployment Steps

#### 1. Launch EC2 Instance

Create `deployment/free-tier/launch-ec2.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Launching Free Tier EC2 Instance..."

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name pre-delinquency-sg \
  --description "Pre-Delinquency Engine Security Group" \
  --query 'GroupId' \
  --output text)

# Allow SSH
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Allow HTTP
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow Dashboard
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --key-name your-key-pair \
  --security-group-ids $SG_ID \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=pre-delinquency-engine}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "✅ Instance launched: $INSTANCE_ID"

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "✅ Instance running at: $PUBLIC_IP"
echo ""
echo "Next steps:"
echo "1. SSH into instance: ssh -i your-key.pem ubuntu@$PUBLIC_IP"
echo "2. Run setup script: bash setup-instance.sh"
```

#### 2. Setup Instance

Create `deployment/free-tier/setup-instance.sh`:

```bash
#!/bin/bash
set -e

echo "🔧 Setting up Pre-Delinquency Engine on EC2..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python
sudo apt-get install -y python3-pip python3-venv

# Clone repository
git clone https://github.com/your-repo/pre-delinquency-engine.git
cd pre-delinquency-engine

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://admin:admin123@postgres:5432/bank_data
REDIS_URL=redis://:redis123@redis:6379
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENVIRONMENT=production
EOF

# Start services
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Initialize database
docker-compose exec -T postgres psql -U admin -d bank_data -f /docker-entrypoint-initdb.d/init.sql

# Generate data
docker-compose exec -T api python -m src.data_generation.synthetic_data

# Train model
docker-compose exec -T api python -m src.models.quick_train

echo "✅ Setup complete!"
echo ""
echo "Access your application:"
echo "  API: http://$(curl -s ifconfig.me):8000"
echo "  Dashboard: http://$(curl -s ifconfig.me):8501"
```

#### 3. Optimized Docker Compose

Create `deployment/free-tier/docker-compose.yml`:

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    container_name: delinquency_db
    environment:
      POSTGRES_DB: bank_data
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    # Resource limits for t3.micro
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 256M
  
  redis:
    image: redis:7-alpine
    container_name: delinquency_redis
    command: redis-server --appendonly yes --requirepass redis123 --maxmemory 128mb
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
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      # Memory optimization
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
    depends_on:
      - postgres
      - redis
      - kafka
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.3'
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
          cpus: '0.2'
          memory: 256M

volumes:
  postgres_data:
  redis_data:
```

---

## Strategy 2: Ultra-Low-Cost Production (After Free Tier)

For when you need production-grade but want to minimize costs.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE (FREE CDN/SSL)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EC2 t3.small ($15/month)                      │
│                    + 50GB EBS ($5/month)                         │
├─────────────────────────────────────────────────────────────────┤
│  All services in Docker Compose                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RDS db.t3.micro ($15/month)                   │
│                    20GB storage                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cost: $35-40/month

---

## Strategy 3: Serverless Alternative (Pay-per-use)

Use AWS Lambda + managed services for true pay-per-use pricing.

### Architecture

```
API Gateway → Lambda (API) → RDS Proxy → RDS PostgreSQL
                ↓
            EventBridge → Lambda (Workers)
                ↓
            DynamoDB Streams
```

### Services

| Service | Free Tier | Cost After Free Tier |
|---------|-----------|---------------------|
| **Lambda** | 1M requests/month | $0.20 per 1M requests |
| **API Gateway** | 1M requests/month | $3.50 per 1M requests |
| **RDS Proxy** | No free tier | $0.015/hour = $11/month |
| **DynamoDB** | 25GB storage | $0.25/GB/month |
| **EventBridge** | Free | $1 per 1M events |

### Cost: $20-50/month (depending on usage)

---

## Comparison Table

| Strategy | Setup Time | Monthly Cost (Year 1) | Monthly Cost (After) | Scalability | Complexity |
|----------|------------|----------------------|---------------------|-------------|------------|
| **Free Tier (EC2)** | 1 hour | $0 | $10-15 | Low | Low |
| **Low-Cost Production** | 2 hours | $35-40 | $35-40 | Medium | Low |
| **Full AWS (Original)** | 3-4 hours | $590-880 | $590-880 | High | High |
| **Serverless** | 4-5 hours | $20-50 | $20-50 | High | Medium |

---

## Recommended Approach

### For Demo/Learning (First 12 Months)
✅ **Use Strategy 1: Free Tier EC2**
- Cost: $0/month
- Perfect for hackathons, demos, learning
- Easy to setup and manage

### For Small Production (After Free Tier)
✅ **Use Strategy 2: Low-Cost Production**
- Cost: $35-40/month
- Good performance for small workloads
- Simple architecture

### For Enterprise Production
✅ **Use Original Full AWS Deployment**
- Cost: $590-880/month
- High availability, auto-scaling
- Production-grade monitoring

---

## Quick Start: Free Tier Deployment

```bash
# 1. Create EC2 instance
bash deployment/free-tier/launch-ec2.sh

# 2. SSH into instance
ssh -i your-key.pem ubuntu@<PUBLIC_IP>

# 3. Setup application
bash deployment/free-tier/setup-instance.sh

# 4. Access application
# API: http://<PUBLIC_IP>:8000
# Dashboard: http://<PUBLIC_IP>:8501
```

**Total time**: 30 minutes  
**Total cost**: $0 (first 12 months)

---

## Free Tier Limits to Watch

### EC2 Free Tier (12 months)
- ✅ 750 hours/month of t2.micro or t3.micro
- ✅ 30GB EBS storage
- ✅ 15GB data transfer out
- ⚠️ **Expires after 12 months**

### Always Free Services
- ✅ Lambda: 1M requests/month
- ✅ DynamoDB: 25GB storage
- ✅ CloudWatch: 10 metrics
- ✅ S3: 5GB storage (first 12 months)

### Not Free (Common Mistakes)
- ❌ Elastic IP (if not attached to running instance)
- ❌ EBS snapshots (after 1GB)
- ❌ Data transfer between regions
- ❌ NAT Gateway
- ❌ Load Balancers

---

## Cost Monitoring

### Setup Billing Alerts

```bash
# Create SNS topic for billing alerts
aws sns create-topic --name billing-alerts

# Subscribe to alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:billing-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Create billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name billing-alert-10-dollars \
  --alarm-description "Alert when bill exceeds $10" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:billing-alerts
```

### Check Current Costs

```bash
# View current month costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost
```

---

## Summary

### Free Tier Reality
- ❌ **Amazon MSK**: NOT free ($150+/month)
- ❌ **ElastiCache**: NOT free ($15-40/month)
- ❌ **NAT Gateway**: NOT free ($33-100/month)
- ❌ **ALB**: NOT free ($16-25/month)
- ✅ **EC2 t3.micro**: FREE for 12 months
- ✅ **RDS db.t2.micro**: FREE for 12 months (750 hours)
- ✅ **S3**: 5GB FREE for 12 months

### Best Options
1. **Free Tier EC2** (Year 1): $0/month
2. **Low-Cost Production** (After Year 1): $35-40/month
3. **Full Production** (Enterprise): $590-880/month

**Recommendation**: Start with Free Tier EC2, then upgrade as needed.

---

**Last Updated**: February 2026  
**Version**: 1.0.0  
**Status**: Free Tier Optimized
