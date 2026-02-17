# Simple AWS Deployment Guide

Deploy your Pre-Delinquency Engine to AWS in one command!

## Prerequisites

1. **AWS Account** with Free Tier eligibility
2. **AWS CLI** installed: `pip install awscli`
3. **Git Bash** (comes with Git for Windows)
4. **AWS Credentials** configured: `aws configure`

## One-Command Deployment

Open Git Bash and run:

```bash
cd hackathon/pre-delinquency-engine
bash deployment/deploy-to-aws.sh
```

That's it! The script will:
1. ✅ Verify your AWS credentials
2. ✅ Launch a Free Tier EC2 instance
3. ✅ Install Docker and dependencies
4. ✅ Deploy all services
5. ✅ Initialize database with data
6. ✅ Start the streaming pipeline

**Total time:** ~15-20 minutes

## What You Get

After deployment completes, you'll have:

- 🌐 **API Server** running at `http://YOUR_IP:8000`
- 📚 **API Documentation** at `http://YOUR_IP:8000/docs`
- 📊 **Dashboard** at `http://YOUR_IP:8501`
- 🔄 **Real-time streaming pipeline** processing transactions
- 🤖 **ML model** making predictions
- 💾 **PostgreSQL database** with synthetic data

## Quick Test

```bash
# Test API health
curl http://YOUR_IP:8000/health

# Get statistics
curl http://YOUR_IP:8000/stats

# Make a prediction
curl -X POST http://YOUR_IP:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST001"}'
```

## SSH Access

```bash
ssh -i deployment/free-tier/pre-delinquency-key.pem ubuntu@YOUR_IP
```

## Useful Commands

### View Logs
```bash
# All services
ssh -i deployment/free-tier/pre-delinquency-key.pem ubuntu@YOUR_IP \
  'cd pre-delinquency-engine && docker-compose -f docker-compose.prod.yml logs -f'

# Specific service
ssh -i deployment/free-tier/pre-delinquency-key.pem ubuntu@YOUR_IP \
  'cd pre-delinquency-engine && docker-compose -f docker-compose.prod.yml logs -f api'
```

### Restart Services
```bash
ssh -i deployment/free-tier/pre-delinquency-key.pem ubuntu@YOUR_IP \
  'cd pre-delinquency-engine && docker-compose -f docker-compose.prod.yml restart'
```

### Stop Everything
```bash
ssh -i deployment/free-tier/pre-delinquency-key.pem ubuntu@YOUR_IP \
  'cd pre-delinquency-engine && docker-compose -f docker-compose.prod.yml down'
```

## Cost

- **First 12 months:** FREE (AWS Free Tier)
- **After 12 months:** ~$10-15/month for t3.micro instance

## Troubleshooting

### SSH Connection Failed
Wait a few more minutes and try again. EC2 instances can take 2-3 minutes to be fully ready.

### Services Not Starting
SSH into the instance and check logs:
```bash
ssh -i deployment/free-tier/pre-delinquency-key.pem ubuntu@YOUR_IP
cd pre-delinquency-engine
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

### Out of Memory
The t3.micro has 1GB RAM. If services crash, try restarting them one at a time:
```bash
docker-compose -f docker-compose.prod.yml restart postgres
docker-compose -f docker-compose.prod.yml restart redis
docker-compose -f docker-compose.prod.yml restart api
```

## Manual Step-by-Step (if needed)

If the one-command deployment fails, you can run steps manually:

```bash
cd deployment/free-tier

# Step 1: Verify AWS
bash 0-verify-aws.sh

# Step 2: Launch EC2
bash 1-launch-ec2.sh

# Step 3: Copy files to instance
bash copy-files-to-ec2.sh

# Step 4: SSH and setup
ssh -i pre-delinquency-key.pem ubuntu@YOUR_IP
bash 2-setup-instance.sh

# Step 5: Initialize data
bash 3-initialize-data.sh

# Step 6: Start pipeline
bash 4-start-pipeline.sh
```

## Cleanup

To delete everything and stop charges:

```bash
# Get instance ID from instance-info.txt
INSTANCE_ID=$(grep "Instance ID:" deployment/free-tier/instance-info.txt | cut -d' ' -f3)

# Terminate instance
aws ec2 terminate-instances --instance-ids $INSTANCE_ID

# Delete security group (after instance is terminated)
aws ec2 delete-security-group --group-name pre-delinquency-engine-sg

# Delete key pair
aws ec2 delete-key-pair --key-name pre-delinquency-key
rm deployment/free-tier/pre-delinquency-key.pem
```

## Next Steps

1. Open the dashboard at `http://YOUR_IP:8501`
2. Explore the API docs at `http://YOUR_IP:8000/docs`
3. Monitor real-time predictions
4. Customize the ML model
5. Add your own data sources

## Support

For issues or questions:
- Check logs on the instance
- Review the detailed deployment scripts in `deployment/free-tier/`
- Ensure your AWS account has Free Tier eligibility
