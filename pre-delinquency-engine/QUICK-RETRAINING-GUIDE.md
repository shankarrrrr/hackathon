# Quick Retraining Guide

## What It Does

Automatically retrains your ML model when 50+ new customers are added to the system.

## Setup (One-Time)

The retraining system is ready to use! Tables are created automatically on first run.

## Test It

```bash
# Test the retraining system
python test_retraining.py
```

Expected output:
```
============================================================
TESTING RETRAINING SYSTEM
============================================================

1️⃣ Initializing retrainer...
   ✅ Retrainer initialized

2️⃣ Checking database tables...
   ✅ model_retraining_log exists (0 records)
   ✅ customer_training_status exists (0 records)

3️⃣ Checking new customers...
   📊 New customers not in training: 1000

4️⃣ Checking retraining threshold...
   ✅ Retraining needed: New customers: 1000

5️⃣ Checking retraining history...
   ℹ️ No retraining history yet

============================================================
✅ ALL TESTS PASSED
============================================================
```

## Run Retraining

```bash
# Check and retrain if needed
python check_and_retrain.py
```

This will:
1. Check if 50+ new customers exist
2. If yes, retrain model with 200 customers
3. Save new model to `data/models/quick/quick_model.json`
4. Log the event with metrics

**Time:** 3-5 minutes for 200 customers

## After Retraining

Restart the API to load the new model:

```bash
# Stop current API (Ctrl+C)
# Then restart:
python -m uvicorn src.serving.api:app --reload
```

## Check Status via API

```bash
# Check if retraining is needed
curl http://localhost:8000/retraining/status

# Response:
{
  "new_customers_count": 75,
  "retraining_needed": true,
  "reason": "New customers: 75",
  "threshold": 50,
  "recent_retraining": [...]
}
```

## Schedule It (Optional)

### Windows
```powershell
# Run daily at 2 AM
schtasks /create /tn "ModelRetraining" /tr "python C:\path\to\check_and_retrain.py" /sc daily /st 02:00
```

### Linux/Mac
```bash
# Add to crontab (run daily at 2 AM)
0 2 * * * cd /path/to/pre-delinquency-engine && python check_and_retrain.py
```

## View History

```sql
-- Check retraining history
SELECT 
    retrain_date,
    customers_trained,
    auc_score,
    model_version
FROM model_retraining_log
ORDER BY retrain_date DESC;
```

## Configuration

Edit `src/models/auto_retrain.py`:

```python
# Change threshold (default: 50)
should_retrain, reason = retrainer.should_retrain(new_customer_threshold=100)

# Change max customers (default: 200)
result = retrainer.retrain_model(max_customers=500)
```

## That's It!

Simple as that. The system now:
- ✅ Tracks new customers
- ✅ Retrains when threshold reached
- ✅ Logs all events
- ✅ Provides API endpoints

For full details, see **RETRAINING.md**
