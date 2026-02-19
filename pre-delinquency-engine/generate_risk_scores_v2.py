#!/usr/bin/env python3
"""
Generate risk scores for V2 customers using pre-computed features
Memory-optimized for AWS Free Tier (1GB RAM)
"""
import pandas as pd
import xgboost as xgb
import psycopg2
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import gc

load_dotenv()

# Database connection
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'bank_data'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', 'admin123')
}

def load_model():
    """Load the trained model"""
    model_path = 'data/models/production/model.json'
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    model = xgb.Booster()
    model.load_model(model_path)
    print(f"✅ Loaded model")
    return model

def load_features_chunk():
    """Load only first 100 rows (memory efficient)"""
    csv_path = 'data/processed/behavioral_features_v2.csv'
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Features not found at {csv_path}")
    
    # Read only first 100 rows
    df = pd.read_csv(csv_path, nrows=100)
    print(f"✅ Loaded {len(df)} customers")
    return df

def get_db_customer_ids():
    """Get customer IDs from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("SELECT customer_id FROM customers;")
    customer_ids = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    print(f"✅ Found {len(customer_ids)} customers in DB")
    return set(str(cid) for cid in customer_ids)

def store_risk_scores(predictions_df):
    """Store risk scores in database (batch insert)"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Clear existing
    cur.execute("DELETE FROM risk_scores;")
    print(f"🗑️  Cleared old scores")
    
    # Batch insert
    values = []
    for _, row in predictions_df.iterrows():
        values.append((
            row['customer_id'],
            datetime.now(),
            float(row['risk_score']),
            row['risk_level'],
            json.dumps(row['top_features'])
        ))
    
    # Insert all at once
    from psycopg2.extras import execute_batch
    execute_batch(cur, """
        INSERT INTO risk_scores 
        (customer_id, observation_date, risk_score, risk_level, top_features)
        VALUES (%s, %s, %s, %s, %s)
    """, values, page_size=50)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Inserted {len(values)} scores")

def main():
    print("🚀 Generating risk scores...")
    
    # Load model
    model = load_model()
    
    # Load only 100 rows
    features_df = load_features_chunk()
    
    # Get DB customer IDs
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT customer_id FROM customers ORDER BY created_at LIMIT 100;")
    db_customer_ids = [str(row[0]) for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    print(f"📊 Processing {len(features_df)} customers")
    
    # Prepare features
    exclude_cols = ['customer_id', 'segment', 'will_default_in_2_4_weeks', 'generation_timestamp']
    feature_cols = [col for col in features_df.columns if col not in exclude_cols]
    X = features_df[feature_cols].fillna(0).astype('float32')
    
    # Predict in batches of 20
    batch_size = 20
    all_results = []
    
    for i in range(0, len(X), batch_size):
        batch_X = X.iloc[i:i+batch_size]
        dmatrix = xgb.DMatrix(batch_X)
        risk_scores = model.predict(dmatrix)
        
        for j, score in enumerate(risk_scores):
            idx = i + j
            risk_score = float(score)
            
            if risk_score >= 0.7:
                risk_level = "CRITICAL"
            elif risk_score >= 0.5:
                risk_level = "HIGH"
            elif risk_score >= 0.3:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            # Top 3 features only (reduce memory)
            feature_values = batch_X.iloc[j].to_dict()
            sorted_features = sorted(feature_values.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
            top_features = [{"feature": f, "value": float(max(-9.9, min(9.9, v)))} for f, v in sorted_features]
            
            all_results.append({
                'customer_id': db_customer_ids[idx],
                'risk_score': risk_score,
                'risk_level': risk_level,
                'top_features': top_features
            })
        
        print(f"  Processed {min(i+batch_size, len(X))}/{len(X)}")
        gc.collect()
    
    results_df = pd.DataFrame(all_results)
    
    # Summary
    print(f"\n📈 Distribution:")
    print(f"   CRITICAL: {len(results_df[results_df['risk_level']=='CRITICAL'])}")
    print(f"   HIGH: {len(results_df[results_df['risk_level']=='HIGH'])}")
    print(f"   MEDIUM: {len(results_df[results_df['risk_level']=='MEDIUM'])}")
    print(f"   LOW: {len(results_df[results_df['risk_level']=='LOW'])}")
    print(f"   Avg: {results_df['risk_score'].mean():.4f}")
    
    # Store
    store_risk_scores(results_df)
    
    print("\n✅ Complete!")
    print("🌐 http://15.206.72.35:8501")

if __name__ == '__main__':
    main()
