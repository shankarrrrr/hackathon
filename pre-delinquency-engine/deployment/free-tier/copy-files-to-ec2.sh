#!/bin/bash
# Copy project files to EC2 instance
# Run this from your LOCAL machine in the hackathon directory

set -e

EC2_IP="13.127.144.56"
KEY_FILE="pre-delinquency-engine/deployment/free-tier/pre-delinquency-key.pem"

echo "📦 Copying project files to EC2 instance..."
echo "=============================================================="
echo ""

# Ensure key has correct permissions
chmod 400 "$KEY_FILE"

# Copy docker directory
echo "📁 Copying docker directory..."
scp -i "$KEY_FILE" -r pre-delinquency-engine/docker ubuntu@$EC2_IP:~/pre-delinquency-engine/
echo "   ✅ Docker files copied"
echo ""

# Copy src directory
echo "📁 Copying src directory..."
scp -i "$KEY_FILE" -r pre-delinquency-engine/src ubuntu@$EC2_IP:~/pre-delinquency-engine/
echo "   ✅ Source files copied"
echo ""

# Copy dashboard directory
echo "📁 Copying dashboard directory..."
scp -i "$KEY_FILE" -r pre-delinquency-engine/dashboard ubuntu@$EC2_IP:~/pre-delinquency-engine/
echo "   ✅ Dashboard files copied"
echo ""

# Copy sql directory
echo "📁 Copying sql directory..."
scp -i "$KEY_FILE" -r pre-delinquency-engine/sql ubuntu@$EC2_IP:~/pre-delinquency-engine/
echo "   ✅ SQL files copied"
echo ""

# Copy requirements.txt
echo "📄 Copying requirements.txt..."
scp -i "$KEY_FILE" pre-delinquency-engine/requirements.txt ubuntu@$EC2_IP:~/pre-delinquency-engine/
echo "   ✅ Requirements file copied"
echo ""

echo "=============================================================="
echo "✅ All files copied successfully!"
echo "=============================================================="
echo ""
echo "📝 Next steps on EC2 instance:"
echo "   1. SSH into the instance:"
echo "      ssh -i $KEY_FILE ubuntu@$EC2_IP"
echo ""
echo "   2. Rebuild the Docker containers:"
echo "      cd ~/pre-delinquency-engine"
echo "      docker-compose -f docker-compose.prod.yml build"
echo "      docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "   3. Run the initialization script:"
echo "      bash ~/3-initialize-data.sh"
echo ""
