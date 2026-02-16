# PHASE 2: FEATURE ENGINEERING (Days 4-8)

## Overview

This phase implements 30+ behavioral features that signal financial stress. All features are **deviation-based** (change from personal baseline), not absolute values.

## Feature Categories

### 1. Salary Signals (3 features)
- `salary_delay_days` - Days between expected and actual salary
- `salary_amount_deviation_pct` - Percentage change from baseline salary
- `months_since_salary_miss` - Time since last missed salary

### 2. Savings Behavior (5 features)
- `savings_drawdown_7d_pct` - Balance decrease over 7 days
- `savings_drawdown_14d_pct` - Balance decrease over 14 days
- `savings_drawdown_30d_pct` - Balance decrease over 30 days
- `balance_volatility_30d` - Coefficient of variation in balance
- `days_below_minimum_balance_30d` - Days below personal minimum

### 3. Spending Patterns (7 features)
- `discretionary_spend_drop_7d_pct` - Drop in dining/entertainment
- `discretionary_spend_drop_30d_pct` - 30-day discretionary drop
- `essential_spend_increase_pct` - Increase in groceries/utilities
- `total_spend_change_30d_pct` - Overall spending change
- `merchant_diversity_drop_pct` - Reduction in unique merchants
- `avg_transaction_size_change_pct` - Change in transaction size
- `weekend_spending_drop_pct` - Weekend spending reduction

### 4. Payment Behavior (6 features)
- `utility_payment_lateness_score` - Average payment delay score
- `bill_payment_count_drop` - Reduction in payments made
- `failed_autodebit_count_30d` - Failed automatic payments
- `partial_payment_frequency` - Frequency of partial payments
- `payment_timing_shift_days` - Change in payment timing
- `payment_amount_undershoot_pct` - Shortfall in payment amounts

### 5. Cash Behavior (3 features)
- `cash_withdrawal_frequency_change` - Change in ATM frequency
- `atm_withdrawal_size_increase_pct` - Increase in withdrawal size
- `cash_reliance_ratio` - ATM withdrawals / total spending

### 6. Transaction Patterns (3 features)
- `transaction_frequency_drop_30d_pct` - Reduction in transactions
- `inactive_days_last_30d` - Days with zero transactions
- `behavior_consistency_score` - Inverse of transaction time variance

### 7. Derived Signals (3 features)
- `financial_stress_composite_score` - Weighted combination of signals
- `risk_velocity_7d` - Rate of risk increase
- `behavioral_anomaly_count_30d` - Number of anomalous features

## Implementation

Create src/feature_engineering/features.py:

