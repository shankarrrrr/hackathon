"""
Automatic model retraining - Simple implementation
Tracks new customers and retrains when threshold is reached
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import xgboost as xgb
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

load_dotenv()

from src.feature_engineering.features import BehavioralFeatureEngineering


class AutoRetrainer:
    """Simple automatic retraining system"""
    
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.db_url)
        self.model_dir = "data/models/quick"
        self.model_path = f"{self.model_dir}/quick_model.json"
        
        # Create retraining metadata table if not exists
        self._init_metadata_table()
    
    def _init_metadata_table(self):
        """Create table to track retraining history"""
        query = """
        CREATE TABLE IF NOT EXISTS model_retraining_log (
            retrain_id SERIAL PRIMARY KEY,
            retrain_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            customers_trained INT NOT NULL,
            samples_trained INT NOT NULL,
            auc_score DECIMAL(5,4),
            precision_score DECIMAL(5,4),
            recall_score DECIMAL(5,4),
            f1_score DECIMAL(5,4),
            model_version VARCHAR(100) NOT NULL,
            trigger_reason VARCHAR(200),
            training_duration_seconds INT
        );
        
        CREATE TABLE IF NOT EXISTS customer_training_status (
            customer_id VARCHAR(255) PRIMARY KEY,
            first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_trained TIMESTAMPTZ,
            prediction_count INT DEFAULT 0,
            included_in_training BOOLEAN DEFAULT FALSE
        );
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()
    
    def check_new_customers(self):
        """Count customers not yet included in training"""
        query = """
        SELECT COUNT(DISTINCT c.customer_id) as new_count
        FROM customers c
        LEFT JOIN customer_training_status cts ON c.customer_id::text = cts.customer_id
        WHERE cts.customer_id IS NULL OR cts.included_in_training = FALSE
        """
        
        df = pd.read_sql(query, self.engine)
        return int(df.iloc[0]['new_count'])
    
    def should_retrain(self, new_customer_threshold=50):
        """Check if retraining should be triggered"""
        new_count = self.check_new_customers()
        
        print(f"📊 New customers not in training: {new_count}")
        
        if new_count >= new_customer_threshold:
            print(f"✅ Threshold reached ({new_count} >= {new_customer_threshold})")
            return True, f"New customers: {new_count}"
        
        return False, None
    
    def retrain_model(self, max_customers=200):
        """Retrain model with all available data"""
        start_time = datetime.now()
        
        print("\n" + "="*60)
        print("🔄 AUTOMATIC MODEL RETRAINING")
        print("="*60)
        
        # Get customers for training (prioritize those not yet trained)
        query = f"""
        SELECT DISTINCT c.customer_id
        FROM customers c
        LEFT JOIN customer_training_status cts ON c.customer_id::text = cts.customer_id
        ORDER BY 
            CASE WHEN cts.included_in_training IS NULL OR cts.included_in_training = FALSE THEN 0 ELSE 1 END,
            RANDOM()
        LIMIT {max_customers}
        """
        
        customers = pd.read_sql(query, self.engine)
        print(f"\n📊 Selected {len(customers)} customers for training")
        
        # Get labels
        labels_query = f"""
        SELECT customer_id, observation_date, label, days_to_default
        FROM labels
        WHERE customer_id IN ({','.join([f"'{c}'" for c in customers['customer_id']])})
        """
        
        labels_df = pd.read_sql(labels_query, self.engine)
        labels_df['observation_date'] = pd.to_datetime(labels_df['observation_date'])
        print(f"📋 Loaded {len(labels_df)} observations")
        print(f"   Positive rate: {labels_df['label'].mean()*100:.2f}%")
        
        # Generate features
        print("\n⚙️ Generating features...")
        engineer = BehavioralFeatureEngineering(db_url=self.db_url)
        
        features_list = []
        for idx, row in labels_df.iterrows():
            if idx % 20 == 0:
                print(f"   Progress: {idx}/{len(labels_df)} ({idx/len(labels_df)*100:.1f}%)")
            
            try:
                features = engineer.compute_all_features(
                    customer_id=row['customer_id'],
                    observation_date=row['observation_date']
                )
                features['label'] = row['label']
                features_list.append(features)
            except Exception as e:
                continue
        
        features_df = pd.DataFrame(features_list)
        print(f"✅ Generated {len(features_df)} feature samples")
        
        # Train model
        print("\n🎯 Training XGBoost model...")
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
        X_test = test_data[feature_cols].fillna(0)
        y_test = test_data['label']
        
        print(f"   Train: {len(X_train)} samples ({y_train.mean()*100:.1f}% positive)")
        print(f"   Test:  {len(X_test)} samples ({y_test.mean()*100:.1f}% positive)")
        
        # Train
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtest = xgb.DMatrix(X_test, label=y_test)
        
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 4,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'scale_pos_weight': (y_train == 0).sum() / (y_train == 1).sum(),
            'random_state': 42
        }
        
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=100,
            evals=[(dtrain, 'train')],
            verbose_eval=False
        )
        
        # Evaluate
        y_pred_proba = model.predict(dtest)
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        auc = roc_auc_score(y_test, y_pred_proba)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        print(f"\n📊 Model Performance:")
        print(f"   AUC-ROC:   {auc:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1 Score:  {f1:.4f}")
        
        # Save model
        os.makedirs(self.model_dir, exist_ok=True)
        model.save_model(self.model_path)
        print(f"\n✅ Model saved to: {self.model_path}")
        
        # Update metadata
        duration = int((datetime.now() - start_time).total_seconds())
        model_version = f"auto_retrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self._log_retraining(
            customers_trained=len(customers),
            samples_trained=len(features_df),
            auc_score=auc,
            precision_score=precision,
            recall_score=recall,
            f1_score=f1,
            model_version=model_version,
            trigger_reason="Automatic retraining triggered",
            duration=duration
        )
        
        # Update customer training status
        self._update_customer_status(customers['customer_id'].tolist())
        
        print(f"\n🎉 Retraining complete in {duration}s!")
        print("="*60)
        
        return {
            'success': True,
            'customers_trained': len(customers),
            'samples_trained': len(features_df),
            'auc': auc,
            'model_version': model_version
        }
    
    def _log_retraining(self, customers_trained, samples_trained, auc_score, 
                       precision_score, recall_score, f1_score, model_version, 
                       trigger_reason, duration):
        """Log retraining event"""
        query = text("""
        INSERT INTO model_retraining_log 
        (customers_trained, samples_trained, auc_score, precision_score, 
         recall_score, f1_score, model_version, trigger_reason, training_duration_seconds)
        VALUES 
        (:customers, :samples, :auc, :precision, :recall, :f1, :version, :reason, :duration)
        """)
        
        with self.engine.connect() as conn:
            conn.execute(query, {
                'customers': customers_trained,
                'samples': samples_trained,
                'auc': auc_score,
                'precision': precision_score,
                'recall': recall_score,
                'f1': f1_score,
                'version': model_version,
                'reason': trigger_reason,
                'duration': duration
            })
            conn.commit()
    
    def _update_customer_status(self, customer_ids):
        """Mark customers as included in training"""
        for customer_id in customer_ids:
            query = text("""
            INSERT INTO customer_training_status (customer_id, last_trained, included_in_training)
            VALUES (:customer_id, NOW(), TRUE)
            ON CONFLICT (customer_id) 
            DO UPDATE SET last_trained = NOW(), included_in_training = TRUE
            """)
            
            with self.engine.connect() as conn:
                conn.execute(query, {'customer_id': str(customer_id)})
                conn.commit()
    
    def get_retraining_history(self, limit=10):
        """Get recent retraining history"""
        query = f"""
        SELECT * FROM model_retraining_log
        ORDER BY retrain_date DESC
        LIMIT {limit}
        """
        
        return pd.read_sql(query, self.engine)


def main():
    """Main retraining check and execution"""
    retrainer = AutoRetrainer()
    
    # Check if retraining needed
    should_retrain, reason = retrainer.should_retrain(new_customer_threshold=50)
    
    if should_retrain:
        print(f"\n🔔 Retraining triggered: {reason}")
        result = retrainer.retrain_model(max_customers=200)
        
        if result['success']:
            print(f"\n✅ SUCCESS: Model retrained with {result['customers_trained']} customers")
            print(f"   AUC: {result['auc']:.4f}")
            print(f"   Version: {result['model_version']}")
    else:
        print("\n✅ No retraining needed at this time")
        print("   Run this script periodically or integrate with your pipeline")


if __name__ == "__main__":
    main()
