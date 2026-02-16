"""
Simple test script for the API
"""

import requests
import json
from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing /health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_root():
    """Test root endpoint"""
    print("\n🏠 Testing / endpoint...")
    response = requests.get(f"{API_URL}/")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def get_sample_customer():
    """Get a sample customer ID from database"""
    print("\n📊 Getting sample customer from database...")
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)
    
    query = "SELECT customer_id FROM customers LIMIT 1"
    df = pd.read_sql(query, engine)
    
    if len(df) > 0:
        customer_id = str(df.iloc[0]['customer_id'])  # Convert UUID to string
        print(f"  Sample customer: {customer_id}")
        return customer_id
    else:
        print("  ⚠️ No customers found in database")
        return None

def test_predict(customer_id):
    """Test prediction endpoint"""
    print(f"\n🎯 Testing /predict endpoint for customer {customer_id}...")
    
    payload = {
        "customer_id": customer_id
    }
    
    response = requests.post(
        f"{API_URL}/predict",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"  Risk Score: {result['risk_score']:.4f}")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Top Features:")
        for feat in result['top_features'][:3]:
            print(f"    - {feat['feature']}: {feat['value']:.4f}")
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def test_stats():
    """Test stats endpoint"""
    print("\n📈 Testing /stats endpoint...")
    response = requests.get(f"{API_URL}/stats")
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"  Total Customers: {stats['total_customers']}")
        print(f"  High Risk: {stats['high_risk_count']}")
        print(f"  Medium Risk: {stats['medium_risk_count']}")
        print(f"  Low Risk: {stats['low_risk_count']}")
        print(f"  Avg Risk Score: {stats['avg_risk_score']:.4f}")
        return True
    else:
        print(f"  Error: {response.text}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("API TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test health
    results.append(("Health Check", test_health()))
    
    # Test root
    results.append(("Root Endpoint", test_root()))
    
    # Get sample customer
    customer_id = get_sample_customer()
    
    if customer_id:
        # Test prediction
        results.append(("Prediction", test_predict(customer_id)))
    
    # Test stats
    results.append(("Stats", test_stats()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print("="*60)

if __name__ == "__main__":
    main()
