# Pre-Delinquency Intervention Engine - Project Plan

🏆 **PRE-DELINQUENCY INTERVENTION ENGINE - REFINED BUILD GUIDE**
Complete AI-Assisted Development Prompt for Integrated IDE

---

## 📋 PROJECT OVERVIEW

**Name:** Pre-Delinquency Intervention Engine  
**Goal:** Win hackathon by building a production-grade ML system that predicts financial stress 2-4 weeks before delinquency  
**Timeline:** 30 days (4 weeks)  
**Deployment:** Google Cloud Platform (using free tier + credits)

**Victory Formula:**
```
Win = (Technical Depth × Live Demo × Clear Story × Business Impact) + Production Architecture
```

---

## 🎯 CORE FEATURES TO BUILD

### MVP Features (Week 1-3) - MUST HAVE
✅ Synthetic transaction data generator (10K customers, 12 months history)  
✅ 30+ behavioral feature engineering pipeline  
✅ XGBoost ML model with 80%+ AUC  
✅ SHAP-based explainability for every prediction  
✅ FastAPI real-time scoring endpoint  
✅ Real-time transaction stream simulator  
✅ Risk score monitoring dashboard (Streamlit)  
✅ Intervention decision engine with empathetic messaging

### Enhancement Features (Week 4) - NICE TO HAVE
⭐ Live real-time WebSocket updates  
⭐ Interactive customer deep-dive interface  
⭐ Model performance tracking dashboard  
⭐ Intervention success metrics tracker  
⭐ Automated alerting system

---

## 🛠️ OPTIMAL TECH STACK

### Core Technologies
```yaml
Language: Python 3.11 
Package Manager: Poetry 
Environment: Docker + Docker Compose  

Data Layer:
  - Database: PostgreSQL 15 with TimescaleDB extension
  - Cache/Queue: Redis 7
  - Feature Store: Feast 0.38+
  - Storage: Google Cloud Storage (for models/data)

ML Stack:
  - Training: XGBoost 2.0 + LightGBM 4.0
  - Explainability: SHAP 0.45+
  - Tracking: MLflow 2.11+
  - Validation: scikit-learn 1.4+

Backend:
  - API: FastAPI 0.110+
  - Task Queue: Celery + Redis
  - WebSockets: FastAPI native WebSocket support

Frontend:
  - Dashboard: Streamlit 1.32+
  - Visualization: Plotly 5.19+
  - Real-time: WebSocket client

Deployment (Google Cloud):
  - Compute: Cloud Run (for API)
  - Database: Cloud SQL for PostgreSQL
  - Cache: Memorystore for Redis
  - Storage: Cloud Storage
  - Monitoring: Cloud Monitoring
  - Secrets: Secret Manager
  - CI/CD: Cloud Build

Development:
  - Code Quality: ruff, black, mypy
  - Testing: pytest, pytest-cov
  - Documentation: MkDocs
```

**Why This Stack Wins:**
- ✅ All production-grade (not toy tools)
- ✅ Runs locally (Docker) + cloud-native (GCP)
- ✅ Fast development (Python ecosystem)
- ✅ Industry-standard (judges recognize it)
- ✅ Free tier compatible (no costs during dev)

---

## 📁 PROJECT STRUCTURE

```
pre-delinquency-engine/
├── .github/
│   └── workflows/
│       └── deploy.yml              # Cloud Build CI/CD
├── data/
│   ├── raw/                        # Generated synthetic data
│   ├── processed/                  # Engineered features
│   └── models/                     # Trained ML models
├── src/
│   ├── __init__.py
│   ├── data_generation/
│   │   ├── __init__.py
│   │   ├── synthetic_data.py       # Data generator
│   │   └── stream_simulator.py    # Real-time simulator
│   ├── feature_engineering/
│   │   ├── __init__.py
│   │   ├── features.py             # Feature definitions
│   │   └── pipeline.py             # Feature pipeline
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train.py                # Model training
│   │   ├── evaluate.py             # Evaluation metrics
│   │   └── predict.py              # Inference
│   ├── explainability/
│   │   ├── __init__.py
│   │   └── shap_explainer.py       # SHAP explanations
│   ├── serving/
│   │   ├── __init__.py
│   │   ├── api.py                  # FastAPI app
│   │   └── websocket.py            # WebSocket handler
│   ├── intervention/
│   │   ├── __init__.py
│   │   ├── decision_engine.py      # Intervention logic
│   │   └── tracker.py              # Outcome tracking
│   └── utils/
│       ├── __init__.py
│       ├── database.py             # DB connections
│       └── config.py               # Configuration
├── feast_repo/
│   ├── feature_store.yaml          # Feast config
│   └── features.py                 # Feature definitions
├── dashboard/
│   ├── app.py                      # Streamlit dashboard
│   ├── pages/
│   │   ├── 1_risk_overview.py
│   │   ├── 2_customer_deepdive.py
│   │   ├── 3_realtime_monitor.py
│   │   ├── 4_model_performance.py
│   │   └── 5_interventions.py
│   └── utils/
│       └── charts.py               # Plotly charts
├── tests/
│   ├── test_features.py
│   ├── test_model.py
│   └── test_api.py
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_analysis.ipynb
│   └── 03_model_experiments.ipynb
├── deployment/
│   ├── cloudbuild.yaml             # GCP Cloud Build
│   ├── app.yaml                    # Cloud Run config
│   └── terraform/                  # IaC (optional)
│       ├── main.tf
│       └── variables.tf
├── docker/
│   ├── Dockerfile.api              # API container
│   ├── Dockerfile.dashboard        # Dashboard container
│   └── Dockerfile.worker           # Celery worker
├── docker-compose.yml              # Local development
├── docker-compose.prod.yml         # Production (GCP)
├── pyproject.toml                  # Poetry dependencies
├── .env.example                    # Environment variables
├── .gitignore
└── README.md
```

