# Free Tier EC2 Deployment Guide

> Deploy Pre-Delinquency Engine to AWS Free Tier EC2 for **$0/month** (first 12 months)

## Overview

This deployment uses a single t3.micro EC2 instance running all services via Docker Compose. It's perfect for:
- Demos and presentations
- Learning and development
- Proof of concept
- Low-traffic production (< 100 requests/minute)

## Cost

- **First 12 months**: $0/month (AWS Free Tier)
- **After 12 months**: ~$10-15/month

## Prerequisites

1. **AWS Account** with Free Tier eligibility
2. **AWS CLI** installed and configured
   ```bash
   pip install awscli
   aws configure
   ```
3. **SSH client** (built-in on Mac/Linux, use PuTTY on Windows)

## Quick Start (5 Steps)

### Step 1: Launch EC2 Instance

```bash
cd hackathon/pre-delinquency-engine/deployment/free-tier
bash 1-launch-ec2.sh
```

**What this does:**
- Creates a t3.micro EC2 instance (Free Tier eligible)
- Sets up security groups (ports 22, 80, 443, 8000, 8501)
- Creates SSH key pair
- Waits for instance to be ready

**Time**: ~3 minutes

**Output**: You'll get the public IP address and SSH command

### Step 2: Copy Setup Script to Instance

```bash
# Use the IP from Step 1
scp -i pre-delinquency-key.pem 2-setup-instance.sh ubuntu@<PUBLIC_IP>:~/
scp -i pre-delinquency-key.pem 3-initialize-data.sh ubuntu@<PUBLIC_IP>:~/
scp -i pre-delinquency-key.pem 4-start-pipeline.sh ubuntu@<PUBLIC_IP>:~/
```

### Step 3: SSH into Instance

```bash
ssh -i pre-delinquency-key.pem ubuntu@<PUBLIC_IP>
```

### Step 4: Run Setup Script

```bash
bash 2-setup-instance.sh
```

**What this does:**
- Installs Docker and Docker Compose
- Clones your repository
- Builds and starts all services (PostgreSQL, Kafka, Redis, API, Dashboard)

**Time**: ~10 minutes

### Step 5: Initialize Data and Start Pipeline

```bash
# Initialize database and generate data
bash 3-initialize-data.sh

# Start streaming pipeline
bash 4-start-pipeline.sh
```

**Time**: ~5 minutes

## Access Your Application

After deployment, access your application at:

- **API**: `http://<PUBLIC_IP>:8000`
- **API Docs**: `http://<PUBLIC_IP>:8000/docs`
- **Dashboard**: `http://<PUBLIC_IP>:8501`

## Architecture

```
┌─────────────────────────────────────────┐
│     EC2 t3.micro (1 vCPU, 1GB RAM)      │
│     30GB EBS Storage                     │
├─────────────────────────────────────────┤
│  Docker Compose Services:               │
│  ├─ PostgreSQL (256MB)                  │
│  ├─ Redis (128MB)                       │
│  ├─ Kafka + Zookeeper (512MB)           │
│  ├─ API (256MB)                         │
│  └─ Dashboard (256MB)                   │
└─────────────────────────────────────────┘
```

## Resource Optimization

The deployment is optimized for t3.micro (1GB RAM):

| Service | CPU Limit | Memory Limit | Purpose |
|---------|-----------|--------------|---------|
| PostgreSQL | 0.25 | 256MB | Database |
| Redis | 0.1 | 128MB | Cache |
| Kafka | 0.2 | 384MB | Message broker |
| Zookeeper | 0.1 | 128MB | Kafka coordination |
| API | 0.25 | 256MB | FastAPI service |
| Dashboard | 0.15 | 256MB | Streamlit UI |

**Total**: ~1.4GB (with overhead, fits in 1GB with swap)

## Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api

# Pipeline logs
tail -f ~/pre-delinquency-engine/pipeline.log
```

### Check Service Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Monitor Kafka Messages

```bash
# Transactions
docker-compose -f docker-compose.prod.yml exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic transactions-stream \
  --from-beginning \
  --max-messages 5

# Predictions
docker-compose -f docker-compose.prod.yml exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic predictions-stream \
  --from-beginning \
  --max-messages 5

