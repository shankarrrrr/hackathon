# Deploy to AWS Free Tier - Simplest Method

> **Deploy the entire Pre-Delinquency Engine on a single EC2 instance for $0/month (first 12 months)**

## Prerequisites

- AWS Account (with free tier available)
- AWS CLI installed and configured
- SSH key pair created in AWS

## Total Time: 20 minutes
## Total Cost: $0 (first 12 months), then ~$10-15/month

---

## Step 1: Launch EC2 Instance (5 minutes)

### Option A: Using AWS Console (Easiest)

1. Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2/)
2. Click "Launch Instance"
3. Configure:
   - **Name**: `pre-delinquency-engine`
   - **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance type**: `t2.micro` or `t3.micro` (Free tier eligible)
   - **Key pair**: Select or create new
   - **Network settings**: 
     - Allow SSH (port 22)
     - Allow HTTP (port 80)
     - Allow Custom TCP (port 8000) - for API
     - Allow Custom TCP (port 8501) - for Dashboard
   - **Storage**: 30 GB gp3 (Free tier eligible)
4. Click "Launch Instance"
5. Wait 2-3 minutes for instance to start
6. Note the **Public IPv4 address**

### Option B: Using AWS CLI (Faster)

```bash
# Create security group
aws ec2 create-security-group \
  --group-name pre-delinquency-sg \
  --description "Pre-Delinquency Engine"

# Get security group ID
SG_ID=$(aws ec2 describe-security-groups \
  --group-names pre-delinquency-sg \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

# Allow inbound traffic
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8501 --cidr 0.0.0.0/0

# Launch instance (replace YOUR-KEY-NAME)
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t2.micro \
  --key-name YOUR-KEY-NAME \
  --security-group-ids $SG_ID \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=pre-delinquency-engine}]'
```

---

## Step 2: Connect to Instance (1 minute)

```bash
# Replace with your key file and public IP
ssh -i your-key.pem ubuntu@YOUR-PUBLIC-IP
```

---

## Step 3: Run Setup Script (10 minutes)

Copy and paste this entire script into your SSH session:

```bash
#!/bin/bash
set -e

echo "🚀 Setting up Pre-Delinquency Engine..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "📦 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
rm get-docker.sh

# Install Docker Compose
echo "📦 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python and Git
sudo apt-get install -y python3-pip python3-venv git

# Clone repository
echo "📥 Cloning repository..."
cd ~
git clone https://github.com/YOUR-USERNAME/pre-delinquency-engine.git
cd pre-delinquency-engine

# Create environment file
echo "⚙️ Creating environment file..."
cat > .env << 'EOF'
DATABASE_URL=postgresql://admin:admin123@postgres:5432/bank_data
REDIS_URL=redis://:redis123@redis:6379
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENVIRONMENT=production
EOF

# Start Docker services
echo "🐳 Starting Docker services..."
newgrp docker << DOCKERCMD
docker-compose up -d
DOCKERCMD

# Wait for services
echo "⏳ Waiting for services to start (60 seconds)..."
sleep 60

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python3 -m src.data_generation.check_db

# Generate synthetic data
echo "📊 Generating synthetic data..."
python3 -m src.data_generation.synthetic_data

# Train model
echo "🤖 Training ML model..."
python3 -m src.models.quick_train

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access your application:"
echo "   API: http://$PUBLIC_IP:8000"
echo "   API Docs: http://$PUBLIC_IP:8000/docs"
echo "   Dashboard: http://$PUBLIC_IP:8501"
echo ""
echo "🚀 Start the services:"
echo "   cd ~/pre-delinquency-engine"
echo "   python3 -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 &"
echo "   streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 &"
echo ""
```

---

## Step 4: Start Services (2 minutes)

```bash
cd ~/pre-delinquency-engine

# Start API (in background)
nohup python3 -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &

# Start Dashboard (in background)
nohup streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &

# Start streaming pipeline (optional)
nohup python3 run_streaming_pipeline.py > streaming.log 2>&1 &
```

---

## Step 5: Access Your Application

Open in your browser:

- **API**: `http://YOUR-PUBLIC-IP:8000`
- **API Documentation**: `http://YOUR-PUBLIC-IP:8000/docs`
- **Dashboard**: `http://YOUR-PUBLIC-IP:8501`

---

## Verify Everything Works

```bash
# Check API health
curl http://localhost:8000/health

# Check Docker containers
docker ps

# View logs
tail -f api.log
tail -f dashboard.log
```

---

## Cost Breakdown

| Service | Configuration | Free Tier | Monthly Cost |
|---------|--------------|-----------|--------------|
| EC2 | t2.micro (1 vCPU, 1GB RAM) | 750 hours | **$0** |
| EBS | 30GB gp3 volume | 30GB free | **$0** |
| Data Transfer | First 100GB out | 100GB free | **$0** |
| **Total** | | | **$0/month** |

**After 12 months**: ~$10-15/month

---

## Setup Billing Alert (Recommended)

```bash
# Install AWS CLI on your local machine
aws cloudwatch put-metric-alarm \
  --alarm-name billing-alert-10-dollars \
  --alarm-description "Alert when bill exceeds $10" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## Troubleshooting

### Services not starting?

```bash
# Check Docker
docker ps
docker-compose logs

# Restart services
cd ~/pre-delinquency-engine
docker-compose restart
```

### Can't access from browser?

1. Check security group allows ports 8000 and 8501
2. Check instance is running: `aws ec2 describe-instances`
3. Verify services are running: `ps aux | grep python`

### Out of memory?

```bash
# Check memory usage
free -h

# Restart services one at a time
pkill -f uvicorn
pkill -f streamlit
# Then start them again
```

---

## Stop Services (to save resources)

```bash
# Stop application
pkill -f uvicorn
pkill -f streamlit
pkill -f run_streaming_pipeline

# Stop Docker
docker-compose down

# Stop EC2 instance (from AWS Console or CLI)
aws ec2 stop-instances --instance-ids YOUR-INSTANCE-ID
```

---

## Clean Up (when done)

```bash
# Terminate instance
aws ec2 terminate-instances --instance-ids YOUR-INSTANCE-ID

# Delete security group
aws ec2 delete-security-group --group-id YOUR-SG-ID
```

---

## Next Steps

1. **Add HTTPS**: Use [Let's Encrypt](https://letsencrypt.org/) with Nginx
2. **Custom Domain**: Point your domain to the EC2 IP
3. **Monitoring**: Setup CloudWatch alarms
4. **Backups**: Enable EBS snapshots
5. **Scale Up**: Upgrade to t3.small when needed

---

## Summary

✅ Single EC2 instance running everything  
✅ All services in Docker containers  
✅ $0/month for first 12 months  
✅ 20 minutes total setup time  
✅ Perfect for demos and learning  

**Need help?** Check the full documentation in `phase-7-aws-deployment-free-tier.md`

---

**Last Updated**: February 2026  
**Version**: 1.0.0