---

## 🚀 PHASE-BY-PHASE IMPLEMENTATION

### ✅ [Phase 0: Project Setup](phase-0-project-setup.md) (Day 1)
- Initialize project structure
- Install dependencies with Poetry
- Setup Docker environment (PostgreSQL, Redis, MLflow)
- Configure environment variables
- **Status:** Complete with full Docker Compose setup

### ✅ [Phase 1: Data Generation](phase-1-data-generation.md) (Days 2-3)
- Create database schema with TimescaleDB
- Build synthetic data generator
- Generate 10K customers with 12 months history
- Create transaction patterns with embedded stress signals
- **Status:** Database schema complete, generator ready

### 📝 [Phase 2: Feature Engineering](phase-2-feature-engineering.md) (Days 4-8)
- Implement 30+ behavioral features
- Salary, savings, spending patterns
- Payment behavior analysis
- Cash withdrawal patterns
- Transaction anomaly detection
- **Status:** Framework ready, awaiting full implementation

### 📝 [Phase 3: Model Training & Explainability](phase-3-model-training.md) (Days 9-12)
- Train XGBoost model
- Implement SHAP explainability
- Model evaluation and metrics
- MLflow experiment tracking
- Threshold optimization
- **Status:** Framework ready, awaiting full implementation

### ✅ [Phase 4: Real-time API & Scoring](phase-4-api-serving.md) (Days 13-15)
- Build FastAPI application
- Real-time scoring endpoints
- WebSocket support for live updates
- Redis caching layer
- Background task processing
- **Status:** Complete with full API implementation

### ✅ [Phase 5: Intervention Engine](phase-5-intervention-engine.md) (Days 16-18)
- Intervention decision logic
- Risk-based messaging
- Empathetic communication templates
- Intervention tracking
- Outcome measurement
- **Status:** Complete with decision engine and tracker

### ✅ [Phase 6: Dashboard Creation](phase-6-dashboard.md) (Days 19-21)
- Streamlit multi-page dashboard (5 pages)
- Risk overview visualization
- Customer deep-dive interface
- Real-time monitoring
- Model performance tracking
- Intervention tracker
- **Status:** Complete with all 5 pages

### ✅ [Phase 7: Google Cloud Deployment](phase-7-gcp-deployment.md) (Days 22-24)
- Cloud Run deployment
- Cloud SQL setup
- Memorystore Redis
- Cloud Storage integration
- CI/CD with Cloud Build
- Terraform IaC
- **Status:** Complete with deployment scripts and Terraform

### ✅ [Phase 8: Demo & Presentation](phase-8-demo-presentation.md) (Days 25-27)
- 5-minute demo script
- Live demonstration strategy
- Q&A preparation (top 5 questions)
- Backup plans
- Submission checklist
- **Status:** Complete with full demo script

---

## 📝 NOTES

- Each phase has its own detailed markdown file
- Follow phases sequentially for best results
- All code is production-ready and can be deployed
- Docker ensures consistent development environment
- GCP free tier covers all deployment costs during development

---

## 🎯 SUCCESS CRITERIA

✅ Working ML model with 80%+ AUC  
✅ Real-time API responding in <100ms  
✅ Interactive dashboard with live updates  
✅ Deployed on Google Cloud Platform  
✅ Complete documentation and demo  
✅ Explainable predictions with SHAP  
✅ Empathetic intervention messaging


---

## 🎯 Quick Reference

