#!/bin/bash
# AWS Credentials Verification Script
# Run this before deployment to verify your AWS setup

set -e

echo "🔍 AWS Credentials Verification"
echo "=============================================================="
echo ""

# Check AWS CLI
echo "1️⃣ Checking AWS CLI installation..."
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1)
    echo "   ✅ AWS CLI installed: $AWS_VERSION"
else
    echo "   ❌ AWS CLI not found"
    echo "   Install with: pip install awscli"
    exit 1
fi
echo ""

# Check credentials
echo "2️⃣ Checking AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
    echo "   ✅ Credentials configured"
    echo "   Account ID: $ACCOUNT_ID"
    echo "   User ARN: $USER_ARN"
else
    echo "   ❌ Credentials not configured"
    echo "   Run: aws configure"
    exit 1
fi
echo ""

# Check region
echo "3️⃣ Checking AWS region..."
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    echo "   ⚠️  No region configured, will use us-east-1"
    REGION="us-east-1"
else
    echo "   ✅ Region configured: $REGION"
fi
echo ""

# Check EC2 permissions
echo "4️⃣ Checking EC2 permissions..."
if aws ec2 describe-regions --region $REGION > /dev/null 2>&1; then
    echo "   ✅ Can access EC2 service"
else
    echo "   ❌ Cannot access EC2 service"
    echo "   Check your IAM permissions"
    exit 1
fi
echo ""

# Check if Free Tier eligible
echo "5️⃣ Checking Free Tier eligibility..."
ACCOUNT_AGE=$(aws iam get-account-summary --query 'SummaryMap.AccountAccessKeysPresent' --output text 2>/dev/null || echo "unknown")
echo "   ℹ️  Free Tier is available for 12 months from account creation"
echo "   ℹ️  Check your eligibility at: https://console.aws.amazon.com/billing/home#/freetier"
echo ""

# Check existing resources
echo "6️⃣ Checking existing resources in $REGION..."

# Check key pairs
KEY_COUNT=$(aws ec2 describe-key-pairs --region $REGION --query 'length(KeyPairs)' --output text)
echo "   Key Pairs: $KEY_COUNT"

# Check security groups
SG_COUNT=$(aws ec2 describe-security-groups --region $REGION --query 'length(SecurityGroups)' --output text)
echo "   Security Groups: $SG_COUNT"

# Check instances
INSTANCE_COUNT=$(aws ec2 describe-instances --region $REGION --query 'length(Reservations[].Instances[])' --output text)
echo "   EC2 Instances: $INSTANCE_COUNT"
echo ""

# Check for existing pre-delinquency resources
echo "7️⃣ Checking for existing pre-delinquency resources..."
EXISTING_KEY=$(aws ec2 describe-key-pairs --region $REGION --key-names pre-delinquency-key --query 'KeyPairs[0].KeyName' --output text 2>/dev/null || echo "None")
if [ "$EXISTING_KEY" != "None" ]; then
    echo "   ⚠️  Key pair 'pre-delinquency-key' already exists"
    echo "   The script will use the existing key"
else
    echo "   ✅ No existing pre-delinquency key pair"
fi

EXISTING_SG=$(aws ec2 describe-security-groups --region $REGION --filters "Name=group-name,Values=pre-delinquency-engine-sg" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "None")
if [ "$EXISTING_SG" != "None" ]; then
    echo "   ⚠️  Security group 'pre-delinquency-engine-sg' already exists: $EXISTING_SG"
    echo "   The script will use the existing security group"
else
    echo "   ✅ No existing pre-delinquency security group"
fi
echo ""

# Summary
echo "=============================================================="
echo "✅ AWS Verification Complete!"
echo "=============================================================="
echo ""
echo "📋 Summary:"
echo "   Account ID: $ACCOUNT_ID"
echo "   Region: $REGION"
echo "   EC2 Access: ✅"
echo "   Ready to deploy: ✅"
echo ""
echo "📝 Next Steps:"
echo "   1. Run: bash 1-launch-ec2.sh"
echo "   2. Follow the instructions"
echo "   3. Your application will be live in ~20 minutes"
echo ""
echo "💰 Cost:"
echo "   First 12 months: \$0 (Free Tier)"
echo "   After 12 months: ~\$10-15/month"
echo ""
