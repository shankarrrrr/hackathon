#!/bin/bash
# Pre-Delinquency Engine - Free Tier EC2 Launch Script
# This script launches a t3.micro EC2 instance (Free Tier eligible)

set -e

echo "🚀 Launching Free Tier EC2 Instance for Pre-Delinquency Engine"
echo "=============================================================="
echo ""

# Configuration
INSTANCE_TYPE="t3.micro"
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION="us-east-1"
    echo "⚠️  No region configured, using default: $REGION"
fi
KEY_NAME="pre-delinquency-key"
PROJECT_NAME="pre-delinquency-engine"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   pip install awscli"
    exit 1
fi

# Check if AWS credentials are configured
echo "🔍 Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    CURRENT_REGION=$(aws configure get region)
    echo "✅ AWS CLI configured"
    echo "   Account ID: $ACCOUNT_ID"
    echo "   Region: $CURRENT_REGION"
else
    echo "❌ AWS credentials not configured. Please run:"
    echo "   aws configure"
    exit 1
fi
echo ""

# Get latest Ubuntu AMI for the region
echo "📦 Finding latest Ubuntu 22.04 AMI..."
AMI_ID=$(aws ec2 describe-images \
    --region $REGION \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

echo "   Using AMI: $AMI_ID"
echo ""

# Create key pair if it doesn't exist
echo "🔑 Checking for SSH key pair..."
if aws ec2 describe-key-pairs --region $REGION --key-names $KEY_NAME &> /dev/null; then
    echo "   ✅ Key pair '$KEY_NAME' already exists"
else
    echo "   Creating new key pair '$KEY_NAME'..."
    aws ec2 create-key-pair \
        --region $REGION \
        --key-name $KEY_NAME \
        --query 'KeyMaterial' \
        --output text > ${KEY_NAME}.pem
    
    chmod 400 ${KEY_NAME}.pem
    echo "   ✅ Key pair created and saved to ${KEY_NAME}.pem"
    echo "   ⚠️  IMPORTANT: Keep this file safe! You'll need it to SSH into the instance."
fi
echo ""

# Create security group
echo "🔒 Creating security group..."
SG_NAME="${PROJECT_NAME}-sg"

# Check if security group exists
SG_ID=$(aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "None")

if [ "$SG_ID" != "None" ]; then
    echo "   ✅ Security group already exists: $SG_ID"
else
    SG_ID=$(aws ec2 create-security-group \
        --region $REGION \
        --group-name $SG_NAME \
        --description "Security group for Pre-Delinquency Engine" \
        --query 'GroupId' \
        --output text)
    
    echo "   ✅ Security group created: $SG_ID"
    
    # Add ingress rules
    echo "   Adding security rules..."
    
    # SSH
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --output text > /dev/null
    
    # HTTP
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --output text > /dev/null
    
    # HTTPS
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --output text > /dev/null
    
    # API (8000)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --output text > /dev/null
    
    # Dashboard (8501)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --protocol tcp \
        --port 8501 \
        --cidr 0.0.0.0/0 \
        --output text > /dev/null
    
    echo "   ✅ Security rules added (SSH, HTTP, HTTPS, 8000, 8501)"
fi
echo ""

# Launch EC2 instance
echo "🚀 Launching EC2 instance ($INSTANCE_TYPE)..."
INSTANCE_ID=$(aws ec2 run-instances \
    --region $REGION \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$PROJECT_NAME},{Key=Project,Value=$PROJECT_NAME}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "   ✅ Instance launched: $INSTANCE_ID"
echo ""

# Wait for instance to be running
echo "⏳ Waiting for instance to start (this may take 1-2 minutes)..."
aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID

echo "   ✅ Instance is running!"
echo ""

# Get instance details
echo "📋 Instance Details:"
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].[PublicIpAddress,PublicDnsName,PrivateIpAddress]' \
    --output text)

PUBLIC_IP=$(echo $INSTANCE_INFO | awk '{print $1}')
PUBLIC_DNS=$(echo $INSTANCE_INFO | awk '{print $2}')
PRIVATE_IP=$(echo $INSTANCE_INFO | awk '{print $3}')

echo "   Instance ID:  $INSTANCE_ID"
echo "   Public IP:    $PUBLIC_IP"
echo "   Public DNS:   $PUBLIC_DNS"
echo "   Private IP:   $PRIVATE_IP"
echo ""

# Save instance info to file
cat > instance-info.txt << EOF
Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Public DNS: $PUBLIC_DNS
Private IP: $PRIVATE_IP
Region: $REGION
Key File: ${KEY_NAME}.pem
EOF

echo "✅ Instance information saved to instance-info.txt"
echo ""

# Wait for instance to be ready for SSH
echo "⏳ Waiting for SSH to be ready (this may take another minute)..."
sleep 30

# Test SSH connection
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if ssh -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@$PUBLIC_IP "echo 'SSH Ready'" &> /dev/null; then
        echo "   ✅ SSH is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES - waiting..."
    sleep 10
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "   ⚠️  SSH not ready yet, but you can try connecting manually in a few minutes"
fi

echo ""
echo "=============================================================="
echo "✅ EC2 Instance Successfully Launched!"
echo "=============================================================="
echo ""
echo "📍 Access Information:"
echo "   SSH Command:  ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo "   API URL:      http://$PUBLIC_IP:8000"
echo "   Dashboard:    http://$PUBLIC_IP:8501"
echo ""
echo "📝 Next Steps:"
echo "   1. Copy setup script to instance:"
echo "      scp -i ${KEY_NAME}.pem deployment/free-tier/2-setup-instance.sh ubuntu@$PUBLIC_IP:~/"
echo ""
echo "   2. SSH into instance:"
echo "      ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
echo ""
echo "   3. Run setup script:"
echo "      bash 2-setup-instance.sh"
echo ""
echo "💡 Tip: The instance is Free Tier eligible for 12 months!"
echo "   After 12 months, it will cost approximately \$10-15/month"
echo ""
