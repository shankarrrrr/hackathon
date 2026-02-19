# Pre-Delinquency Engine - Local Development Setup (Windows)
# Run this script in PowerShell to set up and run everything locally

$ErrorActionPreference = "Stop"

Write-Host "Pre-Delinquency Engine - Local Setup (Windows)" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Docker is not accessible. Please ensure Docker Desktop is running." -ForegroundColor Red
    Write-Host "If Docker is installed but not in PATH, restart PowerShell or your computer." -ForegroundColor Yellow
    exit 1
}

# Check if Docker daemon is running
try {
    docker ps | Out-Null
    Write-Host "Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed. Please install Python 3.8+ first:" -ForegroundColor Red
    Write-Host "   https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Step 1: Start infrastructure services
Write-Host "Step 1: Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d postgres redis zookeeper kafka mlflow
Write-Host "   Infrastructure services started" -ForegroundColor Green
Write-Host ""

# Step 2: Wait for PostgreSQL to be ready
Write-Host "Step 2: Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$maxRetries = 30
$retryCount = 0
$postgresReady = $false

while ($retryCount -lt $maxRetries) {
    try {
        $result = docker-compose exec -T postgres pg_isready -U admin 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   PostgreSQL is ready" -ForegroundColor Green
            $postgresReady = $true
            break
        }
    } catch {
        # Continue waiting
    }
    $retryCount++
    Write-Host "   Attempt $retryCount of $maxRetries - waiting..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if (-not $postgresReady) {
    Write-Host "PostgreSQL failed to start" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 3: Create Python virtual environment
Write-Host "Step 3: Setting up Python environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "   Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "   Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
Write-Host "   Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 4: Set environment variables
Write-Host "Step 4: Setting environment variables..." -ForegroundColor Yellow
$env:DATABASE_URL = "postgresql://admin:admin123@localhost:5432/bank_data"
$env:REDIS_URL = "redis://:redis123@localhost:6379"
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
$env:MLFLOW_TRACKING_URI = "http://localhost:5000"
Write-Host "   Environment variables set" -ForegroundColor Green
Write-Host ""

# Step 5: Initialize database schema
Write-Host "Step 5: Initializing database schema..." -ForegroundColor Yellow
python -m src.data_generation.check_db
Write-Host "   Database schema initialized" -ForegroundColor Green
Write-Host ""

# Step 6: Create Kafka topics
Write-Host "Step 6: Creating Kafka topics..." -ForegroundColor Yellow
python -m src.streaming.setup_topics
Write-Host "   Kafka topics created" -ForegroundColor Green
Write-Host ""

# Step 7: Generate synthetic data
Write-Host "Step 7: Generating synthetic data (this may take 2-3 minutes)..." -ForegroundColor Yellow
python -m src.data_generation.synthetic_data
Write-Host "   Synthetic data generated" -ForegroundColor Green
Write-Host ""

# Step 8: Train ML model
Write-Host "Step 8: Training ML model (this may take 1-2 minutes)..." -ForegroundColor Yellow
python -m src.models.quick_train
Write-Host "   ML model trained" -ForegroundColor Green
Write-Host ""

# Step 9: Verify data
Write-Host "Step 9: Verifying data..." -ForegroundColor Yellow
$customerCount = docker-compose exec -T postgres psql -U admin -d bank_data -t -c "SELECT COUNT(*) FROM customers;" | ForEach-Object { $_.Trim() }
$transactionCount = docker-compose exec -T postgres psql -U admin -d bank_data -t -c "SELECT COUNT(*) FROM transactions;" | ForEach-Object { $_.Trim() }

Write-Host "   Customers:    $customerCount" -ForegroundColor Cyan
Write-Host "   Transactions: $transactionCount" -ForegroundColor Cyan
Write-Host ""

Write-Host "==============================================================" -ForegroundColor Green
Write-Host "LOCAL SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Database Statistics:" -ForegroundColor Cyan
Write-Host "   Customers:    $customerCount" -ForegroundColor White
Write-Host "   Transactions: $transactionCount" -ForegroundColor White
Write-Host "   ML Model:     Trained and ready" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps - Start the application:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   1. Start the API server (in a new PowerShell window):" -ForegroundColor White
Write-Host "      .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "      python -m src.serving.api" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Start the Dashboard (in another PowerShell window):" -ForegroundColor White
Write-Host "      .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "      streamlit run dashboard/app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Start the streaming pipeline (optional):" -ForegroundColor White
Write-Host "      .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "      python run_streaming_pipeline.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Once started, access:" -ForegroundColor Cyan
Write-Host "   API:       http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "   MLflow:    http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Quick test:" -ForegroundColor Yellow
Write-Host "   curl http://localhost:8000/health" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop infrastructure services:" -ForegroundColor Yellow
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host ""
