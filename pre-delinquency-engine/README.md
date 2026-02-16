# Pre-Delinquency Intervention Engine

> **Real-time financial stress detection and proactive intervention system**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Kafka](https://img.shields.io/badge/Kafka-Event--Driven-orange.svg)](https://kafka.apache.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

A production-ready ML system that predicts which customers are at risk of payment default **14-30 days in advance**, enabling proactive interventions to prevent delinquency. Built on **Apache Kafka** for real-time event streaming with **sub-2-second latency**.

### Key Capabilities

✅ **Event-Driven Architecture** - Complete Kafka-based streaming pipeline  
✅ **Real-Time Processing** - Sub-2-second latency from transaction to intervention  
✅ **Behavioral Features** - 30+ deviation-based features (not absolute values)  
✅ **ML Model** - XGBoost with 0.80 AUC-ROC, optimized for high precision  
✅ **Smart Interventions** - Risk-based, multi-channel outreach (phone/SMS/email)  
✅ **REST API** - FastAPI with auto-generated documentation  
✅ **Scalable** - Horizontal scaling with Kafka consumer groups  
✅ **Observable** - Complete event audit trail in PostgreSQL  

## 🏗️ Architecture

```
┌─────────────┐
│Transactions │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Kafka Topic:        │
│ transactions-stream │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Feature Processor   │
│ (Real-time)         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Prediction API      │
│ (XGBoost Model)     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Kafka Topic:        │
│ predictions-stream  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Intervention Worker │
│ (Business Logic)    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Kafka Topic:        │
│ interventions-      │
│ stream              │
└─────────────────────┘
```

### Event Flow

1. **Transaction Simulator** → Streams transactions to Kafka
2. **Feature Processor** → Consumes transactions, computes features, triggers predictions
3. **Prediction API** → Scores customers with ML model, publishes to Kafka
4. **Intervention Worker** → Consumes predictions, triggers interventions based on risk
5. **PostgreSQL** → Stores all events for audit and analytics

### Performance

- **Latency**: <2 seconds end-to-end
- **Throughput**: 1000+ transactions/second
- **Predictions**: ~2-3 per second
- **Scalability**: Horizontal with Kafka consumer groups

## Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### 2. Start Infrastructure

```bash
# Start all services (PostgreSQL, Kafka, Zookeeper)
docker-compose up -d

# Initialize database
python -m src.data_generation.check_db

# Create Kafka topics
python -m src.streaming.setup_topics
```

### 3. Generate Data

```bash
# Generate synthetic data (1000 customers)
python -m src.data_generation.synthetic_data
```

### 4. Train Model

```bash
# Quick training (100 customers, no MLflow)
python -m src.models.quick_train
```

### 5. Start Streaming Pipeline

```bash
# Terminal 1: Start API
python -m uvicorn src.serving.api:app --reload

# Terminal 2: Start all streaming workers
python run_streaming_pipeline.py

# This starts:
# - Transaction Simulator (streams transactions to Kafka)
# - Feature Processor (computes features in real-time)
# - Intervention Worker (triggers interventions)
```

### 6. Monitor

```bash
# View API docs
http://localhost:8000/docs

# Check interventions in database
psql $DATABASE_URL -c "SELECT * FROM interventions ORDER BY timestamp DESC LIMIT 10;"

# Monitor Kafka messages
docker exec delinquency_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interventions-stream \
  --from-beginning
```

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /predict` - Score a single customer
- `POST /batch_predict` - Score multiple customers
- `GET /stats` - Aggregate risk statistics
- `GET /customer/{id}/history` - Customer risk history
- `GET /high_risk_customers` - List high-risk customers

## Intervention Strategies

| Risk Level | Intervention Type | Channel | Priority |
|-----------|------------------|---------|----------|
| CRITICAL | Urgent Outreach | Phone Call | 1 |
| HIGH | Proactive Support | SMS | 2 |
| MEDIUM | Gentle Reminder | Email | 3 |
| LOW | None | - | - |

## Tech Stack

- **Language**: Python 3.11
- **Streaming**: Apache Kafka
- **Database**: PostgreSQL 15
- **ML Framework**: XGBoost, scikit-learn
- **Explainability**: SHAP
- **API**: FastAPI + Uvicorn
- **Containerization**: Docker + Docker Compose

## Project Structure

```
pre-delinquency-engine/
├── src/
│   ├── data_generation/       # Synthetic data generation
│   ├── feature_engineering/   # Behavioral features
│   ├── models/                # ML model training
│   ├── serving/               # FastAPI application
│   ├── streaming/             # Kafka producers/consumers
│   │   ├── kafka_config.py
│   │   ├── producers.py
│   │   ├── consumers.py
│   │   ├── transaction_simulator.py
│   │   ├── feature_processor.py      # Real-time feature computation
│   │   └── intervention_worker.py    # Intervention engine
│   └── explainability/        # SHAP explainer
├── data/
│   ├── raw/                   # Raw CSV data
│   ├── processed/             # Feature datasets
│   └── models/                # Trained models
├── docker/                    # Dockerfiles
├── sql/                       # Database schema
├── run_streaming_pipeline.py  # Start all workers
├── docker-compose.yml         # Infrastructure
└── STREAMING-COMPLETE.md      # Complete documentation
```

## Documentation

- **STREAMING-COMPLETE.md** - Complete streaming architecture guide
- **KAFKA-SETUP.md** - Kafka setup and configuration
- **KAFKA-INTEGRATION.md** - Integration patterns
- **KAFKA-COMPLETE.md** - Kafka implementation details

## Development Workflow

1. Make code changes in `src/`
2. Services will auto-reload (API with `--reload` flag)
3. Monitor logs in each terminal
4. Check database for results
5. View Kafka messages for debugging

## Monitoring

### Kafka Topics

```bash
# List all topics
docker exec delinquency_kafka kafka-topics --list --bootstrap-server localhost:9092

# View messages
docker exec delinquency_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic <topic-name> \
  --from-beginning \
  --max-messages 10
```

### Consumer Lag

```bash
# Check consumer group lag
docker exec delinquency_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group <group-name>
```

### Database Queries

```sql
-- Recent predictions
SELECT customer_id, risk_score, risk_level, score_date
FROM risk_scores
ORDER BY score_date DESC
LIMIT 10;

-- Interventions by risk level
SELECT risk_level, intervention_type, COUNT(*)
FROM interventions
GROUP BY risk_level, intervention_type;
```

## Performance

- **Transaction ingestion**: 1000+ events/second
- **Feature computation**: 50-100 customers/second
- **Prediction latency**: 200-500ms per customer
- **End-to-end latency**: <2 seconds (transaction → intervention)

## Troubleshooting

### Kafka Not Starting
```bash
docker-compose logs kafka
docker-compose restart kafka zookeeper
```

### Consumer Lag Growing
```bash
# Add more consumer instances
# Start additional feature processors in new terminals
python -m src.streaming.feature_processor
```

### API Timeout
```bash
# Check API health
curl http://localhost:8000/health

# Restart API
# Ctrl+C and restart with uvicorn
```

## What's Next?

- **Phase 6**: Dashboard (Streamlit with WebSocket for real-time updates)
- **Phase 7**: GCP Deployment (Cloud Run, Pub/Sub, BigQuery)
- **Phase 8**: Demo & Presentation

## License

MIT License - See LICENSE file for details


## 📊 Project Status

### ✅ Completed (Phases 1-5)

- [x] **Phase 1**: Data Generation - 1000 customers, 600K+ transactions
- [x] **Phase 2**: Feature Engineering - 30+ behavioral features
- [x] **Phase 3**: Model Training - XGBoost with AUC 0.80
- [x] **Phase 4**: API Serving - FastAPI with Kafka integration
- [x] **Phase 5**: Streaming Pipeline - Complete event-driven architecture

### 🚧 Remaining Work

- [ ] **Phase 6**: Dashboard - Streamlit with real-time visualization (2-3 hours)
- [ ] **Phase 7**: GCP Deployment - Cloud Run, Pub/Sub, BigQuery (3-4 hours)
- [ ] **Phase 8**: Demo & Presentation - Video, diagrams, deck (2 hours)

**See [TODO.md](TODO.md) for detailed task list**

## 📚 Documentation

### Getting Started
- **[SETUP.md](SETUP.md)** - Complete setup instructions
- **[QUICK-START.md](QUICK-START.md)** - Quick reference guide
- **[HANDOVER.md](HANDOVER.md)** - Project handover document

### Architecture & Design
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview
- **[STREAMING-COMPLETE.md](STREAMING-COMPLETE.md)** - Kafka streaming details
- **[KAFKA-SETUP.md](KAFKA-SETUP.md)** - Kafka configuration guide

### Development
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines
- **[TODO.md](TODO.md)** - Remaining tasks and priorities

## 🤝 Contributing

This project is ready for collaboration! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development workflow
- Code style guidelines
- Testing procedures
- Common tasks

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Apache Kafka](https://kafka.apache.org/) - Distributed event streaming
- [XGBoost](https://xgboost.readthedocs.io/) - Gradient boosting framework
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [Docker](https://www.docker.com/) - Containerization platform

---

**Status**: Phases 1-5 Complete | **Next**: Dashboard Development  
**Last Updated**: 2024 | **Version**: 1.0.0
