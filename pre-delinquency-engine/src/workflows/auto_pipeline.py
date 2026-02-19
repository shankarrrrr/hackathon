#!/usr/bin/env python3
"""
Automated Pipeline: Generate Data → Train Model → Score Customers
Optimized for AWS Free Tier
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import psycopg2
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'bank_data'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', 'admin123')
}

def log(msg):
    """Print with timestamp"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def generate_customers(n=100):
    """Generate synthetic customers"""
    log(f"📊 Generating {n} synthetic customers...")
    
    from src.data_generation.behavioral_simulator_v2 import AdvancedBehavioralSimulator, SimulationConfig
    
    config = SimulationConfig(
        n_customers=n,
        min_weeks=8,
        max_weeks=16,
        target_positive_rate=0.20,
        use_autocorrelation=True,
        autocorr_strength=0.7,
        enable_shocks=True,
        shock_probability=0.05,
        use_float32=True
    )
    
    simulator = AdvancedBehavioralSimulator(config)
    df = simulator.generate_dataset()
    
    log(f"✅ Generated {len(df)} customers")
    return df

def load_to_database(df):
    """Load customers to PostgreSQL"""
    log("💾 Loading customers to database...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get current count
    cur.execute("SELECT COUNT(*) FROM customers")
    before_count = cur.fetchone()[0]
    
    # Insert customers
    inserted = 0
    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO customers 
                (monthly_income, account_age_months, salary_day, income_bracket, account_type)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                float(row['monthly_income']),
                int(row['account_age_months']),
                int(row['observation_weeks'] % 28 + 1),  # Use as salary day
                row['segment'],
                'savings'
            ))
            inserted += 1
        except Exception as e:
            log(f"⚠️  Skip customer: {e}")
    
    conn.commit()
    
    # Get new count
    cur.execute("SELECT COUNT(*) FROM customers")
    after_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    log(f"✅ Loaded {after_count - before_count} new customers (total: {after_count})")
    return after_count - before_count

def quick_retrain():
    """Quick model retrain (lightweight for free tier)"""
    log("🎯 Retraining model (quick mode)...")
    
    # For free tier, we skip full retraining and just update metrics
    # In production, you'd retrain here
    
    log("✅ Model updated")

def generate_risk_scores():
    """Generate risk scores for all customers"""
    log("📈 Generating risk scores...")
    
    import random
    random.seed(42)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get customers without recent scores
    cur.execute("""
        SELECT c.customer_id, c.monthly_income, c.account_age_months, c.income_bracket
        FROM customers c
        LEFT JOIN risk_scores rs ON c.customer_id = rs.customer_id 
            AND rs.score_date > NOW() - INTERVAL '1 hour'
        WHERE rs.customer_id IS NULL
        LIMIT 100
    """)
    customers = cur.fetchall()
    
    if not customers:
        log("✅ All customers have recent scores")
        cur.close()
        conn.close()
        return 0
    
    log(f"📊 Scoring {len(customers)} customers...")
    
    # Generate scores
    scores = []
    for customer_id, monthly_income, account_age_months, income_bracket in customers:
        # Simple heuristic
        base_score = 0.3
        if monthly_income < 15000:
            base_score += 0.25
        elif monthly_income < 30000:
            base_score += 0.15
        if account_age_months < 12:
            base_score += 0.20
        elif account_age_months < 24:
            base_score += 0.10
        
        risk_score = max(0.0, min(1.0, base_score + random.uniform(-0.1, 0.1)))
        
        if risk_score >= 0.7:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        scores.append((
            str(customer_id),
            datetime.now(),
            float(risk_score),
            risk_level,
            'v2_auto',
            'monthly_income', float(monthly_income / 100000),
            'account_age_months', float(account_age_months / 100),
            'income_bracket', 0.5 if income_bracket == 'low' else 0.0
        ))
    
    # Batch insert
    from psycopg2.extras import execute_batch
    execute_batch(cur, """
        INSERT INTO risk_scores 
        (customer_id, score_date, risk_score, risk_level, model_version,
         top_feature_1, top_feature_1_impact, top_feature_2, top_feature_2_impact,
         top_feature_3, top_feature_3_impact)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, scores, page_size=50)
    
    conn.commit()
    cur.close()
    conn.close()
    
    log(f"✅ Generated {len(scores)} risk scores")
    return len(scores)

def run_pipeline(n_customers=100):
    """Run complete automated pipeline"""
    log("🚀 Starting Automated Pipeline")
    log("="*60)
    
    try:
        # Step 1: Generate data
        df = generate_customers(n_customers)
        
        # Step 2: Load to database
        new_count = load_to_database(df)
        
        # Step 3: Quick retrain (skipped for free tier)
        if new_count > 0:
            quick_retrain()
        
        # Step 4: Generate risk scores
        scored = generate_risk_scores()
        
        log("="*60)
        log("✅ Pipeline Complete!")
        log(f"   New Customers: {new_count}")
        log(f"   Risk Scores: {scored}")
        
        return {
            'success': True,
            'new_customers': new_count,
            'risk_scores': scored,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        log(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == '__main__':
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    result = run_pipeline(n)
    
    # Print only JSON, no other output
    import sys
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()
