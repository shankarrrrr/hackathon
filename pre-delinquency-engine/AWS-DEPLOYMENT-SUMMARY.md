# AWS Deployment Summary - Pre-Delinquency Engine

## Deployment Status: ✅ LIVE

**Instance Details:**
- Region: ap-south-1 (Mumbai)
- Instance ID: i-035026df35b6dad7c
- Instance Type: t3.micro (Free Tier)
- Public IP: 15.206.72.35
- Cost: $0/month (first 12 months)

**Access URLs:**
- API: http://15.206.72.35:8000
- API Docs: http://15.206.72.35:8000/docs
- Dashboard: http://15.206.72.35:8501

---

## Services Running

✅ **PostgreSQL** - Running in Docker (port 5432)
✅ **Redis** - Running in Docker (port 6379)
✅ **Kafka** - Running in Docker (port 9092)
✅ **Zookeeper** - Running in Docker (port 2181)
✅ **MLflow** - Running in Docker (port 5000)
✅ **FastAPI** - Running on host (port 8000)
✅ **Streamlit Dashboard** - Running on host (port 8501)

---

## Current Model Status

**Model:** Quick-trained XGBoost
- Location: `data/models/quick/quick_model.json`
- Features: 30 behavioral features
- Training samples: 100 customers
- Performance: Basic (needs improvement with new dataset)

**Database:**
- Customers: 100
- Transactions: Generated
- Risk Scores: 5 predictions created

---

## Next Steps: Enhanced Model Training

### Step 1: Create Behavioral Simulator

The new behavioral simulator is already created at:
`src/data_generation/behavioral_simulator.py`

This will generate:
- 30,000 customers (configurable)
- 12 weeks of behavioral history
- 35+ ML-ready features
- Realistic financial stress patterns
- 8-12% positive class rate

### Step 2: Files to Upload to EC2

You need to upload these files from your local machine to EC2:

1. **Behavioral Simulator:**
   - Local: `hackathon/pre-delinquency-engine/src/data_generation/behavioral_simulator.py`
   - EC2: `~/hackathon-1/pre-delinquency-engine/src/data_generation/behavioral_simulator.py`

2. **Optimized Trainer:**
   - Local: `hackathon/pre-delinquency-engine/src/models/train_optimized.py`
   - EC2: `~/hackathon-1/pre-delinquency-engine/src/models/train_optimized.py`

3. **Pipeline Runner:**
   - Local: `hackathon/pre-delinquency-engine/run_complete_pipeline.py`
   - EC2: `~/hackathon-1/pre-delinquency-engine/run_complete_pipeline.py`

### Step 3: Upload Files via SCP

From your WSL terminal:

```bash
# Navigate to local project
cd "/mnt/c/Users/LENOVO/Desktop/New folder/hackathon/pre-delinquency-engine"

# Upload behavioral simulator
scp -i ~/pre-delinquency-key.pem \
  src/data_generation/behavioral_simulator.py \
  ubuntu@15.206.72.35:~/hackathon-1/pre-delinquency-engine/src/data_generation/

# Upload optimized trainer
scp -i ~/pre-delinquency-key.pem \
  src/models/train_optimized.py \
  ubuntu@15.206.72.35:~/hackathon-1/pre-delinquency-engine/src/models/

# Upload pipeline runner
scp -i ~/pre-delinquency-key.pem \
  run_complete_pipeline.py \
  ubuntu@15.206.72.35:~/hackathon-1/pre-delinquency-engine/
```

### Step 4: Run Training Pipeline on EC2

SSH into EC2 and run:

```bash
# SSH into instance
ssh -i ~/pre-delinquency-key.pem ubuntu@15.206.72.35

# Navigate to project
cd ~/hackathon-1/pre-delinquency-engine

# Run complete pipeline
python3 run_complete_pipeline.py
```

This will:
1. Generate 30K customer behavioral dataset (~5-10 minutes)
2. Run hyperparameter tuning (10 trials, ~10-15 minutes)
3. Train optimized model with best parameters
4. Optimize classification threshold
5. Compute SHAP explainability
6. Save all artifacts

**Total time:** ~20-30 minutes on Free Tier

### Step 5: Update API to Use New Model

After training completes:

```bash
# Stop current API
pkill -f uvicorn

# Update API to use new model (edit if needed)
# The new model will be at: data/models/production/model.json

# Restart API
nohup python3 -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &

# Verify
curl http://localhost:8000/health
```

---

## Alternative: Manual File Creation on EC2

If SCP doesn't work, you can create files directly on EC2 by copying the content.

