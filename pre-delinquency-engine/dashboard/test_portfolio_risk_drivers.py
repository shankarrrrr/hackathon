"""
Unit tests for calculate_portfolio_risk_drivers function.

Tests the calculate_portfolio_risk_drivers function to ensure it correctly
aggregates risk drivers across the portfolio and returns top 5 drivers.

Requirements: 5.1, 5.4, 5.5
"""

import pytest
import pandas as pd
import sys
import os

# Add parent directory to path to import app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import calculate_portfolio_risk_drivers


def test_calculate_portfolio_risk_drivers_basic():
    """
    Test basic functionality with valid data.
    Should group by top_feature_1, aggregate impacts, and return top 5.
    
    Requirements: 5.1, 5.4, 5.5
    """
    # Arrange: Create test data with various risk drivers
    test_data = pd.DataFrame([
        {'customer_id': '1', 'top_feature_1': 'payment_delay', 'top_feature_1_impact': 0.3},
        {'customer_id': '2', 'top_feature_1': 'payment_delay', 'top_feature_1_impact': 0.2},
        {'customer_id': '3', 'top_feature_1': 'credit_utilization', 'top_feature_1_impact': 0.25},
        {'customer_id': '4', 'top_feature_1': 'missed_payment', 'top_feature_1_impact': 0.15},
        {'customer_id': '5', 'top_feature_1': 'account_age', 'top_feature_1_impact': 0.1},
    ])
    
    # Act: Calculate portfolio risk drivers
    result = calculate_portfolio_risk_drivers(test_data)
    
    # Assert: Check structure
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ['driver_name', 'contribution_pct', 'customer_count']
    
    # Assert: Check top driver is payment_delay (0.5 total impact)
    assert result.iloc[0]['driver_name'] == 'payment_delay'
    assert result.iloc[0]['customer_count'] == 2
    
    # Assert: Check percentage calculation (0.5 / 1.0 = 50%)
    assert abs(result.iloc[0]['contribution_pct'] - 50.0) < 0.01
    
    # Assert: Check sorted descending
    assert result['contribution_pct'].is_monotonic_decreasing


def test_calculate_portfolio_risk_drivers_top_5_limit():
    """
    Test that function returns only top 5 drivers when more exist.
    
    Requirements: 5.5
    """
    # Arrange: Create test data with 7 different drivers
    test_data = pd.DataFrame([
        {'customer_id': '1', 'top_feature_1': 'driver_1', 'top_feature_1_impact': 0.30},
        {'customer_id': '2', 'top_feature_1': 'driver_2', 'top_feature_1_impact': 0.25},
        {'customer_id': '3', 'top_feature_1': 'driver_3', 'top_feature_1_impact': 0.20},
        {'customer_id': '4', 'top_feature_1': 'driver_4', 'top_feature_1_impact': 0.15},
        {'customer_id': '5', 'top_feature_1': 'driver_5', 'top_feature_1_impact': 0.10},
        {'customer_id': '6', 'top_feature_1': 'driver_6', 'top_feature_1_impact': 0.05},
        {'customer_id': '7', 'top_feature_1': 'driver_7', 'top_feature_1_impact': 0.02},
    ])
    
    # Act
    result = calculate_portfolio_risk_drivers(test_data)
    
    # Assert: Should return exactly 5 drivers
    assert len(result) == 5
    
    # Assert: Should include top 5 drivers
    assert 'driver_1' in result['driver_name'].values
    assert 'driver_5' in result['driver_name'].values
    
    # Assert: Should NOT include bottom 2 drivers
    assert 'driver_6' not in result['driver_name'].values
    assert 'driver_7' not in result['driver_name'].values


def test_calculate_portfolio_risk_drivers_empty_dataframe():
    """
    Test that function handles empty DataFrame gracefully.
    
    Requirements: 5.1
    """
    # Arrange: Empty DataFrame
    test_data = pd.DataFrame()
    
    # Act
    result = calculate_portfolio_risk_drivers(test_data)
    
    # Assert: Should return empty DataFrame with correct columns
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
    assert list(result.columns) == ['driver_name', 'contribution_pct', 'customer_count']


