#!/bin/bash
# Pre-Delinquency Engine - Local Development Setup
# Run this script to set up and run everything locally

set -e

echo "🚀 Pre-Delinquency Engine - Local Setup"
echo "=============================================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   Windows: https://docs.docker.com/desktop/install/windows-install/"
    echo "   Mac: https://docs.docker.com/desktop/install/mac-install/"
    echo "   Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Step 1: Start infrastructure services
echo "📦 Step 1: Starting infrastructure services..."
docker-compose up -d postgres redis zookeeper kafka mlflow
echo "   ✅ Infrastructure services started"
echo ""

# Step 2: Wait for PostgreSQL to be ready
echo "⏳ Step 2: Waiting for PostgreSQL to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose exec -T postgres pg_isready -U admin &> /dev/null; then
        echo "   ✅ PostgreSQL is ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES - waiting..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ PostgreSQL failed to start"
    exit 1
fi
echo ""

# Step 3: Create Python virtual environment
echo "🐍 Step 3: Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo "   ✅ Virtual environment already exists"
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

# Step 4: Set environment variables
echo "⚙️  Step 4: Setting environment variables..."
export DATABASE_URL="postgresql://admin:admin123@localhost:5432/bank_data"
export REDIS_URL="redis://:redis123@localhost:6379"
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export MLFLOW_TRACKING_URI="http://localhost:5000"
echo "   ✅ Environment variables set"
echo ""

# Step 5: Initialize database schema
echo "🗄️  Step 5: Initializing database schema..."
python -m src.data_generation.check_db
echo "   ✅ Database schema initialized"
echo ""

# Step 6: Create Kafka topics
echo "📡 Step 6: Creating Kafka topics..."
python -m src.streaming.setup_topics
echo "   ✅ Kafka topics created"
echo ""

# Step 7: Generate synthetic data
echo "📊 Step 7: Generating synthetic data (this may take 2-3 minutes)..."
python -m src.data_generation.synthetic_data
echo "   ✅ Synthetic data generated"
echo ""

# Step 8: Train ML model
echo "🤖 Step 8: Training ML model (this may take 1-2 minutes)..."
python -m src.models.quick_train
echo "   ✅ ML model trained"
echo ""

# Step 9: Verify data
echo "🔍 Step 9: Verifying data..."
CUSTOMER_COUNT=$(docker-compose exec -T postgres psql -U admin -d bank_data -t -c "SELECT COUNT(*) FROM customers;" | tr -d ' \n\r')
TRANSACTION_COUNT=$(docker-compose exec -T postgres psql -U admin -d bank_data -t -c "SELECT COUNT(*) FROM transactions;" | tr -d ' \n\r')

echo "   Customers:    $CUSTOMER_COUNT"
echo "   Transactions: $TRANSACTION_COUNT"
echo ""

echo "=============================================================="
echo "✅ LOCAL SETUP COMPLETE!"
echo "=============================================================="
echo ""
echo "📊 Database Statistics:"
echo "   Customers:    $CUSTOMER_COUNT"
echo "   Transactions: $TRANSACTION_COUNT"
echo "   ML Model:     Trained and ready"
echo ""
echo "🚀 Next Steps - Start the application:"
echo ""
echo "   1. Start the API server (in a new terminal):"
echo "      source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "      python -m src.serving.api"
echo ""
echo "   2. Start the Dashboard (in another terminal):"
echo "      source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "      streamlit run dashboard/app.py"
echo ""
echo "   3. Start the streaming pipeline (optional, in another terminal):"
echo "      source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "      python run_streaming_pipeline.py"
echo ""
echo "📍 Once started, access:"
echo "   API:       http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Dashboard: http://localhost:8501"
echo "   MLflow:    http://localhost:5000"
echo ""
echo "💡 Quick test:"
echo "   curl http://localhost:8000/health"
echo ""
echo "🛑 To stop infrastructure services:"
echo "   docker-compose down"
echo ""
