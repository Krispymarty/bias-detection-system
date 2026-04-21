from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import joblib
import logging
import pandas as pd
import time
from pipeline.model import predict, preprocess_data
from pipeline.explainability import get_shap_explanation

import json
import ast

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage()
        }
        try:
            # If the message is a stringified dictionary (like our analytics), parse it into the JSON
            parsed_msg = ast.literal_eval(record.getMessage())
            if isinstance(parsed_msg, dict):
                log_record.update(parsed_msg)
                del log_record["message"]
        except Exception:
            pass
        return json.dumps(log_record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File handler (JSON format)
log_path = os.path.join(os.path.dirname(__file__), "..", "logs", "api_audit.jsonl")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
file_handler = logging.FileHandler(log_path)
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

import sys

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)

# Prevent duplicates in console
logger.propagate = False

# Initialize FastAPI app
app = FastAPI(
    title="AI Fairness Auditor",
    description="Backend API for fairness evaluation, bias detection, and SHAP explainability.",
    version="1.0.0"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

# Global variables for model storage
MODELS: Dict[str, Any] = {}

from pydantic import BaseModel, Field

# Defines the input contract for the API exactly as specified
class FeatureSet(BaseModel):
    CODE_GENDER: str = Field(..., pattern="^(M|F)$", description="Applicant gender (M or F)")
    AGE: int = Field(..., ge=18, le=100, description="Applicant age. Must be 18-100.")
    AMT_INCOME_TOTAL: float = Field(..., ge=0.0, description="Total income. Cannot be negative.")
    AMT_CREDIT: float = Field(..., ge=1000.0, le=10000000.0, description="Credit amount requested.")
    AMT_ANNUITY: float = Field(..., ge=0.0, description="Loan annuity. Cannot be negative.")
    NAME_EDUCATION_TYPE: str = Field(..., description="Education level string")
    OCCUPATION_TYPE: str = Field(..., description="Occupation type string")
    EXT_SOURCE_1: float = Field(..., ge=0.0, le=1.0, description="Normalized external score 1")
    EXT_SOURCE_2: float = Field(..., ge=0.0, le=1.0, description="Normalized external score 2")
    EXT_SOURCE_3: float = Field(..., ge=0.0, le=1.0, description="Normalized external score 3")
    INCOME_GROUP: str = Field(..., description="Categorical income group")

class AuditRequest(BaseModel):
    domain: str
    features: FeatureSet
    apply_mitigation: bool = False

@app.on_event("startup")
async def load_model_bundle():
    """Load the ML model bundles into memory at startup."""
    global MODELS
    lending_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "production_model_v1.joblib")
    
    try:
        # Load the lending domain model
        MODELS["lending"] = joblib.load(lending_path)
        logger.info("Lending model bundle loaded successfully.")
        
        # Load the fair model if available
        fair_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "fair_model.joblib")
        if os.path.exists(fair_path):
            MODELS["fair_lending"] = joblib.load(fair_path)
            logger.info("Fair model bundle loaded successfully.")
        
        # Load the hiring domain model when Team B provides it
        hiring_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "production_model_hiring.joblib")
        if os.path.exists(hiring_path):
            MODELS["hiring"] = joblib.load(hiring_path)
            logger.info("Hiring model bundle loaded successfully.")
        else:
            # Fallback to lending model if hiring model is missing to prevent crash for hiring domain testing
            MODELS["hiring"] = MODELS.get("lending")
            logger.info("Hiring model not found, falling back to lending model.")
            
    except Exception as e:
        logger.error(f"Failed to load model bundle from {lending_path}: {e}")

def generate_counterfactual_recommendation(model_bundle: Dict[str, Any], X_raw: pd.DataFrame, pred_val: int) -> str:
    """Generates simple perturbation-based recommendations to flip a rejection."""
    if pred_val != 1:
        return "Application approved. No further action needed."
        
    try:
        # Try 1: Increase Income by 20%
        X_cf1 = X_raw.copy()
        X_cf1["AMT_INCOME_TOTAL"] *= 1.2
        if predict(model_bundle, X_cf1)[0] == 0:
            return "Increasing declared income by 20% may flip the decision to Approved."
            
        # Try 2: Reduce Credit by 20%
        X_cf2 = X_raw.copy()
        X_cf2["AMT_CREDIT"] *= 0.8
        if predict(model_bundle, X_cf2)[0] == 0:
            return "Reducing the requested credit amount by 20% may flip the decision to Approved."
            
        # Try 3: Both
        X_cf3 = X_raw.copy()
        X_cf3["AMT_INCOME_TOTAL"] *= 1.2
        X_cf3["AMT_CREDIT"] *= 0.8
        if predict(model_bundle, X_cf3)[0] == 0:
            return "A combination of a 20% higher income and a 20% lower credit request may improve the outcome."
            
        return "No simple adjustments (income or credit size) were found to immediately flip this outcome."
    except Exception as e:
        logger.warning(f"Counterfactual generation failed: {e}")
        return "Could not generate recommendation at this time."

