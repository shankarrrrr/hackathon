# AWS Free Tier Deployment Script (PowerShell)
# Deploys Pre-Delinquency Engine to AWS EC2 t2.micro instance

Write-Host "🚀 AWS Free Tier Deployment Script" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI not found. Please install it first." -ForegroundColor Red
    Write-Host "   Visit: https://aws.amazon.com/cli/"
    exit 1
}

try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS CLI configured" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not configured. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# Get user inputs
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
$KEY_NAME = Read-Host "Enter your SSH key pair name (must exist in AWS)"
$GITHUB_USER = Read-Host "Enter your GitHub username (for repo clone)"
$REPO_NAME = Read-Host "Enter your GitHub repo name [pre-delinquency-engine]"
if ([string]::IsNullOrWhiteSpace($REPO_NAME)) {
    $REPO_NAME = "pre-delinquency-engine"
}

Write-Host ""
Write-Host "Creating AWS resources..." -ForegroundColor Yellow

# Create security group
Write-Host "Creating security group..."
$SG_NAME = "pre-delinquency-sg-$(Get-Date -Format 'yyyyMMddHHmmss')"
try {
    $SG_ID = aws ec2 create-security-group `
        --group-name $SG_NAME `
        --description "Pre-Delinquency Engine Security Group" `
        --query 'GroupId' `
        --output text
} catch {
    $SG_ID = aws ec2 describe-security-groups `
        --group-names pre-delinquency-sg `
        --query 'SecurityGroups[0].GroupId' `
        --output text
}

Write-Host "✅ Security Group: $SG_ID" -ForegroundColor Green

# Configure security group rules
Write-Host "Configuring firewall rules..."
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 2>$null
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 2>$null
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 2>$null
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8501 --cidr 0.0.0.0/0 2>$null

Write-Host "✅ Firewall rules configured" -ForegroundColor Green

# Get latest Ubuntu AMI
Write-Host "Finding latest Ubuntu AMI..."
$AMI_ID = aws ec2 describe-images `
    --owners 099720109477 `
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" `
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' `
    --output text

Write-Host "✅ Using AMI: $AMI_ID" -ForegroundColor Green

# Launch EC2 instance
Write-Host "Launching EC2 instance (t2.micro)..."
$INSTANCE_ID = aws ec2 run-instances `
    --image-id $AMI_ID `
    --instance-type t2.micro `
    --key-name $KEY_NAME `
    --security-group-ids $SG_ID `
    --block-device-mappings '[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":30,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]' `
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=pre-delinquency-engine}]' `
    --query 'Instances[0].InstanceId' `
    --output text

Write-Host "✅ Instance launched: $INSTANCE_ID" -ForegroundColor Green

# Wait for instance to be running
Write-Host "Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
$PUBLIC_IP = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --query 'Reservations[0].Instances[0].PublicIpAddress' `
    --output text

Write-Host "✅ Instance running at: $PUBLIC_IP" -ForegroundColor Green

# Create setup script
Write-Host ""
Write-Host "Creating setup script..." -ForegroundColor Yellow

$SETUP_SCRIPT = @"
#!/bin/bash
set -e

echo "🚀 Setting up Pre-Delinquency Engine..."

# Update system
echo "📦 Updating system..."
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh > /dev/null 2>&1
sudo usermod -aG docker ubuntu
rm get-docker.sh

# Install Docker Compose
echo "📦 Installing Docker Compose..."
sudo curl -sL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-`$(uname -s)-`$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python and Git
echo "📦 Installing Python and Git..."
sudo apt-get install -y python3-pip python3-venv git -qq

# Clone repository
echo "📥 Cloning repository..."
cd ~
git clone https://github.com/$GITHUB_USER/$REPO_NAME.git
cd $REPO_NAME

# Create environment file
echo "⚙️ Creating environment file..."
cat > .env << 'EOF'
DATABASE_URL=postgresql://admin:admin123@postgres:5432/bank_data
REDIS_URL=redis://:redis123@redis:6379
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENVIRONMENT=production
EOF

# Start Docker services
echo "🐳 Starting Docker services..."
sudo docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 60

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt -q

# Initialize database
echo "🗄️ Initializing database..."
python3 -m src.data_generation.check_db

# Generate synthetic data
echo "📊 Generating synthetic data..."
python3 -m src.data_generation.synthetic_data

# Train model
echo "🤖 Training ML model..."
python3 -m src.models.quick_train

# Start services
echo "🚀 Starting application services..."
nohup python3 -m uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
sleep 5
nohup streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &

# Get public IP
PUBLIC_IP=`$(curl -s ifconfig.me)

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access your application:"
echo "   API: http://`$PUBLIC_IP:8000"
echo "   API Docs: http://`$PUBLIC_IP:8000/docs"
echo "   Dashboard: http://`$PUBLIC_IP:8501"
echo ""
"@

$SETUP_SCRIPT | Out-File -FilePath "$env:TEMP\setup-instance.sh" -Encoding UTF8

# Wait for SSH to be ready
Write-Host ""
Write-Host "Waiting for SSH to be ready (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Copy and execute setup script
Write-Host "Copying setup script to instance..." -ForegroundColor Yellow
scp -i "$HOME\.ssh\$KEY_NAME.pem" -o StrictHostKeyChecking=no "$env:TEMP\setup-instance.sh" "ubuntu@${PUBLIC_IP}:/tmp/"

Write-Host "Running setup script (this will take 5-10 minutes)..." -ForegroundColor Yellow
ssh -i "$HOME\.ssh\$KEY_NAME.pem" -o StrictHostKeyChecking=no "ubuntu@$PUBLIC_IP" "bash /tmp/setup-instance.sh"

# Final output
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Instance Details:" -ForegroundColor Yellow
Write-Host "  Instance ID: $INSTANCE_ID"
Write-Host "  Public IP: $PUBLIC_IP"
Write-Host "  Security Group: $SG_ID"
Write-Host ""
Write-Host "Access Your Application:" -ForegroundColor Yellow
Write-Host "  API: http://${PUBLIC_IP}:8000"
Write-Host "  API Docs: http://${PUBLIC_IP}:8000/docs"
Write-Host "  Dashboard: http://${PUBLIC_IP}:8501"
Write-Host ""
Write-Host "SSH Access:" -ForegroundColor Yellow
Write-Host "  ssh -i $HOME\.ssh\$KEY_NAME.pem ubuntu@$PUBLIC_IP"
Write-Host ""
Write-Host "View Logs:" -ForegroundColor Yellow
Write-Host "  ssh -i $HOME\.ssh\$KEY_NAME.pem ubuntu@$PUBLIC_IP 'tail -f ~/pre-delinquency-engine/api.log'"
Write-Host ""
Write-Host "Stop Instance (to save costs):" -ForegroundColor Yellow
Write-Host "  aws ec2 stop-instances --instance-ids $INSTANCE_ID"
Write-Host ""
Write-Host "Terminate Instance (when done):" -ForegroundColor Yellow
Write-Host "  aws ec2 terminate-instances --instance-ids $INSTANCE_ID"
Write-Host "  aws ec2 delete-security-group --group-id $SG_ID"
Write-Host ""
Write-Host "💰 Cost: `$0/month (first 12 months with AWS Free Tier)" -ForegroundColor Green
Write-Host ""
