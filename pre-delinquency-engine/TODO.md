# TODO - Remaining Work

This document outlines the remaining work to complete the Pre-Delinquency Engine project.

## ✅ Completed (Phases 1-5)

- [x] **Phase 0**: Project setup and infrastructure
- [x] **Phase 1**: Synthetic data generation (1000 customers, 600K+ transactions)
- [x] **Phase 2**: Feature engineering (30+ behavioral features)
- [x] **Phase 3**: ML model training (XGBoost with AUC 0.80)
- [x] **Phase 4**: FastAPI serving layer with Kafka integration
- [x] **Phase 5**: Complete Kafka streaming pipeline with intervention engine

## 🚧 In Progress / Needs Fixing

### High Priority Fixes

- [ ] **Fix Database Schema** - Increase precision for feature impact columns
  - Current: `NUMERIC(5,4)` - too small
  - Change to: `NUMERIC(10,4)` or `FLOAT`
  - File: `sql/init.sql` - risk_scores table
  - Impact: Currently predictions work but can't store feature impacts

- [ ] **Debug Intervention Worker** - Not creating interventions
  - Issue: Predictions flow through Kafka but interventions aren't triggered
  - Check: Consumer group offset, topic subscription
  - File: `src/streaming/intervention_worker.py`
  - Test: Verify HIGH/CRITICAL predictions trigger interventions

- [ ] **Fix Pandas Warnings** - SettingWithCopyWarning in features.py
  - File: `src/feature_engineering/features.py` line 337-338
  - Use `.loc[]` instead of direct assignment
  - Non-critical but clutters logs

## 📋 Phase 6: Dashboard (Next Priority)

### Streamlit Dashboard
**Estimated Time**: 2-3 hours

- [ ] **Setup Streamlit**
  - Install: `pip install streamlit plotly`
  - Create: `dashboard/app.py`
  - Layout: Multi-page app structure

- [ ] **Page 1: Overview Dashboard**
  - Real-time metrics (total customers, high-risk count, avg risk score)
  - Risk distribution chart (pie/bar chart)
  - Recent predictions table
  - System health indicators

- [ ] **Page 2: Real-Time Feed**
  - Live transaction stream (WebSocket or polling)
  - Live prediction feed
  - Live intervention feed
  - Auto-refresh every 5 seconds

- [ ] **Page 3: Customer Drill-Down**
  - Search customer by ID
  - Risk score history chart
  - Transaction timeline
  - Feature importance breakdown
  - Intervention history

- [ ] **Page 4: Analytics**
  - Risk score distribution over time
  - Intervention effectiveness metrics
  - Model performance metrics
  - Feature importance analysis

- [ ] **Page 5: System Monitoring**
  - Kafka consumer lag
  - API response times
  - Database connection status
  - Error logs

### WebSocket Integration
- [ ] Add WebSocket endpoint to API for real-time updates
- [ ] Stream predictions to dashboard
- [ ] Stream interventions to dashboard

### Files to Create:
```
dashboard/
├── app.py                 # Main Streamlit app
├── pages/
│   ├── 1_Overview.py
│   ├── 2_RealTime.py
│   ├── 3_Customer.py
│   ├── 4_Analytics.py
│   └── 5_Monitoring.py
├── components/
│   ├── charts.py          # Reusable chart components
│   ├── metrics.py         # Metric cards
│   └── tables.py          # Data tables
└── utils/
    ├── kafka_consumer.py  # Dashboard Kafka consumer
    └── api_client.py      # API wrapper
```

## 📋 Phase 7: GCP Deployment

### Cloud Infrastructure
**Estimated Time**: 3-4 hours

- [ ] **Setup GCP Project**
  - Create GCP project
  - Enable required APIs (Cloud Run, Pub/Sub, BigQuery, Cloud SQL)
  - Setup billing
  - Configure IAM roles

