"""
FastAPI application for real-time risk scoring
Provides REST endpoints for pre-delinquency predictions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import xgboost as xgb
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

from src.feature_engineering.features import BehavioralFeatureEngineering
from src.streaming.producers import PredictionProducer, DashboardProducer
from src.models.auto_retrain import AutoRetrainer

# Initialize FastAPI app
app = FastAPI(
    title="Pre-Delinquency Intervention API",
    description="Real-time financial stress detection and risk scoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
model = None
feature_engineer = None
db_engine = None
feature_names = None
threshold = 0.5
prediction_producer = None
dashboard_producer = None

# ==================== MODELS ====================

class RiskRequest(BaseModel):
    customer_id: str = Field(..., description="Customer UUID")
    observation_date: Optional[str] = Field(None, description="ISO format date (defaults to now)")

class BatchRiskRequest(BaseModel):
    customer_ids: List[str] = Field(..., description="List of customer UUIDs")
    observation_date: Optional[str] = Field(None, description="ISO format date")

class RiskResponse(BaseModel):
    customer_id: str
    risk_score: float
    risk_level: str
    top_features: List[Dict]
    explanation: Dict  # Add explanation field
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    database_connected: bool
    timestamp: str

class StatsResponse(BaseModel):
    total_customers: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    avg_risk_score: float
    last_updated: str

# ==================== STARTUP & SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Initialize models and connections on startup"""
    global model, feature_engineer, db_engine, feature_names, threshold, prediction_producer, dashboard_producer
    
    print("🚀 Starting Pre-Delinquency API...")
    
    try:
        # Load trained model
        print("📦 Loading ML model...")
        model_path = os.getenv("MODEL_PATH", "data/models/quick/quick_model.json")
        
        if not os.path.exists(model_path):
            print(f"  ⚠️ Model not found at {model_path}, using default")
            model_path = "data/models/quick/quick_model.json"
        
        model = xgb.Booster()
        model.load_model(model_path)
        print(f"  ✅ Model loaded from {model_path}")
        
        # Get feature names from model
        feature_names = model.feature_names
        print(f"  ✅ Model expects {len(feature_names)} features")
        
        # Initialize feature engineer
        print("⚙️ Initializing feature engineer...")
        db_url = os.getenv("DATABASE_URL")
        feature_engineer = BehavioralFeatureEngineering(db_url=db_url)
        print("  ✅ Feature engineer initialized")
        
        # Connect to database
        print("🗄️ Connecting to database...")
        db_engine = create_engine(db_url)
        with db_engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        print("  ✅ Database connected")
        
        # Initialize Kafka producers
        print("📡 Initializing Kafka producers...")
        try:
            prediction_producer = PredictionProducer()
            dashboard_producer = DashboardProducer()
            print("  ✅ Kafka producers initialized")
        except Exception as e:
            print(f"  ⚠️ Kafka producers failed (continuing without Kafka): {e}")
            prediction_producer = None
            dashboard_producer = None
        
        print("\n✅ API startup complete!\n")
    
    except Exception as e:
        print(f"❌ Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_engine, prediction_producer, dashboard_producer
    
    print("👋 Shutting down API...")
    
    if db_engine:
        db_engine.dispose()
    
    if prediction_producer:
        prediction_producer.close()
    
    if dashboard_producer:
        dashboard_producer.close()
    
    print("✅ Shutdown complete")

# ==================== ENDPOINTS ====================

@app.get("/", response_model=Dict)
async def root():
    """API root endpoint"""
    return {
        "name": "Pre-Delinquency Intervention API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "batch_predict": "/batch_predict",
            "stats": "/stats",
            "customer_history": "/customer/{customer_id}/history",
            "high_risk": "/high_risk_customers",
            "retraining_status": "/retraining/status",
            "trigger_retraining": "/retraining/trigger"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    
    db_ok = False
    
    try:
        from sqlalchemy import text
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except:
        pass
    
    return HealthResponse(
        status="healthy" if (model and db_ok) else "degraded",
        model_loaded=model is not None,
        database_connected=db_ok,
        timestamp=datetime.now().isoformat()
    )

@app.post("/predict", response_model=RiskResponse)
async def predict_risk(request: RiskRequest):
    """
    Score a single customer and return risk prediction
    """
    try:
        # Parse observation date
        if request.observation_date:
            obs_date = datetime.fromisoformat(request.observation_date)
        else:
            obs_date = datetime.now()
        
        # Compute features
        print(f"⚙️ Computing features for {request.customer_id}...")
        features = feature_engineer.compute_all_features(
            request.customer_id,
            obs_date
        )
        
        # Convert to DataFrame
        features_df = pd.DataFrame([features])
        
        # Exclude metadata columns
        exclude_cols = ['customer_id', 'observation_date']
        feature_cols = [col for col in features_df.columns if col not in exclude_cols]
        X = features_df[feature_cols].fillna(0)
        
        # Ensure feature order matches model
        if feature_names:
            X = X[feature_names]
        
        # Predict risk score
        print(f"🎯 Scoring customer {request.customer_id}...")
        dmatrix = xgb.DMatrix(X)
        risk_score = float(model.predict(dmatrix)[0])
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Get top features (simple version - by absolute value)
        feature_values = X.iloc[0].to_dict()
        sorted_features = sorted(
            feature_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]
        
        # Cap feature impact values to fit database constraints (DECIMAL(5,4) = -9.9999 to 9.9999)
        top_features = [
            {"feature": feat, "value": float(max(-9.9999, min(9.9999, val)))}
            for feat, val in sorted_features
        ]
        
        # Create explanation with top_drivers for dashboard
        top_drivers = []
        for i, (feat, val) in enumerate(sorted_features, 1):
            capped_val = float(max(-9.9999, min(9.9999, val)))
            impact_pct = abs(capped_val) * 10  # Simple percentage calculation
            top_drivers.append({
                "feature": feat,
                "value": f"{capped_val:.4f}",
                "impact": capped_val,
                "impact_pct": min(100, impact_pct)
            })
        
        # Generate explanation text
        explanation_text = f"This customer has a {risk_level.lower()} risk score of {risk_score:.1%}. "
        if risk_score >= 0.5:
            explanation_text += f"Key risk factors include {sorted_features[0][0]} and {sorted_features[1][0]}. "
            explanation_text += "Immediate intervention recommended."
        elif risk_score >= 0.3:
            explanation_text += "Monitor closely for any changes in behavior patterns."
        else:
            explanation_text += "Customer shows stable financial behavior with low risk indicators."
        
        explanation = {
            "explanation_text": explanation_text,
            "top_drivers": top_drivers
        }
        
        # Create response
        response = RiskResponse(
            customer_id=request.customer_id,
            risk_score=risk_score,
            risk_level=risk_level,
            top_features=top_features,
            explanation=explanation,
            timestamp=datetime.now().isoformat()
        )
        
        # Store in risk_scores table
        _store_risk_score(request.customer_id, obs_date, risk_score, risk_level, top_features)
        
        # Publish to Kafka
        if prediction_producer:
            try:
                prediction_producer.send_prediction(response.dict())
                print(f"  📡 Prediction published to Kafka")
            except Exception as e:
                print(f"  ⚠️ Failed to publish to Kafka: {e}")
        
        # Send dashboard update
        if dashboard_producer:
            try:
                dashboard_producer.send_update({
                    'type': 'new_prediction',
                    'customer_id': request.customer_id,
                    'risk_score': risk_score,
                    'risk_level': risk_level
                })
            except Exception as e:
                print(f"  ⚠️ Failed to send dashboard update: {e}")
        
        print(f"✅ Prediction complete: {risk_score:.4f} ({risk_level})")
        
        return response
    
    except Exception as e:
        print(f"❌ Prediction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/batch_predict", response_model=List[RiskResponse])
async def batch_predict(request: BatchRiskRequest):
    """
    Score multiple customers in batch
    """
    try:
        obs_date = datetime.fromisoformat(request.observation_date) if request.observation_date else datetime.now()
        
        print(f"📊 Batch scoring {len(request.customer_ids)} customers...")
        
        responses = []
        
        for customer_id in request.customer_ids:
            try:
                single_request = RiskRequest(
                    customer_id=customer_id,
                    observation_date=obs_date.isoformat()
                )
                response = await predict_risk(single_request)
                responses.append(response)
            except Exception as e:
                print(f"  ⚠️ Failed for {customer_id}: {str(e)}")
                continue
        
        print(f"✅ Batch complete: {len(responses)}/{len(request.customer_ids)} successful")
        
        return responses
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get aggregate risk statistics
    """
    try:
        # Query latest risk scores from database
        query = """
        WITH latest_scores AS (
            SELECT DISTINCT ON (customer_id) 
                customer_id, risk_score, risk_level, score_date
            FROM risk_scores
            ORDER BY customer_id, score_date DESC
        )
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN risk_level IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END) as high_risk,
            SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_risk,
            SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) as low_risk,
            AVG(risk_score) as avg_score,
            MAX(score_date) as last_updated
        FROM latest_scores
        """
        
        df = pd.read_sql(query, db_engine)
        
        if len(df) == 0:
            return StatsResponse(
                total_customers=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                avg_risk_score=0.0,
                last_updated=datetime.now().isoformat()
            )
        
        row = df.iloc[0]
        
        return StatsResponse(
            total_customers=int(row['total']),
            high_risk_count=int(row['high_risk']),
            medium_risk_count=int(row['medium_risk']),
            low_risk_count=int(row['low_risk']),
            avg_risk_score=float(row['avg_score']),
            last_updated=row['last_updated'].isoformat() if pd.notna(row['last_updated']) else datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")

@app.get("/customer/{customer_id}/history")
async def get_customer_history(customer_id: str, days: int = 30):
    """
    Get risk score history for a customer
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = f"""
        SELECT 
            score_date,
            risk_score,
            risk_level,
            top_feature_1,
            top_feature_1_impact,
            top_feature_2,
            top_feature_2_impact
        FROM risk_scores
        WHERE customer_id = '{customer_id}'
          AND score_date >= '{cutoff_date}'
        ORDER BY score_date DESC
        """
        
        df = pd.read_sql(query, db_engine)
        
        if len(df) == 0:
            return {
                "customer_id": customer_id,
                "history": [],
                "message": "No history found"
            }
        
        # Convert timestamps to ISO format
        df['score_date'] = df['score_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        history = df.to_dict('records')
        
        return {
            "customer_id": customer_id,
            "history": history,
            "count": len(history)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History query failed: {str(e)}")

@app.get("/high_risk_customers")
async def get_high_risk_customers(limit: int = 50):
    """
    Get list of customers with high risk scores
    """
    try:
        query = f"""
        WITH latest_scores AS (
            SELECT DISTINCT ON (customer_id) 
                customer_id, risk_score, risk_level, score_date,
                top_feature_1, top_feature_1_impact
            FROM risk_scores
            ORDER BY customer_id, score_date DESC
        )
        SELECT *
        FROM latest_scores
        WHERE risk_level IN ('HIGH', 'CRITICAL')
        ORDER BY risk_score DESC
        LIMIT {limit}
        """
        
        df = pd.read_sql(query, db_engine)
        
        # Convert timestamps
        if len(df) > 0:
            df['score_date'] = df['score_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "count": len(df),
            "customers": df.to_dict('records')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/retraining/status")
async def get_retraining_status():
    """
    Check if model retraining is needed and get history
    """
    try:
        retrainer = AutoRetrainer()
        
        # Check if retraining needed
        new_customers = retrainer.check_new_customers()
        should_retrain, reason = retrainer.should_retrain(new_customer_threshold=50)
        
        # Get recent history
        history = retrainer.get_retraining_history(limit=5)
        history_list = history.to_dict('records') if len(history) > 0 else []
        
        # Convert timestamps to strings
        for record in history_list:
            if 'retrain_date' in record and record['retrain_date']:
                record['retrain_date'] = str(record['retrain_date'])
        
        return {
            "new_customers_count": new_customers,
            "retraining_needed": should_retrain,
            "reason": reason,
            "threshold": 50,
            "recent_retraining": history_list
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.post("/retraining/trigger")
async def trigger_retraining(max_customers: int = 200):
    """
    Manually trigger model retraining
    WARNING: This will take several minutes and block the API
    """
    try:
        print("\n🔔 Manual retraining triggered via API")
        
        retrainer = AutoRetrainer()
        result = retrainer.retrain_model(max_customers=max_customers)
        
        if result['success']:
            return {
                "status": "success",
                "message": "Model retrained successfully. Restart API to load new model.",
                "customers_trained": result['customers_trained'],
                "samples_trained": result['samples_trained'],
                "auc": result['auc'],
                "model_version": result['model_version']
            }
        else:
            raise HTTPException(status_code=500, detail="Retraining failed")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

# ==================== HELPER FUNCTIONS ====================

def _store_risk_score(
    customer_id: str,
    observation_date: datetime,
    risk_score: float,
    risk_level: str,
    top_features: List[Dict]
):
    """Store risk score in database"""
    try:
        # Prepare data
        data = {
            'customer_id': customer_id,
            'score_date': observation_date,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'model_version': 'quick_model_v1',
            'top_feature_1': top_features[0]['feature'] if len(top_features) > 0 else None,
            'top_feature_1_impact': top_features[0]['value'] if len(top_features) > 0 else None,
            'top_feature_2': top_features[1]['feature'] if len(top_features) > 1 else None,
            'top_feature_2_impact': top_features[1]['value'] if len(top_features) > 1 else None,
            'top_feature_3': top_features[2]['feature'] if len(top_features) > 2 else None,
            'top_feature_3_impact': top_features[2]['value'] if len(top_features) > 2 else None,
        }
        
        df = pd.DataFrame([data])
        df.to_sql('risk_scores', db_engine, if_exists='append', index=False)
    
    except Exception as e:
        print(f"⚠️ Failed to store risk score: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.serving.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
