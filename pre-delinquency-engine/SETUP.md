# Setup Guide - Pre-Delinquency Engine

Complete setup instructions for getting the project running on your machine.

## Prerequisites

### Required Software
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/downloads)
- **PostgreSQL Client (psql)** - Optional, for database access

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 10GB free space
- **OS**: Windows 10/11, macOS, or Linux

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd pre-delinquency-engine
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Required packages:**
- fastapi
- uvicorn
- pandas
- numpy
- xgboost
- scikit-learn
- sqlalchemy
- psycopg2-binary
- kafka-python
- python-dotenv
- requests
- joblib

### 4. Setup Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings (optional, defaults work fine)
```

**Default configuration:**
```
DATABASE_URL=postgresql://admin:admin123@localhost:5432/bank_data
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
MODEL_PATH=data/models/quick/quick_model.json
API_URL=http://localhost:8000
```

### 5. Start Docker Services

```bash
# Start all infrastructure services
docker-compose up -d

# Verify services are running
docker-compose ps

# You should see:
# - delinquency_db (PostgreSQL)
# - delinquency_zookeeper (Zookeeper)
# - delinquency_kafka (Kafka)
```

**Wait 30 seconds** for services to fully initialize.

### 6. Create Kafka Topics

```bash
python -m src.streaming.setup_topics
```

**Expected output:**
```
Connected to Kafka successfully
Creating 5 topics...
✅ All topics created successfully!

Existing topics:
  - transactions-stream
  - predictions-stream
  - interventions-stream
  - customer-updates
  - dashboard-updates
```

### 7. Generate Synthetic Data

```bash
python -m src.data_generation.synthetic_data
```

**This will:**
- Generate 1,000 customers
- Create ~600,000 transactions
- Generate ~36,000 payments
- Load all data into PostgreSQL

**Time**: ~3-5 minutes

### 8. Train ML Model

```bash
python -m src.models.quick_train
```

**This will:**
- Extract features for 100 customers
- Train XGBoost model
- Save model to `data/models/quick/quick_model.json`

**Time**: ~2-3 minutes

## Running the System

### Option A: All-in-One (Recommended)

**Terminal 1 - Start API:**
```bash
python -m uvicorn src.serving.api:app --reload
```

**Terminal 2 - Start Workers:**
```bash
python run_streaming_pipeline.py
```

This starts:
- Transaction Simulator
- Feature Processor
- Intervention Worker

### Option B: Individual Components

**Terminal 1 - API:**
```bash
python -m uvicorn src.serving.api:app --reload
```

**Terminal 2 - Feature Processor:**
```bash
python -m src.streaming.feature_processor
```

**Terminal 3 - Intervention Worker:**
```bash
python -m src.streaming.intervention_worker
```

**Terminal 4 - Transaction Simulator:**
```bash
python -m src.streaming.transaction_simulator 1000 50
```

## Verification

### 1. Check API Health

```bash
curl http://localhost:8000/health
```

Or open in browser: http://localhost:8000/docs

### 2. View Kafka Messages

```bash
# View predictions
docker exec delinquency_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic predictions-stream \
  --from-beginning \
  --max-messages 5
```

### 3. Check Database

```bash
# Connect to database
docker exec -it delinquency_db psql -U admin -d bank_data

# Inside psql:
SELECT COUNT(*) FROM customers;
SELECT COUNT(*) FROM transactions;
SELECT COUNT(*) FROM risk_scores;
```

### 4. Run Tests

```bash
python test_streaming_pipeline.py
```

**Expected**: 6/6 tests passed

## Troubleshooting

### Docker Services Won't Start

```bash
# Check Docker is running
docker --version

# Restart Docker Desktop
# Then try again:
docker-compose down
docker-compose up -d
```

### Port Already in Use

```bash
# Check what's using the port
# Windows:
netstat -ano | findstr :8000
# macOS/Linux:
lsof -i :8000

# Kill the process or change port in .env
```

### Kafka Connection Failed

```bash
# Restart Kafka services
docker-compose restart kafka zookeeper

# Wait 30 seconds, then retry
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart if needed
docker-compose restart postgres

# Verify connection
docker exec delinquency_db psql -U admin -d bank_data -c "SELECT 1;"
```

### Python Package Issues

```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall all packages
pip install --force-reinstall -r requirements.txt
```

### Model Not Found

```bash
# Verify model exists
ls data/models/quick/quick_model.json

# If not, retrain:
python -m src.models.quick_train
```

## Stopping the System

### Stop Workers
Press `Ctrl+C` in the terminal running workers

### Stop API
Press `Ctrl+C` in the terminal running API

### Stop Docker Services
```bash
docker-compose down
```

### Complete Cleanup (removes all data)
```bash
docker-compose down -v
```

## Next Steps

After successful setup:
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
2. Check [TODO.md](TODO.md) for remaining work
3. See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
4. Review [STREAMING-COMPLETE.md](STREAMING-COMPLETE.md) for Kafka details

## Getting Help

- Check [README.md](README.md) for project overview
- Review [QUICK-START.md](QUICK-START.md) for quick reference
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Check documentation in each module's docstrings

## System Requirements Check

Run this to verify your system is ready:

```bash
# Check Python version
python --version  # Should be 3.11+

# Check Docker
docker --version
docker-compose --version

# Check available ports
# Windows:
netstat -ano | findstr ":5432 :9092 :8000"
# Should show nothing (ports are free)
```

---

**Setup Time**: ~15-20 minutes total  
**Status**: Production-ready streaming pipeline  
**Next**: Start building Phase 6 (Dashboard) or Phase 7 (Cloud Deployment)