# Interventions
docker-compose -f docker-compose.prod.yml exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interventions-stream \
  --from-beginning \
  --max-messages 5
```

### Check Database

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data

# View recent predictions
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT customer_id, risk_score, risk_level, score_date FROM risk_scores ORDER BY score_date DESC LIMIT 10;"

# View interventions
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT customer_id, intervention_type, channel, timestamp FROM interventions ORDER BY timestamp DESC LIMIT 10;"
```

## Troubleshooting

### Services Won't Start

```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Out of Memory

```bash
# Check memory usage
free -h

# Add swap space (if needed)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Can't Connect to Instance

```bash
# Check security group
aws ec2 describe-security-groups --group-ids <SG_ID>

# Check instance status
aws ec2 describe-instances --instance-ids <INSTANCE_ID>

# Check SSH key permissions
chmod 400 pre-delinquency-key.pem
```

### API Not Responding

```bash
# Check API logs
docker-compose -f docker-compose.prod.yml logs api

# Restart API
docker-compose -f docker-compose.prod.yml restart api

# Check if port is open
curl http://localhost:8000/health
```

## Maintenance

### Update Application

```bash
cd ~/pre-delinquency-engine
git pull
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Backup Database

```bash
# Backup to file
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U admin bank_data > backup.sql

# Copy to local machine
scp -i pre-delinquency-key.pem ubuntu@<PUBLIC_IP>:~/pre-delinquency-engine/backup.sql ./
```

### Restore Database

```bash
# Copy backup to instance
scp -i pre-delinquency-key.pem backup.sql ubuntu@<PUBLIC_IP>:~/pre-delinquency-engine/

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U admin bank_data < backup.sql
```

## Cleanup

### Stop Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### Delete EC2 Instance

```bash
# From your local machine
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>

# Delete security group (after instance is terminated)
aws ec2 delete-security-group --group-id <SG_ID>

# Delete key pair
aws ec2 delete-key-pair --key-name pre-delinquency-key
rm pre-delinquency-key.pem
```

## Performance Expectations

On a t3.micro instance:

- **API Response Time**: 200-500ms
- **Throughput**: 10-50 requests/second
- **Concurrent Users**: 5-10
- **Data Processing**: 100-500 transactions/second

For higher performance, upgrade to:
- **t3.small** (2 vCPU, 2GB RAM): $15/month
- **t3.medium** (2 vCPU, 4GB RAM): $30/month

## Security Recommendations

### 1. Restrict SSH Access

```bash
# Update security group to allow SSH only from your IP
aws ec2 authorize-security-group-ingress \
  --group-id <SG_ID> \
  --protocol tcp \
  --port 22 \
  --cidr <YOUR_IP>/32
```

### 2. Use HTTPS

Install Let's Encrypt SSL certificate:

```bash
sudo apt-get install certbot
sudo certbot certonly --standalone -d your-domain.com
```

### 3. Change Default Passwords

Edit `docker-compose.prod.yml` and change:
- PostgreSQL password
- Redis password

### 4. Enable Firewall

```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000
sudo ufw allow 8501
sudo ufw enable
```

## Cost Monitoring

### Set Up Billing Alerts

```bash
# Create billing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ec2-billing-alert \
  --alarm-description "Alert when EC2 costs exceed $5" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### Check Current Costs

```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "$(date +%Y-%m-01)" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost
```

## FAQ

**Q: Will this work after the Free Tier expires?**  
A: Yes, it will cost ~$10-15/month for the t3.micro instance.

**Q: Can I use a custom domain?**  
A: Yes, point your domain's A record to the instance's public IP.

**Q: How do I scale this?**  
A: Upgrade to a larger instance type or migrate to the full AWS deployment with ECS/MSK.

**Q: Is this production-ready?**  
A: It's suitable for low-traffic production (<100 req/min). For high-traffic, use the full deployment.

**Q: Can I stop the instance to save costs?**  
A: Yes, but you'll lose the public IP unless you use an Elastic IP (costs $0.005/hour when not attached).

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs: `docker-compose -f docker-compose.prod.yml logs`
3. Check AWS documentation
4. Create an issue in the repository

---

**Last Updated**: February 2026  
**Version**: 1.0.0  
**Status**: Production Ready
