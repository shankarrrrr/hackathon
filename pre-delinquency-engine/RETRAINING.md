# Automatic Model Retraining

Simple implementation of automatic model retraining that tracks new customers and retrains when a threshold is reached.

## How It Works

1. **Tracking**: System tracks which customers have been included in model training
2. **Threshold**: When 50+ new customers are added, retraining is triggered
3. **Automatic**: Retrains model with up to 200 customers (mix of new and existing)
4. **Logging**: All retraining events are logged with metrics

## Database Tables

Two new tables are automatically created:

### `model_retraining_log`
Tracks all retraining events with metrics:
- `retrain_date` - When retraining occurred
- `customers_trained` - Number of customers used
- `samples_trained` - Number of training samples
- `auc_score`, `precision_score`, `recall_score`, `f1_score` - Model performance
- `model_version` - Unique version identifier
- `trigger_reason` - Why retraining was triggered
- `training_duration_seconds` - How long it took

### `customer_training_status`
Tracks which customers are in the training set:
- `customer_id` - Customer identifier
- `first_seen` - When customer was first seen
- `last_trained` - Last time included in training
- `included_in_training` - Boolean flag

## Usage

### Option 1: Manual Check (Recommended for Testing)

Run the check script manually:

```bash
python check_and_retrain.py
```

**Output:**
```
============================================================
MODEL RETRAINING CHECK
============================================================

📊 New customers not in training: 75
✅ Threshold reached (75 >= 50)

🔔 Retraining triggered: New customers: 75
   Starting automatic retraining...

============================================================
🔄 AUTOMATIC MODEL RETRAINING
============================================================

📊 Selected 200 customers for training
📋 Loaded 1500 observations
   Positive rate: 15.20%

⚙️ Generating features...
   Progress: 0/1500 (0.0%)
   Progress: 20/1500 (1.3%)
   ...
✅ Generated 1450 feature samples

🎯 Training XGBoost model...
   Train: 1015 samples (15.1% positive)
   Test:  218 samples (15.6% positive)

📊 Model Performance:
   AUC-ROC:   0.8234
   Precision: 0.7891
   Recall:    0.6543
   F1 Score:  0.7156

✅ Model saved to: data/models/quick/quick_model.json

🎉 Retraining complete in 245s!
============================================================

✅ SUCCESS!
   Customers trained: 200
   Samples: 1450
   AUC: 0.8234
   Model version: auto_retrain_20240115_143022

💡 Restart the API to load the new model:
   python -m uvicorn src.serving.api:app --reload
```

### Option 2: Scheduled Execution (Production)

**Windows (Task Scheduler):**
```powershell
# Run daily at 2 AM
schtasks /create /tn "ModelRetraining" /tr "python C:\path\to\check_and_retrain.py" /sc daily /st 02:00
```

**Linux/Mac (Cron):**
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/pre-delinquency-engine && python check_and_retrain.py >> logs/retraining.log 2>&1
```

### Option 3: API Endpoints

Check retraining status via API:

```bash
# Check if retraining is needed
curl http://localhost:8000/retraining/status
```

**Response:**
```json
{
  "new_customers_count": 75,
  "retraining_needed": true,
  "reason": "New customers: 75",
  "threshold": 50,
  "recent_retraining": [
    {
      "retrain_id": 1,
      "retrain_date": "2024-01-15T14:30:22",
      "customers_trained": 200,
      "samples_trained": 1450,
      "auc_score": 0.8234,
      "model_version": "auto_retrain_20240115_143022"
    }
  ]
}
```

Manually trigger retraining:

```bash
# Trigger retraining (WARNING: Takes several minutes)
curl -X POST http://localhost:8000/retraining/trigger
```

**Response:**
```json
{
  "status": "success",
  "message": "Model retrained successfully. Restart API to load new model.",
  "customers_trained": 200,
  "samples_trained": 1450,
  "auc": 0.8234,
  "model_version": "auto_retrain_20240115_143022"
}
```

## Configuration

Edit `src/models/auto_retrain.py` to adjust:

- **Threshold**: Change `new_customer_threshold` (default: 50)
- **Max customers**: Change `max_customers` (default: 200)
- **Model parameters**: Modify XGBoost params in `retrain_model()`

## Monitoring

### View Retraining History

```sql
-- Recent retraining events
SELECT 
    retrain_date,
    customers_trained,
    samples_trained,
    auc_score,
    model_version,
    training_duration_seconds
FROM model_retraining_log
ORDER BY retrain_date DESC
LIMIT 10;
```

### Check Customer Training Status

```sql
-- Customers not yet in training
SELECT COUNT(*) as untrained_count
FROM customers c
LEFT JOIN customer_training_status cts ON c.customer_id::text = cts.customer_id
WHERE cts.customer_id IS NULL OR cts.included_in_training = FALSE;
```

### View Training Coverage

```sql
-- Training coverage statistics
SELECT 
    COUNT(*) as total_customers,
    SUM(CASE WHEN included_in_training THEN 1 ELSE 0 END) as trained,
    SUM(CASE WHEN NOT included_in_training OR included_in_training IS NULL THEN 1 ELSE 0 END) as untrained
FROM customers c
LEFT JOIN customer_training_status cts ON c.customer_id::text = cts.customer_id;
```

## Important Notes

1. **API Restart Required**: After retraining, restart the API to load the new model
2. **Training Time**: Retraining takes 3-5 minutes for 200 customers
3. **Blocking Operation**: API endpoint blocks during retraining (use manual script for production)
4. **Model Versioning**: Each retrain creates a unique version identifier
5. **Data Requirements**: Needs sufficient labeled data for training

## Workflow

```
New Customers Added
        ↓
Check Script Runs (manual/scheduled)
        ↓
Count New Customers
        ↓
Threshold Reached? (50+)
        ↓ YES
Select Customers (200 max)
        ↓
Generate Features
        ↓
Train XGBoost Model
        ↓
Evaluate Performance
        ↓
Save Model (overwrites existing)
        ↓
Log Retraining Event
        ↓
Update Customer Status
        ↓
Restart API (manual)
        ↓
New Model Active
```

## Troubleshooting

### Retraining Fails

```bash
# Check database connection
python -c "from src.models.auto_retrain import AutoRetrainer; r = AutoRetrainer(); print('OK')"

# Check if tables exist
psql $DATABASE_URL -c "SELECT COUNT(*) FROM model_retraining_log;"
```

### Model Not Loading

```bash
# Verify model file exists
ls -lh data/models/quick/quick_model.json

# Check API logs for errors
python -m uvicorn src.serving.api:app --reload
```

### No New Customers Detected

```sql
-- Check customer_training_status table
SELECT * FROM customer_training_status LIMIT 10;

-- Manually reset if needed
TRUNCATE customer_training_status;
```

## Future Enhancements

This is the simplest implementation. Possible improvements:

- **Online Learning**: Incremental updates without full retraining
- **A/B Testing**: Compare old vs new model performance
- **Automated Deployment**: Auto-restart API after retraining
- **Performance Monitoring**: Track model drift over time
- **Rollback**: Keep previous model versions for rollback
- **Distributed Training**: Use more data with distributed XGBoost

## Summary

You now have automatic model retraining that:

✅ Tracks new customers  
✅ Triggers retraining at threshold (50 customers)  
✅ Logs all retraining events with metrics  
✅ Can be run manually or scheduled  
✅ Provides API endpoints for monitoring  
✅ Simple to understand and maintain  

Run `python check_and_retrain.py` to test it!
