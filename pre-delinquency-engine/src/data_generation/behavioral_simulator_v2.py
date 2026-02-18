"""
Advanced Behavioral Time-Series Financial Stress Simulator V2
Production-grade with temporal realism, autocorrelation, and advanced features
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class SimulationConfig:
    """Configuration for simulation"""
    n_customers: int = 30000
    min_weeks: int = 8
    max_weeks: int = 16
    target_positive_rate: float = 0.10
    seed: int = 42
    use_autocorrelation: bool = True
    autocorr_strength: float = 0.7
    enable_shocks: bool = True
    shock_probability: float = 0.05
    use_float32: bool = True  # Memory optimization
    

class AdvancedBehavioralSimulator:
    """Production-grade behavioral simulator with temporal realism"""
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        np.random.seed(self.config.seed)
        self.dtype = np.float32 if self.config.use_float32 else np.float64
        
        # Metadata
        self.metadata = {
            'generation_timestamp': datetime.now().isoformat(),
            'simulation_seed': self.config.seed,
            'n_customers': self.config.n_customers,
            'weeks_range': f"{self.config.min_weeks}-{self.config.max_weeks}",
            'autocorrelation_enabled': self.config.use_autocorrelation,
            'shocks_enabled': self.config.enable_shocks
        }
    
    def generate_customer_profiles(self) -> pd.DataFrame:
        """Generate customer profiles with segments"""
        print(f"  → Generating {self.config.n_customers:,} customer profiles...", end='', flush=True)
        
        n = self.config.n_customers
        
        # Customer segments (income tiers)
        segments = np.random.choice(['low', 'medium', 'high'], n, p=[0.3, 0.5, 0.2])
        
        # Income varies by segment
        income_params = {
            'low': (9.5, 0.4),
            'medium': (10.5, 0.4),
            'high': (11.5, 0.5)
        }
        
        monthly_income = np.array([
            np.random.lognormal(*income_params[seg]) for seg in segments
        ], dtype=self.dtype)
        
        # Variable observation windows
        observation_weeks = np.random.randint(
            self.config.min_weeks, 
            self.config.max_weeks + 1, 
            n
        )
        
        # Random start dates (last 6 months)
        start_dates = [
            datetime.now() - timedelta(days=np.random.randint(0, 180))
            for _ in range(n)
        ]
        
        profiles = pd.DataFrame({
            'customer_id': [f'CUST_{i:06d}' for i in range(n)],
            'segment': segments,
            'monthly_income': monthly_income,
            'account_age_months': np.random.randint(6, 120, n),
            'credit_limit': np.random.lognormal(10, 0.8, n).astype(self.dtype),
            'baseline_savings': np.random.lognormal(9, 1.2, n).astype(self.dtype),
            'observation_weeks': observation_weeks,
            'start_date': start_dates
        })
        
        print(" ✓")
        return profiles
    
    def apply_autocorrelation(self, signal: np.ndarray, strength: float = 0.7) -> np.ndarray:
        """Apply AR(1) autocorrelation to time series"""
        n, weeks = signal.shape
        correlated = np.zeros_like(signal)
        correlated[:, 0] = signal[:, 0]
        
        for t in range(1, weeks):
            correlated[:, t] = strength * correlated[:, t-1] + (1 - strength) * signal[:, t]
        
        return correlated
    
    def inject_financial_shocks(self, signals: Dict[str, np.ndarray], 
                                profiles: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Inject random financial shocks (job loss, bonus, unexpected expense)"""
        if not self.config.enable_shocks:
            return signals
        
        print("  → Injecting financial shocks...", end='', flush=True)
        
        n = len(profiles)
        max_weeks = max(profiles['observation_weeks'])
        
        # Random shock events
        shock_mask = np.random.random((n, max_weeks)) < self.config.shock_probability
        shock_types = np.random.choice(['income_drop', 'expense_spike', 'bonus'], 
                                      size=(n, max_weeks))
        
        for i in range(n):
            weeks = profiles.iloc[i]['observation_weeks']
            for t in range(weeks):
                if shock_mask[i, t]:
                    shock_type = shock_types[i, t]
                    
                    if shock_type == 'income_drop':
                        # Job loss or salary cut
                        signals['salary_drop_pct'][i, t:t+4] -= 0.3
                        signals['liquidity_ratio'][i, t:t+4] *= 0.6
                        signals['failed_autodebits'][i, t:t+4] += 2
                    
                    elif shock_type == 'expense_spike':
                        # Medical emergency, car repair
                        signals['atm_withdrawal_spike'][i, t:t+2] += 5
                        signals['lending_app_transfers'][i, t:t+3] += 3
                        signals['liquidity_ratio'][i, t:t+3] *= 0.7
                    
                    elif shock_type == 'bonus':
                        # Positive shock
                        signals['salary_drop_pct'][i, t] += 0.5
                        signals['liquidity_ratio'][i, t:t+2] *= 1.3
        
        print(" ✓")
        return signals
    
    def simulate_correlated_cash_flow(self, profiles: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Simulate cash flow with autocorrelation and correlations"""
        print("  → Cash flow signals (with autocorrelation)...", end='', flush=True)
        
        n = len(profiles)
        max_weeks = max(profiles['observation_weeks'])
        
        # Base signals (i.i.d.)
        salary_delay_base = np.random.poisson(0.5, (n, max_weeks)).astype(self.dtype)
        salary_drop_base = np.clip(
            np.random.normal(0, 0.15, (n, max_weeks)), -0.5, 0.3
        ).astype(self.dtype)
        
        # Apply autocorrelation
        if self.config.use_autocorrelation:
            salary_delay = self.apply_autocorrelation(salary_delay_base, self.config.autocorr_strength)
            salary_drop = self.apply_autocorrelation(salary_drop_base, self.config.autocorr_strength)
        else:
            salary_delay = salary_delay_base
            salary_drop = salary_drop_base
        
        # Savings and liquidity (correlated with salary)
        savings_change = np.random.normal(0, 0.2, (n, max_weeks)).astype(self.dtype)
        
        # Liquidity correlated with salary drops
        liquidity_base = np.clip(np.random.beta(2, 5, (n, max_weeks)), 0.01, 1).astype(self.dtype)
        liquidity_ratio = liquidity_base * (1 - 0.3 * np.abs(salary_drop))  # Correlation
        
        print(" ✓")
        return {
            'salary_delay_weeks': salary_delay,
            'salary_drop_pct': salary_drop,
            'savings_change': savings_change,
            'liquidity_ratio': liquidity_ratio
        }
    
    def simulate_correlated_payment_stress(self, profiles: pd.DataFrame, 
                                          cash_flow: Dict) -> Dict[str, np.ndarray]:
        """Payment stress correlated with cash flow"""
        print("  → Payment stress (correlated)...", end='', flush=True)
        
        n = len(profiles)
        max_weeks = max(profiles['observation_weeks'])
        
        # Base payment delays
        utility_delay_base = np.random.poisson(1, (n, max_weeks)).astype(self.dtype)
        emi_delay_base = np.random.poisson(0.8, (n, max_weeks)).astype(self.dtype)
        
        # Correlate with salary delays
        salary_stress = cash_flow['salary_delay_weeks'] / 3.0
        utility_delay = utility_delay_base + salary_stress
        emi_delay = emi_delay_base + salary_stress * 0.8
        
        # Failed autodebits correlated with liquidity
        failed_autodebits_base = np.random.poisson(0.3, (n, max_weeks)).astype(self.dtype)
        liquidity_stress = (1 - cash_flow['liquidity_ratio']) * 2
        failed_autodebits = failed_autodebits_base + liquidity_stress
        
        # Credit card behavior
        cc_min_payment = np.clip(np.random.beta(8, 2, (n, max_weeks)), 0, 1).astype(self.dtype)
        
        print(" ✓")
        return {
            'utility_delay_days': utility_delay,
            'emi_delay_days': emi_delay,
            'failed_autodebits': failed_autodebits,
            'cc_min_payment_ratio': cc_min_payment
        }
    
    def simulate_spending_patterns(self, profiles: pd.DataFrame,
                                  cash_flow: Dict) -> Dict[str, np.ndarray]:
        """Spending patterns with correlations"""
        print("  → Spending signals (correlated)...", end='', flush=True)
        
        n = len(profiles)
        max_weeks = max(profiles['observation_weeks'])
        
        # Discretionary spending drops when liquidity is low
        discretionary_base = np.random.normal(0, 0.25, (n, max_weeks)).astype(self.dtype)
        liquidity_effect = (1 - cash_flow['liquidity_ratio']) * 0.4
        discretionary_drop = np.clip(discretionary_base - liquidity_effect, -0.6, 0.5)
        
        # ATM spikes when liquidity is low (cash hoarding)
        atm_base = np.random.poisson(1.5, (n, max_weeks)).astype(self.dtype)
        atm_withdrawal_spike = atm_base + (liquidity_effect * 3).astype(int)
        
        # Risk behaviors
        cash_hoarding = (cash_flow['liquidity_ratio'] < 0.2).astype(int)
        lending_app_transfers = np.random.poisson(0.4, (n, max_weeks)).astype(self.dtype)
        gambling_txns = np.random.poisson(0.2, (n, max_weeks)).astype(self.dtype)
        
        print(" ✓")
        return {
            'discretionary_drop_pct': discretionary_drop,
            'atm_withdrawal_spike': atm_withdrawal_spike,
            'cash_hoarding_flag': cash_hoarding,
            'lending_app_transfers': lending_app_transfers,
            'gambling_txns': gambling_txns
        }
    
    def simulate_cross_product_signals(self, profiles: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Cross-product signals"""
        print("  → Cross-product signals...", end='', flush=True)
        
        n = len(profiles)
        max_weeks = max(profiles['observation_weeks'])
        
        credit_util_change = np.clip(
            np.random.normal(0, 0.2, (n, max_weeks)), -0.5, 0.8
        ).astype(self.dtype)
        multi_account_stress = np.clip(
            np.random.beta(2, 8, (n, max_weeks)), 0, 1
        ).astype(self.dtype)
        channel_anomaly_score = np.clip(
            np.random.beta(1, 9, (n, max_weeks)), 0, 1
        ).astype(self.dtype)
        
        print(" ✓")
        return {
            'credit_util_change': credit_util_change,
            'multi_account_stress': multi_account_stress,
            'channel_anomaly_score': channel_anomaly_score
        }
    
    def compute_rolling_features_vectorized(self, signals: Dict, 
                                           profiles: pd.DataFrame) -> pd.DataFrame:
        """Vectorized rolling feature computation"""
        print("  → Computing rolling features (vectorized)...", end='', flush=True)
        
        features_list = []
        
        for i, row in profiles.iterrows():
            weeks = row['observation_weeks']
            
            # Use last 4 weeks for features
            recent = slice(max(0, weeks-4), weeks)
            prev = slice(max(0, weeks-8), max(0, weeks-4))
            
            feat = {
                'customer_id': row['customer_id'],
                'segment': row['segment'],
                'monthly_income': row['monthly_income'],
                'account_age_months': row['account_age_months'],
                'observation_weeks': weeks,
            }
            
            # Aggregate features (mean, max, min, std)
            for signal_name, signal_data in signals.items():
                recent_data = signal_data[i, recent]
                prev_data = signal_data[i, prev] if weeks > 4 else recent_data
                
                feat[f'{signal_name}_mean'] = float(np.mean(recent_data))
                feat[f'{signal_name}_max'] = float(np.max(recent_data))
                feat[f'{signal_name}_min'] = float(np.min(recent_data))
                feat[f'{signal_name}_std'] = float(np.std(recent_data))
                
                # Trend (recent vs previous)
                feat[f'{signal_name}_trend'] = float(np.mean(recent_data) - np.mean(prev_data))
                
                # Consecutive weeks above threshold
                if 'delay' in signal_name:
                    feat[f'{signal_name}_consec_high'] = self._count_consecutive(recent_data > 1)
            
            # Derived ratios
            feat['failed_autodebits_per_income'] = feat['failed_autodebits_mean'] / (row['monthly_income'] / 10000)
            feat['salary_drop_to_income_ratio'] = abs(feat['salary_drop_pct_mean']) / (row['monthly_income'] / 10000)
            feat['atm_spike_to_savings_ratio'] = feat['atm_withdrawal_spike_mean'] / (row['baseline_savings'] / 1000 + 1)
            
            # Interaction terms
            feat['salary_delay_x_failed_autodebits'] = feat['salary_delay_weeks_max'] * feat['failed_autodebits_mean']
            feat['liquidity_x_salary_drop'] = (1 - feat['liquidity_ratio_mean']) * abs(feat['salary_drop_pct_mean'])
            
            features_list.append(feat)
            
            if (i + 1) % 2000 == 0:
                print(f"\r  → Computing rolling features... {i+1}/{len(profiles)} ({(i+1)*100//len(profiles)}%)", 
                      end='', flush=True)
        
        print(f"\r  → Computing rolling features (vectorized)... ✓")
        return pd.DataFrame(features_list)
    
    @staticmethod
    def _count_consecutive(arr: np.ndarray) -> int:
        """Count maximum consecutive True values"""
        if len(arr) == 0:
            return 0
        max_count = current = 0
        for val in arr:
            if val:
                current += 1
                max_count = max(max_count, current)
            else:
                current = 0
        return max_count
    
    def generate_labels_advanced(self, features: pd.DataFrame) -> np.ndarray:
        """Advanced label generation with non-linear effects"""
        print("  → Generating labels (non-linear)...", end='', flush=True)
        
        # Compute stress score with interaction terms
        stress_score = (
            0.12 * features['salary_delay_weeks_mean'] +
            0.10 * features['salary_delay_weeks_max'] +
            0.08 * np.abs(features['salary_drop_pct_mean']) +
            0.06 * features['salary_drop_pct_std'] +
            0.10 * (1 - features['liquidity_ratio_mean']) +
            0.08 * features['utility_delay_days_mean'] +
            0.07 * features['failed_autodebits_mean'] +
            0.06 * (1 - features['cc_min_payment_ratio_mean']) +
            0.08 * np.abs(features['discretionary_drop_pct_mean']) +
            0.05 * features['lending_app_transfers_mean'] +
            0.06 * features['credit_util_change_mean'] +
            # Interaction terms (non-linear effects)
            0.08 * features['salary_delay_x_failed_autodebits'] / 10 +
            0.06 * features['liquidity_x_salary_drop']
        )
        
        # Normalize
        stress_score = (stress_score - stress_score.min()) / (stress_score.max() - stress_score.min())
        
        # Add noise
        noise = np.random.normal(0, 0.15, len(stress_score))
        stress_score_noisy = np.clip(stress_score + noise, 0, 1)
        
        # Adjust intercept to hit target positive rate
        # Use binary search to find right intercept
        intercept = -2.5
        for _ in range(10):
            logit = intercept + 5 * stress_score_noisy
            probability = 1 / (1 + np.exp(-logit))
            labels = (np.random.random(len(probability)) < probability).astype(int)
            current_rate = labels.mean()
            
            if abs(current_rate - self.config.target_positive_rate) < 0.01:
                break
            
            if current_rate < self.config.target_positive_rate:
                intercept += 0.1
            else:
                intercept -= 0.1
        
        positive_rate = labels.mean()
        print(f" ✓ ({positive_rate*100:.1f}% positive)")
        
        return labels
    
    def generate_dataset(self) -> pd.DataFrame:
        """Main method to generate complete dataset"""
        print(f"\n{'='*60}")
        print("ADVANCED BEHAVIORAL SIMULATOR V2")
        print(f"{'='*60}")
        print(f"Customers: {self.config.n_customers:,}")
        print(f"Time window: {self.config.min_weeks}-{self.config.max_weeks} weeks")
        print(f"Autocorrelation: {self.config.use_autocorrelation}")
        print(f"Financial shocks: {self.config.enable_shocks}")
        print(f"{'='*60}\n")
        
        # Generate profiles
        profiles = self.generate_customer_profiles()
        
        # Simulate correlated behaviors
        cash_flow = self.simulate_correlated_cash_flow(profiles)
        payment_stress = self.simulate_correlated_payment_stress(profiles, cash_flow)
        spending = self.simulate_spending_patterns(profiles, cash_flow)
        cross_product = self.simulate_cross_product_signals(profiles)
        
        # Combine all signals
        all_signals = {**cash_flow, **payment_stress, **spending, **cross_product}
        
        # Inject financial shocks
        all_signals = self.inject_financial_shocks(all_signals, profiles)
        
        # Compute rolling features (vectorized)
        features = self.compute_rolling_features_vectorized(all_signals, profiles)
        
        # Generate labels
        labels = self.generate_labels_advanced(features)
        features['will_default_in_2_4_weeks'] = labels
        
        # Add metadata
        features['generation_timestamp'] = self.metadata['generation_timestamp']
        
        print(f"\n✅ Dataset generated: {len(features):,} samples, {len(features.columns)} features")
        print(f"   Positive class: {labels.sum()} ({labels.mean()*100:.1f}%)")
        print(f"   Negative class: {(1-labels).sum()} ({(1-labels).mean()*100:.1f}%)")
        print(f"   Memory usage: {features.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        return features


def generate_and_save_dataset_v2(config: Optional[SimulationConfig] = None,
                                 output_path: str = 'data/processed/behavioral_features_v2.csv') -> pd.DataFrame:
    """Generate and save advanced dataset"""
    simulator = AdvancedBehavioralSimulator(config)
    df = simulator.generate_dataset()
    
    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")
    
    # Save metadata
    metadata_path = output_path.replace('.csv', '_metadata.json')
    import json
    with open(metadata_path, 'w') as f:
        json.dump(simulator.metadata, f, indent=2)
    print(f"💾 Metadata: {metadata_path}")
    
    return df


if __name__ == '__main__':
    config = SimulationConfig(
        n_customers=30000,
        min_weeks=8,
        max_weeks=16,
        target_positive_rate=0.10,
        use_autocorrelation=True,
        enable_shocks=True
    )
    
    df = generate_and_save_dataset_v2(config)