### File Structure
```
Blueprint Files:
├── README.md                      # Project overview
├── GETTING-STARTED.md             # Your 30-day roadmap
├── plan.md                        # This file - master index
├── phase-0-project-setup.md       # ✅ Complete
├── phase-1-data-generation.md     # ✅ Database schema ready
├── phase-2-feature-engineering.md # 📝 Framework ready
├── phase-3-model-training.md      # 📝 Framework ready
├── phase-4-api-serving.md         # ✅ Complete
├── phase-5-intervention-engine.md # ✅ Complete
├── phase-6-dashboard.md           # ✅ Complete
├── phase-7-gcp-deployment.md      # ✅ Complete
└── phase-8-demo-presentation.md   # ✅ Complete
```

### Key Commands

**Setup:**
```bash
poetry install                    # Install dependencies
docker-compose up -d              # Start services
cp .env.example .env              # Configure environment
```

**Development:**
```bash
python src/data_generation/synthetic_data.py  # Generate data
python src/models/train.py                    # Train model
uvicorn src.serving.api:app --reload          # Start API
streamlit run dashboard/app.py                # Start dashboard
```

**Testing:**
```bash
pytest tests/                     # Run tests
curl http://localhost:8000/health # Test API
curl http://localhost:8000/stats  # Get statistics
```

**Deployment:**
```bash
./deployment/deploy.sh dev        # Deploy to GCP
gcloud run services list          # Check services
```

### Important URLs

**Local Development:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501
- MLflow: http://localhost:5000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Production (after deployment):**
- API: https://delinquency-api-xxxxx.run.app
- Dashboard: https://delinquency-dashboard-xxxxx.run.app

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://admin:admin123@localhost:5432/bank_data

# Redis
REDIS_URL=redis://:redis123@localhost:6379/0

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# API
API_HOST=0.0.0.0
API_PORT=8000

# Model
MODEL_THRESHOLD=0.5
```

### Troubleshooting

**Docker issues:**
```bash
docker-compose down -v            # Clean restart
docker-compose up -d --build      # Rebuild containers
docker-compose logs -f api        # View logs
```

**Database issues:**
```bash
docker-compose exec postgres psql -U admin -d bank_data
\dt                               # List tables
\q                                # Quit
```

**API issues:**
```bash
docker-compose restart api        # Restart API
docker-compose logs api           # Check logs
```

---

## 📊 Success Metrics Tracker

Track your progress:

### Week 1 Goals
- [ ] Docker environment running
- [ ] 10K customers generated
- [ ] Data loaded to PostgreSQL
- [ ] Feature pipeline tested

### Week 2 Goals
- [ ] Model trained (AUC > 0.80)
- [ ] SHAP explanations working
- [ ] API endpoints functional
- [ ] WebSocket streaming

### Week 3 Goals
- [ ] Interventions triggering
- [ ] Dashboard accessible
- [ ] All 5 pages working
- [ ] Real-time updates live

### Week 4 Goals
- [ ] Deployed to GCP
- [ ] Demo rehearsed 10+ times
- [ ] Presentation polished
- [ ] Submission complete

---

## 🎉 Final Checklist

Before submission:

### Code Quality
- [ ] All code committed to Git
- [ ] README.md complete
- [ ] .env.example provided
- [ ] Requirements documented
- [ ] License file added

### Functionality
- [ ] API health check passes
- [ ] Dashboard loads successfully
- [ ] Model predictions working
- [ ] Interventions triggering
- [ ] All features tested

### Documentation
- [ ] Architecture diagram
- [ ] API documentation
- [ ] Deployment guide
- [ ] Demo script
- [ ] Q&A preparation

### Demo
- [ ] Live environment accessible
- [ ] Demo video recorded
- [ ] Slides prepared
- [ ] Backup materials ready
- [ ] Team roles assigned

---

## 💡 Pro Tips for Success

1. **Start with Phase 0** - Don't skip the setup
2. **Test incrementally** - Don't wait until the end
3. **Commit frequently** - Small, atomic commits
4. **Document as you go** - Future you will thank you
5. **Practice the demo** - 10+ times minimum
6. **Prepare backups** - Murphy's Law applies
7. **Focus on the story** - Not just the code
8. **Have fun!** - Enjoy the journey

---

## 🚀 Ready to Start?

1. Read [GETTING-STARTED.md](GETTING-STARTED.md)
2. Begin with [Phase 0: Project Setup](phase-0-project-setup.md)
3. Follow phases sequentially
4. Track progress with checklists
5. Prepare demo early

**Good luck building! 🎯**

---

*Last updated: 2024*
*Built with ❤️ for financial wellness*
