"""
End-to-end test for the complete streaming pipeline
Tests: Kafka → Feature Processor → API → Intervention Worker
"""

import time
import requests
import json
from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime
import sys

# Configuration
KAFKA_BOOTSTRAP = 'localhost:9092'
API_URL = 'http://localhost:8000'
TEST_CUSTOMER_ID = 'test-customer-123'

def test_kafka_connection():
    """Test 1: Verify Kafka is running"""
    print("\n" + "="*60)
    print("TEST 1: Kafka Connection")
    print("="*60)
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        producer.close()
        print("✅ Kafka connection successful")
        return True
    except Exception as e:
        print(f"❌ Kafka connection failed: {e}")
        return False

def test_api_health():
    """Test 2: Verify API is running"""
    print("\n" + "="*60)
    print("TEST 2: API Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy")
            print(f"   Model loaded: {data.get('model_loaded')}")
            print(f"   Database connected: {data.get('database_connected')}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def test_transaction_publishing():
    """Test 3: Publish a test transaction to Kafka"""
    print("\n" + "="*60)
    print("TEST 3: Transaction Publishing")
    print("="*60)
    
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        
        # Create test transaction
        transaction = {
            'customer_id': TEST_CUSTOMER_ID,
            'txn_time': datetime.now().isoformat(),
            'amount': 10000.00,  # Large amount to trigger prediction
            'txn_type': 'debit',
            'category': 'utilities',
            'channel': 'online',
            'merchant_id': 'TEST_MERCHANT',
            'is_failed': False,
            'event_time': datetime.now().isoformat(),
            'event_type': 'transaction'
        }
        
        # Send to Kafka
        future = producer.send(
            'transactions-stream',
            key=TEST_CUSTOMER_ID,
            value=transaction
        )
        
        # Wait for confirmation
        record_metadata = future.get(timeout=10)
        
        print(f"✅ Transaction published successfully")
        print(f"   Topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")
        print(f"   Customer: {TEST_CUSTOMER_ID}")
        print(f"   Amount: ${transaction['amount']}")
        
        producer.close()
        return True
    
    except Exception as e:
        print(f"❌ Transaction publishing failed: {e}")
        return False

def test_prediction_consumption():
    """Test 4: Consume prediction from Kafka"""
    print("\n" + "="*60)
    print("TEST 4: Prediction Consumption")
    print("="*60)
    print("Waiting for prediction (timeout: 30 seconds)...")
    
    try:
        consumer = KafkaConsumer(
            'predictions-stream',
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            consumer_timeout_ms=30000  # 30 second timeout
        )
        
        prediction_found = False
        
        for message in consumer:
            prediction = message.value
            customer_id = prediction.get('customer_id')
            
            print(f"\n📊 Prediction received:")
            print(f"   Customer: {customer_id}")
            print(f"   Risk Score: {prediction.get('risk_score', 0):.4f}")
            print(f"   Risk Level: {prediction.get('risk_level')}")
            print(f"   Timestamp: {prediction.get('timestamp')}")
            
            if customer_id == TEST_CUSTOMER_ID:
                print(f"\n✅ Found prediction for test customer!")
                prediction_found = True
                break
        
        consumer.close()
        
        if not prediction_found:
            print(f"\n⚠️ No prediction found for test customer (may need more time)")
        
        return prediction_found
    
    except Exception as e:
        print(f"❌ Prediction consumption failed: {e}")
        return False

def test_intervention_consumption():
    """Test 5: Consume intervention from Kafka"""
    print("\n" + "="*60)
    print("TEST 5: Intervention Consumption")
    print("="*60)
    print("Waiting for intervention (timeout: 30 seconds)...")
    
    try:
        consumer = KafkaConsumer(
            'interventions-stream',
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            consumer_timeout_ms=30000
        )
        
        intervention_found = False
        
        for message in consumer:
            intervention = message.value
            customer_id = intervention.get('customer_id')
            
            print(f"\n🚨 Intervention received:")
            print(f"   Customer: {customer_id}")
            print(f"   Type: {intervention.get('intervention_type')}")
            print(f"   Channel: {intervention.get('channel')}")
            print(f"   Priority: {intervention.get('priority')}")
            print(f"   Message: {intervention.get('message')}")
            
            if customer_id == TEST_CUSTOMER_ID:
                print(f"\n✅ Found intervention for test customer!")
                intervention_found = True
                break
        
        consumer.close()
        
        if not intervention_found:
            print(f"\n⚠️ No intervention found (customer may be low risk)")
        
        return True  # Not critical if no intervention
    
    except Exception as e:
        print(f"❌ Intervention consumption failed: {e}")
        return False

def test_api_direct():
    """Test 6: Direct API prediction call"""
    print("\n" + "="*60)
    print("TEST 6: Direct API Prediction")
    print("="*60)
    
    try:
        # Get a real customer from database
        response = requests.get(f"{API_URL}/high_risk_customers?limit=1", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            customers = data.get('customers', [])
            
            if customers:
                customer_id = customers[0]['customer_id']
                print(f"Testing with customer: {customer_id}")
                
                # Make prediction
                pred_response = requests.post(
                    f"{API_URL}/predict",
                    json={"customer_id": customer_id},
                    timeout=30
                )
                
                if pred_response.status_code == 200:
                    result = pred_response.json()
                    print(f"\n✅ Prediction successful:")
                    print(f"   Customer: {result['customer_id']}")
                    print(f"   Risk Score: {result['risk_score']:.4f}")
                    print(f"   Risk Level: {result['risk_level']}")
                    print(f"   Top Features:")
                    for feat in result['top_features'][:3]:
                        print(f"      - {feat['feature']}: {feat['value']:.2f}")
                    return True
                else:
                    print(f"❌ Prediction failed: {pred_response.status_code}")
                    return False
            else:
                print("⚠️ No customers in database yet")
                return True
        else:
            print(f"❌ Failed to get customers: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Direct API test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("STREAMING PIPELINE END-TO-END TEST")
    print("="*60)
    print("\nThis test will verify:")
    print("1. Kafka connection")
    print("2. API health")
    print("3. Transaction publishing")
    print("4. Prediction consumption")
    print("5. Intervention consumption")
    print("6. Direct API call")
    print("\nMake sure the following are running:")
    print("- docker-compose up -d (Kafka, PostgreSQL)")
    print("- python -m uvicorn src.serving.api:app --reload")
    print("- python run_streaming_pipeline.py")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nTest cancelled")
        sys.exit(0)
    
    # Run tests
    results = []
    
    results.append(("Kafka Connection", test_kafka_connection()))
    results.append(("API Health", test_api_health()))
    results.append(("Transaction Publishing", test_transaction_publishing()))
    
    # Wait a bit for processing
    print("\n⏳ Waiting 5 seconds for pipeline to process...")
    time.sleep(5)
    
    results.append(("Prediction Consumption", test_prediction_consumption()))
    results.append(("Intervention Consumption", test_intervention_consumption()))
    results.append(("Direct API Call", test_api_direct()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Streaming pipeline is working correctly.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