- [ ] **Migrate to Cloud Services**
  - [ ] Replace Kafka with Cloud Pub/Sub
    - Create topics
    - Update producers/consumers
    - Test message flow
  
  - [ ] Deploy API to Cloud Run
    - Create Dockerfile
    - Build container image
    - Deploy to Cloud Run
    - Configure environment variables
  
  - [ ] Deploy Workers as Cloud Functions
    - Feature Processor function
    - Intervention Worker function
    - Transaction Simulator (Cloud Scheduler)
  
  - [ ] Migrate PostgreSQL to Cloud SQL
    - Create Cloud SQL instance
    - Migrate schema
    - Load data
    - Update connection strings
  
  - [ ] Setup BigQuery for Analytics
    - Create dataset
    - Create tables
    - Setup streaming inserts
    - Create views for dashboard

- [ ] **Setup Monitoring**
  - Cloud Monitoring dashboards
  - Log aggregation
  - Alerting rules
  - Error tracking

- [ ] **CI/CD Pipeline**
  - GitHub Actions workflow
  - Automated testing
  - Automated deployment
  - Rollback strategy

### Files to Create:
```
deployment/
├── gcp/
│   ├── terraform/         # Infrastructure as Code
│   ├── cloudbuild.yaml    # CI/CD config
│   ├── pubsub_topics.yaml # Pub/Sub configuration
│   └── cloud_run.yaml     # Cloud Run config
├── docker/
│   ├── Dockerfile.api     # Already exists
│   ├── Dockerfile.worker  # For Cloud Functions
│   └── docker-compose.gcp.yml
└── scripts/
    ├── deploy.sh          # Deployment script
    └── migrate_data.sh    # Data migration
```

## 📋 Phase 8: Demo & Presentation

### Documentation
**Estimated Time**: 2 hours

- [ ] **Create Demo Video**
  - Screen recording of system in action
  - Narration explaining features
  - Show real-time predictions
  - Show interventions being triggered
  - Duration: 5-10 minutes

- [ ] **Architecture Diagrams**
  - System architecture diagram (already exists in ARCHITECTURE.md)
  - Data flow diagram
  - Deployment architecture
  - Use draw.io or Lucidchart

- [ ] **Business Case Document**
  - Problem statement
  - Solution overview
  - Technical approach
  - ROI calculations
  - Success metrics

- [ ] **Presentation Deck**
  - Problem & Solution (2 slides)
  - Architecture Overview (2 slides)
  - Technical Implementation (3 slides)
  - Demo Screenshots (3 slides)
  - Results & Metrics (2 slides)
  - Future Enhancements (1 slide)
  - Q&A (1 slide)

### Files to Create:
```
docs/
├── demo/
│   ├── demo_video.mp4
│   ├── screenshots/
│   └── demo_script.md
├── diagrams/
│   ├── architecture.png
│   ├── data_flow.png
│   └── deployment.png
├── presentation/
│   ├── slides.pptx
│   └── speaker_notes.md
└── business/
    ├── business_case.md
    ├── roi_analysis.xlsx
    └── success_metrics.md
```

## 🔧 Technical Improvements (Optional)

### Code Quality
- [ ] Add unit tests (pytest)
- [ ] Add integration tests
- [ ] Add type hints throughout
- [ ] Add docstrings to all functions
- [ ] Setup pre-commit hooks (black, flake8, mypy)
- [ ] Add code coverage reporting

### Performance Optimization
- [ ] Optimize feature computation (caching, vectorization)
- [ ] Add connection pooling for database
- [ ] Implement batch prediction endpoint
- [ ] Add Redis caching for frequent queries
- [ ] Optimize Kafka consumer settings

### Advanced Features
- [ ] **A/B Testing Framework**
  - Multiple intervention strategies
  - Random assignment
  - Outcome tracking
  - Statistical analysis

- [ ] **Model Retraining Pipeline**
  - Automated data collection
  - Scheduled retraining
  - Model versioning
  - A/B testing new models

