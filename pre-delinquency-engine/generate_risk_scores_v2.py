#!/usr/bin/env python3
"""
Generate risk scores for V2 customers using pre-computed features
"""
import pandas as pd
import xgboost as xgb
import psycopg2
from datetime import datetime
import json
import os
from dotenv import load_dotenv

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
    print(f"✅ Loaded model from {model_path}")
    return model

def load_features():
    """Load V2 features"""
    csv_path = 'data/processed/behavioral_features_v2.csv'
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Features not found at {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} customers from {csv_path}")
    return df

def get_db_customer_ids():
    """Get customer IDs from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("SELECT customer_id FROM customers;")
    customer_ids = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    print(f"✅ Found {len(customer_ids)} customers in database")
    return set(str(cid) for cid in customer_ids)

def store_risk_scores(predictions_df):
    """Store risk scores in database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Clear existing risk scores
    cur.execute("DELETE FROM risk_scores;")
    print(f"🗑️  Cleared existing risk scores")
    
    # Insert new scores
    inserted = 0
    for _, row in predictions_df.iterrows():
        try:
            cur.execute("""
                INSERT INTO risk_scores 
                (customer_id, observation_date, risk_score, risk_level, top_features)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                row['customer_id'],
                datetime.now(),
                float(row['risk_score']),
                row['risk_level'],
                json.dumps(row['top_features'])
            ))
            inserted += 1
        except Exception as e:
            print(f"⚠️  Failed to insert {row['customer_id']}: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Inserted {inserted} risk scores")

def main():
    print("🚀 Generating risk scores for V2 customers...")
    print()
    
    # Load model and features
    model = load_model()
    features_df = load_features()
    
    # Get database customer IDs
    db_customer_ids = get_db_customer_ids()
    
    # Filter to only customers in database (first 100)
    features_df['customer_id_str'] = features_df['customer_id'].astype(str)
    
    # Map CUST_XXXXXX to UUIDs in database
    # Since we loaded first 100 rows of CSV to DB, we need first 100 rows
    features_df = features_df.head(100).copy()
    
    print(f"📊 Processing {len(features_df)} customers")
    print()
    
    # Prepare features for prediction
    exclude_cols = ['customer_id', 'customer_id_str', 'segment', 'will_default_in_2_4_weeks', 'generation_timestamp']
    feature_cols = [col for col in features_df.columns if col not in exclude_cols]
    
    X = features_df[feature_cols].fillna(0)
    
    # Make predictions
    dmatrix = xgb.DMatrix(X)
    risk_scores = model.predict(dmatrix)
    
    # Create results dataframe
    results = []
    
    # Get actual customer IDs from database (in order)
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT customer_id FROM customers ORDER BY created_at LIMIT 100;")
    db_customer_ids_ordered = [str(row[0]) for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    for i, (idx, row) in enumerate(features_df.iterrows()):
        risk_score = float(risk_scores[i])
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Get top 5 features by absolute value
        feature_values = X.iloc[i].to_dict()
        sorted_features = sorted(
            feature_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]
        
        top_features = [
            {"feature": feat, "value": float(max(-9.9999, min(9.9999, val)))}
            for feat, val in sorted_features
        ]
        
        results.append({
            'customer_id': db_customer_ids_ordered[i],
            'risk_score': risk_score,
            'risk_level': risk_level,
            'top_features': top_features
        })
    
    results_df = pd.DataFrame(results)
    
    # Print summary
    print("📈 Risk Score Distribution:")
    print(f"   CRITICAL (≥0.7): {len(results_df[results_df['risk_level'] == 'CRITICAL'])}")
    print(f"   HIGH (0.5-0.7):  {len(results_df[results_df['risk_level'] == 'HIGH'])}")
    print(f"   MEDIUM (0.3-0.5): {len(results_df[results_df['risk_level'] == 'MEDIUM'])}")
    print(f"   LOW (<0.3):      {len(results_df[results_df['risk_level'] == 'LOW'])}")
    print(f"   Average Score:   {results_df['risk_score'].mean():.4f}")
    print()
    
    # Store in database
    store_risk_scores(results_df)
    
    print()
    print("✅ Risk score generation complete!")
    print(f"🌐 Dashboard: http://15.206.72.35:8501")

if __name__ == '__main__':
    main()
