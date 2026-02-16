# PHASE 4: REAL-TIME API & SCORING (Days 13-15)

## Create FastAPI Application

Create src/serving/api.py:

```python
"""
FastAPI application for real-time risk scoring
Provides REST endpoints and WebSocket for live updates
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import redis
import json
import asyncio
from sqlalchemy import create_engine
import os

from src.models.train import DelinquencyModel
from src.explainability.shap_explainer import RiskExplainer
from src.feature_engineering.features import BehavioralFeatureEngineering

# Initialize FastAPI app
app = FastAPI(
    title="Pre-Delinquency Intervention API",
    description="Real-time financial stress detection and explainable risk scoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
model_wrapper = None
explainer = None
feature_engineer = None
redis_client = None
db_engine = None

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
    explanation: Dict
    timestamp: str
    model_version: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    redis_connected: bool
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
    global model_wrapper, explainer, feature_engineer, redis_client, db_engine
    
    print("🚀 Starting Pre-Delinquency API...")
    
    try:
        # Load trained model
        print("📦 Loading ML model...")
        model_path = os.getenv("MODEL_PATH", "data/models/delinquency_predictor_v1_full.pkl")
        model_wrapper = DelinquencyModel.load_model(model_path)
        print(f"  ✅ Model loaded: {model_wrapper.model_name}")
        
        # Initialize explainer
        print("🔍 Initializing SHAP explainer...")
        explainer = RiskExplainer(
            model=model_wrapper.model,
            feature_names=model_wrapper.feature_names
        )
        print("  ✅ Explainer initialized")
        
        # Initialize feature engineer
        print("⚙️ Initializing feature engineer...")
        db_url = os.getenv("DATABASE_URL")
        feature_engineer = BehavioralFeatureEngineering(db_url=db_url)
        print("  ✅ Feature engineer initialized")
        
        # Connect to Redis
        print("🔗 Connecting to Redis...")
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        print("  ✅ Redis connected")
        
        # Connect to database
        print("🗄️ Connecting to database...")
        db_engine = create_engine(db_url)
        with db_engine.connect() as conn:
            conn.execute("SELECT 1")
        print("  ✅ Database connected")
        
        print("\n✅ API startup complete!\n")
    
    except Exception as e:
        print(f"❌ Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global redis_client, db_engine
    
    print("👋 Shutting down API...")
    
    if redis_client:
        redis_client.close()
    
    if db_engine:
        db_engine.dispose()
    
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
            "customer_history": "/customer/{customer_id}/history"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    
    redis_ok = False
    db_ok = False
    
    try:
        redis_client.ping()
        redis_ok = True
    except:
        pass
    
    try:
        with db_engine.connect() as conn:
            conn.execute("SELECT 1")
        db_ok = True
    except:
        pass
    
    return HealthResponse(
        status="healthy" if (model_wrapper and redis_ok and db_ok) else "degraded",
        model_loaded=model_wrapper is not None,
        redis_connected=redis_ok,
        database_connected=db_ok,
        timestamp=datetime.now().isoformat()
    )

@app.post("/predict", response_model=RiskResponse)
async def predict_risk(request: RiskRequest):
    """
    Score a single customer and return explainable risk prediction
    """
    try:
        # Parse observation date
        if request.observation_date:
            obs_date = datetime.fromisoformat(request.observation_date)
        else:
            obs_date = datetime.now()
        
        # Check cache first
        cache_key = f"risk:{request.customer_id}:{obs_date.date()}"
        cached = redis_client.get(cache_key)
        
        if cached:
            print(f"📦 Cache hit for {request.customer_id}")
            return RiskResponse(**json.loads(cached))
        
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
        X = features_df[feature_cols]
        
        # Predict risk score
        print(f"🎯 Scoring customer {request.customer_id}...")
        risk_score = model_wrapper.predict(X, return_proba=True)[0]
        
        # Generate explanation
        print(f"🔍 Generating explanation...")
        explanation = explainer.explain_prediction(X, risk_score, top_n=5)
        
        # Create response
        response = RiskResponse(
            customer_id=request.customer_id,
            risk_score=risk_score,
            risk_level=explanation['risk_level'],
            explanation=explanation,
            timestamp=datetime.now().isoformat(),
            model_version=model_wrapper.model_name
        )
        
        # Store in Redis (cache for 1 hour)
        redis_client.setex(
            cache_key,
            3600,
            json.dumps(response.dict())
        )
        
        # Store in risk_scores table
        _store_risk_score(request.customer_id, obs_date, risk_score, explanation)
        
        print(f"✅ Prediction complete: {risk_score:.4f} ({explanation['risk_level']})")
        
        return response
    
    except Exception as e:
        print(f"❌ Prediction failed: {str(e)}")
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
        
        return {
            "count": len(df),
            "customers": df.to_dict('records')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# ==================== WEBSOCKET ====================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time risk score updates
    Streams risk scores as they are computed
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Listen for client messages (optional)
            data = await websocket.receive_text()
            
            # In production, this would subscribe to Redis pubsub or Kafka
            # For demo, we simulate with database polling
            await asyncio.sleep(2)
            
            # Get recent risk scores
            query = """
            SELECT 
                customer_id, risk_score, risk_level, score_date
            FROM risk_scores
            WHERE score_date >= NOW() - INTERVAL '5 minutes'
            ORDER BY score_date DESC
            LIMIT 10
            """
            
            df = pd.read_sql(query, db_engine)
            
            if len(df) > 0:
                await websocket.send_json({
                    "type": "risk_updates",
                    "data": df.to_dict('records'),
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ==================== HELPER FUNCTIONS ====================

def _store_risk_score(
    customer_id: str,
    observation_date: datetime,
    risk_score: float,
    explanation: Dict
):
    """Store risk score in database"""
    try:
        top_drivers = explanation.get('top_drivers', [])
        
        # Prepare data
        data = {
            'customer_id': customer_id,
            'score_date': observation_date,
            'risk_score': risk_score,
            'risk_level': explanation['risk_level'],
            'model_version': model_wrapper.model_name,
            'top_feature_1': top_drivers[0]['feature'] if len(top_drivers) > 0 else None,
            'top_feature_1_impact': top_drivers[0]['impact'] if len(top_drivers) > 0 else None,
            'top_feature_2': top_drivers[1]['feature'] if len(top_drivers) > 1 else None,
            'top_feature_2_impact': top_drivers[1]['impact'] if len(top_drivers) > 1 else None,
            'top_feature_3': top_drivers[2]['feature'] if len(top_drivers) > 2 else None,
            'top_feature_3_impact': top_drivers[2]['impact'] if len(top_drivers) > 2 else None,
        }
        
        df = pd.DataFrame([data])
        df.to_sql('risk_scores', db_engine, if_exists='append', index=False)
    
    except Exception as e:
        print(f"⚠️ Failed to store risk score: {str(e)}")

# ==================== BACKGROUND TASKS ====================

from fastapi import BackgroundTasks

@app.post("/trigger_batch_scoring")
async def trigger_batch_scoring(background_tasks: BackgroundTasks):
    """
    Trigger batch scoring of all active customers
    Runs in background
    """
    background_tasks.add_task(_batch_score_all_customers)
    
    return {
        "status": "started",
        "message": "Batch scoring initiated in background",
        "timestamp": datetime.now().isoformat()
    }

async def _batch_score_all_customers():
    """Score all active customers"""
    try:
        print("🚀 Starting batch scoring...")
        
        # Get all active customers
        query = "SELECT customer_id FROM customers LIMIT 1000"
        df = pd.read_sql(query, db_engine)
        
        customer_ids = df['customer_id'].tolist()
        
        print(f"📊 Scoring {len(customer_ids)} customers...")
        
        for i, customer_id in enumerate(customer_ids):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(customer_ids)}")
            
            try:
                request = RiskRequest(customer_id=customer_id)
                await predict_risk(request)
            except:
                continue
        
        print("✅ Batch scoring complete!")
    
    except Exception as e:
        print(f"❌ Batch scoring failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.serving.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

## Run the API

```bash
# Start API server
uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 --reload

# Or with Docker
docker-compose up api

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/stats

# View interactive docs
open http://localhost:8000/docs
```

## API Testing

```bash
# Test single prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "your-customer-uuid"}'

# Test batch prediction
curl -X POST "http://localhost:8000/batch_predict" \
  -H "Content-Type: application/json" \
  -d '{"customer_ids": ["uuid1", "uuid2", "uuid3"]}'

# Get high risk customers
curl "http://localhost:8000/high_risk_customers?limit=10"

# Get customer history
curl "http://localhost:8000/customer/{customer_id}/history?days=30"
```
