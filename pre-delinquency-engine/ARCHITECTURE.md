# Pre-Delinquency Engine - Architecture

## System Overview

The Pre-Delinquency Engine is a real-time, event-driven system for detecting financial stress and triggering proactive interventions before customers default on payments.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                 │
├─────────────────────────────────────────────────────────────────────┤
│  • PostgreSQL (Historical Data)                                      │
│  • Real-time Transaction Feeds                                       │
│  • Customer Profile Updates                                          │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TRANSACTION SIMULATOR                             │
├─────────────────────────────────────────────────────────────────────┤
│  • Reads transactions from PostgreSQL                                │
│  • Streams to Kafka in real-time                                     │
│  • Configurable batch size and delay                                 │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         KAFKA BROKER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Topic: transactions-stream (3 partitions, 7 day retention)         │
│  • Real-time transaction events                                      │
│  • Partitioned by customer_id for ordering                           │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FEATURE PROCESSOR                                 │
├─────────────────────────────────────────────────────────────────────┤
│  • Consumes transaction events                                       │
│  • Intelligent prediction triggering:                                │
│    - Failed transactions                                             │
│    - Large amounts (>5000)                                           │
│    - ATM withdrawals                                                 │
│    - Important categories (utilities, rent, insurance)               │
│    - Periodic checks (every 10th transaction)                        │
│  • Calls Prediction API via HTTP                                     │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PREDICTION API                                  │
├─────────────────────────────────────────────────────────────────────┤
│  • FastAPI + Uvicorn                                                 │
│  • Computes 30+ behavioral features                                  │
│  • XGBoost model scoring                                             │
│  • SHAP explainability                                               │
│  • Stores predictions in PostgreSQL                                  │
│  • Publishes to Kafka                                                │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         KAFKA BROKER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Topic: predictions-stream (3 partitions, 30 day retention)         │
│  • Model predictions with risk scores                                │
│  • Top risk factors                                                  │
│  • Explainability data                                               │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   INTERVENTION WORKER                                │
├─────────────────────────────────────────────────────────────────────┤
│  • Consumes prediction events                                        │
│  • Risk-based intervention strategies:                               │
│    - CRITICAL (≥0.7): Urgent phone call                              │
│    - HIGH (≥0.5): Proactive SMS                                      │
│    - MEDIUM (≥0.3): Gentle email reminder                            │
│  • Publishes intervention events                                     │
│  • Stores in PostgreSQL for tracking                                 │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         KAFKA BROKER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Topic: interventions-stream (2 partitions, 90 day retention)       │
│  • Triggered interventions                                           │
│  • Audit trail for compliance                                        │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DOWNSTREAM SYSTEMS                                │
├─────────────────────────────────────────────────────────────────────┤
│  • Dashboard (Real-time visualization)                               │
│  • CRM Integration (Customer outreach)                               │
│  • Analytics (Intervention effectiveness)                            │
│  • Alerting (Critical risk notifications)                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Transaction Simulator
**File**: `src/streaming/transaction_simulator.py`

**Responsibilities**:
- Read historical transactions from PostgreSQL
- Stream transactions to Kafka in real-time
- Simulate realistic transaction flow

**Configuration**:
- Batch size: Number of transactions per batch
- Delay: Milliseconds between batches
- Total transactions: Total to stream

### 2. Feature Processor
**File**: `src/streaming/feature_processor.py`

**Responsibilities**:
- Consume transaction events from Kafka
- Determine when to trigger predictions
- Call Prediction API via HTTP
- Track processed customers

**Triggering Logic**:
```python
def should_trigger_prediction(transaction):
    if transaction.is_failed:
        return True  # Always trigger on failures
    
    if transaction.amount > 5000:
        return True  # Large transactions
    
    if transaction.channel == 'atm':
        return True  # ATM withdrawals
    
    if transaction.category in ['utilities', 'rent', 'insurance']:
        return True  # Important payments
    
    if transaction_count % 10 == 0:
        return True  # Periodic checks
    
    return False
```

### 3. Prediction API
**File**: `src/serving/api.py`

