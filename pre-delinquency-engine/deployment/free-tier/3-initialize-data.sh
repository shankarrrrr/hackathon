#!/bin/bash
# Pre-Delinquency Engine - Data Initialization Script
# Run this after setup to initialize database and generate data

set -e

echo "📊 Initializing Database and Generating Data"
echo "=============================================================="
echo ""

cd ~/pre-delinquency-engine

# Check if services are running
echo "🔍 Checking if services are running..."
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "❌ Services are not running. Please run 2-setup-instance.sh first"
    exit 1
fi
echo "   ✅ Services are running"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U admin &> /dev/null; then
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

# Initialize database schema
echo "🗄️  Initializing database schema..."
docker-compose -f docker-compose.prod.yml exec -T api python -m src.data_generation.check_db
echo "   ✅ Database schema initialized"
echo ""

# Create Kafka topics
echo "📡 Creating Kafka topics..."
docker-compose -f docker-compose.prod.yml exec -T api python -m src.streaming.setup_topics
echo "   ✅ Kafka topics created"
echo ""

# Generate synthetic data
echo "📊 Generating synthetic data (this may take 2-3 minutes)..."
docker-compose -f docker-compose.prod.yml exec -T api python -m src.data_generation.synthetic_data
echo "   ✅ Synthetic data generated"
echo ""

# Train ML model
echo "🤖 Training ML model (this may take 1-2 minutes)..."
docker-compose -f docker-compose.prod.yml exec -T api python -m src.models.quick_train
echo "   ✅ ML model trained"
echo ""

# Verify data
echo "🔍 Verifying data..."
CUSTOMER_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U admin -d bank_data -t -c "SELECT COUNT(*) FROM customers;" | tr -d ' \n')
TRANSACTION_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U admin -d bank_data -t -c "SELECT COUNT(*) FROM transactions;" | tr -d ' \n')

echo "   Customers:    $CUSTOMER_COUNT"
echo "   Transactions: $TRANSACTION_COUNT"
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo "=============================================================="
echo "✅ Data Initialization Complete!"
echo "=============================================================="
echo ""
echo "📊 Database Statistics:"
echo "   Customers:    $CUSTOMER_COUNT"
echo "   Transactions: $TRANSACTION_COUNT"
echo "   ML Model:     Trained and ready"
echo ""
echo "📍 Test your API:"
echo "   curl http://$PUBLIC_IP:8000/health"
echo "   curl http://$PUBLIC_IP:8000/stats"
echo ""
echo "📝 Next Steps:"
echo "   Start the streaming pipeline:"
echo "   bash deployment/free-tier/4-start-pipeline.sh"
echo ""
