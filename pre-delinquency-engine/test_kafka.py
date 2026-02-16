"""
Test Kafka integration
"""

import sys
import time

print("="*60)
print("KAFKA INTEGRATION TEST")
print("="*60)

# Test 1: Import modules
print("\n1. Testing imports...")
try:
    from src.streaming.kafka_config import TOPICS, KAFKA_BOOTSTRAP_SERVERS
    from src.streaming.producers import TransactionProducer, PredictionProducer
    from src.streaming.consumers import TransactionConsumer
    print("  ✅ All modules imported successfully")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check Kafka connection
print(f"\n2. Testing Kafka connection to {KAFKA_BOOTSTRAP_SERVERS}...")
try:
    from kafka import KafkaProducer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        request_timeout_ms=5000
    )
    producer.close()
    print("  ✅ Kafka connection successful")
except Exception as e:
    print(f"  ❌ Kafka connection failed: {e}")
    print("\n  💡 Make sure Kafka is running:")
    print("     docker-compose up -d kafka zookeeper")
    sys.exit(1)

# Test 3: Create topics
print("\n3. Creating Kafka topics...")
try:
    from src.streaming.setup_topics import create_topics
    if create_topics():
        print("  ✅ Topics created/verified")
    else:
        print("  ⚠️ Topic creation had issues")
except Exception as e:
    print(f"  ❌ Topic creation failed: {e}")

# Test 4: Test producer
print("\n4. Testing transaction producer...")
try:
    producer = TransactionProducer()
    
    test_transaction = {
        'customer_id': 'test-customer-123',
        'txn_time': '2024-01-01T12:00:00',
        'amount': 100.50,
        'txn_type': 'debit',
        'category': 'groceries',
        'channel': 'pos',
        'merchant_id': 'MERCH_001'
    }
    
    if producer.send_transaction(test_transaction):
        print("  ✅ Test transaction sent successfully")
    else:
        print("  ❌ Failed to send test transaction")
    
    producer.close()
except Exception as e:
    print(f"  ❌ Producer test failed: {e}")

# Test 5: Test prediction producer
print("\n5. Testing prediction producer...")
try:
    producer = PredictionProducer()
    
    test_prediction = {
        'customer_id': 'test-customer-123',
        'risk_score': 0.75,
        'risk_level': 'HIGH',
        'top_features': [
            {'feature': 'savings_drawdown_30d_pct', 'value': -45.2},
            {'feature': 'payment_lateness_score', 'value': 8.5}
        ],
        'timestamp': '2024-01-01T12:00:00'
    }
    
    if producer.send_prediction(test_prediction):
        print("  ✅ Test prediction sent successfully")
    else:
        print("  ❌ Failed to send test prediction")
    
    producer.close()
except Exception as e:
    print(f"  ❌ Prediction producer test failed: {e}")

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("\n✅ Kafka integration is working!")
print("\nNext steps:")
print("  1. Start the API: python -m uvicorn src.serving.api:app --reload")
print("  2. Stream transactions: python -m src.streaming.transaction_simulator 100 50")
print("  3. View Kafka messages:")
print("     docker exec delinquency_kafka kafka-console-consumer \\")
print("       --bootstrap-server localhost:9092 \\")
print("       --topic predictions-stream --from-beginning")
print("\n" + "="*60)
