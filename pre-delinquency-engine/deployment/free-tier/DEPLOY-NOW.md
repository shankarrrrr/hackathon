# 🚀 Deploy to AWS Free Tier NOW - Quick Guide

> **Total Time**: 20 minutes | **Cost**: $0 (first 12 months)

## Prerequisites Check

Before you start, make sure you have:

- [ ] AWS Account (with Free Tier eligibility)
- [ ] AWS CLI installed (`pip install awscli`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Terminal/Command Prompt open

## Step-by-Step Deployment

### 1️⃣ Launch EC2 Instance (3 minutes)

```bash
cd hackathon/pre-delinquency-engine/deployment/free-tier
bash 1-launch-ec2.sh
```

**What happens:**
- Creates t3.micro EC2 instance
- Sets up security groups
- Creates SSH key pair
- Outputs public IP address

**Save this information:**
- Public IP: `_________________`
- Key file: `pre-delinquency-key.pem`

---

### 2️⃣ Copy Scripts to Instance (1 minute)

Replace `<PUBLIC_IP>` with your IP from Step 1:

```bash
scp -i pre-delinquency-key.pem 2-setup-instance.sh ubuntu@<PUBLIC_IP>:~/
scp -i pre-delinquency-key.pem 3-initialize-data.sh ubuntu@<PUBLIC_IP>:~/
scp -i pre-delinquency-key.pem 4-start-pipeline.sh ubuntu@<PUBLIC_IP>:~/
```

---

### 3️⃣ SSH into Instance (30 seconds)

```bash
ssh -i pre-delinquency-key.pem ubuntu@<PUBLIC_IP>
```

You should now be connected to your EC2 instance!

---

### 4️⃣ Setup Application (10 minutes)

Run this command on the EC2 instance:

```bash
bash 2-setup-instance.sh
```

**What happens:**
- Installs Docker and Docker Compose
- Clones repository (you'll be asked for the repo URL)
- Builds and starts all services

**⏳ This takes ~10 minutes. Go grab a coffee!**

---

### 5️⃣ Initialize Data (5 minutes)

Still on the EC2 instance:

```bash
bash 3-initialize-data.sh
```

**What happens:**
- Creates database schema
- Generates 1,000 customers and transactions
- Trains ML model
- Creates Kafka topics

---

### 6️⃣ Start Streaming Pipeline (1 minute)

```bash
bash 4-start-pipeline.sh
```

**What happens:**
- Starts transaction simulator
- Starts feature processor
- Starts intervention worker
- Begins real-time processing

---

## ✅ Deployment Complete!

Your application is now live at:

- **API**: `http://<PUBLIC_IP>:8000`
- **API Docs**: `http://<PUBLIC_IP>:8000/docs`
- **Dashboard**: `http://<PUBLIC_IP>:8501`

## Quick Tests

### Test 1: API Health Check

```bash
curl http://<PUBLIC_IP>:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### Test 2: View Statistics

```bash
curl http://<PUBLIC_IP>:8000/stats
```

### Test 3: Open Dashboard

Open in your browser:
```
http://<PUBLIC_IP>:8501
```

## What's Running?

Your EC2 instance is now running:

1. **PostgreSQL** - Storing customer data, transactions, predictions
2. **Redis** - Caching for fast lookups
3. **Kafka** - Real-time event streaming
4. **API** - FastAPI serving predictions
5. **Dashboard** - Streamlit visualization
6. **Workers** - Processing transactions and triggering interventions

## Monitor Your Application

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Just API
docker-compose -f docker-compose.prod.yml logs -f api

# Pipeline
tail -f ~/pre-delinquency-engine/pipeline.log
```

### Check Service Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

### View Recent Predictions

```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT customer_id, risk_score, risk_level, score_date FROM risk_scores ORDER BY score_date DESC LIMIT 10;"
```

### View Interventions

```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT customer_id, intervention_type, channel, timestamp FROM interventions ORDER BY timestamp DESC LIMIT 10;"
```

## Troubleshooting

### Problem: Can't connect to instance

**Solution:**
```bash
# Check instance status
aws ec2 describe-instances --instance-ids <INSTANCE_ID>

# Check security group allows your IP
aws ec2 describe-security-groups --group-ids <SG_ID>
```

### Problem: Services won't start

**Solution:**
```bash
# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Problem: Out of memory

**Solution:**
```bash
# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Problem: API returns errors

**Solution:**
```bash
# Check API logs
docker-compose -f docker-compose.prod.yml logs api

# Restart API
docker-compose -f docker-compose.prod.yml restart api
```

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

## Cleanup (When Done)

### Stop Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### Terminate Instance

```bash
# From your local machine
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>
```

## Next Steps

Now that your application is deployed:

1. **Explore the API**: Visit `http://<PUBLIC_IP>:8000/docs`
2. **View the Dashboard**: Open `http://<PUBLIC_IP>:8501`
3. **Monitor real-time events**: Check the logs
4. **Test predictions**: Use the API to score customers
5. **View interventions**: See which customers are being contacted

## Performance Tips

### Optimize for t3.micro

The deployment is already optimized, but you can:

1. **Reduce Kafka retention**: Edit `docker-compose.prod.yml`
2. **Limit data generation**: Generate fewer customers
3. **Adjust worker frequency**: Slow down transaction simulation

### Upgrade Instance

If you need more performance:

```bash
# Stop instance
aws ec2 stop-instances --instance-ids <INSTANCE_ID>

# Change instance type
aws ec2 modify-instance-attribute \
  --instance-id <INSTANCE_ID> \
  --instance-type t3.small

# Start instance
aws ec2 start-instances --instance-ids <INSTANCE_ID>
```

## Security Checklist

- [ ] Change default passwords in `docker-compose.prod.yml`
- [ ] Restrict SSH access to your IP only
- [ ] Set up HTTPS with Let's Encrypt
- [ ] Enable AWS CloudWatch monitoring
- [ ] Set up billing alerts
- [ ] Regular backups of database

## Support

Need help?

1. Check `README.md` for detailed documentation
2. Review logs for error messages
3. Check AWS documentation
4. Create an issue in the repository

---

## Summary

✅ **Deployed**: Pre-Delinquency Engine on AWS Free Tier  
✅ **Cost**: $0/month (first 12 months)  
✅ **Time**: 20 minutes  
✅ **Services**: All running and operational  
✅ **Access**: API and Dashboard available  

**Your application is now live and processing transactions in real-time!** 🎉

---

**Last Updated**: February 2026  
**Version**: 1.0.0
