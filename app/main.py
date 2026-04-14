from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import joblib

# Initialize FastAPI app
app = FastAPI(
    title="AI Fairness Auditor",
    description="Backend API for fairness evaluation, bias detection, and SHAP explainability.",
    version="1.0.0"
)

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
    lending_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "production_model.joblib")
    
    try:
        # Load the lending domain model
        MODELS["lending"] = joblib.load(lending_path)
        print("Lending model bundle loaded successfully.")
        
        # Space reserved for hiring domain model when Team B provides it
        # MODELS["hiring"] = joblib.load(...)
    except Exception as e:
        print(f"Error loading model bundle: {e}")

@app.post("/v1/audit")
async def run_pipeline(request: AuditRequest):
    """
    Main orchestration endpoint for model inference, fairness auditing, and explanations.
    """
    domain = request.domain.lower()
    if domain not in MODELS:
        raise HTTPException(status_code=400, detail=f"Model for domain '{domain}' is not available.")
    
    MODEL_BUNDLE = MODELS[domain]
    
    import pandas as pd
    from pipeline.model import predict
    
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
        pred_val, prob_val = predict(MODEL_BUNDLE, X_raw)
        
        # Output string based on default risk (1 = Reject/Default Risk, 0 = Approve/Safe)
        prediction_str = "Rejected" if pred_val == 1 else "Approved"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed during preprocessing/prediction: {e}")

    # --- STEP 5: COUNTERFACTUAL LOGIC (SIMPLE PERTURBATION) ---
    recommendation = ""
    if pred_val == 1:  # Only provide recommendations if Rejected
        try:
            # Try 1: Increase Income by 20%
            X_cf1 = X_raw.copy()
            X_cf1["AMT_INCOME_TOTAL"] *= 1.2
            if predict(MODEL_BUNDLE, X_cf1)[0] == 0:
                recommendation = "Increasing declared income by 20% may flip the decision to Approved."
            else:
                # Try 2: Reduce Credit by 20%
                X_cf2 = X_raw.copy()
                X_cf2["AMT_CREDIT"] *= 0.8
                if predict(MODEL_BUNDLE, X_cf2)[0] == 0:
                    recommendation = "Reducing the requested credit amount by 20% may flip the decision to Approved."
                else:
                    # Try 3: Both
                    X_cf3 = X_raw.copy()
                    X_cf3["AMT_INCOME_TOTAL"] *= 1.2
                    X_cf3["AMT_CREDIT"] *= 0.8
                    if predict(MODEL_BUNDLE, X_cf3)[0] == 0:
                        recommendation = "A combination of a 20% higher income and a 20% lower credit request may improve the outcome."
                    else:
                        recommendation = "No simple adjustments (income or credit size) were found to immediately flip this outcome."
        except Exception:
            recommendation = "Could not generate recommendation at this time."
    else:
        recommendation = "Application approved. No further action needed."

    # Placeholder for the actual JSON response
    # Member B Note: SHAP matrices are massive. Slice explanations to TOP 5 features ONLY 
    # to maintain our <500ms API latency requirement. Example: {"AGE": 0.15, "INCOME": -0.05}
    return {
        "prediction": prediction_str,
        "probability": round(float(prob_val), 4),
        "fairness_score": 0,
        "bias_metrics": {},
        "explanation": {},  # <-- SHAP dictionary drops here
        "recommendation": recommendation
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/Cloud Run deployment."""
    return {"status": "healthy", "models_loaded": len(MODELS) > 0, "available_domains": list(MODELS.keys())}
