"""
Validation script for Risk Overview page.

This script performs basic validation checks to ensure the Risk Overview page
components are correctly implemented and can be loaded.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def validate_imports():
    """Validate that all required imports are available."""
    print("✓ Checking imports...")
    
    try:
        import streamlit as st
        print("  ✓ streamlit imported")
    except ImportError as e:
        print(f"  ✗ Failed to import streamlit: {e}")
        return False
    
    try:
        import plotly.graph_objects as go
        print("  ✓ plotly.graph_objects imported")
    except ImportError as e:
        print(f"  ✗ Failed to import plotly: {e}")
        return False
    
    try:
        import pandas as pd
        print("  ✓ pandas imported")
    except ImportError as e:
        print(f"  ✗ Failed to import pandas: {e}")
        return False
    
    try:
        from sqlalchemy import create_engine, text
        print("  ✓ sqlalchemy imported")
    except ImportError as e:
        print(f"  ✗ Failed to import sqlalchemy: {e}")
        return False
    
    try:
        import requests
        print("  ✓ requests imported")
    except ImportError as e:
        print(f"  ✗ Failed to import requests: {e}")
        return False
    
    return True


def validate_dashboard_structure():
    """Validate that the dashboard file exists and has correct structure."""
    print("\n✓ Checking dashboard structure...")
    
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'app.py')
    
    if not os.path.exists(dashboard_path):
        print(f"  ✗ Dashboard file not found at {dashboard_path}")
        return False
    
    print(f"  ✓ Dashboard file exists at {dashboard_path}")
    
    # Read the file and check for key components
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_components = [
        'st.set_page_config',
        'init_connections',
        'load_latest_risk_scores',
        'load_rising_risk_customers',
        'Risk Overview',
        'st.sidebar',
        'go.Histogram',
        'go.Pie'
    ]
    
    for component in required_components:
        if component in content:
            print(f"  ✓ Found component: {component}")
        else:
            print(f"  ✗ Missing component: {component}")
            return False
    
    return True


def validate_sql_queries():
    """Validate that SQL queries are properly structured."""
    print("\n✓ Checking SQL queries...")
    
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'app.py')
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for DISTINCT ON query
    if 'DISTINCT ON (customer_id)' in content:
        print("  ✓ Found DISTINCT ON query for latest risk scores")
    else:
        print("  ✗ Missing DISTINCT ON query")
        return False
    
    # Check for LAG window function
    if 'LAG(risk_score)' in content:
        print("  ✓ Found LAG window function for rising risk")
    else:
        print("  ✗ Missing LAG window function")
        return False
    
    # Check for risk level filtering
    if "risk_level IN ('HIGH', 'CRITICAL')" in content:
        print("  ✓ Found risk level filtering")
    else:
        print("  ✗ Missing risk level filtering")
        return False
    
    # Check for LIMIT 20
    if 'LIMIT 20' in content:
        print("  ✓ Found LIMIT 20 for rising risk table")
    else:
        print("  ✗ Missing LIMIT 20")
        return False
    
    return True


def validate_visualizations():
    """Validate that visualizations are properly configured."""
    print("\n✓ Checking visualizations...")
    
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'app.py')
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for histogram with thresholds
    if 'add_vline' in content and '0.6' in content and '0.8' in content:
        print("  ✓ Found histogram with threshold lines")
    else:
        print("  ✗ Missing histogram threshold lines")
        return False
    
    # Check for color mapping
    color_map_check = all([
        "'LOW': 'green'" in content,
        "'MEDIUM': 'yellow'" in content,
        "'HIGH': 'orange'" in content,
        "'CRITICAL': 'red'" in content
    ])
    
    if color_map_check:
        print("  ✓ Found correct color mapping for risk levels")
    else:
        print("  ✗ Missing or incorrect color mapping")
        return False
    
    # Check for pie chart
    if 'go.Pie' in content:
        print("  ✓ Found pie chart implementation")
    else:
        print("  ✗ Missing pie chart")
        return False
    
    return True


def validate_formatting():
    """Validate that data formatting is correct."""
    print("\n✓ Checking data formatting...")
    
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'app.py')
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for percentage formatting
    if ':.2%' in content:
        print("  ✓ Found percentage formatting with 2 decimals")
    else:
        print("  ✗ Missing percentage formatting")
        return False
    
    return True


def validate_error_handling():
    """Validate that error handling is implemented."""
    print("\n✓ Checking error handling...")
    
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'app.py')
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for try-except blocks
    if 'try:' in content and 'except' in content:
        print("  ✓ Found error handling with try-except blocks")
    else:
        print("  ✗ Missing error handling")
        return False
    
    # Check for empty data handling
    if 'len(df) == 0' in content or 'df is None' in content:
        print("  ✓ Found empty data handling")
    else:
        print("  ✗ Missing empty data handling")
        return False
    
    # Check for st.error or st.warning
    if 'st.error' in content or 'st.warning' in content:
        print("  ✓ Found error/warning messages")
    else:
        print("  ✗ Missing error/warning messages")
        return False
    
    return True


def validate_caching():
    """Validate that caching is properly implemented."""
    print("\n✓ Checking caching...")
    
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'app.py')
    
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for @st.cache_resource
    if '@st.cache_resource' in content:
        print("  ✓ Found @st.cache_resource decorator")
    else:
        print("  ✗ Missing @st.cache_resource decorator")
        return False
    
    # Check for @st.cache_data with ttl
    if '@st.cache_data(ttl=60)' in content:
        print("  ✓ Found @st.cache_data with ttl=60")
    else:
        print("  ✗ Missing @st.cache_data with ttl")
        return False
    
    return True


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("Risk Overview Page Validation")
    print("=" * 70)
    
    checks = [
        ("Imports", validate_imports),
        ("Dashboard Structure", validate_dashboard_structure),
        ("SQL Queries", validate_sql_queries),
        ("Visualizations", validate_visualizations),
        ("Data Formatting", validate_formatting),
        ("Error Handling", validate_error_handling),
        ("Caching", validate_caching)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n✗ Error during {check_name} validation: {e}")
            results.append((check_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All validation checks passed! Risk Overview page is ready.")
        return 0
    else:
        print(f"\n✗ {total - passed} validation check(s) failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