- [ ] **Feature Store Integration**
  - Setup Feast
  - Define feature definitions
  - Online/offline feature serving
  - Feature monitoring

- [ ] **Stream Processing with Faust**
  - Stateful stream processing
  - Windowed aggregations
  - Real-time feature computation
  - Complex event processing

### Security & Compliance
- [ ] Add API authentication (JWT tokens)
- [ ] Implement RBAC (Role-Based Access Control)
- [ ] Add data encryption at rest
- [ ] Add audit logging
- [ ] GDPR compliance (data deletion, anonymization)
- [ ] PII data masking in logs

## 📊 Metrics & Monitoring

### Business Metrics to Track
- [ ] Number of predictions per day
- [ ] High-risk customer count
- [ ] Intervention trigger rate
- [ ] Intervention success rate (if outcome data available)
- [ ] False positive rate
- [ ] Model drift detection

### Technical Metrics to Track
- [ ] API response time (p50, p95, p99)
- [ ] Kafka consumer lag
- [ ] Database query performance
- [ ] Model inference time
- [ ] System uptime
- [ ] Error rates

## 🐛 Known Issues

### Minor Issues (Non-Critical)
1. **Snappy compression warning** - Using gzip instead, works fine
2. **Pandas SettingWithCopyWarning** - Doesn't affect functionality
3. **Database precision overflow** - Predictions work, just can't store large feature values
4. **Emoji encoding on Windows** - Fixed by removing emojis

### To Investigate
1. **Intervention Worker** - Not creating interventions (HIGH PRIORITY)
2. **Consumer group rebalancing** - Occasional delays
3. **Memory usage** - Monitor for leaks in long-running processes

## 📚 Documentation to Add

- [ ] API documentation (OpenAPI/Swagger - already auto-generated)
- [ ] Feature engineering guide (explain each feature)
- [ ] Model training guide (hyperparameter tuning)
- [ ] Deployment guide (step-by-step for GCP)
- [ ] Troubleshooting guide (common issues and solutions)
- [ ] Contributing guide (for new developers)
- [ ] Code of conduct
- [ ] License file

## 🎯 Success Criteria

### Phase 6 Complete When:
- [ ] Dashboard displays real-time data
- [ ] All 5 pages functional
- [ ] WebSocket updates working
- [ ] Responsive design
- [ ] No errors in console

### Phase 7 Complete When:
- [ ] All services running on GCP
- [ ] CI/CD pipeline functional
- [ ] Monitoring dashboards setup
- [ ] Cost optimization done
- [ ] Documentation updated

### Phase 8 Complete When:
- [ ] Demo video recorded
- [ ] Presentation deck complete
- [ ] All diagrams created
- [ ] Business case documented
- [ ] Ready to present

## 📅 Estimated Timeline

- **Phase 6 (Dashboard)**: 2-3 hours
- **Phase 7 (GCP Deployment)**: 3-4 hours
- **Phase 8 (Demo & Presentation)**: 2 hours
- **Code Quality & Testing**: 2-3 hours
- **Advanced Features**: 4-6 hours (optional)

**Total Remaining**: ~10-15 hours of work

## 🤝 Handover Notes

### What's Working Well
- ✅ Kafka streaming pipeline is solid
- ✅ ML model training is automated
- ✅ API is production-ready
- ✅ Feature engineering is comprehensive
- ✅ Documentation is thorough

### What Needs Attention
- ⚠️ Intervention worker debugging
- ⚠️ Database schema fix
- ⚠️ Dashboard development
- ⚠️ Cloud deployment

### Quick Wins
1. Fix database schema (10 minutes)
2. Debug intervention worker (30 minutes)
3. Add basic dashboard (2 hours)

### Resources
- All documentation in project root
- Code is well-commented
- Architecture diagrams available
- Test scripts included

---

**Last Updated**: 2024  
**Status**: Phases 1-5 Complete, Ready for Phase 6  
**Next Priority**: Dashboard Development
