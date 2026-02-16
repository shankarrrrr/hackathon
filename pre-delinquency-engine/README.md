# Pre-Delinquency Intervention Engine

A behavioral ML system for predicting and preventing loan delinquencies before they occur.

## Phase 0: Project Setup - COMPLETED ✅

### What's Been Set Up

1. **Project Structure**
   - Complete directory structure with all necessary folders
   - Python package structure with `__init__.py` files
   - Configuration files for Docker, Poetry, and environment variables

2. **Configuration Files**
   - `pyproject.toml` - Poetry dependencies (XGBoost, FastAPI, Streamlit, etc.)
   - `docker-compose.yml` - PostgreSQL (TimescaleDB), Redis, MLflow services
   - `.env` - Environment variables (copied from `.env.example`)
   - `sql/init.sql` - Complete database schema with 8 tables

3. **Docker Setup**
   - `docker/Dockerfile.api` - FastAPI service
   - `docker/Dockerfile.dashboard` - Streamlit dashboard
   - `docker/Dockerfile.worker` - Celery worker

### Next Steps to Complete Phase 0

1. **Start Docker Desktop**
   ```bash
   # Make sure Docker Desktop is running on Windows
   # You can start it from the Start menu
   ```

2. **Start Docker Services**
   ```bash
   cd pre-delinquency-engine
   docker-compose up -d
   ```

3. **Verify Services**
   ```bash
   docker-compose ps
   ```
   
   You should see:
   - `delinquency_db` (PostgreSQL + TimescaleDB) on port 5432
   - `delinquency_redis` (Redis) on port 6379
   - `delinquency_mlflow` (MLflow) on port 5000

4. **Install Python Dependencies**
   ```bash
   # Install Poetry if not already installed
   pip install poetry
   
   # Install project dependencies
   poetry install
   ```

5. **Verify Database Schema**
   ```bash
   # Connect to PostgreSQL
   docker exec -it delinquency_db psql -U admin -d bank_data
   
   # List tables
   \dt
   
   # Should see: customers, accounts, transactions, loans, payments, 
   #             customer_behavior, predictions, interventions
   ```

### Tech Stack

- **Language**: Python 3.11
- **Package Manager**: Poetry
- **Database**: PostgreSQL 15 + TimescaleDB
- **Cache**: Redis 7
- **ML Tracking**: MLflow
- **ML Framework**: XGBoost, LightGBM, scikit-learn
- **Explainability**: SHAP
- **Feature Store**: Feast
- **API**: FastAPI + Uvicorn
- **Dashboard**: Streamlit
- **Task Queue**: Celery
- **Containerization**: Docker + Docker Compose
- **Cloud**: Google Cloud Platform (GCP)

### Project Structure

```
pre-delinquency-engine/
├── src/                    # Source code
├── data/                   # Data storage
│   ├── raw/               # Raw data
│   ├── processed/         # Processed data
│   └── models/            # Trained models
├── dashboard/             # Streamlit dashboard
├── tests/                 # Unit tests
├── notebooks/             # Jupyter notebooks
├── deployment/            # Deployment configs
├── docker/                # Dockerfiles
├── sql/                   # SQL scripts
├── feast_repo/            # Feast feature store
├── pyproject.toml         # Poetry dependencies
├── docker-compose.yml     # Docker services
└── .env                   # Environment variables
```

## What's Next?

After completing Phase 0 setup:
- **Phase 1**: Data Generation (synthetic customer data)
- **Phase 2**: Feature Engineering (30+ behavioral features)
- **Phase 3**: Model Training (XGBoost + SHAP)
- **Phase 4**: API Development (FastAPI endpoints)
- **Phase 5**: Intervention Engine (decision logic)
- **Phase 6**: Dashboard (5-page Streamlit app)
- **Phase 7**: GCP Deployment
- **Phase 8**: Demo & Presentation

## Quick Start (After Docker is Running)

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Development Workflow

1. Make code changes in `src/` or `dashboard/`
2. Services will auto-reload (volumes are mounted)
3. Access services:
   - API: http://localhost:8000
   - Dashboard: http://localhost:8501
   - MLflow: http://localhost:5000
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

## Troubleshooting

- **Docker not starting**: Make sure Docker Desktop is running
- **Port conflicts**: Check if ports 5432, 6379, 5000, 8000, 8501 are available
- **Poetry install fails**: Make sure Python 3.11 is installed
- **Database connection fails**: Wait for health checks to pass (`docker-compose ps`)
