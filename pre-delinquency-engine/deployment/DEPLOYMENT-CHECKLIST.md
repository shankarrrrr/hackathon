# 🚀 AWS Free Tier Deployment Checklist

## Pre-Deployment Checklist

### ✅ Prerequisites

- [ ] AWS Account created and verified
- [ ] AWS Free Tier eligible (within first 12 months)
- [ ] AWS CLI installed: `pip install awscli`
- [ ] AWS credentials configured: `aws configure`
- [ ] Git installed
- [ ] Terminal/Command Prompt ready

### ✅ Verify AWS Setup

```bash
# Test AWS CLI
aws sts get-caller-identity

# Check region
aws configure get region
```

Expected output: Your AWS account ID and region

---

## Deployment Steps

### Step 1: Launch EC2 Instance ⏱️ 3 minutes

```bash
cd hackathon/pre-delinquency-engine/deployment/free-tier
bash 1-launch-ec2.sh
```

**Checklist:**
- [ ] Script completed without errors
- [ ] Public IP address displayed
- [ ] SSH key file created (`pre-delinquency-key.pem`)
- [ ] Instance info saved to `instance-info.txt`

**Save this info:**
```
Public IP: ___________________
Instance ID: __________________
```

---

### Step 2: Copy Scripts to Instance ⏱️ 1 minute

```bash
# Replace <PUBLIC_IP> with your IP from Step 1
scp -i pre-delinquency-key.pem 2-setup-instance.sh ubuntu@<PUBLIC_IP>:~/
scp -i pre-delinquency-key.pem 3-initialize-data.sh ubuntu@<PUBLIC_IP>:~/
scp -i pre-delinquency-key.pem 4-start-pipeline.sh ubuntu@<PUBLIC_IP>:~/
```

**Checklist:**
- [ ] All 3 scripts copied successfully
- [ ] No permission errors

---

### Step 3: SSH into Instance ⏱️ 30 seconds

```bash
ssh -i pre-delinquency-key.pem ubuntu@<PUBLIC_IP>
```

**Checklist:**
- [ ] Successfully connected to instance
- [ ] Prompt shows `ubuntu@ip-xxx-xxx-xxx-xxx`

---

### Step 4: Setup Application ⏱️ 10 minutes

**On the EC2 instance:**

```bash
bash 2-setup-instance.sh
```

**Checklist:**
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Repository cloned/created
- [ ] Docker images built
- [ ] All services started
- [ ] No error messages

**Verify services are running:**
```bash
docker-compose -f docker-compose.prod.yml ps
```

All services should show "Up"

---

### Step 5: Initialize Data ⏱️ 5 minutes

```bash
bash 3-initialize-data.sh
```

**Checklist:**
- [ ] Database schema created
- [ ] Kafka topics created
- [ ] Synthetic data generated (1000 customers)
- [ ] ML model trained
- [ ] No error messages

**Verify data:**
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT COUNT(*) FROM customers;"
```

Should show ~1000 customers

---

### Step 6: Start Streaming Pipeline ⏱️ 1 minute

```bash
bash 4-start-pipeline.sh
```

**Checklist:**
- [ ] Pipeline started
- [ ] No error messages
- [ ] Log file created

**Verify pipeline is running:**
```bash
tail -f ~/pre-delinquency-engine/pipeline.log
```

Should see transaction processing messages

---

## Post-Deployment Verification

### ✅ Test API

**From your local machine:**

```bash
# Replace <PUBLIC_IP> with your instance IP
curl http://<PUBLIC_IP>:8000/health
```

**Expected response:**
```json
{"status": "healthy"}
```

**Checklist:**
- [ ] API responds to health check
- [ ] Status is "healthy"

---

### ✅ Test API Documentation

**Open in browser:**
```
http://<PUBLIC_IP>:8000/docs
```

**Checklist:**
- [ ] Swagger UI loads
- [ ] All endpoints visible
- [ ] Can test endpoints

---

### ✅ Test Dashboard

**Open in browser:**
```
http://<PUBLIC_IP>:8501
```

**Checklist:**
- [ ] Dashboard loads
- [ ] Data displays correctly
- [ ] No error messages

---

### ✅ Verify Data Processing

**On EC2 instance:**

```bash
# Check recent predictions
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT COUNT(*) FROM risk_scores;"

# Check interventions
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
  -c "SELECT COUNT(*) FROM interventions;"
