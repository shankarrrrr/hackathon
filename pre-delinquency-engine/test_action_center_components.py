"""
Test script to verify Action Center page components with sample data.
This script tests all components without requiring a database connection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add dashboard directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard'))

# Import functions from app.py
from dashboard.app import (
    calculate_kpi_metrics,
    calculate_intervention_simulation,
    calculate_portfolio_risk_drivers,
    trigger_interventions_for_critical_customers
)


def generate_sample_risk_scores(n_customers=100):
    """Generate sample risk score data for testing."""
    np.random.seed(42)
    
    risk_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    risk_level_weights = [0.5, 0.3, 0.15, 0.05]
    
    features = [
        'payment_delay', 'credit_utilization', 'missed_payment',
        'account_age', 'income_volatility', 'bureau_score',
        'payment_history', 'debt_to_income'
    ]
    
    data = {
        'customer_id': [f'cust-{i:04d}' for i in range(n_customers)],
        'risk_score': np.random.beta(2, 5, n_customers),  # Skewed towards lower scores
        'risk_level': np.random.choice(risk_levels, n_customers, p=risk_level_weights),
        'score_date': [datetime.now() - timedelta(hours=np.random.randint(0, 24)) for _ in range(n_customers)],
        'top_feature_1': np.random.choice(features, n_customers),
        'top_feature_1_impact': np.random.uniform(-0.3, 0.5, n_customers)
    }
    
    df = pd.DataFrame(data)
    
    # Adjust risk_score to match risk_level
    df.loc[df['risk_level'] == 'LOW', 'risk_score'] = np.random.uniform(0.0, 0.4, (df['risk_level'] == 'LOW').sum())
    df.loc[df['risk_level'] == 'MEDIUM', 'risk_score'] = np.random.uniform(0.4, 0.6, (df['risk_level'] == 'MEDIUM').sum())
    df.loc[df['risk_level'] == 'HIGH', 'risk_score'] = np.random.uniform(0.6, 0.8, (df['risk_level'] == 'HIGH').sum())
    df.loc[df['risk_level'] == 'CRITICAL', 'risk_score'] = np.random.uniform(0.8, 1.0, (df['risk_level'] == 'CRITICAL').sum())
    
    return df


def generate_sample_rising_risk(n_customers=20):
    """Generate sample rising risk customer data."""
    np.random.seed(43)
    
    features = [
        'payment_delay', 'credit_utilization', 'missed_payment',
        'bureau_score', 'income_volatility'
    ]
    
    data = {
        'customer_id': [f'cust-{i:04d}' for i in range(n_customers)],
        'risk_score': np.random.uniform(0.6, 0.95, n_customers),
        'risk_level': np.random.choice(['HIGH', 'CRITICAL'], n_customers, p=[0.7, 0.3]),
        'top_feature_1': np.random.choice(features, n_customers),
        'risk_change': np.random.uniform(0.05, 0.25, n_customers)
    }
    
    df = pd.DataFrame(data)
    df = df.sort_values('risk_score', ascending=False)
    
    return df


def test_critical_action_panel():
    """Test Critical Action Panel component."""
    print("\n" + "="*80)
    print("TEST 1: Critical Action Panel")
    print("="*80)
    
    df = generate_sample_risk_scores(100)
    critical_df = df[df['risk_level'].isin(['HIGH', 'CRITICAL'])]
    
    print(f"✓ Total customers: {len(df)}")
    print(f"✓ Critical customers (HIGH/CRITICAL): {len(critical_df)}")
    print(f"  - HIGH: {len(df[df['risk_level'] == 'HIGH'])}")
    print(f"  - CRITICAL: {len(df[df['risk_level'] == 'CRITICAL'])}")
    
    if len(critical_df) > 0:
        print(f"✓ Critical Action Panel would display {len(critical_df)} customers")
        print("✓ Three action buttons would be rendered:")
        print("  - View Critical Customers")
        print("  - Trigger Interventions")
        print("  - Assign to Agent")
    else:
        print("⚠ No critical customers found in sample data")
    
    return True


def test_kpi_cards():
    """Test Decision-Oriented KPI Cards."""
    print("\n" + "="*80)
    print("TEST 2: Decision-Oriented KPI Cards")
    print("="*80)
    
    df = generate_sample_risk_scores(100)
    
    # Test without database engine (will use default values for intervention metrics)
    kpi_metrics = calculate_kpi_metrics(df, None)
    
    print(f"✓ Customers at Risk Today: {kpi_metrics['customers_at_risk_today']}")
    print(f"✓ Defaults Avoided (MTD): {kpi_metrics['defaults_avoided_mtd']}")
    print(f"✓ Intervention Effectiveness: {kpi_metrics['intervention_effectiveness']:.2%}")
    print(f"✓ Financial Impact Prevented: ${kpi_metrics['financial_impact_prevented']:,.2f}")
    
    # Verify all required keys are present
