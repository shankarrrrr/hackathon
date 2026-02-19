#!/usr/bin/env python3
"""
Quick script to populate test intervention data for dashboard demo.
This creates realistic intervention records for existing high-risk customers.
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

print("🔄 Populating test intervention data...")

try:
    with engine.connect() as conn:
        # Get high-risk customers
        result = conn.execute(text("""
            SELECT DISTINCT customer_id 
            FROM risk_scores 
            WHERE risk_level IN ('HIGH', 'CRITICAL')
            LIMIT 25
        """))
        customer_ids = [row[0] for row in result]
        
        if not customer_ids:
            print("❌ No high-risk customers found. Run risk scoring first.")
            exit(1)
        
        print(f"✅ Found {len(customer_ids)} high-risk customers")
        
        # Create interventions for the past 30 days
        intervention_types = ['proactive_outreach', 'urgent_contact', 'payment_plan_offer']
        responses = ['contacted', 'payment_made', 'plan_agreed', 'no_response', 'declined']
        
        # Weight responses to show ~70% success rate
        weighted_responses = (
            ['contacted'] * 3 + 
            ['payment_made'] * 2 + 
            ['plan_agreed'] * 2 + 
            ['no_response'] * 2 + 
            ['declined'] * 1
        )
        
        interventions_created = 0
        
        for customer_id in customer_ids:
            # Each customer gets 1-3 interventions
            num_interventions = random.randint(1, 3)
            
            for i in range(num_interventions):
                # Spread interventions over last 30 days
                days_ago = random.randint(1, 30)
                intervention_date = datetime.now() - timedelta(days=days_ago)
                
                intervention_type = random.choice(intervention_types)
                customer_response = random.choice(weighted_responses)
                
                conn.execute(text("""
                    INSERT INTO interventions 
                    (customer_id, intervention_type, intervention_date, customer_response)
                    VALUES (:cid, :type, :date, :response)
                """), {
                    'cid': customer_id,
                    'type': intervention_type,
                    'date': intervention_date,
                    'response': customer_response
                })
                
                interventions_created += 1
        
        conn.commit()
        
        print(f"✅ Created {interventions_created} test interventions")
        
        # Show summary
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN customer_response IN ('contacted', 'payment_made', 'plan_agreed') 
                    THEN 1 ELSE 0 END) as successful
            FROM interventions
        """))
        
        row = result.fetchone()
        total = row[0]
        successful = row[1]
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"\n📊 Intervention Summary:")
        print(f"   Total interventions: {total}")
        print(f"   Successful: {successful}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"\n✅ Dashboard KPIs will now show real data!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
