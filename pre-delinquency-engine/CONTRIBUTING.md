# Contributing Guide

Welcome! This guide will help you understand the project structure and how to contribute effectively.

## Project Overview

This is a **real-time pre-delinquency detection system** that uses machine learning and event streaming to identify customers at risk of payment default 14-30 days in advance.

**Tech Stack:**
- Python 3.11
- FastAPI (API)
- Apache Kafka (Event Streaming)
- PostgreSQL (Database)
- XGBoost (ML Model)
- Docker (Infrastructure)

## Project Structure

```
pre-delinquency-engine/
├── src/                          # Source code
│   ├── data_generation/          # Synthetic data generation
│   ├── feature_engineering/      # Behavioral feature computation
│   ├── models/                   # ML model training
│   ├── serving/                  # FastAPI application
│   ├── streaming/                # Kafka producers/consumers
│   └── explainability/           # SHAP explainer
├── data/                         # Data storage
│   ├── raw/                      # Raw CSV data
│   ├── processed/                # Feature datasets
│   └── models/                   # Trained models
├── dashboard/                    # Streamlit dashboard (TODO)
├── tests/                        # Unit tests
├── deployment/                   # Deployment configs
├── docker/                       # Dockerfiles
├── sql/                          # Database schema
└── docs/                         # Documentation
```

## Getting Started

### 1. Setup Development Environment

```bash
# Clone the repo
git clone <repo-url>
cd pre-delinquency-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start infrastructure
docker-compose up -d

# Setup Kafka topics
python -m src.streaming.setup_topics
```

### 2. Understand the Architecture

