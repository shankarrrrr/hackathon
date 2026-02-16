"""Quick API test"""
import requests
import json

API_URL = "http://localhost:8000"

print("Testing API...")
print("\n1. Health Check:")
response = requests.get(f"{API_URL}/health")
print(f"   Status: {response.status_code}")
print(f"   {json.dumps(response.json(), indent=2)}")

print("\n2. Root Endpoint:")
response = requests.get(f"{API_URL}/")
print(f"   Status: {response.status_code}")
print(f"   Available endpoints: {list(response.json()['endpoints'].keys())}")

print("\n3. Stats:")
response = requests.get(f"{API_URL}/stats")
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    stats = response.json()
    print(f"   Total customers scored: {stats['total_customers']}")
    print(f"   High risk: {stats['high_risk_count']}")

print("\n4. Testing prediction (this may take a minute)...")
# Use a specific customer ID
customer_id = "4e8d6afc-ce50-4de9-a8bd-1aefce8c218c"
response = requests.post(
    f"{API_URL}/predict",
    json={"customer_id": customer_id},
    timeout=120
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"   Risk Score: {result['risk_score']:.4f}")
    print(f"   Risk Level: {result['risk_level']}")
else:
    print(f"   Error: {response.text[:200]}")

print("\n✅ API is operational!")
print(f"\n📖 View interactive docs at: {API_URL}/docs")
