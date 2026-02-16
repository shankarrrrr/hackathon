# Kafka Integration Plan

## Overview
Shift from batch processing to event-driven architecture using Apache Kafka for real-time streaming.

## Architecture Changes

### Current (Batch)
```
PostgreSQL → Feature Engineering → Model → API → Dashboard
```

### Target (Event-Driven with Kafka)
```
Transaction Events → Kafka → Stream Processor → Model → Kafka → Interventions
                      ↓                           ↓
                   Dashboard                  PostgreSQL
```

## Kafka Topics

1. **transactions-stream** - Real-time transaction events
2. **predictions-stream** - Model predictions with SHAP values
3. **interventions-stream** - Triggered interventions
4. **customer-updates** - Customer profile changes
5. **dashboard-updates** - Live dashboard events

## Implementation Timeline

### Phase 4 (API) - Add Kafka Infrastructure
- Add Kafka + Zookeeper to docker-compose.yml
- Create Kafka producers for transaction ingestion
- Set up basic topics and partitioning

### Phase 5 (Interventions) - Event-Driven Processing
- Kafka consumer for transaction stream
- Real-time feature computation (streaming aggregations)
- Publish predictions to predictions-stream
- Intervention engine consumes predictions-stream

### Phase 6 (Dashboard) - Live Updates
- Kafka consumer for dashboard-updates topic
- WebSocket server fed by Kafka
- Real-time charts and alerts

## Docker Compose Addition

```yaml
kafka:
  image: confluentinc/cp-kafka:7.5.0
  container_name: delinquency_kafka
  ports:
    - "9092:9092"
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
    KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
  depends_on:
    - zookeeper

zookeeper:
  image: confluentinc/cp-zookeeper:7.5.0
  container_name: delinquency_zookeeper
  ports:
    - "2181:2181"
  environment:
    ZOOKEEPER_CLIENT_PORT: 2181
    ZOOKEEPER_TICK_TIME: 2000
```

## Benefits

1. **Real-time Processing** - Sub-second latency for predictions
2. **Scalability** - Horizontal scaling with partitions
3. **Decoupling** - Services communicate via events
4. **Replay** - Can replay events for testing/debugging
5. **Audit Trail** - All events logged in Kafka

## Dependencies to Add

```toml
# Add to pyproject.toml
kafka-python = "^2.0.2"
confluent-kafka = "^2.3.0"
faust-streaming = "^0.10.0"  # For stream processing
```

## Status
- [ ] Kafka infrastructure added to docker-compose
- [ ] Transaction producer implemented
- [ ] Prediction consumer/producer implemented
- [ ] Intervention consumer implemented
- [ ] Dashboard WebSocket with Kafka
- [ ] Stream processing for features

**Will implement starting Phase 4**
