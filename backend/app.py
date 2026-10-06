"""
SmartBank AI - Backend API Service
FastAPI inference service for pre-contact term deposit subscription prediction.
"""

import os
import json
import joblib
import pandas as pd
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="SmartBank AI - Campaign Intelligence API",
    description="Pre-Contact Term Deposit Subscription Likelihood & Opportunity Scoring Service",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths to models & outputs
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "best_pipeline.joblib")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
METRICS_PATH = os.path.join(OUTPUTS_DIR, "metrics.json")
EDA_PATH = os.path.join(OUTPUTS_DIR, "eda_summary.json")
FI_PATH = os.path.join(OUTPUTS_DIR, "feature_importance.json")

# Global model holder
model_pipeline = None

def load_pipeline():
    global model_pipeline
    if os.path.exists(MODEL_PATH):
        try:
            model_pipeline = joblib.load(MODEL_PATH)
            print(f"[SmartBank API] Successfully loaded model pipeline from {MODEL_PATH}")
        except Exception as e:
            print(f"[SmartBank API] Error loading model: {e}")
            model_pipeline = None
    else:
        print(f"[SmartBank API] Model file not found at {MODEL_PATH}")

load_pipeline()

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class ClientFeatures(BaseModel):
    age: int = Field(..., ge=18, le=100, description="Age of the client", example=42)
    job: str = Field(..., description="Job type", example="technician")
    marital: str = Field(..., description="Marital status", example="married")
    education: str = Field(..., description="Education level", example="secondary")
    default: str = Field("no", description="Credit in default (yes/no)", example="no")
    balance: float = Field(..., description="Average yearly balance in euros", example=1850.0)
    housing: str = Field(..., description="Housing loan (yes/no)", example="no")
    loan: str = Field("no", description="Personal loan (yes/no)", example="no")
    poutcome: str = Field("unknown", description="Outcome of previous marketing campaign", example="success")
    previous: int = Field(0, ge=0, description="Number of contacts performed before this campaign", example=2)

class PredictionResponse(BaseModel):
    probability: float
    opportunity_score: int
    campaign_priority: str
    prediction_label: str
    recommendation: str
    predictive_signals: List[Dict[str, Any]]
    disclaimer: str

# -------------------------------------------------------------
# API ENDPOINTS
# -------------------------------------------------------------
@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify API and model status."""
    return {
        "status": "healthy",
        "model_loaded": model_pipeline is not None,
        "model_type": "Random Forest Classifier (Ensemble)" if model_pipeline else "None",
        "leakage_safe": True
    }

@app.get("/dashboard", tags=["Intelligence"])
def get_dashboard_data():
    """Retrieves full model metrics, EDA summary, and feature importances for UI display."""
    data = {}
    
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            data["metrics"] = json.load(f)
    else:
        data["metrics"] = None
        
    if os.path.exists(EDA_PATH):
        with open(EDA_PATH, "r", encoding="utf-8") as f:
            data["eda"] = json.load(f)
    else:
        data["eda"] = None
        
    if os.path.exists(FI_PATH):
        with open(FI_PATH, "r", encoding="utf-8") as f:
            data["feature_importance"] = json.load(f)
    else:
        data["feature_importance"] = None
        
    return data

@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
def predict_subscription(features: ClientFeatures):
    """
    Computes pre-contact term deposit subscription probability and opportunity score.
    """
    if model_pipeline is None:
        load_pipeline()
        if model_pipeline is None:
            raise HTTPException(status_code=503, detail="Model pipeline is not loaded. Run training first.")
            
    # Build DataFrame matching training features
    input_df = pd.DataFrame([{
        "job": features.job.strip().lower(),
        "marital": features.marital.strip().lower(),
        "education": features.education.strip().lower(),
        "default": features.default.strip().lower(),
        "housing": features.housing.strip().lower(),
        "loan": features.loan.strip().lower(),
        "poutcome": features.poutcome.strip().lower(),
        "age": features.age,
        "balance": features.balance,
        "previous": features.previous
    }])
    
    try:
        prob = float(model_pipeline.predict_proba(input_df)[0, 1])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Inference error: {str(e)}")
        
    opportunity_score = int(round(prob * 100))
    
    # Priority tiers
    if opportunity_score >= 60:
        priority = "HIGH"
        rec = "High engagement opportunity: Assign to senior relationship manager with premium deposit terms."
    elif opportunity_score >= 35:
        priority = "MEDIUM"
        rec = "Moderate engagement potential: Contact via standard digital or phone campaign with tailored savings offer."
    else:
        priority = "LOW"
        rec = "Low engagement likelihood: Preserve budget by deprioritizing direct outreach or using low-cost automated channel."
        
    prediction_label = "Likely to Subscribe" if prob >= 0.50 else "Unlikely to Subscribe"
    
    # Contextual signals based on customer attributes
    signals = []
    if features.poutcome == "success":
        signals.append({"factor": "Previous Campaign Success", "impact": "Strong Positive", "type": "positive"})
    if features.housing == "no":
        signals.append({"factor": "No Housing Loan Obligation", "impact": "Positive", "type": "positive"})
    if features.balance > 2000:
        signals.append({"factor": "Healthy Account Balance (>€2,000)", "impact": "Positive", "type": "positive"})
    elif features.balance < 100:
        signals.append({"factor": "Low Account Balance (<€100)", "impact": "Restraining", "type": "negative"})
    if features.age >= 60:
        signals.append({"factor": "Retirement/Senior Demographics", "impact": "Positive", "type": "positive"})
    if features.housing == "yes":
        signals.append({"factor": "Active Housing Loan Commitment", "impact": "Restraining", "type": "negative"})
    if features.loan == "yes":
        signals.append({"factor": "Active Personal Loan", "impact": "Restraining", "type": "negative"})
        
    if not signals:
        signals.append({"factor": "Standard Profile Baseline", "impact": "Neutral", "type": "neutral"})
        
    return PredictionResponse(
        probability=round(prob, 4),
        opportunity_score=opportunity_score,
        campaign_priority=priority,
        prediction_label=prediction_label,
        recommendation=rec,
        predictive_signals=signals,
        disclaimer="The Opportunity Score translates predictive likelihood into a campaign prioritization signal. It represents statistical association and does not guarantee subscription."
    )
