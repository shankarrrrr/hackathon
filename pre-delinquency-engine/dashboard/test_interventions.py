"""
Unit tests for intervention triggering functionality.

Tests the trigger_interventions_for_critical_customers function to ensure
it correctly creates intervention records for HIGH and CRITICAL risk customers.
"""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import uuid


def test_trigger_interventions_creates_correct_intervention_types():
    """
    Test that intervention_type is correctly determined based on risk_level.
    CRITICAL → urgent_contact, HIGH → proactive_outreach
    
    Requirements: 1.5
    """
    # Arrange: Create test data with HIGH and CRITICAL customers
    test_data = pd.DataFrame([
        {
            'customer_id': str(uuid.uuid4()),
            'risk_score': 0.85,
            'risk_level': 'CRITICAL',
            'score_date': datetime.now(),
            'top_feature_1': 'payment_delay'
        },
        {
            'customer_id': str(uuid.uuid4()),
            'risk_score': 0.65,
            'risk_level': 'HIGH',
            'score_date': datetime.now(),
            'top_feature_1': 'credit_utilization'
        },
        {
            'customer_id': str(uuid.uuid4()),
            'risk_score': 0.35,
            'risk_level': 'MEDIUM',
            'score_date': datetime.now(),
            'top_feature_1': 'account_age'
        }
    ])
    
    # Mock database engine and connection
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn
    
    # Track executed queries
    executed_queries = []
    
    def capture_execute(query, params):
        executed_queries.append({
            'query': str(query),
            'params': params
        })
    
    mock_conn.execute.side_effect = capture_execute
    
    # Import and patch the function
    with patch('app.engine', mock_engine):
        from app import trigger_interventions_for_critical_customers
        
        # Act: Trigger interventions
        result = trigger_interventions_for_critical_customers(test_data)
    
    # Assert: Check result
    assert result['success'] is True
    assert result['count'] == 2  # Only HIGH and CRITICAL customers
    assert 'Successfully created 2 intervention(s)' in result['message']
    
    # Assert: Check that correct intervention types were used
    assert len(executed_queries) == 2
    
    # Find CRITICAL customer intervention
    critical_intervention = next(
        q for q in executed_queries 
        if q['params']['risk_score'] == 0.85
    )
    assert critical_intervention['params']['intervention_type'] == 'urgent_contact'
    
    # Find HIGH customer intervention
    high_intervention = next(
        q for q in executed_queries 
        if q['params']['risk_score'] == 0.65
    )
    assert high_intervention['params']['intervention_type'] == 'proactive_outreach'


def test_trigger_interventions_handles_empty_dataset():
    """
    Test that the function handles empty datasets gracefully.
    
    Requirements: 1.5
    """
    # Arrange: Empty dataframe
    test_data = pd.DataFrame(columns=['customer_id', 'risk_score', 'risk_level'])
    
    # Mock database engine
    mock_engine = MagicMock()
    
    with patch('app.engine', mock_engine):
        from app import trigger_interventions_for_critical_customers
        
        # Act
        result = trigger_interventions_for_critical_customers(test_data)
    
    # Assert
    assert result['success'] is True
    assert result['count'] == 0
    assert 'No critical customers found' in result['message']


def test_trigger_interventions_handles_no_critical_customers():
    """
    Test that the function handles datasets with no HIGH/CRITICAL customers.
    
    Requirements: 1.5
    """
    # Arrange: Only LOW and MEDIUM risk customers
    test_data = pd.DataFrame([
        {
            'customer_id': str(uuid.uuid4()),
            'risk_score': 0.25,
            'risk_level': 'LOW',
            'score_date': datetime.now()
        },
        {
            'customer_id': str(uuid.uuid4()),
            'risk_score': 0.45,
            'risk_level': 'MEDIUM',
            'score_date': datetime.now()
        }
    ])
    
    # Mock database engine
    mock_engine = MagicMock()
    
    with patch('app.engine', mock_engine):
        from app import trigger_interventions_for_critical_customers
        
        # Act
        result = trigger_interventions_for_critical_customers(test_data)
    
    # Assert
    assert result['success'] is True
    assert result['count'] == 0
    assert 'No critical customers found' in result['message']


def test_trigger_interventions_handles_database_error():
    """
    Test that the function handles database errors gracefully.
    
    Requirements: 1.5
    """
    # Arrange: Test data
    test_data = pd.DataFrame([
        {
            'customer_id': str(uuid.uuid4()),
            'risk_score': 0.85,
            'risk_level': 'CRITICAL',
            'score_date': datetime.now()
        }
    ])
    
    # Mock database engine that raises an error
    mock_engine = MagicMock()
    mock_engine.begin.side_effect = Exception("Database connection failed")
    
    with patch('app.engine', mock_engine):
        from app import trigger_interventions_for_critical_customers
        
        # Act
        result = trigger_interventions_for_critical_customers(test_data)
    
    # Assert
    assert result['success'] is False
    assert result['count'] == 0
    assert 'Error creating interventions' in result['message']


def test_trigger_interventions_handles_no_engine():
    """
    Test that the function handles missing database engine.
    
    Requirements: 1.5
    """
    # Arrange: Test data
    test_data = pd.DataFrame([
        {
            'customer_id': str(uuid.uuid4()),
            'risk_score': 0.85,
            'risk_level': 'CRITICAL',
            'score_date': datetime.now()
        }
    ])
    
    with patch('app.engine', None):
        from app import trigger_interventions_for_critical_customers
        
        # Act
        result = trigger_interventions_for_critical_customers(test_data)
    
    # Assert
    assert result['success'] is False
    assert result['count'] == 0
    assert 'Database connection not available' in result['message']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
