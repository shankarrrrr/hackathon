#!/usr/bin/env python3
"""
Retrain model with synthetic oversampling and threshold tuning.
Handles extreme class imbalance by generating synthetic positive samples.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_recall_curve, f1_score, precision_score, 
    recall_score, confusion_matrix, average_precision_score,
    roc_auc_score
)
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("🚀 Starting model retraining with synthetic oversampling...")

# Load data
print("\n📊 Loading dataset...")
features_df = pd.read_csv('data/processed/features_quick.csv')
print(f"Original dataset: {len(features_df)} samples")

# Separate features and target
X = features_df.drop(['customer_id', 'will_default'], axis=1)
y = features_df['will_default']

print(f"Class distribution:")
print(f"  Negative (0): {(y == 0).sum()} ({(y == 0).sum() / len(y) * 100:.1f}%)")
print(f"  Positive (1): {(y == 1).sum()} ({(y == 1).sum() / len(y) * 100:.1f}%)")

# Step 1: Generate synthetic positive samples
print("\n🔬 Generating synthetic positive samples...")

# Get positive samples
positive_mask = y == 1
X_positive = X[positive_mask]
y_positive = y[positive_mask]

n_positives = len(X_positive)
n_negatives = (y == 0).sum()

# Calculate how many synthetic samples to generate
# Target: 30-40% positive class
target_positive_ratio = 0.35
n_synthetic = int((n_negatives * target_positive_ratio) / (1 - target_positive_ratio)) - n_positives

print(f"Generating {n_synthetic} synthetic positive samples...")

# Generate synthetic samples by adding noise to existing positives
synthetic_samples = []
for _ in range(n_synthetic):
    # Randomly select a positive sample
    idx = np.random.randint(0, len(X_positive))
    base_sample = X_positive.iloc[idx].copy()
    
    # Add small Gaussian noise to numeric features
    noise_scale = 0.1  # 10% noise
    for col in X_positive.columns:
        if X_positive[col].dtype in ['float64', 'int64']:
            std = X_positive[col].std()
            if std > 0:
                noise = np.random.normal(0, std * noise_scale)
                base_sample[col] += noise
    
    synthetic_samples.append(base_sample)

# Create synthetic dataframe
X_synthetic = pd.DataFrame(synthetic_samples, columns=X_positive.columns)
y_synthetic = pd.Series([1] * n_synthetic)

# Merge with original data
X_balanced = pd.concat([X, X_synthetic], ignore_index=True)
y_balanced = pd.concat([y, y_synthetic], ignore_index=True)

print(f"\n✅ Balanced dataset: {len(X_balanced)} samples")
print(f"Class distribution after oversampling:")
print(f"  Negative (0): {(y_balanced == 0).sum()} ({(y_balanced == 0).sum() / len(y_balanced) * 100:.1f}%)")
print(f"  Positive (1): {(y_balanced == 1).sum()} ({(y_balanced == 1).sum() / len(y_balanced) * 100:.1f}%)")

# Step 2: Split data with stratification
print("\n📊 Splitting data...")
X_temp, X_test, y_temp, y_test = train_test_split(
    X_balanced, y_balanced, test_size=0.15, random_state=42, stratify=y_balanced
)
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp  # 0.176 * 0.85 ≈ 0.15
)

print(f"Train: {len(X_train)} samples ({(y_train == 1).sum() / len(y_train) * 100:.1f}% positive)")
print(f"Val:   {len(X_val)} samples ({(y_val == 1).sum() / len(y_val) * 100:.1f}% positive)")
print(f"Test:  {len(X_test)} samples ({(y_test == 1).sum() / len(y_test) * 100:.1f}% positive)")

# Step 3: Train model with scale_pos_weight
print("\n🎯 Training XGBoost model...")

# Calculate scale_pos_weight for remaining imbalance
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
print(f"Using scale_pos_weight: {scale_pos_weight:.2f}")

# Create DMatrix
dtrain = xgb.DMatrix(X_train, label=y_train)
dval = xgb.DMatrix(X_val, label=y_val)
dtest = xgb.DMatrix(X_test, label=y_test)

# Training parameters
params = {
    'objective': 'binary:logistic',
    'eval_metric': ['auc', 'logloss'],
    'max_depth': 4,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'scale_pos_weight': scale_pos_weight,
    'seed': 42
}

# Train with early stopping
evals = [(dtrain, 'train'), (dval, 'val')]
model = xgb.train(
    params,
    dtrain,
    num_boost_round=200,
    evals=evals,
    early_stopping_rounds=20,
    verbose_eval=10
)

print(f"\n✅ Training complete! Best iteration: {model.best_iteration}")

# Step 4: Tune classification threshold using PR curve
print("\n🎚️ Tuning classification threshold...")

# Get predictions on validation set
y_val_proba = model.predict(dval)

# Calculate precision-recall curve
precisions, recalls, thresholds = precision_recall_curve(y_val, y_val_proba)

# Calculate F1 scores for each threshold
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)

# Find threshold that maximizes F1
best_threshold_idx = np.argmax(f1_scores)
best_threshold = thresholds[best_threshold_idx] if best_threshold_idx < len(thresholds) else 0.5
best_f1 = f1_scores[best_threshold_idx]

print(f"Optimal threshold: {best_threshold:.4f} (F1: {best_f1:.4f})")
print(f"  Precision: {precisions[best_threshold_idx]:.4f}")
print(f"  Recall: {recalls[best_threshold_idx]:.4f}")

# Step 5: Evaluate on test set
print("\n📊 Evaluating on test set...")

y_test_proba = model.predict(dtest)
y_test_pred = (y_test_proba >= best_threshold).astype(int)

# Calculate metrics
test_precision = precision_score(y_test, y_test_pred)
test_recall = recall_score(y_test, y_test_pred)
test_f1 = f1_score(y_test, y_test_pred)
test_pr_auc = average_precision_score(y_test, y_test_proba)
test_roc_auc = roc_auc_score(y_test, y_test_proba)
cm = confusion_matrix(y_test, y_test_pred)

print("\n" + "=" * 60)
print("FINAL TEST SET RESULTS")
print("=" * 60)
print(f"ROC-AUC:     {test_roc_auc:.4f}")
print(f"PR-AUC:      {test_pr_auc:.4f}")
print(f"Precision:   {test_precision:.4f}")
print(f"Recall:      {test_recall:.4f}")
print(f"F1 Score:    {test_f1:.4f}")
print(f"Threshold:   {best_threshold:.4f}")
print("\nConfusion Matrix:")
print(f"True Negatives:  {cm[0][0]}")
print(f"False Positives: {cm[0][1]}")
print(f"False Negatives: {cm[1][0]}")
print(f"True Positives:  {cm[1][1]}")
print("=" * 60)

# Save model
print("\n💾 Saving model...")
model_path = 'data/models/quick/quick_model_balanced.json'
model.save_model(model_path)
print(f"✅ Model saved to: {model_path}")

# Save metrics
metrics = {
    'roc_auc': float(test_roc_auc),
    'pr_auc': float(test_pr_auc),
    'precision': float(test_precision),
    'recall': float(test_recall),
    'f1_score': float(test_f1),
    'optimal_threshold': float(best_threshold),
    'confusion_matrix': {
        'true_negatives': int(cm[0][0]),
        'false_positives': int(cm[0][1]),
        'false_negatives': int(cm[1][0]),
        'true_positives': int(cm[1][1])
    },
    'training_info': {
        'original_samples': len(features_df),
        'synthetic_samples': n_synthetic,
        'total_samples': len(X_balanced),
        'train_samples': len(X_train),
        'val_samples': len(X_val),
        'test_samples': len(X_test),
        'scale_pos_weight': float(scale_pos_weight),
        'best_iteration': int(model.best_iteration)
    }
}

metrics_path = 'data/models/evaluation/metrics.json'
Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"✅ Metrics saved to: {metrics_path}")

# Save threshold for API
threshold_config = {
    'threshold': float(best_threshold),
    'model_path': model_path
}

with open('data/models/quick/threshold_config.json', 'w') as f:
    json.dump(threshold_config, f, indent=2)

print("\n🎉 Retraining complete!")
print(f"\nTo use the new model:")
print(f"1. Update API to load: {model_path}")
print(f"2. Use threshold: {best_threshold:.4f}")
print(f"3. Restart API service")
