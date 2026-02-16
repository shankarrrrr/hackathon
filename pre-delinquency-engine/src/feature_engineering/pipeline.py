"""
Feature engineering pipeline for batch processing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
from datetime import datetime, timedelta
from src.feature_engineering.features import BehavioralFeatureEngineering
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()


class FeaturePipeline:
    """Orchestrate feature computation for training/inference"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.db_url)
        self.feature_engineer = BehavioralFeatureEngineering(db_url)
    
    def generate_training_features(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        output_path: str = "data/processed/features.csv"
    ):
        """Generate features for all customers in date range"""
        
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=180)
        
        print(f"🚀 Generating training features from {start_date.date()} to {end_date.date()}")
        
        # Get all customer-date combinations from labels
        query = f"""
        SELECT customer_id, observation_date
        FROM labels
        WHERE observation_date >= '{start_date}'
          AND observation_date <= '{end_date}'
        ORDER BY observation_date
        """
        
        label_df = pd.read_sql(query, self.engine)
        print(f"  Found {len(label_df)} observations")
        
        if len(label_df) == 0:
            print("❌ No labels found in date range")
            return None
        
        # Compute features in batch
        features_df = self.feature_engineer.compute_batch_features(
            customer_ids=label_df['customer_id'].tolist(),
            observation_dates=pd.to_datetime(label_df['observation_date']).tolist(),
            n_jobs=4
        )
        
        # Merge with labels
        labels_query = f"""
        SELECT customer_id, observation_date, label, days_to_default, default_amount
        FROM labels
        WHERE observation_date >= '{start_date}'
          AND observation_date <= '{end_date}'
        """
        labels_full = pd.read_sql(labels_query, self.engine)
        
        # Merge features with labels
        final_df = features_df.merge(
            labels_full,
            on=['customer_id', 'observation_date'],
            how='left'
        )
        
        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_df.to_csv(output_path, index=False)
        print(f"✅ Features saved to {output_path}")
        print(f"   Shape: {final_df.shape}")
        print(f"   Default rate: {final_df['label'].mean():.1%}")
        
        return final_df
    
    def generate_inference_features(
        self,
        customer_ids: list,
        observation_date: datetime = None
    ) -> pd.DataFrame:
        """Generate features for real-time inference"""
        
        if observation_date is None:
            observation_date = datetime.now()
        
        print(f"🔮 Generating inference features for {len(customer_ids)} customers")
        
        observation_dates = [observation_date] * len(customer_ids)
        
        features_df = self.feature_engineer.compute_batch_features(
            customer_ids=customer_ids,
            observation_dates=observation_dates,
            n_jobs=4
        )
        
        return features_df


if __name__ == "__main__":
    pipeline = FeaturePipeline()
    
    # Generate features for all available data
    features_df = pipeline.generate_training_features()
    
    if features_df is not None:
        print("\n📊 Feature Statistics:")
        print(features_df.describe())
        
        print("\n🔍 Missing Values:")
        print(features_df.isnull().sum()[features_df.isnull().sum() > 0])
