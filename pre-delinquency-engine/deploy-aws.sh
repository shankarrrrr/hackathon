#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 AWS Free Tier Deployment Script${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    echo "   Visit: https://aws.amazon.com/cli/"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"

# Get user inputs
echo ""
echo -e "${YELLOW}Configuration:${NC}"
read -p "Enter your SSH key pair name (must exist in AWS): " KEY_NAME
read -p "Enter your GitHub username (for repo clone): " GITHUB_USER
read -p "Enter your GitHub repo name [pre-delinquency-engine]: " REPO_NAME
REPO_NAME=${REPO_NAME:-pre-delinquency-engine}

echo ""
echo -e "${YELLOW}Creating AWS resources...${NC}"

# Create security group
echo "Creating security group..."
SG_ID=$(aws ec2 create-security-group \
  --group-name pre-delinquency-sg-$(date +%s) \
  --description "Pre-Delinquency Engine Security Group" \
  --query 'GroupId' \
  --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
    --group-names pre-delinquency-sg \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

echo -e "${GREEN}✅ Security Group: $SG_ID${NC}"

# Configure security group rules
echo "Configuring firewall rules..."
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8501 --cidr 0.0.0.0/0 2>/dev/null || true

echo -e "${GREEN}✅ Firewall rules configured${NC}"

# Get latest Ubuntu AMI
echo "Finding latest Ubuntu AMI..."
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text)

echo -e "${GREEN}✅ Using AMI: $AMI_ID${NC}"

# Launch EC2 instance
echo "Launching EC2 instance (t2.micro)..."
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t2.micro \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3","DeleteOnTermination":true}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=pre-delinquency-engine}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo -e "${GREEN}✅ Instance launched: $INSTANCE_ID${NC}"

# Wait for instance to be running
echo "Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo -e "${GREEN}✅ Instance running at: $PUBLIC_IP${NC}"

# Create setup script
echo ""
echo -e "${YELLOW}Creating setup script...${NC}"

cat > /tmp/setup-instance.sh << 'SETUP_SCRIPT'
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
sudo curl -sL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Python and Git
echo "📦 Installing Python and Git..."
sudo apt-get install -y python3-pip python3-venv git -qq

# Clone repository
echo "📥 Cloning repository..."
cd ~
git clone https://github.com/GITHUB_USER/REPO_NAME.git
cd REPO_NAME

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
PUBLIC_IP=$(curl -s ifconfig.me)

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access your application:"
echo "   API: http://$PUBLIC_IP:8000"
echo "   API Docs: http://$PUBLIC_IP:8000/docs"
echo "   Dashboard: http://$PUBLIC_IP:8501"
echo ""
SETUP_SCRIPT

# Replace placeholders
sed -i "s/GITHUB_USER/$GITHUB_USER/g" /tmp/setup-instance.sh
sed -i "s/REPO_NAME/$REPO_NAME/g" /tmp/setup-instance.sh

# Wait for SSH to be ready
echo ""
echo -e "${YELLOW}Waiting for SSH to be ready (30 seconds)...${NC}"
sleep 30

# Copy and execute setup script
echo -e "${YELLOW}Copying setup script to instance...${NC}"
scp -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no /tmp/setup-instance.sh ubuntu@$PUBLIC_IP:/tmp/

echo -e "${YELLOW}Running setup script (this will take 5-10 minutes)...${NC}"
ssh -i ~/.ssh/$KEY_NAME.pem -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "bash /tmp/setup-instance.sh"

# Final output
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Instance Details:${NC}"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  Security Group: $SG_ID"
echo ""
echo -e "${YELLOW}Access Your Application:${NC}"
echo "  API: http://$PUBLIC_IP:8000"
echo "  API Docs: http://$PUBLIC_IP:8000/docs"
echo "  Dashboard: http://$PUBLIC_IP:8501"
echo ""
echo -e "${YELLOW}SSH Access:${NC}"
echo "  ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo ""
echo -e "${YELLOW}View Logs:${NC}"
echo "  ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP 'tail -f ~/pre-delinquency-engine/api.log'"
echo ""
echo -e "${YELLOW}Stop Instance (to save costs):${NC}"
echo "  aws ec2 stop-instances --instance-ids $INSTANCE_ID"
echo ""
echo -e "${YELLOW}Terminate Instance (when done):${NC}"
echo "  aws ec2 terminate-instances --instance-ids $INSTANCE_ID"
echo "  aws ec2 delete-security-group --group-id $SG_ID"
echo ""
echo -e "${GREEN}💰 Cost: \$0/month (first 12 months with AWS Free Tier)${NC}"
echo ""