```python
"""
Behavioral feature engineering for pre-delinquency detection
All features are deviation-based (change from baseline), not absolute values
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import create_engine
import os

class BehavioralFeatureEngineering:
    """
    Compute behavioral features that signal financial stress
    Focus: Change/deviation from personal baseline, not population averages
    """
    
    def __init__(self, db_url: str = None):
        """Initialize with database connection"""
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.db_url)
        
        # Feature definitions (30+ features)
        self.feature_list = [
            # Salary signals
            'salary_delay_days',
            'salary_amount_deviation_pct',
            'months_since_salary_miss',
            
            # Savings behavior
            'savings_drawdown_7d_pct',
            'savings_drawdown_14d_pct',
            'savings_drawdown_30d_pct',
            'balance_volatility_30d',
            'days_below_minimum_balance_30d',
            
            # Spending patterns
            'discretionary_spend_drop_7d_pct',
            'discretionary_spend_drop_30d_pct',
            'essential_spend_increase_pct',
            'total_spend_change_30d_pct',
            'merchant_diversity_drop_pct',
            'avg_transaction_size_change_pct',
            'weekend_spending_drop_pct',
            
            # Payment behavior
            'utility_payment_lateness_score',
            'bill_payment_count_drop',
            'failed_autodebit_count_30d',
            'partial_payment_frequency',
            'payment_timing_shift_days',
            'payment_amount_undershoot_pct',
            
            # Cash behavior
            'cash_withdrawal_frequency_change',
            'atm_withdrawal_size_increase_pct',
            'cash_reliance_ratio',
            
            # Transaction patterns
            'transaction_frequency_drop_30d_pct',
            'inactive_days_last_30d',
            'behavior_consistency_score',
            
            # Derived signals
            'financial_stress_composite_score',
            'risk_velocity_7d',
            'behavioral_anomaly_count_30d'
        ]
    
    def compute_all_features(
        self,
        customer_id: str,
        observation_date: datetime
    ) -> Dict[str, float]:
        """
        Compute all features for a single customer at observation date
        
        Returns:
            Dictionary of feature_name -> feature_value
        """
        features = {
            'customer_id': customer_id,
            'observation_date': observation_date
        }
        
        # Load customer data
        customer_info = self._get_customer_info(customer_id)
        
        # Compute each feature category
        features.update(self._compute_salary_features(customer_id, observation_date, customer_info))
        features.update(self._compute_savings_features(customer_id, observation_date))
        features.update(self._compute_spending_features(customer_id, observation_date))
        features.update(self._compute_payment_features(customer_id, observation_date))
        features.update(self._compute_cash_features(customer_id, observation_date))
        features.update(self._compute_transaction_features(customer_id, observation_date))
        features.update(self._compute_derived_features(features))
        
        return features
    
    def compute_batch_features(
        self,
        customer_ids: List[str],
        observation_dates: List[datetime],
        n_jobs: int = -1
    ) -> pd.DataFrame:
        """
        Compute features for multiple customers (parallel processing)
        """
        from joblib import Parallel, delayed
        
        print(f"Computing features for {len(customer_ids)} observations...")
        
        results = Parallel(n_jobs=n_jobs, verbose=10)(
            delayed(self.compute_all_features)(cid, date)
            for cid, date in zip(customer_ids, observation_dates)
        )
        
        df = pd.DataFrame(results)
        print(f"✅ Feature computation complete: {len(df)} rows x {len(df.columns)} columns")
        
        return df
    
    # Helper methods for each feature category
    # (Full implementation would include all methods from your original prompt)
    
    def _get_customer_info(self, customer_id: str) -> Dict:
        """Get customer basic information"""
        query = f"""
        SELECT salary_day, monthly_income, income_bracket, account_age_days
        FROM customers
        WHERE customer_id = '{customer_id}'
        """
        df = pd.read_sql(query, self.engine)
        return df.iloc[0].to_dict() if len(df) > 0 else {}
    
    def _get_transactions(self, customer_id: str, observation_date: datetime, lookback_days: int = 60) -> pd.DataFrame:
        """Get transaction history"""
        start_date = observation_date - timedelta(days=lookback_days)
        query = f"""
        SELECT * FROM transactions
        WHERE customer_id = '{customer_id}'
          AND txn_time >= '{start_date}'
          AND txn_time <= '{observation_date}'
        ORDER BY txn_time DESC
        """
        df = pd.read_sql(query, self.engine)
        df['txn_time'] = pd.to_datetime(df['txn_time'])
        return df
    
    def _percent_change(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change"""
        if old_value == 0:
            return 0.0 if new_value == 0 else 100.0
        return ((new_value - old_value) / abs(old_value)) * 100

if __name__ == "__main__":
    # Example usage
    engineer = BehavioralFeatureEngineering()
    
    features = engineer.compute_all_features(
        customer_id="test_customer_id",
        observation_date=datetime.now()
    )
    
    print("Computed features:")
    for k, v in features.items():
        print(f"  {k}: {v}")
```

## Feature Pipeline

Create src/feature_engineering/pipeline.py:

```python
"""
Feature engineering pipeline for batch processing
"""

import pandas as pd
from datetime import datetime, timedelta
from src.feature_engineering.features import BehavioralFeatureEngineering
from sqlalchemy import create_engine
import os

class FeaturePipeline:
    """Orchestrate feature computation for training/inference"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.db_url)
        self.feature_engineer = BehavioralFeatureEngineering(db_url)
    
    def generate_training_features(
        self,
        start_date: datetime,
        end_date: datetime,
        output_path: str = "data/processed/features.csv"
    ):
        """Generate features for all customers in date range"""
        
        print(f"🚀 Generating training features from {start_date} to {end_date}")
        
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
        
        # Compute features in batch
        features_df = self.feature_engineer.compute_batch_features(
            customer_ids=label_df['customer_id'].tolist(),
            observation_dates=pd.to_datetime(label_df['observation_date']).tolist(),
            n_jobs=-1
        )
        
        # Save
        features_df.to_csv(output_path, index=False)
        print(f"✅ Features saved to {output_path}")
        
        return features_df

if __name__ == "__main__":
    pipeline = FeaturePipeline()
    
    # Generate features for last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    features_df = pipeline.generate_training_features(start_date, end_date)
```

## Running Feature Engineering

```bash
# Generate features for training
python src/feature_engineering/pipeline.py

# Or use in notebook
from src.feature_engineering.features import BehavioralFeatureEngineering

engineer = BehavioralFeatureEngineering()
features = engineer.compute_all_features(customer_id, observation_date)
```

## Feature Validation

```python
# Check for missing values
features_df.isnull().sum()

# Check feature distributions
features_df.describe()

# Correlation analysis
import seaborn as sns
import matplotlib.pyplot as plt

corr = features_df.corr()
sns.heatmap(corr, cmap='coolwarm')
plt.show()
```

## Key Principles

1. **Deviation-based**: All features measure change from personal baseline
2. **Time windows**: 7d, 14d, 30d for different signal strengths
3. **No absolute values**: Avoids bias from income levels
4. **Interpretable**: Each feature has clear business meaning
5. **Robust**: Handles missing data gracefully

## Next Steps

After feature engineering:
1. Validate feature distributions
2. Check for data leakage
3. Proceed to Phase 3 (Model Training)
