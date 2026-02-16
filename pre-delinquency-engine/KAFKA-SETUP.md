# Kafka Integration Setup Guide

## Overview

The pre-delinquency engine now supports real-time event streaming using Apache Kafka for:
- Transaction ingestion
- Real-time predictions
- Intervention triggers
- Dashboard live updates

## Architecture

```
Transactions → Kafka → Feature Processor → Model → Kafka → Interventions
                ↓                                      ↓
           Dashboard                              PostgreSQL
```

## Quick Start

### 1. Start Kafka Infrastructure

```bash
# Start Kafka, Zookeeper, and other services
docker-compose up -d kafka zookeeper postgres redis

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

### 2. Install Python Dependencies

```bash
pip install kafka-python confluent-kafka
```

### 3. Create Kafka Topics

```bash
cd pre-delinquency-engine
python -m src.streaming.setup_topics
```

Expected output:
```
✅ All topics created successfully!

Existing topics:
  - transactions-stream
  - predictions-stream
  - interventions-stream
  - customer-updates
  - dashboard-updates
```

### 4. Test Kafka Connection

```bash
# Test producer
python -c "from src.streaming.producers import TransactionProducer; p = TransactionProducer(); print('✅ Connected')"

# Test consumer
python -c "from src.streaming.consumers import TransactionConsumer; print('✅ Consumer ready')"
```

## Usage Examples

### Stream Historical Transactions

```bash
# Stream 1000 transactions with 100ms delay
python -m src.streaming.transaction_simulator 1000 100

# Stream 500 transactions with 50ms delay
python -m src.streaming.transaction_simulator 500 50
```

### Stream Live Transactions

```bash
# Generate 10 transactions per second
python -m src.streaming.transaction_simulator live 10

# Generate 50 transactions per second
python -m src.streaming.transaction_simulator live 50
```

### Start API with Kafka

```bash
# API will automatically connect to Kafka on startup
python -m uvicorn src.serving.api:app --reload --host 0.0.0.0 --port 8000
```

The API will:
- ✅ Publish predictions to `predictions-stream`
- ✅ Send dashboard updates to `dashboard-updates`
- ✅ Continue working even if Kafka is unavailable

### Consume Predictions

```python
from src.streaming.consumers import PredictionConsumer

def process_prediction(prediction):
    print(f"Customer: {prediction['customer_id']}")
    print(f"Risk Score: {prediction['risk_score']}")
    print(f"Risk Level: {prediction['risk_level']}")

consumer = PredictionConsumer(callback=process_prediction)
consumer.start()
```

## Kafka Topics

| Topic | Purpose | Partitions | Retention |
|-------|---------|------------|-----------|
| `transactions-stream` | Real-time transaction events | 3 | 7 days |
| `predictions-stream` | Model predictions with features | 3 | 30 days |
| `interventions-stream` | Triggered interventions | 2 | 90 days |
| `customer-updates` | Customer profile changes | 2 | 30 days (compacted) |
| `dashboard-updates` | Live dashboard events | 1 | 1 day |

## Monitoring

### Check Kafka Status

```bash
# Check if Kafka is running
docker-compose ps kafka

# View Kafka logs
docker-compose logs -f kafka

# List topics
docker exec delinquency_kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe a topic
docker exec delinquency_kafka kafka-topics --describe --topic transactions-stream --bootstrap-server localhost:9092
```

### Monitor Consumer Lag

```bash
# Check consumer group lag
docker exec delinquency_kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group prediction-service-group
```

### View Messages

```bash
# Consume from beginning
docker exec delinquency_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic predictions-stream --from-beginning --max-messages 10
```

## Troubleshooting

### Kafka Won't Start

```bash
# Check Zookeeper is running
docker-compose ps zookeeper

# Restart Kafka
docker-compose restart kafka

# Check logs
docker-compose logs kafka
```

### Connection Refused

```bash
# Verify Kafka is listening
netstat -an | grep 9092

# Check KAFKA_ADVERTISED_LISTENERS in docker-compose.yml
# Should be: localhost:9092 for local development
```

### Topics Not Created

```bash
# Manually create a topic
docker exec delinquency_kafka kafka-topics --create --topic test-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Delete a topic
docker exec delinquency_kafka kafka-topics --delete --topic test-topic --bootstrap-server localhost:9092
```

## Environment Variables

Add to `.env`:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CLIENT_ID=delinquency-engine

# Enable/Disable Kafka
ENABLE_KAFKA=true
```

## Performance Tuning

### Producer Settings

```python
# In kafka_config.py
PRODUCER_CONFIG = {
    'acks': 'all',  # Wait for all replicas (slower but safer)
    'compression_type': 'snappy',  # Compress messages
    'batch_size': 16384,  # Batch size in bytes
    'linger_ms': 10,  # Wait 10ms to batch messages
}
```

### Consumer Settings

```python
# In kafka_config.py
CONSUMER_CONFIG = {
    'max_poll_records': 500,  # Process 500 messages per poll
    'session_timeout_ms': 30000,  # 30 second timeout
    'auto_commit_interval_ms': 5000,  # Commit every 5 seconds
}
```

## Next Steps

1. ✅ Kafka infrastructure running
2. ✅ Topics created
3. ✅ API publishing predictions
4. 🔄 Build intervention consumer (Phase 5)
5. 🔄 Add dashboard WebSocket (Phase 6)
6. 🔄 Implement stream processing for features

## Resources

- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [kafka-python Docs](https://kafka-python.readthedocs.io/)
- [Confluent Kafka Python](https://docs.confluent.io/kafka-clients/python/current/overview.html)
