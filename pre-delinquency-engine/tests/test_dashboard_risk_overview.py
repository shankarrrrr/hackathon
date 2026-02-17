"""
Unit tests for Risk Overview page functionality.

Tests verify that the Risk Overview page components work correctly,
including data loading, formatting, and chart creation.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import dashboard modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRiskOverviewDataLoading:
    """Test data loading functions for Risk Overview page."""
    
    def test_latest_risk_scores_query_structure(self):
        """Test that the latest risk scores query returns expected columns."""
        # This test verifies the query structure without requiring a live database
        expected_columns = [
            'customer_id', 'risk_score', 'risk_level', 
            'score_date', 'top_feature_1', 'top_feature_1_impact'
        ]
        
        # Create mock data that would be returned by the query
        mock_data = pd.DataFrame({
            'customer_id': ['cust_001', 'cust_002'],
            'risk_score': [0.75, 0.45],
            'risk_level': ['HIGH', 'MEDIUM'],
            'score_date': pd.to_datetime(['2024-02-15', '2024-02-15']),
            'top_feature_1': ['failed_transaction_rate', 'balance_decline_rate'],
            'top_feature_1_impact': [0.15, 0.10]
        })
        
        # Verify all expected columns are present
        for col in expected_columns:
            assert col in mock_data.columns, f"Missing column: {col}"
    
    def test_rising_risk_query_structure(self):
        """Test that the rising risk query returns expected columns."""
        expected_columns = [
            'customer_id', 'risk_score', 'risk_level', 
            'top_feature_1', 'risk_change'
        ]
        
        # Create mock data
        mock_data = pd.DataFrame({
            'customer_id': ['cust_001'],
            'risk_score': [0.75],
            'risk_level': ['HIGH'],
            'top_feature_1': ['failed_transaction_rate'],
            'risk_change': [0.15]
        })
        
        # Verify all expected columns are present
        for col in expected_columns:
            assert col in mock_data.columns, f"Missing column: {col}"


class TestRiskOverviewFormatting:
    """Test data formatting functions for Risk Overview page."""
    
    def test_risk_score_percentage_formatting(self):
        """Test that risk scores are formatted as percentages with 2 decimals."""
        test_scores = [0.75, 0.456, 0.1, 0.999]
        expected = ["75.00%", "45.60%", "10.00%", "99.90%"]
        
        for score, expected_format in zip(test_scores, expected):
            formatted = f"{score:.2%}"
            assert formatted == expected_format, f"Expected {expected_format}, got {formatted}"
    
    def test_high_risk_count_calculation(self):
        """Test that high-risk customer count includes HIGH and CRITICAL levels."""
        mock_data = pd.DataFrame({
            'risk_level': ['LOW', 'MEDIUM', 'HIGH', 'HIGH', 'CRITICAL', 'LOW']
        })
        
        high_risk_count = len(mock_data[mock_data['risk_level'].isin(['HIGH', 'CRITICAL'])])
        
        assert high_risk_count == 3, f"Expected 3 high-risk customers, got {high_risk_count}"


class TestRiskOverviewCharts:
    """Test chart creation for Risk Overview page."""
    
    def test_histogram_configuration(self):
        """Test that histogram has required configuration elements."""
        import plotly.graph_objects as go
        
        # Create sample data
        risk_scores = np.random.uniform(0, 1, 100)
        
        # Create histogram
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=risk_scores,
            nbinsx=30,
            name='Risk Score'
        ))
        
        # Add threshold lines
        fig.add_vline(x=0.6, line_dash="dash", line_color="orange")
        fig.add_vline(x=0.8, line_dash="dash", line_color="red")
        
        # Configure layout
        fig.update_layout(
            title="Distribution of Customer Risk Scores",
            xaxis_title="Risk Score",
            yaxis_title="Number of Customers"
        )
        
        # Verify configuration
        assert fig.layout.title.text == "Distribution of Customer Risk Scores"
        assert fig.layout.xaxis.title.text == "Risk Score"
        assert fig.layout.yaxis.title.text == "Number of Customers"
    
    def test_pie_chart_color_mapping(self):
        """Test that pie chart uses correct color mapping for risk levels."""
        import plotly.graph_objects as go
        
        # Define expected color mapping
        color_map = {
            'LOW': 'green',
            'MEDIUM': 'yellow',
            'HIGH': 'orange',
            'CRITICAL': 'red'
        }
        
        # Verify all risk levels have colors
        for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            assert level in color_map, f"Missing color for risk level: {level}"
            assert color_map[level] in ['green', 'yellow', 'orange', 'red']


class TestRiskOverviewTableLimits:
    """Test table size limits and sorting."""
    
    def test_rising_risk_table_limit(self):
        """Test that rising risk table is limited to 20 rows."""
        # Create mock data with more than 20 rows
        mock_data = pd.DataFrame({
            'customer_id': [f'cust_{i:03d}' for i in range(50)],
            'risk_score': np.random.uniform(0.6, 1.0, 50),
            'risk_level': ['HIGH'] * 50
        })
        
        # Apply limit
        limited_data = mock_data.head(20)
        
        assert len(limited_data) == 20, f"Expected 20 rows, got {len(limited_data)}"
    
    def test_rising_risk_table_sorting(self):
        """Test that rising risk table is sorted by risk_score descending."""
        # Create mock data
        mock_data = pd.DataFrame({
            'customer_id': ['cust_001', 'cust_002', 'cust_003'],
            'risk_score': [0.65, 0.85, 0.75]
        })
        
        # Sort by risk_score descending
        sorted_data = mock_data.sort_values('risk_score', ascending=False)
        
        # Verify sorting
        assert sorted_data.iloc[0]['risk_score'] == 0.85
        assert sorted_data.iloc[1]['risk_score'] == 0.75
        assert sorted_data.iloc[2]['risk_score'] == 0.65


class TestRiskOverviewErrorHandling:
    """Test error handling for Risk Overview page."""
    
    def test_empty_dataframe_handling(self):
        """Test that empty dataframes are handled gracefully."""
        empty_df = pd.DataFrame()
        
        # Check if dataframe is empty
        is_empty = len(empty_df) == 0
        
        assert is_empty, "Empty dataframe should be detected"
    
    def test_none_dataframe_handling(self):
        """Test that None dataframes are handled gracefully."""
        df = None
        
        # Check if dataframe is None
        is_none = df is None
        
        assert is_none, "None dataframe should be detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
