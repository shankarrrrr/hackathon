#!/usr/bin/env python3
"""
Generate historical risk scores to enable rising risk detection.
Creates 2-3 risk scores per customer with realistic trends.
"""

import os
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import random

# Get database URL from environment
db_url = os.getenv(
    'DATABASE_URL',
    'postgresql://admin:admin123@localhost:5432/bank_data'
)

engine = create_engine(db_url)

print("🔄 Generating historical risk scores...")

try:
    with engine.connect() as conn:
        # Get all customers with their current risk scores
        result = conn.execute(text("""
            SELECT DISTINCT ON (customer_id)
                customer_id,
                risk_score,
                risk_level,
                model_version,
                top_feature_1,
                top_feature_1_impact,
                top_feature_2,
                top_feature_2_impact,
                top_feature_3,
                top_feature_3_impact,
                score_date
            FROM risk_scores
            ORDER BY customer_id, score_date DESC
        """))
        
        customers = [dict(row._mapping) for row in result]
        
        if not customers:
            print("❌ No customers found. Run risk scoring first.")
            exit(1)
        
        print(f"✅ Found {len(customers)} customers")
        
        scores_created = 0
        
        for customer in customers:
            current_score = float(customer['risk_score'])  # Convert Decimal to float
            current_date = customer['score_date']
            
            # Generate 2 historical scores (7 days ago and 14 days ago)
            for days_back in [7, 14]:
                historical_date = current_date - timedelta(days=days_back)
                
                # Calculate historical score with realistic variation
                # Most customers: slight increase over time
                # Some customers: decrease (improved)
                trend = random.choice(['rising', 'rising', 'rising', 'stable', 'falling'])
                
                if trend == 'rising':
                    # Score was lower in the past
                    variation = random.uniform(0.05, 0.15)
                    historical_score = max(0.0, current_score - variation)
                elif trend == 'falling':
                    # Score was higher in the past (customer improved)
                    variation = random.uniform(0.05, 0.10)
                    historical_score = min(1.0, current_score + variation)
                else:
                    # Stable with minor fluctuation
                    variation = random.uniform(-0.03, 0.03)
                    historical_score = max(0.0, min(1.0, current_score + variation))
                
                # Determine risk level for historical score
                if historical_score >= 0.75:
                    historical_level = 'CRITICAL'
                elif historical_score >= 0.60:
                    historical_level = 'HIGH'
                elif historical_score >= 0.40:
                    historical_level = 'MEDIUM'
                else:
                    historical_level = 'LOW'
                
                # Insert historical score
                conn.execute(text("""
                    INSERT INTO risk_scores 
                    (customer_id, risk_score, risk_level, score_date, model_version,
                     top_feature_1, top_feature_1_impact,
                     top_feature_2, top_feature_2_impact,
                     top_feature_3, top_feature_3_impact)
                    VALUES 
                    (:cid, :score, :level, :date, :model_version,
                     :f1, :f1_impact, :f2, :f2_impact, :f3, :f3_impact)
                """), {
                    'cid': customer['customer_id'],
                    'score': historical_score,
                    'level': historical_level,
                    'date': historical_date,
                    'model_version': customer['model_version'],
                    'f1': customer['top_feature_1'],
                    'f1_impact': customer['top_feature_1_impact'],
                    'f2': customer['top_feature_2'],
                    'f2_impact': customer['top_feature_2_impact'],
                    'f3': customer['top_feature_3'],
                    'f3_impact': customer['top_feature_3_impact']
                })
                
                scores_created += 1
        
        conn.commit()
        
        print(f"✅ Created {scores_created} historical risk scores")
        
        # Count rising risk customers
        result = conn.execute(text("""
            WITH risk_trends AS (
                SELECT 
                    customer_id,
                    risk_score,
                    risk_level,
                    score_date,
                    LAG(risk_score) OVER (PARTITION BY customer_id ORDER BY score_date) as prev_risk_score
                FROM risk_scores
            ),
            latest_trends AS (
                SELECT DISTINCT ON (customer_id)
                    customer_id,
                    risk_score,
                    risk_level,
                    prev_risk_score,
                    score_date
                FROM risk_trends
                ORDER BY customer_id, score_date DESC
            )
            SELECT COUNT(*) as rising_count
            FROM latest_trends
            WHERE risk_level IN ('HIGH', 'CRITICAL')
                AND prev_risk_score IS NOT NULL
                AND risk_score > prev_risk_score
        """))
        
        rising_count = result.fetchone()[0]
        
        print(f"\n📊 Rising Risk Summary:")
        print(f"   Customers with rising risk: {rising_count}")
        print(f"\n✅ Dashboard will now show rising risk trends!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
