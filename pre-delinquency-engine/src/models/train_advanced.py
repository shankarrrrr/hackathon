"""
Advanced Model Training Pipeline
Implements feature engineering, ensemble methods, and advanced tuning
"""

import numpy as np
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier, Pool
import yaml
import json
from pathlib import Path
from typing import Dict, Tuple, Any, List
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_recall_curve, f1_score, precision_score,
    recall_score, confusion_matrix, average_precision_score,
    roc_auc_score, fbeta_score
)
from imblearn.over_sampling import SMOTE, ADASYN
import warnings
warnings.filterwarnings('ignore')


class AdvancedFeatureEngineering:
    """Advanced feature engineering for behavioral data"""
    
    @staticmethod
    def create_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features"""
        print("  → Creating interaction features...", end='', flush=True)
        
        # Check if V2 features (with suffixes) or V1 features
        is_v2 = 'salary_delay_weeks_mean' in df.columns
        
        if is_v2:
            # V2 feature names
            df['salary_delay_x_failed_autodebits_v2'] = df['salary_delay_weeks_max'] * df['failed_autodebits_mean']
            df['payment_stress_composite'] = df['utility_delay_days_mean'] * df['emi_delay_days_mean']
            df['liquidity_stress'] = (1 - df['liquidity_ratio_mean']) * abs(df['salary_drop_pct_mean'])
            
            # Normalized by account age
            df['salary_delay_per_account_age'] = df['salary_delay_weeks_mean'] / (df['account_age_months'] + 1)
            df['failed_autodebits_per_account_age'] = df['failed_autodebits_mean'] / (df['account_age_months'] + 1)
            
            # Credit behavior interactions
            df['credit_util_x_payment_stress'] = df['credit_util_change_mean'] * df['utility_delay_days_mean']
            df['lending_app_x_gambling'] = df['lending_app_transfers_mean'] * df['gambling_txns_mean']
        else:
            # V1 feature names
            df['salary_delay_x_failed_autodebits'] = df['max_salary_delay'] * df['total_failed_autodebits']
            df['payment_stress_composite'] = df['avg_utility_delay'] * df['avg_emi_delay']
            df['liquidity_stress'] = (1 - df['avg_liquidity_ratio']) * abs(df['avg_salary_drop'])
            
            # Normalized by account age
            df['salary_delay_per_account_age'] = df['avg_salary_delay'] / (df['account_age_months'] + 1)
            df['failed_autodebits_per_account_age'] = df['total_failed_autodebits'] / (df['account_age_months'] + 1)
            
            # Credit behavior interactions
            df['credit_util_x_payment_stress'] = df['avg_credit_util_change'] * df['avg_utility_delay']
            df['lending_app_x_gambling'] = df['total_lending_app_txns'] * df['total_gambling_txns']
        
        print(" ✓")
        return df
    
    @staticmethod
    def create_financial_ratios(df: pd.DataFrame) -> pd.DataFrame:
        """Create financial ratio features"""
        print("  → Creating financial ratios...", end='', flush=True)
        
        # Check if V2 features
        is_v2 = 'salary_delay_weeks_mean' in df.columns
        
        if is_v2:
            # V2 feature names
            df['min_to_avg_liquidity_ratio'] = df['liquidity_ratio_min'] / (df['liquidity_ratio_mean'] + 0.01)
            df['liquidity_volatility'] = df['liquidity_ratio_std']
            
            # Payment ratios
            df['payment_reliability_score'] = 1 / (1 + df['utility_delay_days_mean'] + df['emi_delay_days_mean'])
            df['credit_health_score'] = df['cc_min_payment_ratio_mean'] * (1 - abs(df['credit_util_change_mean']))
            
            # Stress intensity
            df['overall_stress_score'] = (
                df['salary_delay_weeks_mean'] + 
                df['failed_autodebits_mean'] + 
                df['utility_delay_days_mean'] +
                df['lending_app_transfers_mean']
            ) / 4
        else:
            # V1 feature names
            df['min_to_avg_liquidity_ratio'] = df['min_liquidity_ratio'] / (df['avg_liquidity_ratio'] + 0.01)
            df['liquidity_volatility'] = df['avg_liquidity_ratio'] - df['min_liquidity_ratio']
            
            # Payment ratios
            df['payment_reliability_score'] = 1 / (1 + df['avg_utility_delay'] + df['avg_emi_delay'])
            df['credit_health_score'] = df['avg_cc_min_payment'] * (1 - df['avg_credit_util_change'])
            
            # Stress intensity
            df['overall_stress_score'] = (
                df['avg_salary_delay'] + 
                df['total_failed_autodebits'] + 
                df['avg_utility_delay'] +
                df['total_lending_app_txns']
            ) / 4
        
        print(" ✓")
        return df
    
    @staticmethod
    def clip_outliers(df: pd.DataFrame, features: List[str], percentile: float = 99) -> pd.DataFrame:
        """Clip outliers at specified percentile"""
        print("  → Clipping outliers...", end='', flush=True)
        
        clipped_count = 0
        for feat in features:
            if feat in df.columns:
                upper = df[feat].quantile(percentile / 100)
                df[feat] = df[feat].clip(upper=upper)
                clipped_count += 1
        
        print(f" ✓ ({clipped_count} features)")
        return df
    
    @staticmethod
    def prune_low_importance_features(df: pd.DataFrame, importance_dict: Dict, 
                                     threshold: float = 0.01) -> pd.DataFrame:
        """Remove features with low SHAP importance"""
        if not importance_dict:
            return df
        
        print(f"  → Pruning features (threshold={threshold})...", end='', flush=True)
        
        low_importance = [f['feature'] for f in importance_dict.get('feature_importance', [])
                         if f['importance'] < threshold]
        
        df = df.drop(columns=[f for f in low_importance if f in df.columns], errors='ignore')
        
        print(f" ✓ (removed {len(low_importance)} features)")
        return df


class AdvancedModelTrainer:
    """Advanced model training with ensemble and tuning"""
    
    def __init__(self, config_path: str = 'config/training_config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.models = {}
        self.best_threshold = 0.5
        self.feature_names = None
        self.scaler = StandardScaler()
        
    def load_and_engineer_features(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Load data and apply feature engineering"""
        print("\n📊 Loading and engineering features...")
        print("="*70)
        
        df = pd.read_csv(self.config['dataset']['output_path'])
        
        # Separate features and target
        X = df.drop(['customer_id', 'will_default_in_2_4_weeks'], axis=1)
        y = df['will_default_in_2_4_weeks']
        
        # Handle categorical and non-numeric columns
        print("  → Processing data types...", end='', flush=True)
        
        # Encode segment if present (V2 feature)
        if 'segment' in X.columns:
            segment_map = {'low': 0, 'medium': 1, 'high': 2}
            X['segment_encoded'] = X['segment'].map(segment_map)
            X = X.drop('segment', axis=1)
        
        # Drop timestamp columns
        timestamp_cols = [col for col in X.columns if 'timestamp' in col.lower() or 'date' in col.lower()]
        X = X.drop(columns=timestamp_cols, errors='ignore')
        
        # Convert all remaining columns to numeric
        for col in X.columns:
            if X[col].dtype == 'object':
                try:
                    X[col] = pd.to_numeric(X[col], errors='coerce')
                except:
                    X = X.drop(col, axis=1)
        
        # Fill any NaN values
        X = X.fillna(0)
        
        print(" ✓")
        
        # Feature engineering
        fe = AdvancedFeatureEngineering()
        X = fe.create_interaction_features(X)
        X = fe.create_financial_ratios(X)
        
        # Clip outliers on key features (check both V1 and V2 names)
        is_v2 = 'salary_delay_weeks_mean' in X.columns
        if is_v2:
            outlier_features = ['salary_delay_weeks_mean', 'salary_delay_weeks_max', 
                              'failed_autodebits_mean', 'utility_delay_days_mean', 
                              'utility_delay_days_max']
        else:
            outlier_features = ['avg_salary_delay', 'max_salary_delay', 'total_failed_autodebits',
                               'avg_utility_delay', 'max_utility_delay']
        X = fe.clip_outliers(X, outlier_features, percentile=99)
        
        self.feature_names = X.columns.tolist()
        
        print(f"✅ Dataset: {len(df):,} samples, {len(X.columns)} features")
        print(f"   Positive rate: {y.mean()*100:.2f}%")
        
        return X, y
    
    def create_splits_with_resampling(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Create splits and apply SMOTE to training set"""
        print("\n📊 Creating splits with resampling...")
        
        test_size = self.config['split']['test_size']
        val_size = self.config['split']['val_size']
        
        # Train+Val / Test split
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Train / Val split
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_ratio, random_state=42, stratify=y_temp
        )
        
        print(f"Original train: {len(X_train):,} ({(y_train==1).mean()*100:.2f}% pos)")
        
        # Apply SMOTE to training set only
        print("  → Applying SMOTE...", end='', flush=True)
        smote = SMOTE(random_state=42, k_neighbors=5)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
        print(f" ✓ ({len(X_train_resampled):,} samples, {(y_train_resampled==1).mean()*100:.2f}% pos)")
        
        return {
            'X_train': X_train_resampled, 'y_train': y_train_resampled,
            'X_val': X_val, 'y_val': y_val,
            'X_test': X_test, 'y_test': y_test
        }
    
    def train_xgboost(self, splits: Dict) -> xgb.Booster:
        """Train XGBoost with expanded hyperparameter search"""
        print("\n🎯 Training XGBoost...")
        print("="*70)
        
        dtrain = xgb.DMatrix(splits['X_train'], label=splits['y_train'])
        dval = xgb.DMatrix(splits['X_val'], label=splits['y_val'])
        
        best_score = 0
        best_model = None
        best_params = None
        
        n_trials = 20  # Expanded search
        
        for trial in range(n_trials):
            params = {
                'objective': 'binary:logistic',
                'eval_metric': 'auc',
                'seed': 42,
                'nthread': -1,
                'max_depth': np.random.choice([3, 4, 5, 6, 7, 8, 10]),
                'learning_rate': np.random.uniform(0.01, 0.2),
                'subsample': np.random.uniform(0.5, 1.0),
                'colsample_bytree': np.random.uniform(0.5, 1.0),
                'min_child_weight': np.random.choice([1, 3, 5, 7, 10]),
                'gamma': np.random.uniform(0, 5),
                'reg_alpha': np.random.uniform(0, 2),
                'reg_lambda': np.random.uniform(0.5, 3)
            }
            
            model = xgb.train(
                params, dtrain,
                num_boost_round=300,
                evals=[(dval, 'val')],
                early_stopping_rounds=50,
                verbose_eval=False
            )
            
            y_val_proba = model.predict(dval)
            val_auc = roc_auc_score(splits['y_val'], y_val_proba)
            
            if trial % 5 == 0:
                print(f"Trial {trial+1}/{n_trials}: AUC={val_auc:.4f}")
            
            if val_auc > best_score:
                best_score = val_auc
                best_model = model
                best_params = params
        
        print(f"\n✅ Best XGBoost AUC: {best_score:.4f}")
        self.models['xgboost'] = best_model
        return best_model
    
    def train_lightgbm(self, splits: Dict) -> lgb.Booster:
        """Train LightGBM"""
        print("\n🎯 Training LightGBM...")
        print("="*70)
        
        train_data = lgb.Dataset(splits['X_train'], label=splits['y_train'])
        val_data = lgb.Dataset(splits['X_val'], label=splits['y_val'], reference=train_data)
        
        best_score = 0
        best_model = None
        
        for trial in range(15):
            params = {
                'objective': 'binary',
                'metric': 'auc',
                'boosting_type': 'gbdt',
                'seed': 42,
                'num_leaves': np.random.choice([15, 31, 63, 127]),
                'learning_rate': np.random.uniform(0.01, 0.2),
                'feature_fraction': np.random.uniform(0.5, 1.0),
                'bagging_fraction': np.random.uniform(0.5, 1.0),
                'bagging_freq': 5,
                'min_child_samples': np.random.choice([10, 20, 30, 50]),
                'reg_alpha': np.random.uniform(0, 2),
                'reg_lambda': np.random.uniform(0.5, 3),
                'verbose': -1
            }
            
            model = lgb.train(
                params, train_data,
                num_boost_round=300,
                valid_sets=[val_data],
                callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
            )
            
            y_val_proba = model.predict(splits['X_val'])
            val_auc = roc_auc_score(splits['y_val'], y_val_proba)
            
            if trial % 5 == 0:
                print(f"Trial {trial+1}/15: AUC={val_auc:.4f}")
            
            if val_auc > best_score:
                best_score = val_auc
                best_model = model
        
        print(f"\n✅ Best LightGBM AUC: {best_score:.4f}")
        self.models['lightgbm'] = best_model
        return best_model
    
    def train_catboost(self, splits: Dict) -> CatBoostClassifier:
        """Train CatBoost"""
        print("\n🎯 Training CatBoost...")
        print("="*70)
        
        train_pool = Pool(splits['X_train'], splits['y_train'])
        val_pool = Pool(splits['X_val'], splits['y_val'])
        
        model = CatBoostClassifier(
            iterations=300,
            learning_rate=0.05,
            depth=6,
            loss_function='Logloss',
            eval_metric='AUC',
            random_seed=42,
            early_stopping_rounds=50,
            verbose=50
        )
        
        model.fit(train_pool, eval_set=val_pool)
        
        y_val_proba = model.predict_proba(splits['X_val'])[:, 1]
        val_auc = roc_auc_score(splits['y_val'], y_val_proba)
        
        print(f"\n✅ CatBoost AUC: {val_auc:.4f}")
        self.models['catboost'] = model
        return model
    
    def create_ensemble(self, splits: Dict) -> Dict:
        """Create weighted ensemble of models"""
        print("\n🎯 Creating ensemble...")
        print("="*70)
        
        # Get predictions from each model
        xgb_pred = self.models['xgboost'].predict(xgb.DMatrix(splits['X_val']))
        lgb_pred = self.models['lightgbm'].predict(splits['X_val'])
        cat_pred = self.models['catboost'].predict_proba(splits['X_val'])[:, 1]
        
        # Find optimal weights
        best_auc = 0
        best_weights = None
        
        for w1 in np.arange(0.2, 0.6, 0.1):
            for w2 in np.arange(0.2, 0.6, 0.1):
                w3 = 1 - w1 - w2
                if w3 < 0.1:
                    continue
                
                ensemble_pred = w1 * xgb_pred + w2 * lgb_pred + w3 * cat_pred
                auc = roc_auc_score(splits['y_val'], ensemble_pred)
                
                if auc > best_auc:
                    best_auc = auc
                    best_weights = {'xgboost': w1, 'lightgbm': w2, 'catboost': w3}
        
        print(f"✅ Best ensemble AUC: {best_auc:.4f}")
        print(f"   Weights: {best_weights}")
        
        return best_weights
    
    def optimize_threshold_advanced(self, splits: Dict, ensemble_weights: Dict) -> float:
        """Optimize threshold using F2 score (recall-weighted)"""
        print("\n🎚️ Optimizing threshold (F2 score)...")
        
        # Get ensemble predictions
        xgb_pred = self.models['xgboost'].predict(xgb.DMatrix(splits['X_val']))
        lgb_pred = self.models['lightgbm'].predict(splits['X_val'])
        cat_pred = self.models['catboost'].predict_proba(splits['X_val'])[:, 1]
        
        ensemble_pred = (
            ensemble_weights['xgboost'] * xgb_pred +
            ensemble_weights['lightgbm'] * lgb_pred +
            ensemble_weights['catboost'] * cat_pred
        )
        
        precisions, recalls, thresholds = precision_recall_curve(splits['y_val'], ensemble_pred)
        
        # Calculate F2 score (weights recall 2x more than precision)
        f2_scores = (5 * precisions * recalls) / (4 * precisions + recalls + 1e-10)
        best_idx = np.argmax(f2_scores)
        best_threshold = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
        
        print(f"Optimal threshold: {best_threshold:.4f}")
        print(f"  F2 Score: {f2_scores[best_idx]:.4f}")
        print(f"  Precision: {precisions[best_idx]:.4f}")
        print(f"  Recall: {recalls[best_idx]:.4f}")
        
        return best_threshold
    
    def evaluate_with_cv(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """5-fold cross-validation evaluation"""
        print("\n📊 5-Fold Cross-Validation...")
        print("="*70)
        
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = {'roc_auc': [], 'pr_auc': [], 'f1': [], 'f2': []}
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
            X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
            y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]
            
            # Quick XGBoost model for CV
            dtrain = xgb.DMatrix(X_train_fold, label=y_train_fold)
            dval = xgb.DMatrix(X_val_fold, label=y_val_fold)
            
            params = {'objective': 'binary:logistic', 'eval_metric': 'auc', 'max_depth': 6, 
                     'learning_rate': 0.05, 'seed': 42}
            model = xgb.train(params, dtrain, num_boost_round=100, verbose_eval=False)
            
            y_pred_proba = model.predict(dval)
            y_pred = (y_pred_proba >= 0.5).astype(int)
            
            cv_scores['roc_auc'].append(roc_auc_score(y_val_fold, y_pred_proba))
            cv_scores['pr_auc'].append(average_precision_score(y_val_fold, y_pred_proba))
            cv_scores['f1'].append(f1_score(y_val_fold, y_pred))
            cv_scores['f2'].append(fbeta_score(y_val_fold, y_pred, beta=2))
            
            print(f"Fold {fold}: ROC-AUC={cv_scores['roc_auc'][-1]:.4f}, "
                  f"PR-AUC={cv_scores['pr_auc'][-1]:.4f}")
        
        print(f"\n✅ CV Results (mean ± std):")
        for metric, scores in cv_scores.items():
            print(f"   {metric.upper()}: {np.mean(scores):.4f} ± {np.std(scores):.4f}")
        
        return cv_scores
    
    def run(self):
        """Execute advanced training pipeline"""
        print("\n" + "="*70)
        print("ADVANCED MODEL TRAINING PIPELINE")
        print("="*70)
        
        # Load and engineer features
        X, y = self.load_and_engineer_features()
        
        # Cross-validation
        cv_results = self.evaluate_with_cv(X, y)
        
        # Create splits with SMOTE
        splits = self.create_splits_with_resampling(X, y)
        
        # Train multiple models
        self.train_xgboost(splits)
        self.train_lightgbm(splits)
        self.train_catboost(splits)
        
        # Create ensemble
        ensemble_weights = self.create_ensemble(splits)
        
        # Optimize threshold
        self.best_threshold = self.optimize_threshold_advanced(splits, ensemble_weights)
        
        print("\n" + "="*70)
        print("✅ ADVANCED TRAINING COMPLETE!")
        print("="*70)


if __name__ == '__main__':
    trainer = AdvancedModelTrainer()
    trainer.run()
