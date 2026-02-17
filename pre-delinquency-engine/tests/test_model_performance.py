"""
Unit tests for Model Performance page functionality.
"""

import json
import os
import pytest


def test_metrics_file_exists():
    """Test that the metrics.json file exists in the expected location."""
    metrics_path = "data/models/evaluation/metrics.json"
    assert os.path.exists(metrics_path), f"Metrics file not found at {metrics_path}"


def test_metrics_file_valid_json():
    """Test that the metrics.json file contains valid JSON."""
    metrics_path = "data/models/evaluation/metrics.json"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    assert isinstance(metrics, dict), "Metrics should be a dictionary"


def test_metrics_contains_required_fields():
    """Test that the metrics file contains all required fields."""
    metrics_path = "data/models/evaluation/metrics.json"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    required_fields = [
        'auc_roc', 'precision', 'recall', 'f1_score',
        'true_positives', 'true_negatives', 'false_positives', 'false_negatives',
        'accuracy'
    ]
    
    for field in required_fields:
        assert field in metrics, f"Required field '{field}' missing from metrics"


def test_metrics_values_in_valid_range():
    """Test that metric values are in valid ranges."""
    metrics_path = "data/models/evaluation/metrics.json"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Test that probability metrics are between 0 and 1
    probability_metrics = ['auc_roc', 'precision', 'recall', 'f1_score', 'accuracy']
    for metric in probability_metrics:
        value = metrics.get(metric, -1)
        assert 0 <= value <= 1, f"{metric} should be between 0 and 1, got {value}"
    
    # Test that confusion matrix values are non-negative integers
    confusion_metrics = ['true_positives', 'true_negatives', 'false_positives', 'false_negatives']
    for metric in confusion_metrics:
        value = metrics.get(metric, -1)
        assert value >= 0, f"{metric} should be non-negative, got {value}"
        assert isinstance(value, (int, float)), f"{metric} should be numeric, got {type(value)}"


def test_confusion_matrix_calculations():
    """Test that confusion matrix values are consistent with accuracy."""
    metrics_path = "data/models/evaluation/metrics.json"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    tp = metrics.get('true_positives', 0)
    tn = metrics.get('true_negatives', 0)
    fp = metrics.get('false_positives', 0)
    fn = metrics.get('false_negatives', 0)
    accuracy = metrics.get('accuracy', 0)
    
    # Calculate accuracy from confusion matrix
    total = tp + tn + fp + fn
    if total > 0:
        calculated_accuracy = (tp + tn) / total
        # Allow small floating point differences
        assert abs(calculated_accuracy - accuracy) < 0.01, \
            f"Accuracy mismatch: calculated {calculated_accuracy:.4f}, stored {accuracy:.4f}"


def test_business_metrics_calculations():
    """Test that business metrics can be calculated from confusion matrix."""
    metrics_path = "data/models/evaluation/metrics.json"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    tp = metrics.get('true_positives', 0)
    tn = metrics.get('true_negatives', 0)
    fp = metrics.get('false_positives', 0)
    fn = metrics.get('false_negatives', 0)
    
    # Calculate false alarm rate (FP / (FP + TN))
    if (fp + tn) > 0:
        false_alarm_rate = fp / (fp + tn)
        assert 0 <= false_alarm_rate <= 1, f"False alarm rate should be between 0 and 1, got {false_alarm_rate}"
    
    # Calculate detection rate (TP / (TP + FN)) - same as recall
    if (tp + fn) > 0:
        detection_rate = tp / (tp + fn)
        recall = metrics.get('recall', 0)
        # Allow small floating point differences
        assert abs(detection_rate - recall) < 0.01, \
            f"Detection rate should match recall: calculated {detection_rate:.4f}, stored {recall:.4f}"


def test_metrics_formatting():
    """Test that metrics can be formatted correctly for display."""
    metrics_path = "data/models/evaluation/metrics.json"
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Test AUC-ROC formatting (4 decimals)
    auc_roc = metrics.get('auc_roc', 0)
    formatted_auc = f"{auc_roc:.4f}"
    assert len(formatted_auc.split('.')[1]) == 4, "AUC-ROC should have 4 decimal places"
    
    # Test precision formatting (percentage)
    precision = metrics.get('precision', 0)
    formatted_precision = f"{precision:.1%}"
    assert '%' in formatted_precision, "Precision should be formatted as percentage"
    
    # Test F1 score formatting (4 decimals)
    f1_score = metrics.get('f1_score', 0)
    formatted_f1 = f"{f1_score:.4f}"
    assert len(formatted_f1.split('.')[1]) == 4, "F1 score should have 4 decimal places"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
