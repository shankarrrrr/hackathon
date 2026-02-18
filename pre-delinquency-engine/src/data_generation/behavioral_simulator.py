"""
Behavioral Time-Series Financial Stress Simulator
Generates realistic customer financial behavior over 12 weeks
Optimized for AWS Free Tier (1 vCPU, 1GB RAM)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class BehavioralSimulator:
    """Simulates realistic financial behavior patterns over time"""
    
    def __init__(self, n_customers: int = 30000, weeks: int = 12, seed: int = 42):
        self.n_customers = n_customers
        self.weeks = weeks
        self.seed = seed
        np.random.seed(seed)
        
    def generate_customer_profiles(self) -> pd.DataFrame:
        """Generate base customer profiles"""
        print(f"Generating {self.n_customers} customer profiles...")
        
        profiles = {
            'customer_id': [f'CUST_{i:06d}' for i in range(self.n_customers)],
            'monthly_income': np.random.lognormal(10.5, 0.5, self.n_customers),
            'account_age_months': np.random.randint(6, 120, self.n_customers),
            'credit_limit': np.random.lognormal(10, 0.8, self.n_customers),
            'baseline_savings': np.random.lognormal(9, 1.2, self.n_customers),
        }
        
        return pd.DataFrame(profiles)
    
    def simulate_cash_flow_signals(self, profiles: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Simulate cash flow behavior over time"""
        n = len(profiles)
        
        # Salary credit patterns
        salary_delay_weeks = np.random.poisson(0.5, (n, self.weeks))
        salary_drop_pct = np.clip(np.random.normal(0, 0.15, (n, self.weeks)), -0.5, 0.3)
        
        # Savings behavior
        savings_change = np.random.normal(0, 0.2, (n, self.weeks))
        liquidity_ratio = np.clip(np.random.beta(2, 5, (n, self.weeks)), 0.01, 1)
        
        return {
            'salary_delay_weeks': salary_delay_weeks,
            'salary_drop_pct': salary_drop_pct,
            'savings_change': savings_change,
            'liquidity_ratio': liquidity_ratio
        }
    
    def simulate_payment_stress(self, profiles: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Simulate payment stress indicators"""
        n = len(profiles)
        
        # Payment delays
        utility_delay_days = np.random.poisson(1, (n, self.weeks))
        emi_delay_days = np.random.poisson(0.8, (n, self.weeks))
        
        # Failed transactions
        failed_autodebits = np.random.poisson(0.3, (n, self.weeks))
        
        # Credit card behavior
        cc_min_payment_ratio = np.clip(np.random.beta(8, 2, (n, self.weeks)), 0, 1)
        
        return {
            'utility_delay_days': utility_delay_days,
            'emi_delay_days': emi_delay_days,
            'failed_autodebits': failed_autodebits,
            'cc_min_payment_ratio': cc_min_payment_ratio
        }
    
    def simulate_spending_signals(self, profiles: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Simulate spending pattern changes"""
        n = len(profiles)
        
        # Spending changes
        discretionary_drop_pct = np.clip(np.random.normal(0, 0.25, (n, self.weeks)), -0.6, 0.5)
        atm_withdrawal_spike = np.random.poisson(1.5, (n, self.weeks))
        
        # Risk behaviors
        cash_hoarding_flag = (np.random.random((n, self.weeks)) > 0.85).astype(int)
        lending_app_transfers = np.random.poisson(0.4, (n, self.weeks))
        gambling_txns = np.random.poisson(0.2, (n, self.weeks))
        
        return {
            'discretionary_drop_pct': discretionary_drop_pct,
            'atm_withdrawal_spike': atm_withdrawal_spike,
            'cash_hoarding_flag': cash_hoarding_flag,
            'lending_app_transfers': lending_app_transfers,
            'gambling_txns': gambling_txns
        }
    
    def simulate_cross_product_signals(self, profiles: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Simulate cross-product stress indicators"""
        n = len(profiles)
        
        # Credit utilization
        credit_util_change = np.clip(np.random.normal(0, 0.2, (n, self.weeks)), -0.5, 0.8)
        
        # Multi-account stress
        multi_account_stress = np.clip(np.random.beta(2, 8, (n, self.weeks)), 0, 1)
        
        # Channel anomalies
        channel_anomaly_score = np.clip(np.random.beta(1, 9, (n, self.weeks)), 0, 1)
        
        return {
            'credit_util_change': credit_util_change,
            'multi_account_stress': multi_account_stress,
            'channel_anomaly_score': channel_anomaly_score
        }
    
    def aggregate_features(self, 
                          profiles: pd.DataFrame,
                          cash_flow: Dict,
                          payment_stress: Dict,
                          spending: Dict,
                          cross_product: Dict) -> pd.DataFrame:
        """Aggregate time-series into ML-ready features"""
        print("Aggregating features...")
        
        features = []
        
        for i in range(len(profiles)):
            # Aggregate over last 4 weeks (most recent)
            recent_weeks = slice(-4, None)
            
            feat = {
                'customer_id': profiles.iloc[i]['customer_id'],
                'monthly_income': profiles.iloc[i]['monthly_income'],
                'account_age_months': profiles.iloc[i]['account_age_months'],
                
                # Cash flow aggregates
                'avg_salary_delay': cash_flow['salary_delay_weeks'][i, recent_weeks].mean(),
                'max_salary_delay': cash_flow['salary_delay_weeks'][i, recent_weeks].max(),
                'avg_salary_drop': cash_flow['salary_drop_pct'][i, recent_weeks].mean(),
                'min_salary_drop': cash_flow['salary_drop_pct'][i, recent_weeks].min(),
                'savings_volatility': cash_flow['savings_change'][i, recent_weeks].std(),
                'avg_liquidity_ratio': cash_flow['liquidity_ratio'][i, recent_weeks].mean(),
                'min_liquidity_ratio': cash_flow['liquidity_ratio'][i, recent_weeks].min(),
                
                # Payment stress aggregates
                'avg_utility_delay': payment_stress['utility_delay_days'][i, recent_weeks].mean(),
                'max_utility_delay': payment_stress['utility_delay_days'][i, recent_weeks].max(),
                'avg_emi_delay': payment_stress['emi_delay_days'][i, recent_weeks].mean(),
                'max_emi_delay': payment_stress['emi_delay_days'][i, recent_weeks].max(),
                'total_failed_autodebits': payment_stress['failed_autodebits'][i, recent_weeks].sum(),
                'avg_cc_min_payment': payment_stress['cc_min_payment_ratio'][i, recent_weeks].mean(),
                'min_cc_min_payment': payment_stress['cc_min_payment_ratio'][i, recent_weeks].min(),
                
                # Spending aggregates
                'avg_discretionary_drop': spending['discretionary_drop_pct'][i, recent_weeks].mean(),
                'max_discretionary_drop': spending['discretionary_drop_pct'][i, recent_weeks].max(),
                'total_atm_spikes': spending['atm_withdrawal_spike'][i, recent_weeks].sum(),
                'cash_hoarding_weeks': spending['cash_hoarding_flag'][i, recent_weeks].sum(),
                'total_lending_app_txns': spending['lending_app_transfers'][i, recent_weeks].sum(),
                'total_gambling_txns': spending['gambling_txns'][i, recent_weeks].sum(),
                
                # Cross-product aggregates
                'avg_credit_util_change': cross_product['credit_util_change'][i, recent_weeks].mean(),
                'max_credit_util_change': cross_product['credit_util_change'][i, recent_weeks].max(),
                'avg_multi_account_stress': cross_product['multi_account_stress'][i, recent_weeks].mean(),
                'max_multi_account_stress': cross_product['multi_account_stress'][i, recent_weeks].max(),
                'avg_channel_anomaly': cross_product['channel_anomaly_score'][i, recent_weeks].mean(),
                'max_channel_anomaly': cross_product['channel_anomaly_score'][i, recent_weeks].max(),
                
                # Trend features (comparing recent 4 weeks to previous 4 weeks)
                'salary_delay_trend': (
                    cash_flow['salary_delay_weeks'][i, -4:].mean() - 
                    cash_flow['salary_delay_weeks'][i, -8:-4].mean()
                ),
                'payment_stress_trend': (
                    payment_stress['utility_delay_days'][i, -4:].mean() - 
                    payment_stress['utility_delay_days'][i, -8:-4].mean()
                ),
                'spending_stress_trend': (
                    spending['discretionary_drop_pct'][i, -4:].mean() - 
                    spending['discretionary_drop_pct'][i, -8:-4].mean()
                ),
            }
            
            features.append(feat)
        
        return pd.DataFrame(features)
    
    def generate_labels(self, features: pd.DataFrame) -> np.ndarray:
        """Generate probabilistic labels using logistic-style function"""
        print("Generating labels...")
        
        # Compute stress score (weighted combination)
        stress_score = (
            0.15 * features['avg_salary_delay'] +
            0.12 * features['max_salary_delay'] +
            0.10 * np.abs(features['avg_salary_drop']) +
            0.08 * features['savings_volatility'] +
            0.10 * (1 - features['avg_liquidity_ratio']) +
            0.08 * features['avg_utility_delay'] +
            0.07 * features['total_failed_autodebits'] +
            0.06 * (1 - features['avg_cc_min_payment']) +
            0.08 * np.abs(features['avg_discretionary_drop']) +
            0.05 * features['total_lending_app_txns'] +
            0.06 * features['avg_credit_util_change'] +
            0.05 * features['avg_multi_account_stress']
        )
        
        # Normalize to 0-1
        stress_score = (stress_score - stress_score.min()) / (stress_score.max() - stress_score.min())
        
        # Add noise to prevent perfect separation
        noise = np.random.normal(0, 0.15, len(stress_score))
        stress_score_noisy = np.clip(stress_score + noise, 0, 1)
        
        # Convert to probability using logistic function
        # Adjust intercept to get ~10% positive rate
        logit = -2.5 + 5 * stress_score_noisy
        probability = 1 / (1 + np.exp(-logit))
        
        # Generate binary labels
        labels = (np.random.random(len(probability)) < probability).astype(int)
        
        positive_rate = labels.mean()
        print(f"Generated labels: {positive_rate*100:.1f}% positive rate")
        
        return labels
    
    def generate_dataset(self) -> pd.DataFrame:
        """Main method to generate complete dataset"""
        print(f"\n{'='*60}")
        print("BEHAVIORAL FINANCIAL STRESS SIMULATOR")
        print(f"{'='*60}")
        print(f"Customers: {self.n_customers:,}")
        print(f"Time window: {self.weeks} weeks")
        print(f"{'='*60}\n")
        
        # Generate profiles
        profiles = self.generate_customer_profiles()
        
        # Simulate behaviors
        print("Simulating behavioral signals...")
        cash_flow = self.simulate_cash_flow_signals(profiles)
        payment_stress = self.simulate_payment_stress(profiles)
        spending = self.simulate_spending_signals(profiles)
        cross_product = self.simulate_cross_product_signals(profiles)
        
        # Aggregate features
        features = self.aggregate_features(
            profiles, cash_flow, payment_stress, spending, cross_product
        )
        
        # Generate labels
        labels = self.generate_labels(features)
        features['will_default_in_2_4_weeks'] = labels
        
        print(f"\n✅ Dataset generated: {len(features)} samples, {len(features.columns)} features")
        print(f"   Positive class: {labels.sum()} ({labels.mean()*100:.1f}%)")
        print(f"   Negative class: {(1-labels).sum()} ({(1-labels).mean()*100:.1f}%)")
        
        return features


def generate_and_save_dataset(n_customers: int = 30000, 
                              output_path: str = 'data/processed/behavioral_features.csv',
                              seed: int = 42) -> pd.DataFrame:
    """Generate dataset and save to CSV"""
    
    simulator = BehavioralSimulator(n_customers=n_customers, weeks=12, seed=seed)
    dataset = simulator.generate_dataset()
    
    # Save to CSV
    print(f"\n💾 Saving dataset to: {output_path}")
    dataset.to_csv(output_path, index=False)
    print(f"✅ Dataset saved successfully!")
    
    # Print summary statistics
    print(f"\n{'='*60}")
    print("DATASET SUMMARY")
    print(f"{'='*60}")
    print(f"Shape: {dataset.shape}")
    print(f"Memory usage: {dataset.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    print(f"\nFeature statistics:")
    print(dataset.describe().T[['mean', 'std', 'min', 'max']].round(3))
    
    return dataset


if __name__ == '__main__':
    # Generate dataset
    dataset = generate_and_save_dataset(n_customers=30000)
    
    print(f"\n{'='*60}")
    print("✅ DATASET GENERATION COMPLETE")
    print(f"{'='*60}")
