# PHASE 3: MODEL TRAINING & EXPLAINABILITY (Days 9-12)

## Overview

Train XGBoost model with SHAP explainability, optimized for pre-delinquency detection with high precision.

## Model Training Pipeline

Create src/models/train.py:

```python
"""
XGBoost model training with SHAP explainability
Optimized for pre-delinquency detection (14-30 day window)
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, roc_curve,
    precision_score, recall_score, f1_score, confusion_matrix
)
import mlflow
import mlflow.xgboost
from typing import Dict, Tuple
import joblib
from pathlib import Path
import json
from datetime import datetime

class DelinquencyModel:
    """
    Pre-delinquency prediction model with explainability
    Optimized for high precision (minimize false alarms)
    """
    
    def __init__(self, model_name: str = "delinquency_predictor"):
        self.model_name = model_name
        self.model = None
        self.threshold = 0.5
        self.feature_names = None
        self.feature_importance = None
        self.training_history = {}
    
    def prepare_data(
        self,
        features_df: pd.DataFrame,
        labels_df: pd.DataFrame,
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Tuple:
        """
        Prepare train/val/test splits with temporal ordering
        """
        print("📊 Preparing training data...")
        
        # Merge features with labels
        data = features_df.merge(
            labels_df[['customer_id', 'observation_date', 'label']],
            on=['customer_id', 'observation_date'],
            how='inner'
        )
        
        print(f"  Total samples: {len(data):,}")
        print(f"  Positive samples: {data['label'].sum():,} ({data['label'].mean()*100:.2f}%)")
        
        # Sort by observation_date for temporal split
        data = data.sort_values('observation_date').reset_index(drop=True)
        
        # Identify feature columns
        exclude_cols = ['customer_id', 'observation_date', 'label']
        feature_cols = [col for col in data.columns if col not in exclude_cols]
        self.feature_names = feature_cols
        
        # Split data temporally
        n = len(data)
        train_end = int(n * (1 - test_size - val_size))
        val_end = int(n * (1 - test_size))
        
        train_data = data.iloc[:train_end]
        val_data = data.iloc[train_end:val_end]
        test_data = data.iloc[val_end:]
        
        X_train = train_data[feature_cols]
        y_train = train_data['label']
        
        X_val = val_data[feature_cols]
        y_val = val_data['label']
        
        X_test = test_data[feature_cols]
        y_test = test_data['label']
        
        print(f"\n  Train: {len(X_train):,} samples ({y_train.mean()*100:.2f}% positive)")
        print(f"  Val:   {len(X_val):,} samples ({y_val.mean()*100:.2f}% positive)")
        print(f"  Test:  {len(X_test):,} samples ({y_test.mean()*100:.2f}% positive)")
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        params: Dict = None,
        num_boost_round: int = 300,
        early_stopping_rounds: int = 30
    ):
        """
        Train XGBoost model with class imbalance handling
        """
        print("\n🎯 Training XGBoost model...")
        
        # Calculate scale_pos_weight for class imbalance
        neg_count = (y_train == 0).sum()
        pos_count = (y_train == 1).sum()
        scale_pos_weight = neg_count / pos_count
        
        print(f"  Class imbalance ratio: {scale_pos_weight:.2f}")
        
        # Default parameters
        if params is None:
            params = {
                'objective': 'binary:logistic',
                'eval_metric': ['auc', 'logloss'],
                'max_depth': 6,
                'learning_rate': 0.05,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 5,
                'gamma': 0.1,
                'reg_alpha': 0.1,
                'reg_lambda': 1.0,
                'scale_pos_weight': scale_pos_weight,
                'tree_method': 'hist',
                'random_state': 42,
                'n_jobs': -1
            }
        
        # Create DMatrix
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=self.feature_names)
        dval = xgb.DMatrix(X_val, label=y_val, feature_names=self.feature_names)
        
        # Start MLflow run
        with mlflow.start_run(run_name=f"{self.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            # Log parameters
            mlflow.log_params(params)
            mlflow.log_param("num_boost_round", num_boost_round)
            mlflow.log_param("train_size", len(X_train))
            mlflow.log_param("positive_rate", y_train.mean())
            
            # Train model
            evals = [(dtrain, 'train'), (dval, 'val')]
            evals_result = {}
            
            self.model = xgb.train(
                params,
                dtrain,
                num_boost_round=num_boost_round,
                evals=evals,
                evals_result=evals_result,
                early_stopping_rounds=early_stopping_rounds,
                verbose_eval=10
            )
            
            self.training_history = evals_result
            
            # Get best iteration
            best_iteration = self.model.best_iteration
            print(f"\n  ✅ Best iteration: {best_iteration}")
            print(f"  ✅ Best validation AUC: {evals_result['val']['auc'][best_iteration]:.4f}")
            
            # Optimize threshold
            y_val_pred_proba = self.model.predict(dval)
            self.threshold = self._optimize_threshold(y_val, y_val_pred_proba, target_precision=0.70)
            
            print(f"  ✅ Optimized threshold: {self.threshold:.4f}")
            
            # Log metrics
            mlflow.log_metric("best_iteration", best_iteration)
            mlflow.log_metric("val_auc", evals_result['val']['auc'][best_iteration])
            mlflow.log_metric("optimized_threshold", self.threshold)
            
            # Feature importance
            self.feature_importance = self.model.get_score(importance_type='gain')
            
            # Save model
            mlflow.xgboost.log_model(
                self.model,
                "model",
                registered_model_name=self.model_name
            )
            
            print("\n✅ Training complete!")
        
        return self.model
    
    def _optimize_threshold(
        self,
        y_true: pd.Series,
        y_pred_proba: np.ndarray,
        target_precision: float = 0.70
    ) -> float:
        """
        Optimize classification threshold for target precision
        """
        precisions, recalls, thresholds = precision_recall_curve(y_true, y_pred_proba)
        
        # Find threshold where precision >= target
        valid_indices = np.where(precisions >= target_precision)[0]
        
        if len(valid_indices) == 0:
            print(f"  ⚠️ Warning: Could not achieve target precision {target_precision:.2f}")
            f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
            return thresholds[np.argmax(f1_scores)]
        
        # Among valid thresholds, choose one that maximizes recall
        best_idx = valid_indices[np.argmax(recalls[valid_indices])]
        
        print(f"  📊 At threshold {thresholds[best_idx]:.4f}:")
        print(f"     Precision: {precisions[best_idx]:.4f}")
        print(f"     Recall: {recalls[best_idx]:.4f}")
        
        return float(thresholds[best_idx])
    
    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        save_path: str = "data/models/evaluation"
    ) -> Dict[str, float]:
        """
        Comprehensive model evaluation
        """
        print("\n📊 Evaluating model on test set...")
        
        Path(save_path).mkdir(parents=True, exist_ok=True)
        
        # Predict
        dtest = xgb.DMatrix(X_test, feature_names=self.feature_names)
        y_pred_proba = self.model.predict(dtest)
        y_pred = (y_pred_proba >= self.threshold).astype(int)
        
        # Calculate metrics
        metrics = {
            'auc_roc': roc_auc_score(y_test, y_pred_proba),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'accuracy': (y_pred == y_test).mean(),
        }
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        
        metrics.update({
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp),
            'false_positive_rate': fp / (fp + tn),
            'true_positive_rate': tp / (tp + fn),
        })
        
        # Print metrics
        print("\n" + "="*60)
        print("EVALUATION RESULTS")
        print("="*60)
        print(f"\nModel Performance:")
        print(f"  AUC-ROC:    {metrics['auc_roc']:.4f}")
        print(f"  Precision:  {metrics['precision']:.4f}")
        print(f"  Recall:     {metrics['recall']:.4f}")
        print(f"  F1 Score:   {metrics['f1_score']:.4f}")
        
        # Save metrics
        with open(f"{save_path}/metrics.json", 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print("\n✅ Evaluation complete!")
        print(f"📁 Results saved to: {save_path}/")
        
        return metrics
    
    def save_model(self, save_path: str = "data/models"):
        """Save trained model and metadata"""
        Path(save_path).mkdir(parents=True, exist_ok=True)
        
        # Save XGBoost model
        model_file = f"{save_path}/{self.model_name}.json"
        self.model.save_model(model_file)
        
        # Save metadata
        metadata = {
            'model_name': self.model_name,
            'threshold': self.threshold,
            'feature_names': self.feature_names,
            'best_iteration': self.model.best_iteration,
            'training_date': datetime.now().isoformat()
        }
        
        with open(f"{save_path}/{self.model_name}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save with joblib
        joblib.dump(self, f"{save_path}/{self.model_name}_full.pkl")
        
        print(f"✅ Model saved to: {save_path}/")
    
    @classmethod
    def load_model(cls, load_path: str):
        """Load saved model"""
        return joblib.load(f"{load_path}")

if __name__ == "__main__":
    # Example training pipeline
    print("🚀 Starting model training pipeline...")
    
    # Load features and labels
    features_df = pd.read_csv("data/processed/features.csv")
    labels_df = pd.read_csv("data/raw/labels.csv")
    
    # Initialize model
    model = DelinquencyModel(model_name="delinquency_predictor_v1")
    
    # Prepare data
    X_train, y_train, X_val, y_val, X_test, y_test = model.prepare_data(
        features_df, labels_df
    )
    
    # Train model
    model.train(X_train, y_train, X_val, y_val)
    
    # Evaluate
    metrics = model.evaluate(X_test, y_test)
    
    # Save model
    model.save_model("data/models")
    
    print("\n🎉 Training pipeline complete!")
```

