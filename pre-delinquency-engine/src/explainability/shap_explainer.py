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
            'salary_missed_count_90d': 'Missed Salary Payments',
            'savings_drawdown_30d_pct': 'Savings Drawdown',
            'savings_volatility_30d': 'Savings Volatility',
            'min_balance_30d': 'Minimum Balance',
            'discretionary_spend_drop_30d_pct': 'Discretionary Spending Drop',
            'merchant_diversity_30d': 'Merchant Diversity',
            'weekend_spending_ratio_30d': 'Weekend Spending',
            'utility_payment_lateness_score': 'Payment Delay Score',
            'failed_autodebit_count_30d': 'Failed Auto-payments',
            'partial_payment_ratio_30d': 'Partial Payments',
            'atm_frequency_30d': 'ATM Usage',
            'large_withdrawal_count_30d': 'Large Withdrawals',
            'cash_preference_ratio_30d': 'Cash Preference',
            'transaction_frequency_drop_30d_pct': 'Transaction Frequency Drop',
            'inactive_days_30d': 'Inactive Days',
            'transaction_consistency_score': 'Transaction Consistency',
            'financial_stress_composite': 'Financial Stress Score',
            'risk_velocity_30d': 'Risk Velocity',
            'anomaly_count_30d': 'Anomaly Count',
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
    
    def _format_feature_value(self, feature: str, value: float) -> str:
        """Format feature value for display"""
        if pd.isna(value):
            return "N/A"
        
        # Percentage features
        if 'pct' in feature or 'ratio' in feature:
            return f"{value:.1f}%"
        
        # Count features
        if 'count' in feature or 'days' in feature:
            return f"{int(value)}"
        
        # Score features
        if 'score' in feature:
            return f"{value:.2f}"
        
        return f"{value:.2f}"
    
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