**Responsibilities**:
- Serve REST API for predictions
- Compute behavioral features
- Score customers with XGBoost model
- Publish predictions to Kafka
- Store results in PostgreSQL

**Endpoints**:
- `POST /predict` - Score single customer
- `POST /batch_predict` - Score multiple customers
- `GET /stats` - Aggregate statistics
- `GET /customer/{id}/history` - Risk history
- `GET /high_risk_customers` - High-risk list

**Feature Engineering**:
- 30+ behavioral features
- Deviation-based (change from baseline)
- Categories:
  - Salary signals (3 features)
  - Savings behavior (5 features)
  - Spending patterns (7 features)
  - Payment behavior (6 features)
  - Cash behavior (3 features)
  - Transaction patterns (3 features)
  - Derived signals (3 features)

### 4. Intervention Worker
**File**: `src/streaming/intervention_worker.py`

**Responsibilities**:
- Consume prediction events from Kafka
- Apply intervention strategies
- Publish intervention events
- Store interventions in database

**Intervention Strategies**:
```python
STRATEGIES = {
    'CRITICAL': {
        'type': 'urgent_outreach',
        'channel': 'phone_call',
        'priority': 1,
        'message': 'Urgent: High risk detected. Contact immediately.'
    },
    'HIGH': {
        'type': 'proactive_support',
        'channel': 'sms',
        'priority': 2,
        'message': 'We noticed changes. Would you like to discuss options?'
    },
    'MEDIUM': {
        'type': 'gentle_reminder',
        'channel': 'email',
        'priority': 3,
        'message': 'Reminder: Upcoming payments due.'
    }
}
```

## Data Flow

### Transaction Event Flow
```
1. Transaction occurs
   ↓
2. Simulator publishes to Kafka (transactions-stream)
   ↓
3. Feature Processor consumes event
   ↓
4. Processor decides if prediction needed
   ↓
5. If yes, calls Prediction API
   ↓
6. API computes features from PostgreSQL
   ↓
7. API scores with XGBoost model
   ↓
8. API publishes prediction to Kafka (predictions-stream)
   ↓
9. API stores prediction in PostgreSQL
   ↓
10. Intervention Worker consumes prediction
    ↓
11. Worker applies intervention strategy
    ↓
12. Worker publishes intervention to Kafka (interventions-stream)
    ↓
13. Worker stores intervention in PostgreSQL
    ↓
14. Downstream systems consume intervention
```

### Latency Breakdown
```
Transaction → Kafka:           ~10ms
Kafka → Feature Processor:     ~50ms
Feature Processor → API:       ~200-500ms
API → Kafka:                   ~10ms
Kafka → Intervention Worker:   ~50ms
Intervention Worker → Kafka:   ~10ms

Total End-to-End:              ~330-630ms (< 1 second)
```

## Kafka Topics

### transactions-stream
- **Partitions**: 3
- **Retention**: 7 days
- **Replication**: 1 (increase for production)
- **Key**: customer_id (for ordering)
- **Purpose**: Real-time transaction events

### predictions-stream
- **Partitions**: 3
- **Retention**: 30 days
- **Replication**: 1
- **Key**: customer_id
- **Purpose**: Model predictions with risk scores

### interventions-stream
- **Partitions**: 2
- **Retention**: 90 days (compliance)
- **Replication**: 1
- **Key**: customer_id
- **Purpose**: Triggered interventions

### customer-updates
- **Partitions**: 2
- **Retention**: 30 days
- **Compaction**: Enabled
- **Key**: customer_id
- **Purpose**: Customer profile changes

### dashboard-updates
- **Partitions**: 1
- **Retention**: 1 day
- **Replication**: 1
- **Purpose**: Real-time dashboard events

## Database Schema

### risk_scores
```sql
CREATE TABLE risk_scores (
    customer_id VARCHAR(255),
    score_date TIMESTAMP,
    risk_score FLOAT,
    risk_level VARCHAR(50),
    model_version VARCHAR(100),
    top_feature_1 VARCHAR(255),
    top_feature_1_impact FLOAT,
    top_feature_2 VARCHAR(255),
    top_feature_2_impact FLOAT,
    top_feature_3 VARCHAR(255),
    top_feature_3_impact FLOAT,
    PRIMARY KEY (customer_id, score_date)
);
```

