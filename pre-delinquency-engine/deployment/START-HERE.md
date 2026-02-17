# 🚀 START HERE - AWS Free Tier Deployment

> Deploy your Pre-Delinquency Engine to AWS in 20 minutes for **$0/month**

## Quick Links

- **Quick Deploy**: [DEPLOY-NOW.md](free-tier/DEPLOY-NOW.md) - Step-by-step guide
- **Full Documentation**: [README.md](free-tier/README.md) - Complete reference
- **Checklist**: [DEPLOYMENT-CHECKLIST.md](DEPLOYMENT-CHECKLIST.md) - Verification steps

## What You're Deploying

A complete real-time ML system that:
- Processes transactions in real-time
- Predicts customer delinquency risk
- Triggers proactive interventions
- Provides API and dashboard

## Cost

- **First 12 months**: $0/month (AWS Free Tier)
- **After 12 months**: ~$10-15/month

## Prerequisites

1. AWS Account (Free Tier eligible)
2. AWS CLI installed: `pip install awscli`
3. AWS credentials configured: `aws configure`

## Deployment (5 Commands)

```bash
# 1. Launch EC2 instance
cd deployment/free-tier
bash 1-launch-ec2.sh

# 2. Copy scripts (replace <PUBLIC_IP>)
scp -i pre-delinquency-key.pem *.sh ubuntu@<PUBLIC_IP>:~/

# 3. SSH into instance
ssh -i pre-delinquency-key.pem ubuntu@<PUBLIC_IP>

# 4. Setup (on EC2 instance)
bash 2-setup-instance.sh
bash 3-initialize-data.sh
bash 4-start-pipeline.sh

# 5. Access your application
# API: http://<PUBLIC_IP>:8000
# Dashboard: http://<PUBLIC_IP>:8501
```

## What Gets Deployed

```
EC2 t3.micro Instance (Free Tier)
├── PostgreSQL (database)
├── Redis (cache)
├── Kafka (message broker)
├── FastAPI (API service)
├── Streamlit (dashboard)
└── Workers (real-time processing)
```

## After Deployment

Your application will be live at:
- **API**: `http://<PUBLIC_IP>:8000`
- **API Docs**: `http://<PUBLIC_IP>:8000/docs`
- **Dashboard**: `http://<PUBLIC_IP>:8501`

## Need Help?

1. **Quick Start**: Read [DEPLOY-NOW.md](free-tier/DEPLOY-NOW.md)
2. **Full Guide**: Read [README.md](free-tier/README.md)
3. **Troubleshooting**: Check [DEPLOYMENT-CHECKLIST.md](DEPLOYMENT-CHECKLIST.md)

## Alternative Deployments

- **Full Production**: See [phase-7-aws-deployment.md](../../phase-7-aws-deployment.md)
- **Free Tier Guide**: See [phase-7-aws-deployment-free-tier.md](../../phase-7-aws-deployment-free-tier.md)

---

**Ready to deploy? Start with [DEPLOY-NOW.md](free-tier/DEPLOY-NOW.md)** 🚀
