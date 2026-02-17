#!/bin/bash
# Pre-Delinquency Engine - One-Click AWS Deployment
# Run this from Git Bash on Windows to deploy everything

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION=${AWS_REGION:-us-east-1}
KEY_NAME="pre-delinquency-key"
DEPLOYMENT_DIR="deployment/free-tier"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Pre-Delinquency Engine - AWS Deployment Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print step headers
print_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to handle errors
handle_error() {
    echo -e "${RED}❌ Error: $1${NC}"
    echo -e "${YELLOW}💡 Tip: $2${NC}"
    exit 1
}

# Step 1: Verify AWS credentials
print_step "Step 1/5: Verifying AWS Credentials"

if ! command -v aws &> /dev/null; then
    handle_error "AWS CLI not found" "Install with: pip install awscli"
fi

if ! aws sts get-caller-identity > /dev/null 2>&1; then
    handle_error "AWS credentials not configured" "Run: aws configure"
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS credentials verified${NC}"
echo "   Account ID: $ACCOUNT_ID"
echo "   Region: $REGION"

# Step 2: Launch EC2 instance
print_step "Step 2/5: Launching EC2 Instance"

cd $DEPLOYMENT_DIR
bash 1-launch-ec2.sh

# Read instance info
if [ ! -f "instance-info.txt" ]; then
    handle_error "Instance info not found" "Check if 1-launch-ec2.sh completed successfully"
fi

PUBLIC_IP=$(grep "Public IP:" instance-info.txt | cut -d' ' -f3)
INSTANCE_ID=$(grep "Instance ID:" instance-info.txt | cut -d' ' -f3)

echo -e "${GREEN}✅ EC2 instance launched${NC}"
echo "   Instance ID: $INSTANCE_ID"
echo "   Public IP: $PUBLIC_IP"

# Step 3: Wait for SSH to be ready
print_step "Step 3/5: Waiting for SSH Connection"

echo "⏳ Waiting for instance to be fully ready..."
sleep 45

MAX_RETRIES=15
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if ssh -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@$PUBLIC_IP "echo 'SSH Ready'" &> /dev/null 2>&1; then
        echo -e "${GREEN}✅ SSH connection established${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 10
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    handle_error "SSH connection failed" "Try connecting manually: ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
fi

# Step 4: Copy files and setup instance
print_step "Step 4/5: Setting Up Instance"

echo "📦 Copying deployment scripts to instance..."
scp -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no \
    2-setup-instance.sh \
    3-initialize-data.sh \
    4-start-pipeline.sh \
    ubuntu@$PUBLIC_IP:~/ || handle_error "Failed to copy files" "Check SSH connection"

echo -e "${GREEN}✅ Files copied${NC}"
echo ""

echo "🔧 Running setup script on instance (this takes 5-10 minutes)..."
ssh -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "bash 2-setup-instance.sh" || \
    handle_error "Setup failed" "SSH into instance and check logs: ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"

echo -e "${GREEN}✅ Instance setup complete${NC}"

# Step 5: Initialize data and start pipeline
print_step "Step 5/5: Initializing Data and Starting Pipeline"

echo "📊 Initializing database and generating data..."
ssh -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "bash 3-initialize-data.sh" || \
    handle_error "Data initialization failed" "Check logs on instance"

echo -e "${GREEN}✅ Data initialized${NC}"
echo ""

echo "🚀 Starting streaming pipeline..."
ssh -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "bash 4-start-pipeline.sh" || \
    handle_error "Pipeline start failed" "Check logs on instance"

echo -e "${GREEN}✅ Pipeline started${NC}"

# Final summary
cd ../../..
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              🎉 DEPLOYMENT SUCCESSFUL! 🎉                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📍 Your Application URLs:${NC}"
echo "   🌐 API:       http://$PUBLIC_IP:8000"
echo "   📚 API Docs:  http://$PUBLIC_IP:8000/docs"
echo "   📊 Dashboard: http://$PUBLIC_IP:8501"
echo ""
echo -e "${GREEN}🔐 SSH Access:${NC}"
echo "   ssh -i $DEPLOYMENT_DIR/${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo ""
echo -e "${GREEN}💡 Quick Commands:${NC}"
echo "   Test API:     curl http://$PUBLIC_IP:8000/health"
echo "   View stats:   curl http://$PUBLIC_IP:8000/stats"
echo "   View logs:    ssh -i $DEPLOYMENT_DIR/${KEY_NAME}.pem ubuntu@$PUBLIC_IP 'docker-compose -f pre-delinquency-engine/docker-compose.prod.yml logs -f'"
echo ""
echo -e "${YELLOW}💰 Cost Information:${NC}"
echo "   First 12 months: FREE (AWS Free Tier)"
echo "   After 12 months: ~\$10-15/month"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "   Keep your key file safe: $DEPLOYMENT_DIR/${KEY_NAME}.pem"
echo "   Instance ID: $INSTANCE_ID"
echo ""
echo -e "${GREEN}✨ Deployment completed in $(date)${NC}"
echo ""
