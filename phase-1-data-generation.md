# PHASE 1: DATA GENERATION (Days 2-3)

## Create Database Schema

Create sql/init.sql:

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    salary_day INT NOT NULL CHECK (salary_day BETWEEN 1 AND 31),
    monthly_income DECIMAL(12,2) NOT NULL,
    income_bracket VARCHAR(20) NOT NULL,
    account_age_days INT NOT NULL,
    account_type VARCHAR(20) DEFAULT 'savings',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions table (hypertable for time-series)
CREATE TABLE IF NOT EXISTS transactions (
    txn_id BIGSERIAL,
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    txn_time TIMESTAMPTZ NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    txn_type VARCHAR(20) NOT NULL CHECK (txn_type IN ('debit', 'credit')),
    category VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    merchant_id VARCHAR(100),
    is_failed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('transactions', 'txn_time', if_not_exists => TRUE);

-- Daily balances table
CREATE TABLE IF NOT EXISTS daily_balances (
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    balance_date DATE NOT NULL,
    opening_balance DECIMAL(12,2) NOT NULL,
    closing_balance DECIMAL(12,2) NOT NULL,
    min_balance DECIMAL(12,2) NOT NULL,
    max_balance DECIMAL(12,2) NOT NULL,
    total_credits DECIMAL(12,2) DEFAULT 0,
    total_debits DECIMAL(12,2) DEFAULT 0,
    txn_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (customer_id, balance_date)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    payment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    payment_type VARCHAR(50) NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    paid_date DATE,
    paid_amount DECIMAL(12,2),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'paid', 'partial', 'missed', 'late')),
    days_late INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Labels table (for ML training)
CREATE TABLE IF NOT EXISTS labels (
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    observation_date DATE NOT NULL,
    label INT NOT NULL CHECK (label IN (0, 1)),
    days_to_default INT,
    default_date DATE,
    default_amount DECIMAL(12,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (customer_id, observation_date)
);

-- Risk scores table
CREATE TABLE IF NOT EXISTS risk_scores (
    score_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    score_date TIMESTAMPTZ NOT NULL,
    risk_score DECIMAL(5,4) NOT NULL CHECK (risk_score BETWEEN 0 AND 1),
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    model_version VARCHAR(50) NOT NULL,
    top_feature_1 VARCHAR(100),
    top_feature_1_impact DECIMAL(5,4),
    top_feature_2 VARCHAR(100),
    top_feature_2_impact DECIMAL(5,4),
    top_feature_3 VARCHAR(100),
    top_feature_3_impact DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_risk_scores_customer_date ON risk_scores(customer_id, score_date DESC);

-- Interventions table
CREATE TABLE IF NOT EXISTS interventions (
    intervention_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    intervention_date TIMESTAMPTZ NOT NULL,
    intervention_type VARCHAR(50) NOT NULL,
    risk_score DECIMAL(5,4) NOT NULL,
    message_sent TEXT,
    delivery_status VARCHAR(20) DEFAULT 'pending',
    customer_response VARCHAR(20),
    response_date TIMESTAMPTZ,
    outcome VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_transactions_customer_time ON transactions(customer_id, txn_time DESC);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_payments_customer_status ON payments(customer_id, status);
CREATE INDEX idx_payments_due_date ON payments(due_date);
CREATE INDEX idx_labels_customer_date ON labels(customer_id, observation_date DESC);
CREATE INDEX idx_interventions_customer_date ON interventions(customer_id, intervention_date DESC);

-- Create MLflow database
CREATE DATABASE mlflow;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interventions_updated_at BEFORE UPDATE ON interventions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

## Create Synthetic Data Generator

[PLACEHOLDER: Full synthetic_data.py code will be added when you provide Phase 1 details]

## Run Data Generation

```bash
# Create directory structure
mkdir -p data/raw data/processed data/models

# Generate data
python src/data_generation/synthetic_data.py
```