```

**Checklist:**
- [ ] Predictions are being created
- [ ] Interventions are being triggered
- [ ] Counts are increasing over time

---

### ✅ Monitor Kafka Messages

```bash
# Check transactions
docker-compose -f docker-compose.prod.yml exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic transactions-stream \
  --from-beginning \
  --max-messages 5

# Check predictions
docker-compose -f docker-compose.prod.yml exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic predictions-stream \
  --from-beginning \
  --max-messages 5
```

**Checklist:**
- [ ] Transactions flowing through Kafka
- [ ] Predictions flowing through Kafka
- [ ] Messages are well-formed JSON

---

## Security Checklist

### ✅ Immediate Security Steps

- [ ] Change default PostgreSQL password
- [ ] Change default Redis password
- [ ] Restrict SSH access to your IP only
- [ ] Set up billing alerts

### ✅ Optional Security Enhancements

- [ ] Set up HTTPS with Let's Encrypt
- [ ] Enable AWS CloudWatch monitoring
- [ ] Configure firewall (ufw)
- [ ] Set up automated backups

---

## Cost Monitoring Checklist

### ✅ Set Up Billing Alerts

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

**Checklist:**
- [ ] Billing alarm created
- [ ] Email notification configured
- [ ] Test alert received

---

## Troubleshooting Checklist

### ❌ If Services Won't Start

```bash
# Check Docker status
sudo systemctl status docker

# Check logs
docker-compose -f docker-compose.prod.yml logs

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### ❌ If Out of Memory

```bash
# Check memory
free -h

# Add swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### ❌ If Can't Connect to Instance

```bash
# Check instance status
aws ec2 describe-instances --instance-ids <INSTANCE_ID>

# Check security group
aws ec2 describe-security-groups --group-ids <SG_ID>
```

---

## Success Criteria

### ✅ Deployment is Successful When:

- [ ] EC2 instance is running
- [ ] All Docker services are up
- [ ] API responds to health checks
- [ ] Dashboard loads in browser
- [ ] Data is being processed
- [ ] Predictions are being made
- [ ] Interventions are being triggered
- [ ] Kafka messages are flowing
- [ ] No error messages in logs

---

## Final Verification

### ✅ Complete System Test

1. **API Test:**
   ```bash
   curl http://<PUBLIC_IP>:8000/stats
   ```
   Should return statistics

2. **Dashboard Test:**
   Open `http://<PUBLIC_IP>:8501` in browser
   Should show visualizations

3. **Real-time Test:**
   Watch logs for 1 minute:
   ```bash
   tail -f ~/pre-delinquency-engine/pipeline.log
   ```
   Should see transactions being processed

4. **Database Test:**
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d bank_data \
     -c "SELECT customer_id, risk_score, risk_level FROM risk_scores ORDER BY score_date DESC LIMIT 5;"
   ```
   Should show recent predictions

---

## Deployment Complete! 🎉

### Your Application URLs:

- **API**: `http://<PUBLIC_IP>:8000`
- **API Docs**: `http://<PUBLIC_IP>:8000/docs`
- **Dashboard**: `http://<PUBLIC_IP>:8501`

### Cost Summary:

- **First 12 months**: $0/month (Free Tier)
- **After 12 months**: ~$10-15/month

### What's Running:

- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Kafka message broker
- ✅ FastAPI service
- ✅ Streamlit dashboard
- ✅ Real-time streaming pipeline

---

## Next Steps

1. **Explore the API**: Try different endpoints
2. **Monitor the system**: Watch logs and metrics
3. **Test predictions**: Score different customers
4. **View interventions**: See triggered actions
5. **Customize**: Modify intervention strategies

---

## Maintenance Checklist

### Daily:
- [ ] Check service status
- [ ] Review logs for errors
- [ ] Monitor resource usage

### Weekly:
- [ ] Backup database
- [ ] Review billing
- [ ] Update application if needed

### Monthly:
- [ ] Review security settings
- [ ] Check for updates
- [ ] Optimize performance

---

## Support

Need help?

1. Check `deployment/free-tier/README.md`
2. Review `deployment/free-tier/DEPLOY-NOW.md`
3. Check logs for error messages
4. Review AWS documentation
5. Create an issue in the repository

---

**Deployment Status**: ✅ Complete  
**Total Time**: ~20 minutes  
**Cost**: $0 (Free Tier)  
**Last Updated**: February 2026
