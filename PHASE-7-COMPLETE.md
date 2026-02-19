# ✅ Phase 7: AWS Deployment - COMPLETE

## What Was Created

All deployment files and scripts for AWS Free Tier deployment have been created and are ready to use.

## Files Created

### 📁 Deployment Scripts (`hackathon/pre-delinquency-engine/deployment/free-tier/`)

1. **1-launch-ec2.sh** - Launches Free Tier EC2 instance
   - Creates t3.micro instance
   - Sets up security groups
   - Creates SSH key pair
   - Outputs connection info

2. **2-setup-instance.sh** - Sets up the EC2 instance
   - Installs Docker & Docker Compose
   - Clones repository
   - Builds and starts all services

3. **3-initialize-data.sh** - Initializes data
   - Creates database schema
   - Generates synthetic data
   - Trains ML model
   - Creates Kafka topics

4. **4-start-pipeline.sh** - Starts streaming pipeline
   - Launches transaction simulator
   - Starts feature processor
   - Starts intervention worker

### 📚 Documentation

1. **DEPLOY-NOW.md** - Quick deployment guide (20 minutes)
2. **README.md** - Complete documentation with troubleshooting
3. **DEPLOYMENT-CHECKLIST.md** - Step-by-step verification checklist
4. **START-HERE.md** - Entry point with quick links

### 📄 Additional Guides

1. **phase-7-aws-deployment.md** - Full production deployment ($590-880/month)
2. **phase-7-aws-deployment-free-tier.md** - Free Tier optimization guide

## How to Deploy NOW

### Option 1: Quick Deploy (Recommended)

```bash
cd hackathon/pre-delinquency-engine/deployment/free-tier

# Follow the guide
cat DEPLOY-NOW.md
```

### Option 2: Step-by-Step with Checklist

```bash
cd hackathon/pre-delinquency-engine/deployment

# Follow the checklist
cat DEPLOYMENT-CHECKLIST.md
```

## Deployment Summary

### What You Get

- ✅ Complete ML system running on AWS
- ✅ Real-time transaction processing
- ✅ API with auto-generated docs
- ✅ Interactive dashboard
- ✅ All services containerized
- ✅ Production-ready setup

### Cost

- **First 12 months**: $0/month (AWS Free Tier)
- **After 12 months**: ~$10-15/month

### Time Required

- **Setup**: 20 minutes
- **Learning curve**: Minimal (scripts do everything)

### Architecture

```
EC2 t3.micro (1 vCPU, 1GB RAM, 30GB Storage)
├── PostgreSQL (256MB) - Database
├── Redis (128MB) - Cache
├── Kafka (384MB) - Message Broker
├── Zookeeper (128MB) - Kafka Coordination
├── API (256MB) - FastAPI Service
└── Dashboard (256MB) - Streamlit UI
```

## Quick Start Commands

```bash
# 1. Navigate to deployment directory
cd hackathon/pre-delinquency-engine/deployment/free-tier

# 2. Launch EC2 instance (3 minutes)
bash 1-launch-ec2.sh

# 3. Copy scripts to instance (1 minute)
# Replace <PUBLIC_IP> with your IP from step 2
scp -i pre-delinquency-key.pem 2-setup-instance.sh ubuntu@<PUBLIC_IP>:~/
scp -i pre-delinquency-key.pem 3-initialize-data.sh ubuntu@<PUBLIC_IP>:~/
scp -i pre-delinquency-key.pem 4-start-pipeline.sh ubuntu@<PUBLIC_IP>:~/

# 4. SSH into instance
ssh -i pre-delinquency-key.pem ubuntu@<PUBLIC_IP>

# 5. Run setup (on EC2 instance - 10 minutes)
bash 2-setup-instance.sh

# 6. Initialize data (5 minutes)
bash 3-initialize-data.sh

# 7. Start pipeline (1 minute)
bash 4-start-pipeline.sh

# 8. Access your application
# API: http://<PUBLIC_IP>:8000
# Dashboard: http://<PUBLIC_IP>:8501
```

