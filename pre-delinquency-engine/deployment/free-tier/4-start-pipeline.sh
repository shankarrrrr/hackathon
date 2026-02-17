#!/bin/bash
# Pre-Delinquency Engine - Start Streaming Pipeline
# Run this to start the real-time streaming pipeline

set -e

echo "🚀 Starting Streaming Pipeline"
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

# Create systemd service for streaming pipeline
echo "⚙️  Creating systemd service for streaming pipeline..."
sudo tee /etc/systemd/system/delinquency-pipeline.service > /dev/null << 'EOF'
[Unit]
Description=Pre-Delinquency Engine Streaming Pipeline
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/pre-delinquency-engine
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml exec -T api python run_streaming_pipeline.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "   ✅ Systemd service created"
echo ""

# Reload systemd
sudo systemctl daemon-reload

# Start the pipeline in the background
echo "🚀 Starting streaming pipeline..."
nohup docker-compose -f docker-compose.prod.yml exec -T api python run_streaming_pipeline.py > pipeline.log 2>&1 &
PIPELINE_PID=$!

echo "   ✅ Pipeline started (PID: $PIPELINE_PID)"
echo "   Logs: tail -f ~/pre-delinquency-engine/pipeline.log"
echo ""

# Wait a bit for pipeline to start
sleep 10

# Check if pipeline is running
if ps -p $PIPELINE_PID > /dev/null; then
    echo "   ✅ Pipeline is running"
else
    echo "   ⚠️  Pipeline may have stopped, check logs"
fi
echo ""

# Monitor Kafka topics
echo "📊 Checking Kafka topics..."
docker-compose -f docker-compose.prod.yml exec -T kafka kafka-topics --list --bootstrap-server localhost:9092
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo "=============================================================="
echo "✅ Streaming Pipeline Started!"
echo "=============================================================="
echo ""
echo "📍 Your application is fully operational:"
echo "   API:       http://$PUBLIC_IP:8000"
echo "   API Docs:  http://$PUBLIC_IP:8000/docs"
echo "   Dashboard: http://$PUBLIC_IP:8501"
echo ""
echo "📊 Monitor the pipeline:"
echo "   View logs:        tail -f ~/pre-delinquency-engine/pipeline.log"
echo "   Check API health: curl http://$PUBLIC_IP:8000/health"
echo "   View stats:       curl http://$PUBLIC_IP:8000/stats"
echo ""
echo "🔍 Monitor Kafka messages:"
echo "   Transactions:   docker-compose -f docker-compose.prod.yml exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic transactions-stream --from-beginning --max-messages 5"
echo "   Predictions:    docker-compose -f docker-compose.prod.yml exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic predictions-stream --from-beginning --max-messages 5"
echo "   Interventions:  docker-compose -f docker-compose.prod.yml exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic interventions-stream --from-beginning --max-messages 5"
echo ""
echo "💡 Useful Commands:"
echo "   Stop pipeline:    pkill -f run_streaming_pipeline"
echo "   Restart pipeline: bash deployment/free-tier/4-start-pipeline.sh"
echo "   View all logs:    docker-compose -f docker-compose.prod.yml logs -f"
echo ""
