#!/usr/bin/env python3
"""
Generate simple risk scores based on heuristics
For AWS Free Tier - no ML model needed
"""
import psycopg2
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import random

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'bank_data'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', 'admin123')
}

def calculate_risk_score(monthly_income, account_age_months, income_bracket):
    """
    Simple heuristic-based risk scoring
    """
    base_score = 0.3
    
    # Income factor (lower income = higher risk)
    if monthly_income < 15000:
        base_score += 0.25
    elif monthly_income < 30000:
        base_score += 0.15
    elif monthly_income < 50000:
        base_score += 0.05
    
    # Account age factor (newer accounts = higher risk)
    if account_age_months < 12:
        base_score += 0.20
    elif account_age_months < 24:
        base_score += 0.10
    elif account_age_months < 48:
        base_score += 0.05
    
    # Add some randomness for realism
    noise = random.uniform(-0.1, 0.1)
    risk_score = max(0.0, min(1.0, base_score + noise))
    
    return risk_score

def main():
    print("🚀 Generating risk scores...")
    
    # Connect to DB
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get customers
    cur.execute("""
        SELECT customer_id, monthly_income, account_age_months, income_bracket
        FROM customers
        ORDER BY created_at
        LIMIT 100
    """)
    customers = cur.fetchall()
    print(f"✅ Found {len(customers)} customers")
    
    # Clear old scores
    cur.execute("DELETE FROM risk_scores;")
    print("🗑️  Cleared old scores")
    
    # Generate scores
    results = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    scores = []
    
    for customer_id, monthly_income, account_age_months, income_bracket in customers:
        risk_score = calculate_risk_score(monthly_income, account_age_months, income_bracket)
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        results[risk_level] += 1
        
        # Simple top features
        top_features = [
            {"feature": "monthly_income", "value": float(monthly_income / 100000)},
            {"feature": "account_age_months", "value": float(account_age_months / 100)},
            {"feature": "income_bracket", "value": 0.5 if income_bracket == 'low' else 0.0}
        ]
        
        scores.append((
            str(customer_id),
            datetime.now(),
            float(risk_score),
            risk_level,
            json.dumps(top_features)
        ))
    
    # Batch insert
    from psycopg2.extras import execute_batch
    execute_batch(cur, """
        INSERT INTO risk_scores 
        (customer_id, observation_date, risk_score, risk_level, top_features)
        VALUES (%s, %s, %s, %s, %s)
    """, scores, page_size=50)
    
    conn.commit()
    cur.close()
    conn.close()
    
    # Print summary
    avg_score = sum(s[2] for s in scores) / len(scores)
    print(f"\n📈 Distribution:")
    print(f"   CRITICAL: {results['CRITICAL']}")
    print(f"   HIGH: {results['HIGH']}")
    print(f"   MEDIUM: {results['MEDIUM']}")
    print(f"   LOW: {results['LOW']}")
    print(f"   Avg: {avg_score:.4f}")
    
    print(f"\n✅ Inserted {len(scores)} scores")
    print("🌐 http://15.206.72.35:8501")

if __name__ == '__main__':
    random.seed(42)
    main()
