"""
Quick training script with minimal data for fast iteration
Uses only 100 customers to speed up feature generation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

from src.feature_engineering.features import BehavioralFeatureEngineering
from src.models.train import DelinquencyModel

print("🚀 Quick Training Pipeline - 100 Customers Only")
print("="*60)

# Connect to database
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

# Get 100 random customers
print("\n📊 Selecting 100 random customers...")
query = """
SELECT customer_id 
FROM customers 
ORDER BY RANDOM() 
LIMIT 100
"""
customers = pd.read_sql(query, engine)
print(f"  Selected {len(customers)} customers")

# Get labels for these customers
print("\n📋 Loading labels...")
labels_query = f"""
SELECT customer_id, observation_date, label, days_to_default
FROM labels
WHERE customer_id IN ({','.join([f"'{c}'" for c in customers['customer_id']])})
"""
labels_df = pd.read_sql(labels_query, engine)
labels_df['observation_date'] = pd.to_datetime(labels_df['observation_date'])
print(f"  Loaded {len(labels_df)} observations")
print(f"  Positive rate: {labels_df['label'].mean()*100:.2f}%")

# Generate features (this is the slow part)
print("\n⚙️ Generating features (this may take a few minutes)...")
engineer = BehavioralFeatureEngineering(db_url=db_url)

features_list = []
for idx, row in labels_df.iterrows():
    if idx % 10 == 0:
        print(f"  Progress: {idx}/{len(labels_df)} ({idx/len(labels_df)*100:.1f}%)")
    
    try:
        features = engineer.compute_all_features(
            customer_id=row['customer_id'],
            observation_date=row['observation_date']
        )
        features['label'] = row['label']
        features['days_to_default'] = row['days_to_default']
        features_list.append(features)
    except Exception as e:
        print(f"  ⚠️ Error for customer {row['customer_id']}: {e}")
        continue

features_df = pd.DataFrame(features_list)
print(f"\n✅ Feature generation complete: {len(features_df)} samples")

# Save features
output_path = "data/processed/features_quick.csv"
features_df.to_csv(output_path, index=False)
print(f"📁 Features saved to: {output_path}")

# Train model (without MLflow)
print("\n🎯 Training model...")
import xgboost as xgb
from sklearn.metrics import roc_auc_score, precision_recall_curve

# Prepare data
exclude_cols = ['customer_id', 'observation_date', 'label', 'days_to_default']
feature_cols = [col for col in features_df.columns if col not in exclude_cols]

# Split data
n = len(features_df)
train_end = int(n * 0.7)
val_end = int(n * 0.85)

train_data = features_df.iloc[:train_end]
val_data = features_df.iloc[train_end:val_end]
test_data = features_df.iloc[val_end:]

X_train = train_data[feature_cols].fillna(0)
y_train = train_data['label']
X_val = val_data[feature_cols].fillna(0)
y_val = val_data['label']
X_test = test_data[feature_cols].fillna(0)
y_test = test_data['label']

print(f"  Train: {len(X_train)} samples ({y_train.mean()*100:.1f}% positive)")
print(f"  Val:   {len(X_val)} samples ({y_val.mean()*100:.1f}% positive)")
print(f"  Test:  {len(X_test)} samples ({y_test.mean()*100:.1f}% positive)")

# Train XGBoost
dtrain = xgb.DMatrix(X_train, label=y_train)
dval = xgb.DMatrix(X_val, label=y_val)
dtest = xgb.DMatrix(X_test, label=y_test)

params = {
    'objective': 'binary:logistic',
    'eval_metric': ['auc', 'logloss'],
    'max_depth': 4,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'scale_pos_weight': (y_train == 0).sum() / (y_train == 1).sum(),
    'random_state': 42
}

evals = [(dtrain, 'train'), (dval, 'val')]
model = xgb.train(
    params,
    dtrain,
    num_boost_round=100,
    evals=evals,
    early_stopping_rounds=20,
    verbose_eval=10
)

print(f"\n✅ Training complete! Best iteration: {model.best_iteration}")

# Evaluate
print("\n📊 Evaluating model...")
y_pred_proba = model.predict(dtest)
y_pred = (y_pred_proba >= 0.5).astype(int)

from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

auc = roc_auc_score(y_test, y_pred_proba)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

print(f"\n{'='*60}")
print("EVALUATION RESULTS")
print(f"{'='*60}")
print(f"\nModel Performance:")
print(f"  AUC-ROC:    {auc:.4f}")
print(f"  Precision:  {precision:.4f}")
print(f"  Recall:     {recall:.4f}")
print(f"  F1 Score:   {f1:.4f}")
print(f"\nConfusion Matrix:")
print(f"  True Positives:  {tp}")
print(f"  False Positives: {fp}")
print(f"  True Negatives:  {tn}")
print(f"  False Negatives: {fn}")

# Save model
import os
os.makedirs("data/models/quick", exist_ok=True)
model.save_model("data/models/quick/quick_model.json")
print(f"\n✅ Model saved to: data/models/quick/quick_model.json")

print("\n🎉 Quick training complete!")
print(f"\n📊 Final Metrics:")
print(f"  AUC-ROC: {auc:.4f}")
print(f"  Precision: {precision:.4f}")
print(f"  Recall: {recall:.4f}")
print(f"  F1 Score: {f1:.4f}")