Read these in order:
1. [README.md](README.md) - Project overview
2. [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
3. [STREAMING-COMPLETE.md](STREAMING-COMPLETE.md) - Kafka details
4. [TODO.md](TODO.md) - Remaining work

### 3. Run the System

```bash
# Terminal 1: Start API
python -m uvicorn src.serving.api:app --reload

# Terminal 2: Start workers
python run_streaming_pipeline.py

# Terminal 3: Run tests
python test_streaming_pipeline.py
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow these guidelines:
- Write clean, readable code
- Add docstrings to functions
- Follow PEP 8 style guide
- Add comments for complex logic
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run the system
python -m uvicorn src.serving.api:app --reload
python run_streaming_pipeline.py

# Run tests
python test_streaming_pipeline.py

# Check for errors in logs
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add dashboard overview page"
# or
git commit -m "fix: resolve intervention worker bug"
```

**Commit Message Format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python Style

```python
# Good: Clear function with docstring
def compute_risk_score(customer_id: str, observation_date: datetime) -> float:
    """
    Compute risk score for a customer at a specific date.
    
    Args:
        customer_id: Customer UUID
        observation_date: Date to compute score for
    
    Returns:
        Risk score between 0 and 1
    """
    features = compute_features(customer_id, observation_date)
    score = model.predict(features)
    return float(score)

# Bad: No docstring, unclear naming
def calc(c, d):
    f = get_f(c, d)
    return m.pred(f)
```

### Naming Conventions

- **Functions**: `snake_case` - `compute_features()`
- **Classes**: `PascalCase` - `FeatureProcessor`
- **Constants**: `UPPER_SNAKE_CASE` - `KAFKA_BOOTSTRAP_SERVERS`
- **Variables**: `snake_case` - `risk_score`

### File Organization

```python
# 1. Standard library imports
import os
from datetime import datetime

# 2. Third-party imports
import pandas as pd
from kafka import KafkaConsumer

# 3. Local imports
from src.feature_engineering.features import BehavioralFeatureEngineering
```

## Adding New Features

### Adding a New Behavioral Feature

1. **Define the feature** in `src/feature_engineering/features.py`:

```python
def _compute_new_feature(self, customer_id: str, observation_date: datetime) -> Dict:
    """Compute your new feature"""
    features = {}
    
    # Your logic here
    features['new_feature_name'] = calculated_value
    
    return features
```

2. **Add to feature list**:

```python
self.feature_list = [
    # ... existing features
    'new_feature_name',
]
```

3. **Call in compute_all_features**:

```python
features.update(self._compute_new_feature(customer_id, observation_date))
```

### Adding a New API Endpoint

1. **Add endpoint** in `src/serving/api.py`:

```python
@app.get("/your-endpoint")
async def your_endpoint():
    """Endpoint description"""
    try:
        # Your logic
        return {"result": "data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Test it**:
```bash
curl http://localhost:8000/your-endpoint
```

### Adding a New Kafka Consumer

1. **Create consumer** in `src/streaming/`:

```python
class YourConsumer:
    def __init__(self, callback):
        self.callback = callback
        self.consumer = KafkaConsumer(
            TOPICS['YOUR_TOPIC'],
            **CONSUMER_CONFIG,
            group_id='your-group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
    
    def start(self):
        for message in self.consumer:
            self.callback(message.value)
```

2. **Add to pipeline** in `run_streaming_pipeline.py`

## Testing

### Manual Testing

```bash
# 1. Start the system
python -m uvicorn src.serving.api:app --reload
python run_streaming_pipeline.py

# 2. Check API
curl http://localhost:8000/health

# 3. View Kafka messages
docker exec delinquency_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic predictions-stream \
  --from-beginning \
  --max-messages 5

# 4. Check database
docker exec delinquency_db psql -U admin -d bank_data \
  -c "SELECT COUNT(*) FROM risk_scores;"
```

### Automated Testing

```bash
# Run end-to-end test
python test_streaming_pipeline.py

# Expected: 6/6 tests passed
```

### Adding Unit Tests

Create tests in `tests/` directory:

```python
# tests/test_features.py
import pytest
from src.feature_engineering.features import BehavioralFeatureEngineering

def test_feature_computation():
    engineer = BehavioralFeatureEngineering()
    features = engineer.compute_all_features(
        customer_id="test-123",
        observation_date=datetime.now()
    )
    assert 'risk_score' in features
    assert 0 <= features['risk_score'] <= 1
```

Run with:
```bash
pytest tests/
```

## Common Tasks

### Regenerate Data

```bash
python -m src.data_generation.synthetic_data
```

### Retrain Model

```bash
python -m src.models.quick_train
```

### Reset Kafka Topics

```bash
docker exec delinquency_kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --delete --topic predictions-stream

python -m src.streaming.setup_topics
```

### Reset Database

```bash
docker-compose down -v
docker-compose up -d
python -m src.data_generation.synthetic_data
```

### View Logs

```bash
# API logs
# Check terminal where uvicorn is running

# Kafka logs
docker-compose logs kafka

# PostgreSQL logs
docker-compose logs postgres
```

## Debugging Tips

### API Not Responding

1. Check if it's running: `curl http://localhost:8000/health`
2. Check logs in terminal
3. Verify port 8000 is not in use: `netstat -ano | findstr :8000`

### Kafka Messages Not Flowing

1. Check topics exist: `docker exec delinquency_kafka kafka-topics --list --bootstrap-server localhost:9092`
2. Check consumer lag: `docker exec delinquency_kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group feature-processor-group`
3. Restart Kafka: `docker-compose restart kafka zookeeper`

### Database Connection Error

1. Check PostgreSQL is running: `docker-compose ps postgres`
2. Test connection: `docker exec delinquency_db psql -U admin -d bank_data -c "SELECT 1;"`
3. Check .env file has correct DATABASE_URL

### Model Not Loading

1. Check model exists: `ls data/models/quick/quick_model.json`
2. Retrain if missing: `python -m src.models.quick_train`
3. Check MODEL_PATH in .env

## Documentation

### Adding Documentation

- **Code**: Add docstrings to all functions/classes
- **API**: FastAPI auto-generates docs at `/docs`
- **Architecture**: Update ARCHITECTURE.md for major changes
- **Setup**: Update SETUP.md if setup process changes

### Documentation Style

```python
def function_name(param1: str, param2: int) -> bool:
    """
    One-line summary of what the function does.
    
    More detailed explanation if needed. Explain the purpose,
    not the implementation details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is invalid
    
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

## Getting Help

### Resources

- **Documentation**: Check all .md files in project root
- **Code Comments**: Read inline comments in source files
- **API Docs**: http://localhost:8000/docs
- **Architecture**: ARCHITECTURE.md

### Common Questions

**Q: Where do I add a new feature?**  
A: `src/feature_engineering/features.py`

**Q: How do I add a new API endpoint?**  
A: `src/serving/api.py`

**Q: Where are Kafka topics configured?**  
A: `src/streaming/kafka_config.py`

**Q: How do I change the ML model?**  
A: `src/models/train.py` or `src/models/quick_train.py`

**Q: Where is the database schema?**  
A: `sql/init.sql`

## Project Priorities

### Current Focus (Phase 6)
1. Build Streamlit dashboard
2. Add WebSocket for real-time updates
3. Create visualization components

### Next Phase (Phase 7)
1. Deploy to Google Cloud Platform
2. Replace Kafka with Cloud Pub/Sub
3. Setup CI/CD pipeline

### Future Enhancements
1. A/B testing framework
2. Model retraining pipeline
3. Feature store integration
4. Advanced stream processing

## Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] Functions have docstrings
- [ ] Changes are tested manually
- [ ] No errors in logs
- [ ] Documentation updated if needed
- [ ] Commit messages are clear
- [ ] No sensitive data in code
- [ ] .env.example updated if new env vars added

## Contact

For questions or issues:
- Check [TODO.md](TODO.md) for known issues
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Check existing documentation
- Create an issue on GitHub

---

**Happy Coding!** 🚀

Remember: Clean code is better than clever code. Write code that your future self will thank you for.
