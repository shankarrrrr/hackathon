# PHASE 7: GOOGLE CLOUD DEPLOYMENT (Days 22-24) ⭐

## GCP Deployment Strategy

Complete infrastructure setup for production deployment on Google Cloud Platform using free tier and credits.

## Cloud Build Configuration

Create deployment/cloudbuild.yaml:

```yaml
# Cloud Build configuration for automated deployment
steps:
  # Build API container
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/delinquency-api:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/delinquency-api:latest'
      - '-f'
      - 'docker/Dockerfile.api'
      - '.'
    id: 'build-api'
  
  # Build dashboard container
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/delinquency-dashboard:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/delinquency-dashboard:latest'
      - '-f'
      - 'docker/Dockerfile.dashboard'
      - '.'
    id: 'build-dashboard'
  
  # Push API image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/delinquency-api:$SHORT_SHA'
    id: 'push-api'
    waitFor: ['build-api']
  
  # Push dashboard image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/delinquency-dashboard:$SHORT_SHA'
    id: 'push-dashboard'
    waitFor: ['build-dashboard']
  
  # Deploy API to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'delinquency-api'
      - '--image'
      - 'gcr.io/$PROJECT_ID/delinquency-api:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-env-vars'
      - 'DATABASE_URL=$$DATABASE_URL,REDIS_URL=$$REDIS_URL'
      - '--max-instances'
      - '10'
      - '--memory'
      - '2Gi'
      - '--cpu'
      - '2'
      - '--timeout'
      - '300'
    secretEnv: ['DATABASE_URL', 'REDIS_URL']
    id: 'deploy-api'
    waitFor: ['push-api']
  
  # Deploy dashboard to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'delinquency-dashboard'
      - '--image'
      - 'gcr.io/$PROJECT_ID/delinquency-dashboard:$SHORT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-env-vars'
      - 'API_URL=https://delinquency-api-xxxxx.run.app,DATABASE_URL=$$DATABASE_URL'
      - '--max-instances'
      - '5'
      - '--memory'
      - '1Gi'
    secretEnv: ['DATABASE_URL']
    id: 'deploy-dashboard'
    waitFor: ['push-dashboard', 'deploy-api']

availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/database-url/versions/latest
      env: 'DATABASE_URL'
    - versionName: projects/$PROJECT_ID/secrets/redis-url/versions/latest
      env: 'REDIS_URL'

options:
  machineType: 'N1_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY

timeout: 1800s
```

## Terraform Infrastructure

[Full Terraform configuration from your prompt]

## Deployment Script

Create deployment/deploy.sh:

```bash
#!/bin/bash
# Pre-Delinquency Engine - GCP Deployment Script
# Usage: ./deploy.sh [dev|staging|prod]

set -e

ENVIRONMENT=${1:-dev}
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"

echo "🚀 Deploying Pre-Delinquency Engine to GCP ($ENVIRONMENT)"
echo "=================================================="

# Step 1: Set GCP project
gcloud config set project $PROJECT_ID

# Step 2: Enable APIs
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    storage.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com

# Step 3: Build containers
gcloud builds submit \
    --config=deployment/cloudbuild.yaml \
    --substitutions=_ENVIRONMENT=$ENVIRONMENT \
    .

# Step 4: Apply Terraform
cd deployment/terraform
terraform init
terraform apply -var="project_id=$PROJECT_ID" -auto-approve
cd ../..

# Step 5: Get deployment URLs
API_URL=$(gcloud run services describe delinquency-api --region=$REGION --format="value(status.url)")
DASHBOARD_URL=$(gcloud run services describe delinquency-dashboard --region=$REGION --format="value(status.url)")

echo ""
echo "✅ Deployment Complete!"
echo "📍 API URL:       $API_URL"
echo "📍 Dashboard URL: $DASHBOARD_URL"
```

## Cost Estimation

| Service | Free Tier | Estimated Usage | Cost |
|---------|-----------|-----------------|------|
| Cloud Run | 2M requests/month | Demo load | **$0** |
| Cloud SQL | f1-micro instance | 10GB storage | **$0-5/month** |
| Memorystore Redis | 1GB basic | Cache | **$30/month** |
| Cloud Storage | 5GB | Models & data | **$0** |
| Cloud Build | 120 build-minutes/day | CI/CD | **$0** |
| **Total** | | | **$30-35/month** |

💡 **Tip**: Use free trial credits ($300) to run for 8-10 months free!

## Quick Deployment Guide

### 1. Setup GCP Project
```bash
gcloud projects create delinquency-engine-demo
gcloud config set project delinquency-engine-demo
```

### 2. Deploy Infrastructure
```bash
./deployment/deploy.sh dev
```

### 3. Verify Deployment
```bash
curl $API_URL/health
```

## Monitoring & Logs

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Setup monitoring
gcloud monitoring dashboards create --config-from-file=deployment/monitoring-dashboard.json
```

## Cleanup

```bash
# Delete all resources
terraform destroy

# Or delete project
gcloud projects delete delinquency-engine-demo
```