### interventions
```sql
CREATE TABLE interventions (
    intervention_id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255),
    risk_score FLOAT,
    risk_level VARCHAR(50),
    intervention_type VARCHAR(100),
    message TEXT,
    channel VARCHAR(50),
    priority INTEGER,
    timestamp TIMESTAMP,
    status VARCHAR(50),
    outcome VARCHAR(50),
    outcome_date TIMESTAMP
);
```

## Scalability

### Horizontal Scaling
```
Feature Processor:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Instance 1  │  │ Instance 2  │  │ Instance 3  │
│ Partition 0 │  │ Partition 1 │  │ Partition 2 │
└─────────────┘  └─────────────┘  └─────────────┘
       ↓                ↓                ↓
    Kafka Consumer Group (automatic load balancing)
```

### Vertical Scaling
- Increase API instances behind load balancer
- Scale PostgreSQL with read replicas
- Scale Kafka brokers for higher throughput

### Performance Tuning
- Batch size optimization
- Consumer prefetch settings
- API connection pooling
- Database query optimization
- Model inference optimization

## Monitoring

### Key Metrics

**Throughput**:
- Transactions/second
- Predictions/second
- Interventions/second

**Latency**:
- End-to-end latency (p50, p95, p99)
- API response time
- Feature computation time
- Model inference time

**Consumer Lag**:
- Feature processor lag
- Intervention worker lag
- Dashboard consumer lag

**Business Metrics**:
- High-risk customer count
- Intervention trigger rate
- False positive rate
- Intervention effectiveness

### Monitoring Tools
- Kafka Manager for topic monitoring
- Prometheus for metrics collection
- Grafana for visualization
- PostgreSQL slow query log
- Application logs (structured JSON)

## Fault Tolerance

### Kafka
- Message replication across brokers
- Consumer group automatic failover
- Offset management (at-least-once delivery)

### API
- Graceful Kafka failure handling
- Continues working if Kafka is down
- Database connection pooling
- Retry logic with exponential backoff

### Workers
- Automatic restart on failure
- Checkpoint/resume from last offset
- Dead letter queue for failed messages
- Circuit breaker pattern

## Security

### Authentication
- Kafka SASL/SCRAM authentication
- API key authentication for REST API
- Database connection encryption

### Authorization
- Kafka ACLs for topic access
- Role-based access control (RBAC)
- Customer data encryption at rest

### Compliance
- 90-day intervention audit trail
- PII data masking in logs
- GDPR compliance (data deletion)
- SOC 2 compliance ready

## Deployment

### Local Development
```bash
docker-compose up -d
python -m uvicorn src.serving.api:app --reload
python run_streaming_pipeline.py
```

### Production (GCP)
```
Cloud Run (API)
    ↓
Cloud Pub/Sub (instead of Kafka)
    ↓
Cloud Functions (Workers)
    ↓
Cloud SQL (PostgreSQL)
    ↓
BigQuery (Analytics)
```

## Cost Optimization

### Kafka
- Right-size partitions (3-5 per topic)
- Optimize retention periods
- Use compression (snappy/lz4)

### API
- Auto-scaling based on load
- Connection pooling
- Response caching

### Database
- Query optimization
- Proper indexing
- Partition large tables

## Future Enhancements

### Phase 6: Dashboard
- Real-time WebSocket updates
- Interactive charts
- Intervention tracking
- Customer drill-down

### Phase 7: Advanced ML
- Online learning
- A/B testing framework
- Multi-model ensemble
- Automated retraining

### Phase 8: Integration
- CRM integration
- SMS/Email gateway
- Payment gateway
- Credit bureau APIs

## Summary

The Pre-Delinquency Engine is a production-ready, event-driven system that:

✅ Processes transactions in real-time (<1s latency)  
✅ Detects financial stress with ML (XGBoost)  
✅ Triggers intelligent interventions automatically  
✅ Scales horizontally with Kafka  
✅ Provides complete observability  
✅ Maintains audit trail for compliance  

The architecture is designed for high throughput, low latency, and fault tolerance, making it suitable for production deployment in financial institutions.