@app.post("/v1/audit")
async def run_pipeline(request: AuditRequest):
    """
    Main orchestration endpoint for model inference, fairness auditing, and explanations.
    """
    start_time = time.time()
    logger.info(f"Received audit request for domain: {request.domain}")
    domain = request.domain.lower()
    if domain not in MODELS:
        logger.error(f"Domain '{domain}' requested but not loaded.")
        raise HTTPException(status_code=400, detail=f"Model for domain '{domain}' is not available.")
    
    MODEL_BUNDLE = MODELS[domain]
    
    # --- STEP 2: INPUT VALIDATION & DATAFRAME CONVERSION ---
    # Extract features safely
    raw_features = request.features.model_dump()
    
    # Handle specific mapping required by model.py and bias.py
    # UI sends CODE_GENDER ("M" or "F"), but pipelines explicitly want CODE_GENDER_M
    gender = raw_features.pop("CODE_GENDER", "F")
    raw_features["CODE_GENDER_M"] = 1 if gender == "M" else 0
    
    # Convert JSON features to exactly one-row Pandas DataFrame for pipeline ingestion
    try:
        X_raw = pd.DataFrame([raw_features])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to convert features to DataFrame: {e}")

    # --- STEP 3 & 4: SAFE PREPROCESSING & MODEL INFERENCE ---
    # The predict() function in model.py automatically delegates to preprocess_data()
    # ensuring training_columns perfectly align. It will output 1 (Reject) or 0 (Approve).
    try:
        if request.apply_mitigation and f"fair_{domain}" in MODELS:
            logger.info(f"Applying Fairlearn Mitigation for domain: {domain}")
            FAIR_BUNDLE = MODELS[f"fair_{domain}"]
            fair_model = FAIR_BUNDLE["fair_model"]
            
            X_processed, _, _ = preprocess_data(
                X_raw, 
                training_columns=FAIR_BUNDLE.get("training_columns"), 
                income_bins=FAIR_BUNDLE.get("income_bins")
            )
            
            gender_val = "Male" if raw_features["CODE_GENDER_M"] == 1 else "Female"
            age_val = "Older" if raw_features.get("AGE", 0) > 40 else "Younger"
            sensitive = pd.Series([f"{gender_val}_{age_val}"])
            
            pred_val = int(fair_model.predict(X_processed, sensitive_features=sensitive)[0])
            try:
                prob_val = float(fair_model.predict_proba(X_processed, sensitive_features=sensitive)[0][1])
            except Exception:
                prob_val = float(predict(MODEL_BUNDLE, X_raw)[1])
                
            prediction_str = "Rejected" if pred_val == 1 else "Approved"
            logger.info(f"Fair inference complete. Prediction: {prediction_str}, Probability: {float(prob_val):.4f}")
        else:
            pred_val, prob_val = predict(MODEL_BUNDLE, X_raw)
            prediction_str = "Rejected" if pred_val == 1 else "Approved"
            logger.info(f"Inference complete. Prediction: {prediction_str}, Probability: {float(prob_val):.4f}")
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed during preprocessing/prediction.")

    # --- STEP 5: COUNTERFACTUAL LOGIC (SIMPLE PERTURBATION) ---
    probability = round(float(prob_val), 4)
    confidence = "High" if probability > 0.8 else "Medium" if probability > 0.6 else "Low"
    
    # Structured Inference Analytics Logging
    logger.info(str({
        "event": "inference_completed",
        "domain": domain,
        "prediction": prediction_str,
        "probability": probability,
        "confidence": confidence,
        "threshold": round(float(MODEL_BUNDLE.get("optimal_threshold", 0.5)), 4),
        "model_version": MODEL_BUNDLE.get("version", "v1")
    }))

    if prediction_str == "Rejected":
        recommendation = generate_counterfactual_recommendation(MODEL_BUNDLE, X_raw, pred_val)
    else:
        recommendation = "Application approved. No further action needed."
        
    latency_ms = (time.time() - start_time) * 1000
    if latency_ms > 500:
        logger.warning(f"Audit request took {latency_ms:.2f}ms (EXCEEDS 500ms SLA!)")
    else:
        logger.info(f"Audit request completed in {latency_ms:.2f}ms")
        
    try:
        X_processed, _, _ = preprocess_data(
            X_raw, 
            training_columns=MODEL_BUNDLE.get("training_columns"), 
            income_bins=MODEL_BUNDLE.get("income_bins")
        )
        raw_explanation = get_shap_explanation(MODEL_BUNDLE, X_processed, top_n=5)
        explanation_dict = {
            item["feature"]: item["shap_value"] 
            for item in raw_explanation["top_features"]
        }
    except Exception as e:
        logger.error(f"Error generating SHAP explanation: {e}")
        explanation_dict = {}

    return {
        "prediction": prediction_str,
        "probability": probability,
        "confidence": confidence,
        "threshold": round(float(MODEL_BUNDLE.get("optimal_threshold", 0.5)), 4),
        "fairness_score": 0,
        "bias_metrics": {},
        "explanation": explanation_dict,  # <-- Member B: SHAP dictionary drops here
        "recommendation": recommendation,
        "model_version": "fair_model" if request.apply_mitigation and f"fair_{domain}" in MODELS else MODEL_BUNDLE.get("version", "v1"),
        "mitigation_applied": request.apply_mitigation and f"fair_{domain}" in MODELS
    }

@app.get("/v1/fairness_report")
async def get_fairness_report():
    """Returns the full before/after fairness metrics report."""
    report_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "mitigation_report.json")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Fairness report not found. Run python_mitigation.py first.")
    
    import json
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/Cloud Run deployment."""
    return {"status": "healthy", "models_loaded": len(MODELS) > 0, "available_domains": list(MODELS.keys())}
