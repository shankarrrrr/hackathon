# PHASE 0: PROJECT SETUP (Day 1)

## Step 1: Initialize Project

```bash
# Create project directory
mkdir pre-delinquency-engine && cd pre-delinquency-engine

# Initialize git
git init
git branch -M main

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Poetry
pip install poetry

# Initialize Poetry project
poetry init --name pre-delinquency-engine --python "^3.11"
```

## Step 2: Install Core Dependencies

Create pyproject.toml:

```toml
[tool.poetry]
name = "pre-delinquency-engine"
version = "0.1.0"
description = "Pre-delinquency intervention system using behavioral ML"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"

# Data & Database
pandas = "^2.2.0"
numpy = "^1.26.0"
sqlalchemy = "^2.0.0"
psycopg2-binary = "^2.9.9"
redis = "^5.0.0"
faker = "^24.0.0"

# ML & Feature Engineering
xgboost = "^2.0.0"
lightgbm = "^4.3.0"
scikit-learn = "^1.4.0"
shap = "^0.45.0"
feast = {extras = ["redis"], version = "^0.38.0"}
mlflow = "^2.11.0"

# API & Backend
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.28.0"}
pydantic = "^2.6.0"
pydantic-settings = "^2.2.0"
celery = "^5.3.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
python-multipart = "^0.0.9"
websockets = "^12.0"

# Dashboard & Visualization
streamlit = "^1.32.0"
plotly = "^5.19.0"
altair = "^5.2.0"

# Google Cloud
google-cloud-storage = "^2.14.0"
google-cloud-sql-connector = "^1.8.0"
google-cloud-logging = "^3.9.0"
google-cloud-secret-manager = "^2.18.0"

# Development & Testing
pytest = "^8.0.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.23.0"
black = "^24.2.0"
ruff = "^0.3.0"
mypy = "^1.8.0"
ipykernel = "^6.29.0"
jupyter = "^1.0.0"

[tool.poetry.dev-dependencies]
mkdocs = "^1.5.0"
mkdocs-material = "^9.5.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

```bash
# Install dependencies
poetry install
```

## Step 3: Setup Docker Environment

Create docker-compose.yml:

```yaml
version: '3.9'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: delinquency_db
    environment:
      POSTGRES_DB: bank_data
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    container_name: delinquency_redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass redis123
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.11.0
    container_name: delinquency_mlflow
    ports:
      - "5000:5000"
    environment:
      BACKEND_STORE_URI: postgresql://admin:admin123@postgres:5432/mlflow
      DEFAULT_ARTIFACT_ROOT: ./mlruns
    volumes:
      - mlflow_data:/mlflow
    command: >
      mlflow server
      --backend-store-uri postgresql://admin:admin123@postgres:5432/mlflow
      --default-artifact-root ./mlruns
      --host 0.0.0.0
      --port 5000
    depends_on:
      postgres:
        condition: service_healthy
  
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    container_name: delinquency_api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/bank_data
      REDIS_URL: redis://:redis123@redis:6379/0
      MLFLOW_TRACKING_URI: http://mlflow:5000
    volumes:
      - ./src:/app/src
      - ./data:/app/data
      - ./feast_repo:/app/feast_repo
    command: uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
  
  dashboard:
    build:
      context: .
      dockerfile: docker/Dockerfile.dashboard
    container_name: delinquency_dashboard
    ports:
      - "8501:8501"
    environment:
      API_URL: http://api:8000
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/bank_data
    volumes:
      - ./dashboard:/app/dashboard
      - ./src:/app/src
    command: streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
    depends_on:
      - api
    restart: unless-stopped
  
  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    container_name: delinquency_worker
    environment:
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/bank_data
      REDIS_URL: redis://:redis123@redis:6379/0
    volumes:
      - ./src:/app/src
      - ./data:/app/data
    command: celery -A src.serving.tasks worker --loglevel=info
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  mlflow_data:
```

Create docker/Dockerfile.api:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.serving.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create docker/Dockerfile.dashboard:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==1.7.1

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

Create docker/Dockerfile.worker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.7.1

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . .

CMD ["celery", "-A", "src.serving.tasks", "worker", "--loglevel=info"]
```

Create .env.example:

```bash
# Database
DATABASE_URL=postgresql://admin:admin123@localhost:5432/bank_data
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bank_data
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123

# Redis
REDIS_URL=redis://:redis123@localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis123

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-here-change-in-production

# Dashboard
DASHBOARD_PORT=8501

# Google Cloud (for deployment)
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GCS_BUCKET=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Model Settings
MODEL_THRESHOLD=0.5
BATCH_SIZE=1000
FEATURE_WINDOW_DAYS=30
PREDICTION_WINDOW_START=14
PREDICTION_WINDOW_END=30

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

```bash
# Copy to actual .env
cp .env.example .env

# Start services
docker-compose up -d

# Verify all services are running
docker-compose ps
```
