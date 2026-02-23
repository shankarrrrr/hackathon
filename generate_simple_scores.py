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
        
        # Calculate feature impacts (contribution to risk score)
        # Higher values = more risk contribution
        income_impact = 0.0
        if monthly_income < 15000:
            income_impact = 0.25
        elif monthly_income < 30000:
            income_impact = 0.15
        elif monthly_income < 50000:
            income_impact = 0.05
        
        age_impact = 0.0
        if account_age_months < 12:
            age_impact = 0.20
        elif account_age_months < 24:
            age_impact = 0.10
        elif account_age_months < 48:
            age_impact = 0.05
        
        bracket_impact = 0.10 if income_bracket == 'low' else 0.0
        
        # Top features with actual impact values
        top_features = [
            {"feature": "monthly_income", "impact": income_impact},
            {"feature": "account_age_months", "impact": age_impact},
            {"feature": "income_bracket", "impact": bracket_impact}
        ]
        
        scores.append((
            str(customer_id),
            datetime.now(),
            float(risk_score),
            risk_level,
            'v2_heuristic',
            top_features[0]['feature'],
            top_features[0]['impact'],
            top_features[1]['feature'],
            top_features[1]['impact'],
            top_features[2]['feature'],
            top_features[2]['impact']
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
    
    # Print summary
    avg_score = sum(s[2] for s in scores) / len(scores)
    print(f"\n📈 Distribution:")
    print(f"   CRITICAL: {results['CRITICAL']}")
    print(f"   HIGH: {results['HIGH']}")
    print(f"   MEDIUM: {results['MEDIUM']}")
    print(f"   LOW: {results['LOW']}")
    print(f"   Avg: {avg_score:.4f}")
    
    print(f"\n✅ Inserted {len(scores)} scores")
    print("🌐 http://13.201.206.221:8501")

if __name__ == '__main__':
    random.seed(42)
    main()
