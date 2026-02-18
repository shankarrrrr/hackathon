# Deploy to AWS from WSL Ubuntu

> **Deploy Pre-Delinquency Engine to AWS Free Tier from Windows WSL**

## Prerequisites

1. Windows with WSL Ubuntu installed
2. AWS Account with free tier available
3. AWS CLI configured in WSL

---

## Step 1: Setup WSL Environment (5 minutes)

Open WSL Ubuntu terminal and run:

```bash
# Update WSL Ubuntu
sudo apt update && sudo apt upgrade -y

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt install unzip -y
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Verify installation
aws --version
```

---

## Step 2: Configure AWS CLI (2 minutes)

```bash
# Configure AWS credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: us-east-1
# Default output format: json
```

**Get AWS credentials:**
1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Click your name → Security Credentials
3. Create Access Key → CLI
4. Copy Access Key ID and Secret Access Key

---

## Step 3: Create SSH Key Pair (2 minutes)

```bash
# Create SSH key in AWS
aws ec2 create-key-pair \
  --key-name pre-delinquency-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/pre-delinquency-key.pem

# Set correct permissions
chmod 400 ~/.ssh/pre-delinquency-key.pem

# Verify key was created
aws ec2 describe-key-pairs --key-names pre-delinquency-key
```

---

## Step 4: Run Deployment Script (10 minutes)

```bash
# Navigate to project directory
cd /mnt/c/Users/YOUR-USERNAME/path/to/hackathon/pre-delinquency-engine

# Make script executable
chmod +x deploy-aws.sh

# Run deployment
./deploy-aws.sh
```

**When prompted, enter:**
- SSH key pair name: `pre-delinquency-key`
- GitHub username: `your-github-username`
- GitHub repo name: `pre-delinquency-engine` (or press Enter for default)

The script will:
1. ✅ Create security group
2. ✅ Launch EC2 t2.micro instance
3. ✅ Install Docker and dependencies
4. ✅ Clone your repository
5. ✅ Start all services
6. ✅ Generate data and train model

---

## Step 5: Access Your Application

After deployment completes, you'll see:

```
🎉 Deployment Complete!

Access Your Application:
  API: http://YOUR-IP:8000
  API Docs: http://YOUR-IP:8000/docs
  Dashboard: http://YOUR-IP:8501
```

Open these URLs in your Windows browser!

---

## Alternative: Manual Deployment (if script fails)

### Option A: Deploy Using AWS Console

