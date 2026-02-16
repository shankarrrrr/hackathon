"""
Run the complete streaming pipeline
Starts all workers in separate processes
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# Store process references
processes = []

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n" + "=" * 60)
    print("SHUTTING DOWN ALL WORKERS")
    print("=" * 60)
    
    for name, proc in processes:
        print(f"Stopping {name}...")
        proc.terminate()
    
    # Wait for all to terminate
    for name, proc in processes:
        proc.wait()
        print(f"  ✅ {name} stopped")
    
    print("\n✅ All workers stopped successfully")
    sys.exit(0)

def start_worker(name, command):
    """Start a worker process"""
    print(f"Starting {name}...")
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    processes.append((name, proc))
    return proc

def main():
    """Start all streaming workers"""
    
    print("=" * 60)
    print("PRE-DELINQUENCY ENGINE - STREAMING PIPELINE")
    print("=" * 60)
    print()
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check if Kafka is running
    print("Checking Kafka connection...")
    kafka_check = subprocess.run(
        "docker ps | findstr kafka",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if not kafka_check.stdout:
        print("❌ Kafka not running!")
        print("Please start Kafka first:")
        print("  docker-compose up -d kafka zookeeper")
        sys.exit(1)
    
    print("✅ Kafka is running")
    print()
    
    # Check if API is running
    print("Checking API connection...")
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("⚠️ API returned non-200 status")
    except:
        print("❌ API not running!")
        print("Please start the API first:")
        print("  python -m uvicorn src.serving.api:app --reload")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("STARTING WORKERS")
    print("=" * 60)
    print()
    
    # Start workers
    workers = [
        ("Feature Processor", "python -m src.streaming.feature_processor"),
        ("Intervention Worker", "python -m src.streaming.intervention_worker"),
        ("Transaction Simulator", "python -m src.streaming.transaction_simulator 1000 50")
    ]
    
    for name, command in workers:
        start_worker(name, command)
        time.sleep(2)  # Stagger startup
    
    print()
    print("=" * 60)
    print("ALL WORKERS STARTED")
    print("=" * 60)
    print()
    print("Pipeline components:")
    print("  1. Transaction Simulator - Streaming transactions to Kafka")
    print("  2. Feature Processor - Computing features and triggering predictions")
    print("  3. Intervention Worker - Processing predictions and triggering interventions")
    print()
    print("Event flow:")
    print("  Transactions → Kafka → Feature Processor → API → Predictions → Kafka → Intervention Worker")
    print()
    print("Press Ctrl+C to stop all workers")
    print("=" * 60)
    print()
    
    # Monitor workers
    try:
        while True:
            time.sleep(1)
            
            # Check if any worker died
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\n❌ {name} stopped unexpectedly!")
                    print("Stopping all workers...")
                    signal_handler(None, None)
    
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
