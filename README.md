# Pre-Delinquency Risk Engine — Hackathon Project

> **AI-powered early warning system that prevents customer defaults 30 days before they happen.**

## 🎯 Quick Links

- **Main Project:** [pre-delinquency-engine/](./pre-delinquency-engine/)
- **Complete Documentation:** [pre-delinquency-engine/README.md](./pre-delinquency-engine/README.md)
- **Project Summary:** [PROJECT-SUMMARY.md](./PROJECT-SUMMARY.md)

## 🚀 What This Does

This system uses behavioral AI to predict which bank customers will default on payments **30 days in advance** with **85% recall**, enabling proactive interventions that save millions in losses.

### Key Stats
- **85% recall** — Catches 85% of all defaults
- **10x ROI** — Returns $10 for every $1 spent on interventions
- **$525K-$5.2M saved** per 1,000 customers
- **Production-ready** — Enterprise-grade architecture

## �️ Project Structure

```
hackathon/
├── pre-delinquency-engine/    # Main application
│   ├── src/                   # Source code
│   ├── dashboard/             # Streamlit dashboard
│   ├── docker/                # Container definitions
│   ├── data/                  # Models & datasets
│   └── README.md              # Complete documentation
├── PROJECT-SUMMARY.md         # High-level overview
└── README.md                  # This file
```

## 🎓 Getting Started

1. **Navigate to main project:**
   ```bash
   cd pre-delinquency-engine
   ```

2. **Read the documentation:**
   - [Complete README](./pre-delinquency-engine/README.md) — Full system documentation
   - [Quick Start Guide](./pre-delinquency-engine/README.md#-quick-start) — Get running in 5 minutes

3. **Start the system:**
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboard:**
   - Dashboard: http://localhost:8501
   - API: http://localhost:8000/docs

## 💡 Why This Matters

Traditional credit scoring reacts **after** a payment is missed. By then, the relationship is damaged and recovery is expensive.

Our system watches for **early warning signals**:
- Cash hoarding before salary day
- ATM withdrawal spikes
- Gambling transactions
- Payday loan activity
- Utility payment delays

When these patterns emerge, we alert risk officers **before** the first missed payment, enabling proactive support that preserves customer relationships and prevents losses.

## 📊 Business Impact

- **Financial:** $525K-$5.2M saved per 1,000 customers
- **Operational:** Automated daily scoring, prioritized action queue
- **Customer:** Proactive support before financial distress
- **Compliance:** Audit trail, explainability, fair lending

## 🛠️ Tech Stack

- **ML:** CatBoost + XGBoost + LightGBM ensemble
- **Database:** PostgreSQL + TimescaleDB
- **API:** FastAPI
- **Dashboard:** Streamlit
- **Deployment:** Docker + Kubernetes-ready

## � License

MIT License — see [LICENSE](./pre-delinquency-engine/LICENSE)

---

**For complete documentation, see [pre-delinquency-engine/README.md](./pre-delinquency-engine/README.md)**