1. **Launch EC2 Instance:**
   - Go to [EC2 Console](https://console.aws.amazon.com/ec2/)
   - Click "Launch Instance"
   - Name: `pre-delinquency-engine`
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: `t2.micro` (Free tier)
   - Key pair: `pre-delinquency-key`
   - Security group: Allow ports 22, 80, 8000, 8501
   - Storage: 30 GB gp3
   - Click "Launch Instance"

2. **Connect via WSL:**
   ```bash
   # Get instance public IP from AWS Console
   ssh -i ~/.ssh/pre-delinquency-key.pem ubuntu@YOUR-PUBLIC-IP
   ```

3. **Run setup on instance:**
   ```bash
   # Copy and paste this entire block:
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker ubuntu
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # Install Python and Git
   sudo apt install -y python3-pip python3-venv git
   
   # Clone repository (replace with your repo)
   git clone https://github.com/YOUR-USERNAME/pre-delinquency-engine.git
   cd pre-delinquency-engine
   
   # Create .env file
   cat > .env << 'EOF'
   DATABASE_URL=postgresql://admin:admin123@postgres:5432/bank_data
   REDIS_URL=redis://:redis123@redis:6379
   KAFKA_BOOTSTRAP_SERVERS=kafka:9092
   ENVIRONMENT=production
   EOF
   
   # Start Docker services
   newgrp docker << DOCKERCMD
   docker-compose up -d
   DOCKERCMD
   
   # Wait for services
   sleep 60
   
   # Install Python dependencies
   pip3 install -r requirements.txt
   
   # Initialize database
   python3 -m src.data_generation.check_db
   
   # Generate data
   python3 -m src.data_generation.synthetic_data
   
   # Train model
   python3 -m src.models.quick_train
   
   # Start API
   nohup python3 -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
   
   # Start Dashboard
   nohup streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &
   
   echo "✅ Setup complete!"
   echo "API: http://$(curl -s ifconfig.me):8000"
   echo "Dashboard: http://$(curl -s ifconfig.me):8501"
   ```

### Option B: Local Development in WSL

If you just want to test locally without AWS:

```bash
# Navigate to project
cd /mnt/c/Users/YOUR-USERNAME/path/to/hackathon/pre-delinquency-engine

# Install Docker in WSL (if not already)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Restart WSL or run
newgrp docker

# Start services
docker-compose up -d

# Wait for services
sleep 60

# Install Python dependencies
pip3 install -r requirements.txt

# Initialize database
python3 -m src.data_generation.check_db

# Generate data
python3 -m src.data_generation.synthetic_data

# Train model
python3 -m src.models.quick_train

# Start API
python3 -m uvicorn src.serving.api:app --reload --host 0.0.0.0 --port 8000 &

# Start Dashboard
streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 &

# Access from Windows browser
# API: http://localhost:8000
# Dashboard: http://localhost:8501
```

---

## Troubleshooting

### AWS CLI not found after installation
```bash
# Add to PATH
echo 'export PATH=/usr/local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Permission denied when running script
```bash
chmod +x deploy-aws.sh
```

### SSH connection refused
```bash
# Wait 30 seconds after instance launch
# Check security group allows port 22
aws ec2 describe-security-groups --group-ids YOUR-SG-ID
```

### Docker permission denied in WSL
```bash
sudo usermod -aG docker $USER
newgrp docker
# Or restart WSL
```

### Can't access from Windows browser
```bash
# Make sure services bind to 0.0.0.0, not 127.0.0.1
# Check WSL IP
ip addr show eth0 | grep inet

# Access using WSL IP from Windows
# http://WSL-IP:8000
```

### Script fails at GitHub clone
```bash
# Make sure your repo is public, or setup SSH keys
# Or manually clone after SSH into instance
```

---

## Useful Commands

### Check deployment status
```bash
# From WSL, SSH into instance
ssh -i ~/.ssh/pre-delinquency-key.pem ubuntu@YOUR-PUBLIC-IP

# Check Docker containers
docker ps

# Check API logs
tail -f ~/pre-delinquency-engine/api.log

# Check Dashboard logs
tail -f ~/pre-delinquency-engine/dashboard.log

# Check if services are running
curl http://localhost:8000/health
```

### Stop/Start instance
```bash
# Stop instance (from WSL)
aws ec2 stop-instances --instance-ids YOUR-INSTANCE-ID

# Start instance
aws ec2 start-instances --instance-ids YOUR-INSTANCE-ID

# Get new public IP after start
aws ec2 describe-instances --instance-ids YOUR-INSTANCE-ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text
```

### Clean up
```bash
# Terminate instance
aws ec2 terminate-instances --instance-ids YOUR-INSTANCE-ID

# Delete security group (after instance terminates)
aws ec2 delete-security-group --group-id YOUR-SG-ID

# Delete key pair
aws ec2 delete-key-pair --key-name pre-delinquency-key
rm ~/.ssh/pre-delinquency-key.pem
```

---

## Cost Monitoring

```bash
# Setup billing alert
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

# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost
```

---

## Summary

✅ Deploy from WSL Ubuntu using bash script  
✅ Single command deployment  
✅ $0/month for first 12 months  
✅ Access from Windows browser  
✅ Full Docker environment on EC2  

**Total time:** 20 minutes  
**Total cost:** $0 (first year)

---

**Need help?** Check:
- `DEPLOY-AWS-FREE-TIER.md` - Detailed AWS guide
- `README.md` - Project documentation
- `QUICK-START.md` - Quick reference

---

**Last Updated:** February 2026  
**Version:** 1.0.0
