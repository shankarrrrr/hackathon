"""
XGBoost model training with SHAP explainability
Optimized for pre-delinquency detection (14-30 day window)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

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
from dotenv import load_dotenv

load_dotenv()


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
        test_size: float = 0.2,
        val_size: float = 0.1
    ) -> Tuple:
        """
        Prepare train/val/test splits with temporal ordering
        """
        print("📊 Preparing training data...")
        
        # Check if label column exists
        if 'label' not in features_df.columns:
            raise ValueError("features_df must contain 'label' column")
        
        data = features_df.copy()
        
        print(f"  Total samples: {len(data):,}")
        print(f"  Positive samples: {data['label'].sum():,} ({data['label'].mean()*100:.2f}%)")
        
        # Sort by observation_date for temporal split
        if 'observation_date' in data.columns:
            data = data.sort_values('observation_date').reset_index(drop=True)
        
        # Identify feature columns
        exclude_cols = ['customer_id', 'observation_date', 'label', 'days_to_default', 'default_date', 'default_amount']
        feature_cols = [col for col in data.columns if col not in exclude_cols]
        self.feature_names = feature_cols
        
        # Handle missing values
        data[feature_cols] = data[feature_cols].fillna(0)
        
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
        scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
        
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
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000'))
        
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
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'accuracy': (y_pred == y_test).mean(),
        }
        
        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        
        metrics.update({
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp),
            'false_positive_rate': fp / (fp + tn) if (fp + tn) > 0 else 0,
            'true_positive_rate': tp / (tp + fn) if (tp + fn) > 0 else 0,
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
        print(f"\nConfusion Matrix:")
        print(f"  True Positives:  {tp}")
        print(f"  False Positives: {fp}")
        print(f"  True Negatives:  {tn}")
        print(f"  False Negatives: {fn}")
        
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
    print("🚀 Starting model training pipeline...")
    
    # First, generate features if not exists
    features_path = "data/processed/features.csv"
    
    if not os.path.exists(features_path):
        print("\n📊 Features not found. Generating features first...")
        from src.feature_engineering.pipeline import FeaturePipeline
        
        pipeline = FeaturePipeline()
        features_df = pipeline.generate_training_features(output_path=features_path)
        
        if features_df is None:
            print("❌ Feature generation failed!")
            sys.exit(1)
    else:
        print(f"\n📂 Loading features from {features_path}...")
        features_df = pd.read_csv(features_path)
    
    print(f"  Loaded {len(features_df):,} samples with {len(features_df.columns)} columns")
    
    # Initialize model
    model = DelinquencyModel(model_name="delinquency_predictor_v1")
    
    # Prepare data
    X_train, y_train, X_val, y_val, X_test, y_test = model.prepare_data(features_df)
    
    # Train model
    model.train(X_train, y_train, X_val, y_val)
    
    # Evaluate
    metrics = model.evaluate(X_test, y_test)
    
    # Save model
    model.save_model("data/models")
    
    print("\n🎉 Training pipeline complete!")
    print(f"\n📊 Final Metrics:")
    print(f"  AUC-ROC: {metrics['auc_roc']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")
    print(f"  F1 Score: {metrics['f1_score']:.4f}")