def test_calculate_portfolio_risk_drivers_none_input():
    """
    Test that function handles None input gracefully.
    
    Requirements: 5.1
    """
    # Act
    result = calculate_portfolio_risk_drivers(None)
    
    # Assert: Should return empty DataFrame with correct columns
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
    assert list(result.columns) == ['driver_name', 'contribution_pct', 'customer_count']


def test_calculate_portfolio_risk_drivers_missing_columns():
    """
    Test that function handles missing required columns gracefully.
    
    Requirements: 5.1
    """
    # Arrange: DataFrame without required columns
    test_data = pd.DataFrame([
        {'customer_id': '1', 'risk_score': 0.8},
        {'customer_id': '2', 'risk_score': 0.6},
    ])
    
    # Act
    result = calculate_portfolio_risk_drivers(test_data)
    
    # Assert: Should return empty DataFrame with correct columns
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
    assert list(result.columns) == ['driver_name', 'contribution_pct', 'customer_count']


def test_calculate_portfolio_risk_drivers_with_null_values():
    """
    Test that function handles null values in top_feature_1 or impact.
    
    Requirements: 5.4
    """
    # Arrange: Data with some null values
    test_data = pd.DataFrame([
        {'customer_id': '1', 'top_feature_1': 'payment_delay', 'top_feature_1_impact': 0.3},
        {'customer_id': '2', 'top_feature_1': None, 'top_feature_1_impact': 0.2},
        {'customer_id': '3', 'top_feature_1': 'credit_utilization', 'top_feature_1_impact': None},
        {'customer_id': '4', 'top_feature_1': 'missed_payment', 'top_feature_1_impact': 0.15},
    ])
    
    # Act
    result = calculate_portfolio_risk_drivers(test_data)
    
    # Assert: Should only include valid rows
    assert len(result) == 2  # Only rows 1 and 4 are valid
    assert 'payment_delay' in result['driver_name'].values
    assert 'missed_payment' in result['driver_name'].values


def test_calculate_portfolio_risk_drivers_aggregation():
    """
    Test that function correctly aggregates impacts for same driver.
    
    Requirements: 5.4
    """
    # Arrange: Multiple customers with same driver
    test_data = pd.DataFrame([
        {'customer_id': '1', 'top_feature_1': 'payment_delay', 'top_feature_1_impact': 0.2},
        {'customer_id': '2', 'top_feature_1': 'payment_delay', 'top_feature_1_impact': 0.3},
        {'customer_id': '3', 'top_feature_1': 'payment_delay', 'top_feature_1_impact': 0.1},
        {'customer_id': '4', 'top_feature_1': 'other_driver', 'top_feature_1_impact': 0.4},
    ])
    
    # Act
    result = calculate_portfolio_risk_drivers(test_data)
    
    # Assert: payment_delay should have aggregated impact of 0.6
    payment_delay_row = result[result['driver_name'] == 'payment_delay'].iloc[0]
    
    # Total impact is 1.0, payment_delay is 0.6, so 60%
    assert abs(payment_delay_row['contribution_pct'] - 60.0) < 0.01
    assert payment_delay_row['customer_count'] == 3


def test_calculate_portfolio_risk_drivers_percentage_sum():
    """
    Test that contribution percentages are calculated correctly.
    
    Requirements: 5.4
    """
    # Arrange: Simple test data
    test_data = pd.DataFrame([
        {'customer_id': '1', 'top_feature_1': 'driver_a', 'top_feature_1_impact': 0.5},
        {'customer_id': '2', 'top_feature_1': 'driver_b', 'top_feature_1_impact': 0.3},
        {'customer_id': '3', 'top_feature_1': 'driver_c', 'top_feature_1_impact': 0.2},
    ])
    
    # Act
    result = calculate_portfolio_risk_drivers(test_data)
    
    # Assert: Percentages should sum to 100%
    total_pct = result['contribution_pct'].sum()
    assert abs(total_pct - 100.0) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