I can provide the complete file contents in smaller chunks that you can paste directly into the EC2 terminal using `cat > filename << 'EOF'` ... `EOF`.

Would you like me to provide the files this way instead?

---

## Monitoring & Maintenance

**View Logs:**
```bash
# API logs
tail -f ~/hackathon-1/pre-delinquency-engine/api.log

# Dashboard logs
tail -f ~/hackathon-1/pre-delinquency-engine/dashboard.log

# Docker logs
docker-compose logs -f
```

**Check Services:**
```bash
# Running processes
ps aux | grep -E "uvicorn|streamlit"

# Docker containers
docker ps

# Database
docker exec delinquency_db psql -U admin -d bank_data -c "SELECT COUNT(*) FROM customers;"
```

**Stop/Start:**
```bash
# Stop services
pkill -f uvicorn
pkill -f streamlit
docker-compose down

# Start services
docker-compose up -d
nohup python3 -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
nohup ~/.local/bin/streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &
```

---

## Cost Management

**Current Cost:** $0/month (Free Tier)

**After 12 Months:** ~$10-15/month

**To Minimize Costs:**
- Stop instance when not in use: `aws ec2 stop-instances --instance-ids i-035026df35b6dad7c`
- Start when needed: `aws ec2 start-instances --instance-ids i-035026df35b6dad7c`
- Note: Public IP changes after stop/start

**Billing Alerts:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name billing-alert-10-dollars \
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

**API Not Responding:**
```bash
# Check if running
ps aux | grep uvicorn

# Check logs
tail -50 api.log

# Restart
pkill -f uvicorn
nohup python3 -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

**Dashboard Not Loading:**
```bash
# Check if running
ps aux | grep streamlit

# Check logs
tail -50 dashboard.log

# Restart
pkill -f streamlit
nohup ~/.local/bin/streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &
```

**Out of Memory:**
```bash
# Check memory
free -h

# Stop Docker to free memory
docker-compose down

# Restart with limited resources
docker-compose up -d
```

---

## Security Recommendations

1. **Restrict Security Group:**
   - Currently allows 0.0.0.0/0 (all IPs)
   - Restrict to your IP only for production

2. **Use HTTPS:**
   - Setup Let's Encrypt SSL certificate
   - Use Nginx reverse proxy

3. **Change Default Passwords:**
   - PostgreSQL: admin/admin123
   - Redis: redis123

4. **Enable AWS CloudWatch:**
   - Monitor CPU, memory, disk usage
   - Set up alerts

---

## Project Structure

```
pre-delinquency-engine/
├── config/
│   └── training_config.yaml          # Training configuration
├── src/
│   ├── data_generation/
│   │   ├── behavioral_simulator.py   # New behavioral data generator
│   │   └── synthetic_data.py         # Old generator (deprecated)
│   ├── models/
│   │   ├── train_optimized.py        # New optimized trainer
│   │   └── quick_train.py            # Old trainer
│   ├── serving/
│   │   └── api.py                    # FastAPI application
│   └── feature_engineering/
│       └── features.py
├── dashboard/
│   ├── app.py                        # Streamlit dashboard
│   └── ui_components.py
├── data/
│   ├── processed/                    # Feature datasets
│   ├── models/
│   │   ├── production/               # Production models
│   │   └── evaluation/               # Metrics and SHAP
│   └── raw/                          # Raw data
├── docker-compose.yml
├── run_complete_pipeline.py          # End-to-end runner
└── .env                              # Environment variables
```

---

## Success Metrics

**Current Status:**
- ✅ Infrastructure deployed
- ✅ Services running
- ✅ Basic model trained
- ✅ API functional
- ✅ Dashboard accessible
- ⏳ Enhanced model pending

**After Enhanced Training:**
- 🎯 ROC-AUC: 0.75-0.90
- 🎯 Recall: >0.70 (catch 70%+ of defaults)
- 🎯 Precision: >0.30 (30%+ accuracy on flags)
- 🎯 F1 Score: >0.45

---

## Contact & Support

**Instance Access:**
- SSH: `ssh -i ~/pre-delinquency-key.pem ubuntu@15.206.72.35`
- Region: ap-south-1
- Security Group: sg-02dc6171202b3d42d

**Documentation:**
- API Docs: http://15.206.72.35:8000/docs
- README: ~/hackathon-1/pre-delinquency-engine/README.md
- This file: ~/hackathon-1/pre-delinquency-engine/AWS-DEPLOYMENT-SUMMARY.md

---

**Last Updated:** February 19, 2026
**Status:** Production Ready (Basic Model) | Enhanced Model Pending
**Version:** 1.0.0