## SHAP Explainability

Create src/explainability/shap_explainer.py:

```python
"""
SHAP-based explainability for pre-delinquency predictions
Generates human-readable explanations for each risk score
"""

import shap
import pandas as pd
import numpy as np
from typing import Dict, List
import xgboost as xgb

class RiskExplainer:
    """
    Generate SHAP-based explanations for risk predictions
    Converts technical features into business-friendly language
    """
    
    def __init__(self, model: xgb.Booster, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer = shap.TreeExplainer(model)
        
        # Human-readable feature names
        self.feature_name_mapping = {
            'salary_delay_days': 'Salary Timing Delay',
            'salary_amount_deviation_pct': 'Salary Amount Change',
            'savings_drawdown_30d_pct': 'Savings Drawdown',
            'discretionary_spend_drop_30d_pct': 'Discretionary Spending Drop',
            'utility_payment_lateness_score': 'Payment Delay Score',
            'failed_autodebit_count_30d': 'Failed Auto-payments',
            # ... more mappings
        }
    
    def explain_prediction(
        self,
        X_customer: pd.DataFrame,
        risk_score: float,
        top_n: int = 5
    ) -> Dict:
        """
        Generate comprehensive explanation for a single prediction
        """
        # Compute SHAP values
        dmatrix = xgb.DMatrix(X_customer, feature_names=self.feature_names)
        shap_values = self.explainer.shap_values(X_customer)
        
        # Get base value
        base_value = self.explainer.expected_value
        
        # Create feature impact DataFrame
        feature_impacts = pd.DataFrame({
            'feature': self.feature_names,
            'feature_value': X_customer.iloc[0].values,
            'shap_value': shap_values[0],
            'abs_impact': np.abs(shap_values[0])
        })
        
        # Sort by absolute impact
        feature_impacts = feature_impacts.sort_values('abs_impact', ascending=False)
        
        # Get top drivers
        top_drivers = []
        for idx, row in feature_impacts.head(top_n).iterrows():
            driver = {
                'feature': self._humanize_feature_name(row['feature']),
                'impact': float(row['shap_value']),
                'impact_pct': float(row['shap_value'] / (abs(base_value) + 0.001) * 100),
                'direction': 'increased risk' if row['shap_value'] > 0 else 'decreased risk',
                'value': self._format_feature_value(row['feature'], row['feature_value'])
            }
            top_drivers.append(driver)
        
        # Generate explanation text
        explanation_text = self._generate_explanation_text(top_drivers, risk_score)
        
        # Risk level
        risk_level = self._get_risk_level(risk_score)
        
        # Recommendation
        recommendation = self._generate_recommendation(risk_level, top_drivers)
        
        return {
            'risk_score': float(risk_score),
            'risk_level': risk_level,
            'base_value': float(base_value),
            'top_drivers': top_drivers,
            'explanation_text': explanation_text,
            'recommendation': recommendation
        }
    
    def _humanize_feature_name(self, feature: str) -> str:
        """Convert feature code to human-readable name"""
        return self.feature_name_mapping.get(feature, feature.replace('_', ' ').title())
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Classify risk score into levels"""
        if risk_score >= 0.8:
            return 'CRITICAL'
        elif risk_score >= 0.6:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_explanation_text(self, top_drivers: List[Dict], risk_score: float) -> str:
        """Generate natural language explanation"""
        risk_level = self._get_risk_level(risk_score)
        
        if risk_level == 'CRITICAL':
            text = "⚠️ **Critical risk detected.** "
        elif risk_level == 'HIGH':
            text = "🔴 **High risk identified.** "
        elif risk_level == 'MEDIUM':
            text = "🟡 **Moderate risk observed.** "
        else:
            text = "🟢 **Low risk profile.** "
        
        if len(top_drivers) >= 2:
            driver1 = top_drivers[0]
            driver2 = top_drivers[1]
            
            text += f"Risk is primarily driven by {driver1['feature'].lower()} "
            text += f"({driver1['impact_pct']:+.0f}%) and {driver2['feature'].lower()} "
            text += f"({driver2['impact_pct']:+.0f}%). "
        
        return text
    
    def _generate_recommendation(self, risk_level: str, top_drivers: List[Dict]) -> str:
        """Generate intervention recommendation"""
        if risk_level == 'CRITICAL':
            return "**Immediate Action Required:** Contact customer within 24 hours."
        elif risk_level == 'HIGH':
            return "**Proactive Outreach:** Reach out within 3-5 days."
        elif risk_level == 'MEDIUM':
            return "**Monitoring:** Continue to monitor account activity."
        else:
            return "**No Action Needed:** Account is healthy."
```

## Running Training

```bash
# Train model
python src/models/train.py

# View MLflow UI
mlflow ui --port 5000

# Load trained model
from src.models.train import DelinquencyModel
model = DelinquencyModel.load_model("data/models/delinquency_predictor_v1_full.pkl")
```

## Expected Results

- **AUC-ROC:** 0.82-0.85
- **Precision:** 72%+
- **Recall:** 68%+
- **F1 Score:** 0.70+

## Next Steps

After training:
1. Review evaluation metrics
2. Analyze feature importance
3. Test SHAP explanations
4. Proceed to Phase 4 (API Serving)
