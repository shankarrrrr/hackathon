#!/usr/bin/env python3
"""
Train Pre-Delinquency Model on Behavioral Dataset
Optimized for AWS Free Tier (1 vCPU, 1GB RAM)
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_recall_curve, f1_score, precision_score,
    recall_score, confusion_matrix, average_precision_score,
    roc_auc_score, classification_report
)
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("PRE-DELINQUENCY MODEL TRAINING")
print("="*70)

# Load dataset
print("\n📊 Loading behavioral dataset...")
df = pd.read_csv('data/processed/behavioral_features.csv')
print(f"Dataset shape: {df.shape}")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# Separate features and target
X = df.drop(['customer_id', 'will_default_in_2_4_weeks'], axis=1)
y = df['will_default_in_2_4_weeks']

print(f"\nClass distribution:")
print(f"  Negative (0): {(y==0).sum():,} ({(y==0).mean()*100:.2f}%)")
print(f"  Positive (1): {(y==1).sum():,} ({(y==1).mean()*100:.2f}%)")

# Stratified split
print("\n📊 Creating stratified train/val/test split...")
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp
)

print(f"Train: {len(X_train):,} samples ({(y_train==1).mean()*100:.2f}% positive)")
print(f"Val:   {len(X_val):,} samples ({(y_val==1).mean()*100:.2f}% positive)")
print(f"Test:  {len(X_test):,} samples ({(y_test==1).mean()*100:.2f}% positive)")

# Calculate scale_pos_weight
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
print(f"\nUsing scale_pos_weight: {scale_pos_weight:.2f}")

# Create DMatrix (memory efficient)
print("\n🔄 Creating DMatrix objects...")
dtrain = xgb.DMatrix(X_train, label=y_train)
dval = xgb.DMatrix(X_val, label=y_val)
dtest = xgb.DMatrix(X_test, label=y_test)

# Training parameters (optimized for Free Tier)
params = {
    'objective': 'binary:logistic',
    'eval_metric': ['auc', 'logloss'],
    'max_depth': 5,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'scale_pos_weight': scale_pos_weight,
    'min_child_weight': 3,
    'gamma': 0.1,
    'reg_alpha': 0.1,
    'reg_lambda': 1.0,
    'seed': 42,
    'nthread': 1  # Single thread for Free Tier
}

# Train model
print("\n🎯 Training XGBoost model...")
print("="*70)

evals = [(dtrain, 'train'), (dval, 'val')]
model = xgb.train(
    params,
    dtrain,
    num_boost_round=300,
    evals=evals,
    early_stopping_rounds=30,
    verbose_eval=20
)

print(f"\n✅ Training complete! Best iteration: {model.best_iteration}")

# Tune threshold on validation set
print("\n🎚️ Tuning classification threshold...")
y_val_proba = model.predict(dval)

precisions, recalls, thresholds = precision_recall_curve(y_val, y_val_proba)
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)

best_idx = np.argmax(f1_scores)
best_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
best_f1_val = f1_scores[best_idx]

print(f"Optimal threshold: {best_threshold:.4f}")
print(f"  Validation F1: {best_f1_val:.4f}")
print(f"  Validation Precision: {precisions[best_idx]:.4f}")
print(f"  Validation Recall: {recalls[best_idx]:.4f}")

# Evaluate on test set
print("\n📊 Evaluating on test set...")
print("="*70)

y_test_proba = model.predict(dtest)
y_test_pred = (y_test_proba >= best_threshold).astype(int)

# Calculate metrics
test_roc_auc = roc_auc_score(y_test, y_test_proba)
test_pr_auc = average_precision_score(y_test, y_test_proba)
test_precision = precision_score(y_test, y_test_pred)
test_recall = recall_score(y_test, y_test_pred)
test_f1 = f1_score(y_test, y_test_pred)
cm = confusion_matrix(y_test, y_test_pred)

print("\nTEST SET RESULTS")
print("="*70)
print(f"ROC-AUC:       {test_roc_auc:.4f}")
print(f"PR-AUC:        {test_pr_auc:.4f}")
print(f"Precision:     {test_precision:.4f}")
print(f"Recall:        {test_recall:.4f}")
print(f"F1 Score:      {test_f1:.4f}")
print(f"Threshold:     {best_threshold:.4f}")
print(f"\nConfusion Matrix:")
print(f"  True Negatives:  {cm[0][0]:,}")
print(f"  False Positives: {cm[0][1]:,}")
print(f"  False Negatives: {cm[1][0]:,}")
print(f"  True Positives:  {cm[1][1]:,}")
print("="*70)

print("\nClassification Report:")
print(classification_report(y_test, y_test_pred, target_names=['No Default', 'Will Default']))

# Feature importance
print("\nTop 15 Most Important Features:")
print("="*70)
importance = model.get_score(importance_type='gain')
importance_df = pd.DataFrame({
    'feature': importance.keys(),
    'importance': importance.values()
}).sort_values('importance', ascending=False).head(15)

for idx, row in importance_df.iterrows():
    print(f"  {row['feature']:30s} {row['importance']:8.1f}")

# Save model
print("\n💾 Saving model and metrics...")
model_path = 'data/models/quick/behavioral_model.json'
Path(model_path).parent.mkdir(parents=True, exist_ok=True)
model.save_model(model_path)
print(f"✅ Model saved: {model_path}")

# Save metrics
metrics = {
    'test_metrics': {
        'roc_auc': float(test_roc_auc),
        'pr_auc': float(test_pr_auc),
        'precision': float(test_precision),
        'recall': float(test_recall),
        'f1_score': float(test_f1),
        'optimal_threshold': float(best_threshold)
    },
    'confusion_matrix': {
        'true_negatives': int(cm[0][0]),
        'false_positives': int(cm[0][1]),
        'false_negatives': int(cm[1][0]),
        'true_positives': int(cm[1][1])
    },
    'training_info': {
        'n_samples': len(df),
        'n_features': len(X.columns),
        'train_samples': len(X_train),
        'val_samples': len(X_val),
        'test_samples': len(X_test),
        'positive_rate': float(y.mean()),
        'scale_pos_weight': float(scale_pos_weight),
        'best_iteration': int(model.best_iteration)
    },
    'feature_importance': importance_df.to_dict('records')
}

metrics_path = 'data/models/evaluation/metrics.json'
Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"✅ Metrics saved: {metrics_path}")

# Save threshold config
threshold_config = {
    'threshold': float(best_threshold),
    'model_path': model_path
}
with open('data/models/quick/threshold_config.json', 'w') as f:
    json.dump(threshold_config, f, indent=2)

print("\n" + "="*70)
print("✅ TRAINING COMPLETE!")
print("="*70)
print(f"\nModel performance:")
print(f"  - Can identify {test_recall*100:.1f}% of customers who will default")
print(f"  - {test_precision*100:.1f}% of flagged customers actually default")
print(f"  - Overall F1 score: {test_f1:.3f}")
print(f"\nNext steps:")
print(f"  1. Update API to use: {model_path}")
print(f"  2. Use threshold: {best_threshold:.4f}")
print(f"  3. Restart API service")
print("="*70)