## Prerequisites

Before deploying, ensure you have:

- [ ] AWS Account (Free Tier eligible)
- [ ] AWS CLI installed: `pip install awscli`
- [ ] AWS credentials configured: `aws configure`
- [ ] Terminal/Command Prompt

## Verification

After deployment, verify:

1. **API Health**: `curl http://<PUBLIC_IP>:8000/health`
2. **API Docs**: Open `http://<PUBLIC_IP>:8000/docs`
3. **Dashboard**: Open `http://<PUBLIC_IP>:8501`
4. **Logs**: `docker-compose -f docker-compose.prod.yml logs -f`

## What's Running

Once deployed, your system will be:

- ✅ Processing transactions in real-time
- ✅ Computing behavioral features
- ✅ Scoring customers with ML model
- ✅ Triggering interventions based on risk
- ✅ Storing all events in PostgreSQL
- ✅ Streaming events through Kafka
- ✅ Serving API requests
- ✅ Displaying dashboard

## Monitoring

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
```

### Check Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### View Data
```bash
# Recent predictions
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT * FROM risk_scores ORDER BY score_date DESC LIMIT 10;"

# Interventions
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT * FROM interventions ORDER BY timestamp DESC LIMIT 10;"
```

## Troubleshooting

### Services Won't Start
```bash
sudo systemctl restart docker
docker-compose -f docker-compose.prod.yml restart
```

### Out of Memory
```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Can't Connect
```bash
# Check instance status
aws ec2 describe-instances --instance-ids <INSTANCE_ID>

# Check security group
aws ec2 describe-security-groups --group-ids <SG_ID>
```

## Security Recommendations

1. **Change default passwords** in `docker-compose.prod.yml`
2. **Restrict SSH access** to your IP only
3. **Set up HTTPS** with Let's Encrypt
4. **Enable billing alerts** to monitor costs
5. **Regular backups** of database

## Cost Monitoring

### Set Up Billing Alert
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name ec2-billing-alert \
  --alarm-description "Alert when costs exceed $5" \
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

## Cleanup

When you're done:

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Terminate instance (from local machine)
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>

# Delete security group
aws ec2 delete-security-group --group-id <SG_ID>

# Delete key pair
aws ec2 delete-key-pair --key-name pre-delinquency-key
rm pre-delinquency-key.pem
```

## Next Steps

1. **Deploy Now**: Follow `deployment/free-tier/DEPLOY-NOW.md`
2. **Explore API**: Visit `http://<PUBLIC_IP>:8000/docs`
3. **View Dashboard**: Open `http://<PUBLIC_IP>:8501`
4. **Monitor System**: Check logs and metrics
5. **Customize**: Modify intervention strategies

## Alternative Deployments

If you need more than Free Tier:

- **Low-Cost Production** ($35-40/month): Use t3.small + RDS
- **Full Production** ($590-880/month): Use ECS Fargate + MSK + ElastiCache
- **Serverless** ($20-50/month): Use Lambda + API Gateway + DynamoDB

See `phase-7-aws-deployment.md` for full production deployment.

## Support

Need help?

1. Check `deployment/free-tier/README.md` for detailed docs
2. Review `deployment/free-tier/DEPLOY-NOW.md` for quick guide
3. Use `DEPLOYMENT-CHECKLIST.md` for verification
4. Check logs for error messages
5. Review AWS documentation

## Summary

✅ **Phase 7 Complete**: All deployment files created  
✅ **Ready to Deploy**: Scripts are ready to run  
✅ **Cost**: $0/month for first 12 months  
✅ **Time**: 20 minutes to deploy  
✅ **Difficulty**: Easy (scripts do everything)  

**You're ready to deploy to AWS! Start with `deployment/free-tier/DEPLOY-NOW.md`** 🚀

---

**Status**: Phase 7 Complete  
**Last Updated**: February 2026  
**Version**: 1.0.0
