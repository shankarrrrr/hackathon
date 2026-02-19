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
from dotenv import load_dotenv

load_dotenv()


class BehavioralFeatureEngineering:
    """
    Compute behavioral features that signal financial stress
    Focus: Change/deviation from personal baseline, not population averages
    """
    
    def __init__(self, db_url: str = None):
        """Initialize with database connection"""
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = None  # Will be created on demand
        
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
        n_jobs: int = 4
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
    
    # ==================== HELPER METHODS ====================
    
    def _get_engine(self):
        """Get or create database engine"""
        if self.engine is None:
            self.engine = create_engine(self.db_url)
        return self.engine
    
    def _get_customer_info(self, customer_id: str) -> Dict:
        """Get customer basic information"""
        query = f"""
        SELECT salary_day, monthly_income, income_bracket, account_age_days
        FROM customers
        WHERE customer_id = '{customer_id}'
        """
        df = pd.read_sql(query, self._get_engine())
        return df.iloc[0].to_dict() if len(df) > 0 else {}
    
    def _get_transactions(self, customer_id: str, observation_date: datetime, lookback_days: int = 90) -> pd.DataFrame:
        """Get transaction history"""
        start_date = observation_date - timedelta(days=lookback_days)
        query = f"""
        SELECT * FROM transactions
        WHERE customer_id = '{customer_id}'
          AND txn_time >= '{start_date}'
          AND txn_time <= '{observation_date}'
        ORDER BY txn_time DESC
        """
        df = pd.read_sql(query, self._get_engine())
        if len(df) > 0:
            df['txn_time'] = pd.to_datetime(df['txn_time']).dt.tz_localize(None)
        return df
    
    def _get_payments(self, customer_id: str, observation_date: datetime, lookback_days: int = 90) -> pd.DataFrame:
        """Get payment history"""
        start_date = observation_date - timedelta(days=lookback_days)
        query = f"""
        SELECT * FROM payments
        WHERE customer_id = '{customer_id}'
          AND due_date >= '{start_date}'
          AND due_date <= '{observation_date}'
        ORDER BY due_date DESC
        """
        df = pd.read_sql(query, self._get_engine())
        if len(df) > 0:
            df['due_date'] = pd.to_datetime(df['due_date']).dt.tz_localize(None)
            df['paid_date'] = pd.to_datetime(df['paid_date']).dt.tz_localize(None)
        return df
    
    def _percent_change(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change"""
        if old_value == 0:
            return 0.0 if new_value == 0 else 100.0
        return ((new_value - old_value) / abs(old_value)) * 100
    
    # ==================== SALARY FEATURES ====================
    
    def _compute_salary_features(self, customer_id: str, observation_date: datetime, customer_info: Dict) -> Dict:
        """Compute salary-related features"""
        features = {}
        
        txns = self._get_transactions(customer_id, observation_date, lookback_days=90)
        salary_txns = txns[txns['category'] == 'salary']
        
        if len(salary_txns) == 0:
            features['salary_delay_days'] = 0.0
            features['salary_amount_deviation_pct'] = 0.0
            features['months_since_salary_miss'] = 0.0
            return features
        
        # Expected salary day
        expected_day = customer_info.get('salary_day', 1)
        monthly_income = customer_info.get('monthly_income', 0)
        
        # Recent salary (last 30 days)
        recent_salary = salary_txns[
            salary_txns['txn_time'] >= (observation_date - timedelta(days=30))
        ]
        
        if len(recent_salary) > 0:
            last_salary = recent_salary.iloc[0]
            actual_day = last_salary['txn_time'].day
            features['salary_delay_days'] = max(0, actual_day - expected_day)
            features['salary_amount_deviation_pct'] = self._percent_change(monthly_income, last_salary['amount'])
        else:
            features['salary_delay_days'] = 30.0  # Missed salary
            features['salary_amount_deviation_pct'] = -100.0
        
        # Months since salary miss
        if len(salary_txns) >= 2:
            salary_dates = salary_txns['txn_time'].dt.to_period('M')
            expected_months = pd.period_range(
                start=salary_dates.min(),
                end=salary_dates.max(),
                freq='M'
            )
            missing_months = len(expected_months) - len(salary_dates.unique())
            features['months_since_salary_miss'] = missing_months
        else:
            features['months_since_salary_miss'] = 0.0
        
        return features
    
    # ==================== SAVINGS FEATURES ====================
    
    def _compute_savings_features(self, customer_id: str, observation_date: datetime) -> Dict:
        """Compute savings/balance features"""
        features = {}
        
        txns = self._get_transactions(customer_id, observation_date, lookback_days=60)
        
        if len(txns) == 0:
            return {k: 0.0 for k in [
                'savings_drawdown_7d_pct', 'savings_drawdown_14d_pct',
                'savings_drawdown_30d_pct', 'balance_volatility_30d',
                'days_below_minimum_balance_30d'
            ]}
        
        # Calculate daily balances
        txns = txns.sort_values('txn_time')
        txns['balance_change'] = txns.apply(
            lambda x: x['amount'] if x['txn_type'] == 'credit' else -x['amount'],
            axis=1
        )
        txns['balance'] = txns['balance_change'].cumsum()
        
        # Drawdown calculations
        balance_7d_ago = txns[txns['txn_time'] <= (observation_date - timedelta(days=7))]['balance'].iloc[-1] if len(txns[txns['txn_time'] <= (observation_date - timedelta(days=7))]) > 0 else 0
        balance_14d_ago = txns[txns['txn_time'] <= (observation_date - timedelta(days=14))]['balance'].iloc[-1] if len(txns[txns['txn_time'] <= (observation_date - timedelta(days=14))]) > 0 else 0
        balance_30d_ago = txns[txns['txn_time'] <= (observation_date - timedelta(days=30))]['balance'].iloc[-1] if len(txns[txns['txn_time'] <= (observation_date - timedelta(days=30))]) > 0 else 0
        current_balance = txns['balance'].iloc[-1]
        
        features['savings_drawdown_7d_pct'] = self._percent_change(balance_7d_ago, current_balance) if balance_7d_ago != 0 else 0.0
        features['savings_drawdown_14d_pct'] = self._percent_change(balance_14d_ago, current_balance) if balance_14d_ago != 0 else 0.0
        features['savings_drawdown_30d_pct'] = self._percent_change(balance_30d_ago, current_balance) if balance_30d_ago != 0 else 0.0
        
        # Balance volatility (coefficient of variation)
        recent_30d = txns[txns['txn_time'] >= (observation_date - timedelta(days=30))]
        if len(recent_30d) > 0 and recent_30d['balance'].mean() != 0:
            features['balance_volatility_30d'] = (recent_30d['balance'].std() / abs(recent_30d['balance'].mean())) * 100
        else:
            features['balance_volatility_30d'] = 0.0
        
        # Days below minimum balance
        if len(recent_30d) > 0:
            min_balance = recent_30d['balance'].min()
            baseline_min = txns[txns['txn_time'] < (observation_date - timedelta(days=30))]['balance'].quantile(0.1) if len(txns[txns['txn_time'] < (observation_date - timedelta(days=30))]) > 0 else min_balance
            features['days_below_minimum_balance_30d'] = len(recent_30d[recent_30d['balance'] < baseline_min])
        else:
            features['days_below_minimum_balance_30d'] = 0.0
        
        return features
    
    # ==================== SPENDING FEATURES ====================
    
    def _compute_spending_features(self, customer_id: str, observation_date: datetime) -> Dict:
        """Compute spending pattern features"""
        features = {}
        
        txns = self._get_transactions(customer_id, observation_date, lookback_days=60)
        debits = txns[txns['txn_type'] == 'debit']
        
        if len(debits) == 0:
            return {k: 0.0 for k in [
                'discretionary_spend_drop_7d_pct', 'discretionary_spend_drop_30d_pct',
                'essential_spend_increase_pct', 'total_spend_change_30d_pct',
                'merchant_diversity_drop_pct', 'avg_transaction_size_change_pct',
                'weekend_spending_drop_pct'
            ]}
        
        # Discretionary categories
        discretionary = ['dining', 'entertainment', 'shopping']
        essential = ['groceries', 'utilities', 'rent']
        
        # Recent vs baseline periods
        recent_7d = debits[debits['txn_time'] >= (observation_date - timedelta(days=7))]
        recent_30d = debits[debits['txn_time'] >= (observation_date - timedelta(days=30))]
        baseline = debits[debits['txn_time'] < (observation_date - timedelta(days=30))]
        
        # Discretionary spending
        disc_recent_7d = recent_7d[recent_7d['category'].isin(discretionary)]['amount'].sum()
        disc_baseline_7d = baseline[baseline['category'].isin(discretionary)]['amount'].sum() / (len(baseline) / 7) if len(baseline) > 0 else 0
        features['discretionary_spend_drop_7d_pct'] = self._percent_change(disc_baseline_7d, disc_recent_7d)
        
        disc_recent_30d = recent_30d[recent_30d['category'].isin(discretionary)]['amount'].sum()
        disc_baseline_30d = baseline[baseline['category'].isin(discretionary)]['amount'].sum() / (len(baseline) / 30) if len(baseline) > 0 else 0
        features['discretionary_spend_drop_30d_pct'] = self._percent_change(disc_baseline_30d, disc_recent_30d)
        
        # Essential spending
        ess_recent = recent_30d[recent_30d['category'].isin(essential)]['amount'].sum()
        ess_baseline = baseline[baseline['category'].isin(essential)]['amount'].sum() / (len(baseline) / 30) if len(baseline) > 0 else 0
        features['essential_spend_increase_pct'] = self._percent_change(ess_baseline, ess_recent)
        
        # Total spending
        total_recent = recent_30d['amount'].sum()
        total_baseline = baseline['amount'].sum() / (len(baseline) / 30) if len(baseline) > 0 else 0
        features['total_spend_change_30d_pct'] = self._percent_change(total_baseline, total_recent)
        
        # Merchant diversity
        merchants_recent = recent_30d['merchant_id'].nunique()
        merchants_baseline = baseline['merchant_id'].nunique() / (len(baseline) / 30) if len(baseline) > 0 else 0
        features['merchant_diversity_drop_pct'] = self._percent_change(merchants_baseline, merchants_recent)
        
        # Average transaction size
        avg_recent = recent_30d['amount'].mean() if len(recent_30d) > 0 else 0
        avg_baseline = baseline['amount'].mean() if len(baseline) > 0 else 0
        features['avg_transaction_size_change_pct'] = self._percent_change(avg_baseline, avg_recent)
        
        # Weekend spending
        recent_30d['is_weekend'] = recent_30d['txn_time'].dt.dayofweek >= 5
        baseline['is_weekend'] = baseline['txn_time'].dt.dayofweek >= 5
        weekend_recent = recent_30d[recent_30d['is_weekend']]['amount'].sum()
        weekend_baseline = baseline[baseline['is_weekend']]['amount'].sum() / (len(baseline) / 30) if len(baseline) > 0 else 0
        features['weekend_spending_drop_pct'] = self._percent_change(weekend_baseline, weekend_recent)
        
        return features
    
    # ==================== PAYMENT FEATURES ====================
    
    def _compute_payment_features(self, customer_id: str, observation_date: datetime) -> Dict:
        """Compute payment behavior features"""
        features = {}
        
        payments = self._get_payments(customer_id, observation_date, lookback_days=90)
        
        if len(payments) == 0:
            return {k: 0.0 for k in [
                'utility_payment_lateness_score', 'bill_payment_count_drop',
                'failed_autodebit_count_30d', 'partial_payment_frequency',
                'payment_timing_shift_days', 'payment_amount_undershoot_pct'
            ]}
        
        recent_30d = payments[payments['due_date'] >= (observation_date - timedelta(days=30))]
        baseline = payments[payments['due_date'] < (observation_date - timedelta(days=30))]
        
        # Payment lateness score
        if len(recent_30d) > 0:
            features['utility_payment_lateness_score'] = recent_30d['days_late'].mean()
        else:
            features['utility_payment_lateness_score'] = 0.0
        
        # Payment count drop
        count_recent = len(recent_30d)
        count_baseline = len(baseline) / (len(baseline) / 30) if len(baseline) > 0 else 0
        features['bill_payment_count_drop'] = count_baseline - count_recent
        
        # Failed payments
        features['failed_autodebit_count_30d'] = len(recent_30d[recent_30d['status'] == 'missed'])
        
        # Partial payments
        if len(recent_30d) > 0:
            features['partial_payment_frequency'] = len(recent_30d[recent_30d['status'] == 'partial']) / len(recent_30d)
        else:
            features['partial_payment_frequency'] = 0.0
        
        # Payment timing shift
        if len(recent_30d) > 0 and len(baseline) > 0:
            recent_timing = (recent_30d['paid_date'] - recent_30d['due_date']).dt.days.mean()
            baseline_timing = (baseline['paid_date'] - baseline['due_date']).dt.days.mean()
            features['payment_timing_shift_days'] = recent_timing - baseline_timing
        else:
            features['payment_timing_shift_days'] = 0.0
        
        # Payment undershoot
        if len(recent_30d) > 0:
            undershoot = recent_30d[recent_30d['paid_amount'].notna()]
            if len(undershoot) > 0:
                features['payment_amount_undershoot_pct'] = ((undershoot['amount'] - undershoot['paid_amount']) / undershoot['amount'] * 100).mean()
            else:
                features['payment_amount_undershoot_pct'] = 0.0
        else:
            features['payment_amount_undershoot_pct'] = 0.0
        
        return features
    
    # ==================== CASH FEATURES ====================
    
    def _compute_cash_features(self, customer_id: str, observation_date: datetime) -> Dict:
        """Compute cash withdrawal features"""
        features = {}
        
        txns = self._get_transactions(customer_id, observation_date, lookback_days=60)
        atm_txns = txns[(txns['channel'] == 'atm') & (txns['txn_type'] == 'debit')]
        
        if len(atm_txns) == 0:
            return {k: 0.0 for k in [
                'cash_withdrawal_frequency_change',
                'atm_withdrawal_size_increase_pct',
                'cash_reliance_ratio'
            ]}
        
        recent_30d = atm_txns[atm_txns['txn_time'] >= (observation_date - timedelta(days=30))]
        baseline = atm_txns[atm_txns['txn_time'] < (observation_date - timedelta(days=30))]
        
        # Frequency change
        freq_recent = len(recent_30d)
        freq_baseline = len(baseline) / (len(baseline) / 30) if len(baseline) > 0 else 0
        features['cash_withdrawal_frequency_change'] = freq_recent - freq_baseline
        
        # Withdrawal size
        size_recent = recent_30d['amount'].mean() if len(recent_30d) > 0 else 0
        size_baseline = baseline['amount'].mean() if len(baseline) > 0 else 0
        features['atm_withdrawal_size_increase_pct'] = self._percent_change(size_baseline, size_recent)
        
        # Cash reliance ratio
        all_debits = txns[(txns['txn_type'] == 'debit') & (txns['txn_time'] >= (observation_date - timedelta(days=30)))]
        if len(all_debits) > 0:
            features['cash_reliance_ratio'] = recent_30d['amount'].sum() / all_debits['amount'].sum()
        else:
            features['cash_reliance_ratio'] = 0.0
        
        return features
    
    # ==================== TRANSACTION PATTERN FEATURES ====================
    
    def _compute_transaction_features(self, customer_id: str, observation_date: datetime) -> Dict:
        """Compute transaction pattern features"""
        features = {}
        
        txns = self._get_transactions(customer_id, observation_date, lookback_days=60)
        
        if len(txns) == 0:
            return {k: 0.0 for k in [
                'transaction_frequency_drop_30d_pct',
                'inactive_days_last_30d',
                'behavior_consistency_score'
            ]}
        
        recent_30d = txns[txns['txn_time'] >= (observation_date - timedelta(days=30))]
        baseline = txns[txns['txn_time'] < (observation_date - timedelta(days=30))]
        
        # Frequency drop
        freq_recent = len(recent_30d)
        freq_baseline = len(baseline) / (len(baseline) / 30) if len(baseline) > 0 else 0
        features['transaction_frequency_drop_30d_pct'] = self._percent_change(freq_baseline, freq_recent)
        
        # Inactive days
        if len(recent_30d) > 0:
            date_range = pd.date_range(
                start=observation_date - timedelta(days=30),
                end=observation_date,
                freq='D'
            )
            active_days = recent_30d['txn_time'].dt.date.unique()
            features['inactive_days_last_30d'] = len(date_range) - len(active_days)
        else:
            features['inactive_days_last_30d'] = 30.0
        
        # Behavior consistency (inverse of time variance)
        if len(recent_30d) > 1:
            txn_hours = recent_30d['txn_time'].dt.hour
            hour_variance = txn_hours.var()
            features['behavior_consistency_score'] = 100 / (1 + hour_variance) if hour_variance > 0 else 100.0
        else:
            features['behavior_consistency_score'] = 0.0
        
        return features
    
    # ==================== DERIVED FEATURES ====================
    
    def _compute_derived_features(self, features: Dict) -> Dict:
        """Compute composite and derived features"""
        derived = {}
        
        # Financial stress composite score (weighted combination)
        stress_components = [
            features.get('savings_drawdown_30d_pct', 0) * 0.2,
            features.get('discretionary_spend_drop_30d_pct', 0) * 0.15,
            features.get('utility_payment_lateness_score', 0) * 0.25,
            features.get('failed_autodebit_count_30d', 0) * 10 * 0.2,
            features.get('salary_delay_days', 0) * 0.1,
            features.get('inactive_days_last_30d', 0) * 0.1
        ]
        derived['financial_stress_composite_score'] = sum(stress_components)
        
        # Risk velocity (7-day change in stress)
        # Simplified: use recent drawdown as proxy
        derived['risk_velocity_7d'] = features.get('savings_drawdown_7d_pct', 0)
        
        # Behavioral anomaly count (features beyond 2 std devs)
        anomaly_count = 0
        thresholds = {
            'savings_drawdown_30d_pct': -50,
            'discretionary_spend_drop_30d_pct': -40,
            'utility_payment_lateness_score': 7,
            'failed_autodebit_count_30d': 2,
            'inactive_days_last_30d': 10
        }
        
        for feature, threshold in thresholds.items():
            value = features.get(feature, 0)
            if abs(value) > abs(threshold):
                anomaly_count += 1
        
        derived['behavioral_anomaly_count_30d'] = anomaly_count
        
        return derived


if __name__ == "__main__":
    # Example usage
    engineer = BehavioralFeatureEngineering()
    
    # Get a sample customer
    query = "SELECT customer_id FROM customers LIMIT 1"
    sample_customer = pd.read_sql(query, engineer.engine).iloc[0]['customer_id']
    
    features = engineer.compute_all_features(
        customer_id=sample_customer,
        observation_date=datetime.now()
    )
    
    print("Computed features:")
    for k, v in features.items():
        print(f"  {k}: {v}")
