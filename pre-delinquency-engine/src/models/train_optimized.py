"""
Optimized Model Training Pipeline
Free Tier Safe with Hyperparameter Tuning and Explainability
"""

import numpy as np
import pandas as pd
import xgboost as xgb
import yaml
import json
from pathlib import Path
from typing import Dict, Tuple, Any
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_recall_curve, f1_score, precision_score,
    recall_score, confusion_matrix, average_precision_score,
    roc_auc_score, classification_report
)
import warnings
warnings.filterwarnings('ignore')


class ModelTrainer:
    """Handles model training with hyperparameter tuning and evaluation"""
    
    def __init__(self, config_path: str = 'config/training_config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model = None
        self.best_threshold = 0.5
        self.feature_names = None
        
    def load_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Load and prepare dataset"""
        print("\n📊 Loading dataset...")
        df = pd.read_csv(self.config['dataset']['output_path'])
        
        X = df.drop(['customer_id', 'will_default_in_2_4_weeks'], axis=1)
        y = df['will_default_in_2_4_weeks']
        
        self.feature_names = X.columns.tolist()
        
        print(f"Dataset: {len(df):,} samples, {len(X.columns)} features")
        print(f"Positive rate: {y.mean()*100:.2f}%")
        
        return X, y
    
    def create_splits(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Create stratified train/val/test splits"""
        print("\n📊 Creating stratified splits...")
        
        test_size = self.config['split']['test_size']
        val_size = self.config['split']['val_size']
        
        # Train+Val / Test split
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, 
            random_state=self.config['split']['random_state'],
            stratify=y
        )
        
        # Train / Val split
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_ratio,
            random_state=self.config['split']['random_state'],
            stratify=y_temp
        )
        
        print(f"Train: {len(X_train):,} ({(y_train==1).mean()*100:.2f}% pos)")
        print(f"Val:   {len(X_val):,} ({(y_val==1).mean()*100:.2f}% pos)")
        print(f"Test:  {len(X_test):,} ({(y_test==1).mean()*100:.2f}% pos)")
        
        return {
            'X_train': X_train, 'y_train': y_train,
            'X_val': X_val, 'y_val': y_val,
            'X_test': X_test, 'y_test': y_test
        }
    
    def random_search_hyperparameters(self, splits: Dict) -> Dict:
        """Lightweight random search for hyperparameters"""
        if not self.config['hyperparameter_tuning']['enabled']:
            return self.config['model']['base_params']
        
        print("\n🔍 Hyperparameter tuning (Random Search)...")
        print("="*70)
        
        search_space = self.config['hyperparameter_tuning']['search_space']
        n_trials = self.config['hyperparameter_tuning']['n_trials']
        
        # Calculate scale_pos_weight
        scale_pos_weight = (splits['y_train'] == 0).sum() / (splits['y_train'] == 1).sum()
        
        # Create DMatrix
        dtrain = xgb.DMatrix(splits['X_train'], label=splits['y_train'])
        dval = xgb.DMatrix(splits['X_val'], label=splits['y_val'])
        
        best_score = 0
        best_params = None
        
        for trial in range(n_trials):
            # Sample random parameters
            params = {
                'objective': self.config['model']['objective'],
                'eval_metric': self.config['model']['eval_metric'],
                'scale_pos_weight': scale_pos_weight,
                'seed': self.config['dataset']['seed'],
                'nthread': self.config['model']['nthread'],
                'max_depth': np.random.choice(search_space['max_depth']),
                'learning_rate': np.random.choice(search_space['learning_rate']),
                'subsample': np.random.choice(search_space['subsample']),
                'colsample_bytree': np.random.choice(search_space['colsample_bytree']),
                'min_child_weight': np.random.choice(search_space['min_child_weight']),
                'gamma': np.random.choice(search_space['gamma']),
                'reg_alpha': np.random.choice(search_space['reg_alpha']),
                'reg_lambda': np.random.choice(search_space['reg_lambda'])
            }
            
            # Train model
            evals = [(dtrain, 'train'), (dval, 'val')]
            model = xgb.train(
                params, dtrain,
                num_boost_round=self.config['model']['num_boost_round'],
                evals=evals,
                early_stopping_rounds=self.config['model']['early_stopping_rounds'],
                verbose_eval=False
            )
            
            # Evaluate
            y_val_proba = model.predict(dval)
            val_auc = roc_auc_score(splits['y_val'], y_val_proba)
            
            print(f"Trial {trial+1}/{n_trials}: AUC={val_auc:.4f} | "
                  f"depth={params['max_depth']}, lr={params['learning_rate']:.3f}")
            
            if val_auc > best_score:
                best_score = val_auc
                best_params = params.copy()
        
        print(f"\n✅ Best validation AUC: {best_score:.4f}")
        print(f"Best parameters: {best_params}")
        
        return best_params
    
    def train_final_model(self, splits: Dict, params: Dict) -> xgb.Booster:
        """Train final model with best parameters"""
        print("\n🎯 Training final model...")
        print("="*70)
        
        dtrain = xgb.DMatrix(splits['X_train'], label=splits['y_train'])
        dval = xgb.DMatrix(splits['X_val'], label=splits['y_val'])
        
        evals = [(dtrain, 'train'), (dval, 'val')]
        model = xgb.train(
            params, dtrain,
            num_boost_round=self.config['model']['num_boost_round'],
            evals=evals,
            early_stopping_rounds=self.config['model']['early_stopping_rounds'],
            verbose_eval=20
        )
        
        print(f"\n✅ Training complete! Best iteration: {model.best_iteration}")
        
        return model
    
    def optimize_threshold(self, model: xgb.Booster, splits: Dict) -> float:
        """Optimize classification threshold using PR curve"""
        print("\n🎚️ Optimizing classification threshold...")
        
        dval = xgb.DMatrix(splits['X_val'])
        y_val_proba = model.predict(dval)
        
        precisions, recalls, thresholds = precision_recall_curve(
            splits['y_val'], y_val_proba
        )
        
        objective = self.config['threshold_optimization']['objective']
        
        if objective == 'f1':
            # Maximize F1 score
            f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
            best_idx = np.argmax(f1_scores)
            metric_name = "F1"
            metric_value = f1_scores[best_idx]
        
        elif objective == 'recall':
            # Maximize recall while maintaining minimum precision
            min_precision = 0.3
            valid_idx = precisions >= min_precision
            if valid_idx.any():
                valid_recalls = recalls[valid_idx]
                best_idx = np.where(valid_idx)[0][np.argmax(valid_recalls)]
            else:
                best_idx = np.argmax(recalls)
            metric_name = "Recall"
            metric_value = recalls[best_idx]
        
        best_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
        
        print(f"Optimal threshold: {best_threshold:.4f}")
        print(f"  {metric_name}: {metric_value:.4f}")
        print(f"  Precision: {precisions[best_idx]:.4f}")
        print(f"  Recall: {recalls[best_idx]:.4f}")
        
        return best_threshold
    
    def evaluate_model(self, model: xgb.Booster, splits: Dict, 
                      threshold: float) -> Dict:
        """Comprehensive model evaluation"""
        print("\n📊 Evaluating model...")
        print("="*70)
        
        dtest = xgb.DMatrix(splits['X_test'])
        y_test_proba = model.predict(dtest)
        
        results = {}
        
        # Evaluate at different thresholds
        for thresh_name, thresh_val in [('default_0.5', 0.5), ('optimized', threshold)]:
            y_pred = (y_test_proba >= thresh_val).astype(int)
            
            metrics = {
                'threshold': float(thresh_val),
                'roc_auc': float(roc_auc_score(splits['y_test'], y_test_proba)),
                'pr_auc': float(average_precision_score(splits['y_test'], y_test_proba)),
                'precision': float(precision_score(splits['y_test'], y_pred)),
                'recall': float(recall_score(splits['y_test'], y_pred)),
                'f1': float(f1_score(splits['y_test'], y_pred))
            }
            
            cm = confusion_matrix(splits['y_test'], y_pred)
            metrics['confusion_matrix'] = {
                'tn': int(cm[0][0]),
                'fp': int(cm[0][1]),
                'fn': int(cm[1][0]),
                'tp': int(cm[1][1])
            }
            
            results[thresh_name] = metrics
            
            print(f"\n{thresh_name.upper()} (threshold={thresh_val:.4f}):")
            print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
            print(f"  PR-AUC:    {metrics['pr_auc']:.4f}")
            print(f"  Precision: {metrics['precision']:.4f}")
            print(f"  Recall:    {metrics['recall']:.4f}")
            print(f"  F1:        {metrics['f1']:.4f}")
            print(f"  CM: TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")
        
        return results
    
    def compute_shap_values(self, model: xgb.Booster, splits: Dict) -> Dict:
        """Compute SHAP values for explainability (lightweight)"""
        if not self.config['explainability']['enabled']:
            return {}
        
        print("\n🔍 Computing SHAP values...")
        
        try:
            import shap
            
            sample_size = min(
                self.config['explainability']['sample_size'],
                len(splits['X_test'])
            )
            
            X_sample = splits['X_test'].sample(n=sample_size, random_state=42)
            
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)
            
            # Get feature importance
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': mean_abs_shap
            }).sort_values('importance', ascending=False)
            
            top_n = self.config['explainability']['top_features']
            
            print(f"\nTop {top_n} Important Features (SHAP):")
            print("="*70)
            for idx, row in importance_df.head(top_n).iterrows():
                print(f"  {row['feature']:30s} {row['importance']:8.4f}")
            
            return {
                'feature_importance': importance_df.to_dict('records'),
                'sample_size': sample_size
            }
        
        except ImportError:
            print("⚠️ SHAP not installed, skipping explainability")
            return {}
    
    def save_artifacts(self, model: xgb.Booster, results: Dict, 
                      shap_results: Dict, best_params: Dict):
        """Save model and evaluation artifacts"""
        print("\n💾 Saving artifacts...")
        
        # Save model
        model_path = Path(self.config['output']['model_path'])
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(model_path))
        print(f"✅ Model: {model_path}")
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_to_native(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            return obj
        
        # Save metrics
        metrics = {
            'evaluation': convert_to_native(results),
            'training_params': convert_to_native(best_params),
            'shap_analysis': convert_to_native(shap_results),
            'dataset_info': {
                'n_samples': int(len(pd.read_csv(self.config['dataset']['output_path']))),
                'n_features': int(len(self.feature_names)),
                'positive_rate': int(results['optimized']['confusion_matrix']['tp'] + 
                                results['optimized']['confusion_matrix']['fn'])
            }
        }
        
        metrics_path = Path(self.config['output']['metrics_path'])
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ Metrics: {metrics_path}")
        
        # Save threshold config
        threshold_config = {
            'threshold': float(self.best_threshold),
            'model_path': str(model_path)
        }
        
        threshold_path = Path(self.config['output']['threshold_config_path'])
        threshold_path.parent.mkdir(parents=True, exist_ok=True)
        with open(threshold_path, 'w') as f:
            json.dump(threshold_config, f, indent=2)
        print(f"✅ Threshold config: {threshold_path}")
    
    def run(self):
        """Execute complete training pipeline"""
        print("\n" + "="*70)
        print("OPTIMIZED MODEL TRAINING PIPELINE")
        print("="*70)
        
        # Load data
        X, y = self.load_data()
        
        # Create splits
        splits = self.create_splits(X, y)
        
        # Hyperparameter tuning
        best_params = self.random_search_hyperparameters(splits)
        
        # Train final model
        model = self.train_final_model(splits, best_params)
        self.model = model
        
        # Optimize threshold
        self.best_threshold = self.optimize_threshold(model, splits)
        
        # Evaluate
        results = self.evaluate_model(model, splits, self.best_threshold)
        
        # SHAP explainability
        shap_results = self.compute_shap_values(model, splits)
        
        # Save artifacts
        self.save_artifacts(model, results, shap_results, best_params)
        
        print("\n" + "="*70)
        print("✅ TRAINING PIPELINE COMPLETE!")
        print("="*70)
        
        opt_metrics = results['optimized']
        print(f"\nFinal Model Performance (Optimized Threshold):")
        print(f"  ROC-AUC:   {opt_metrics['roc_auc']:.4f}")
        print(f"  Recall:    {opt_metrics['recall']:.4f}")
        print(f"  Precision: {opt_metrics['precision']:.4f}")
        print(f"  F1 Score:  {opt_metrics['f1']:.4f}")
        print("="*70)


if __name__ == '__main__':
    trainer = ModelTrainer()
    trainer.run()
