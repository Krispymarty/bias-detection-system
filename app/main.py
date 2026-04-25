from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator
from typing import Dict, Any, Optional
import os
import joblib
import logging
import pandas as pd
import time
import sys
import json
import ast

# Ensure the parent directory is in the Python path so pipeline can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.model import predict, preprocess_data
from pipeline.explainability import get_shap_explanation


# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage()
        }
        try:
            parsed_msg = ast.literal_eval(record.getMessage())
            if isinstance(parsed_msg, dict):
                log_record.update(parsed_msg)
                del log_record["message"]
        except Exception:
            pass
        return json.dumps(log_record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_path = os.path.join(os.path.dirname(__file__), "..", "logs", "api_audit.jsonl")
os.makedirs(os.path.dirname(log_path), exist_ok=True)
file_handler = logging.FileHandler(log_path)
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)
logger.propagate = False


# ---------------------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# PHASE 4 — HUMAN-FRIENDLY 422 ERROR HANDLER
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Replace cryptic Pydantic errors with clear, frontend-friendly messages."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid input format",
            "details": exc.errors(),
            "fix": "Check /docs for correct schema and data types. Also see /v1/example for a working payload."
        }
    )


# ---------------------------------------------------------------------------
# MODEL REGISTRY  (populated at startup)
# ---------------------------------------------------------------------------

MODELS: Dict[str, Any] = {}
FAIRNESS_REPORT: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# STARTUP
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def load_model_bundle():
    """Load the ML model bundles into memory at startup."""
    global MODELS, FAIRNESS_REPORT

    lending_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "production_model_v1.joblib")
    try:
        MODELS["lending"] = joblib.load(lending_path)
        logger.info("Lending model bundle loaded successfully.")

        fair_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "fair_model.joblib")
        if os.path.exists(fair_path):
            MODELS["fair_lending"] = joblib.load(fair_path)
            logger.info("Fair model bundle loaded successfully.")

        hiring_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "production_model_hiring.joblib")
        if os.path.exists(hiring_path):
            MODELS["hiring"] = joblib.load(hiring_path)
            logger.info("Hiring model bundle loaded successfully.")
        else:
            MODELS["hiring"] = MODELS.get("lending")
            logger.info("Hiring model not found, falling back to lending model.")

    except Exception as e:
        logger.error(f"Failed to load model bundle at startup: {e}")

    report_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "mitigation_report.json")
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                FAIRNESS_REPORT = json.load(f)
            logger.info("Fairness report loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load fairness report: {e}")


# ---------------------------------------------------------------------------
# PHASE 2 + 3 — STRICT + FORGIVING REQUEST SCHEMA
# ---------------------------------------------------------------------------

class FeatureSet(BaseModel):
    """
    Canonical input schema.
    Accepts gender as either:
      - CODE_GENDER_M: 0 or 1   (binary integer)
      - CODE_GENDER: "M" or "F" (human-readable string)
    All other fields are strictly validated.
    """

    # Gender — accept EITHER format; normalised by validator below
    CODE_GENDER_M: Optional[int] = Field(None, ge=0, le=1, description="Gender as binary: 1=Male, 0=Female")
    CODE_GENDER: Optional[str] = Field(None, description="Gender as string: 'M' or 'F'")

    # Core applicant fields
    AGE: int = Field(..., ge=18, le=100, description="Applicant age (18–100)")
    AMT_INCOME_TOTAL: float = Field(..., ge=0.0, description="Total annual income (≥ 0)")
    AMT_CREDIT: float = Field(..., ge=1000.0, le=10_000_000.0, description="Requested credit amount")
    AMT_ANNUITY: float = Field(..., ge=0.0, description="Monthly loan annuity (≥ 0)")
    NAME_EDUCATION_TYPE: str = Field(..., description="Highest education level")
    OCCUPATION_TYPE: str = Field(..., description="Applicant's occupation type")
    EXT_SOURCE_1: float = Field(..., ge=0.0, le=1.0, description="Normalised external score 1 (0–1)")
    EXT_SOURCE_2: float = Field(..., ge=0.0, le=1.0, description="Normalised external score 2 (0–1)")
    EXT_SOURCE_3: float = Field(..., ge=0.0, le=1.0, description="Normalised external score 3 (0–1)")
    INCOME_GROUP: str = Field(..., description="Categorical income group (Low / Medium / High)")

    @model_validator(mode="before")
    @classmethod
    def normalize_inputs(cls, values: dict) -> dict:
        """
        Phase 1.2 / Phase 3: Accept messy real-world gender strings and
        derive CODE_GENDER_M safely.  Accepted inputs:
          'M', 'MALE', 'male'  → 1
          'F', 'FEMALE', 'female' → 0
          integer 0 / 1 via CODE_GENDER_M → kept as-is
        Never raises; always returns a usable dict.
        """
        try:
            cgm = values.get("CODE_GENDER_M")
            cg = values.get("CODE_GENDER")

            if cgm is None:
                if isinstance(cg, str):
                    # Accept 'M', 'male', 'MALE', 'F', 'female', 'FEMALE'
                    normalised = cg.strip().upper()
                    values["CODE_GENDER_M"] = 1 if normalised in ("M", "MALE") else 0
                elif isinstance(cg, (int, float)):
                    values["CODE_GENDER_M"] = int(cg)
                else:
                    values["CODE_GENDER_M"] = 0  # safe default → Female

            # Keep CODE_GENDER in sync so downstream pops work cleanly
            if values.get("CODE_GENDER") is None and values.get("CODE_GENDER_M") is not None:
                values["CODE_GENDER"] = "M" if int(values["CODE_GENDER_M"]) == 1 else "F"
        except Exception:
            # Absolute last resort — never crash schema validation
            values.setdefault("CODE_GENDER_M", 0)

        return values


class AuditRequest(BaseModel):
    domain: str
    features: FeatureSet
    apply_mitigation: bool = False


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

# Phase 1.1 — Safe INCOME_GROUP normalizer (case-insensitive, never crashes)
_INCOME_GROUP_MAP = {"low": "Low", "medium": "Medium", "high": "High"}

def _normalize_income_group(val: Any) -> str:
    """Normalise free-text income group to canonical casing. Defaults to 'Medium'."""
    try:
        return _INCOME_GROUP_MAP.get(str(val).strip().lower(), "Medium")
    except Exception:
        return "Medium"


def _build_sensitive_group_safe(raw_features: dict) -> str:
    """Build the Fairlearn sensitive-group string safely."""
    gender_val = "Male" if raw_features.get("CODE_GENDER_M") == 1 else "Female"
    age_val = "Older" if raw_features.get("AGE", 0) > 40 else "Younger"
    income_val = raw_features.get("INCOME_GROUP", "Low")
    return f"{gender_val}_{age_val}_{income_val}"


def _extract_raw_features(request: AuditRequest) -> dict:
    """
    Convert validated FeatureSet → plain dict with CODE_GENDER_M (int).
    Drops CODE_GENDER string form and applies safe income normalisation.
    """
    raw = request.features.model_dump()
    raw.pop("CODE_GENDER", None)                         # remove string form
    raw["CODE_GENDER_M"] = int(raw.get("CODE_GENDER_M") or 0)
    # Phase 1.1: normalise INCOME_GROUP so 'medium', 'MEDIUM', etc. all work
    try:
        raw["INCOME_GROUP"] = _normalize_income_group(raw.get("INCOME_GROUP", "Medium"))
    except Exception:
        pass
    return raw


def generate_counterfactual_recommendation(model_bundle: Dict[str, Any], X_raw: pd.DataFrame, pred_val: int) -> str:
    """Generates simple perturbation-based recommendations to flip a rejection."""
    if pred_val != 1:
        return "Application approved. No further action needed."
    try:
        X_cf1 = X_raw.copy()
        X_cf1["AMT_INCOME_TOTAL"] *= 1.2
        if predict(model_bundle, X_cf1)[0] == 0:
            return "Increasing declared income by 20% may flip the decision to Approved."

        X_cf2 = X_raw.copy()
        X_cf2["AMT_CREDIT"] *= 0.8
        if predict(model_bundle, X_cf2)[0] == 0:
            return "Reducing the requested credit amount by 20% may flip the decision to Approved."

        X_cf3 = X_raw.copy()
        X_cf3["AMT_INCOME_TOTAL"] *= 1.2
        X_cf3["AMT_CREDIT"] *= 0.8
        if predict(model_bundle, X_cf3)[0] == 0:
            return "A combination of a 20% higher income and a 20% lower credit request may improve the outcome."

        return "No simple adjustments (income or credit size) were found to immediately flip this outcome."
    except Exception as e:
        logger.warning(f"Counterfactual generation failed: {e}")
        return "Could not generate recommendation at this time."


# ---------------------------------------------------------------------------
# HEALTH / ROOT
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    """Health check for Docker / Cloud Run."""
    return {
        "status": "healthy",
        "models_loaded": len(MODELS) > 0,
        "available_domains": list(MODELS.keys())
    }


# ---------------------------------------------------------------------------
# PHASE 7 — SELF-DOCUMENTATION ENDPOINT
# ---------------------------------------------------------------------------

@app.get("/v1/example")
def example_payload():
    """
    Returns multiple named example payloads.
    Frontend teams should copy one of these — never guess the schema.
    Includes an edge-case example with messy casing to demonstrate normalization.
    """
    _base = {
        "domain": "lending",
        "apply_mitigation": False,
    }
    return {
        "_note": (
            "CODE_GENDER accepts 'M'/'F'/'male'/'female' OR CODE_GENDER_M: 0/1. "
            "INCOME_GROUP accepts 'low'/'medium'/'high' (any casing). "
            "See /docs for full schema."
        ),
        "examples": [
            {
                "name": "Standard Female Applicant",
                "payload": {
                    **_base,
                    "features": {
                        "CODE_GENDER": "F",
                        "AGE": 42,
                        "AMT_INCOME_TOTAL": 90000.0,
                        "AMT_CREDIT": 180000.0,
                        "AMT_ANNUITY": 9000.0,
                        "NAME_EDUCATION_TYPE": "Secondary / secondary special",
                        "OCCUPATION_TYPE": "Laborers",
                        "EXT_SOURCE_1": 0.50,
                        "EXT_SOURCE_2": 0.60,
                        "EXT_SOURCE_3": 0.55,
                        "INCOME_GROUP": "Low"
                    }
                }
            },
            {
                "name": "Standard Male Applicant",
                "payload": {
                    **_base,
                    "features": {
                        "CODE_GENDER": "M",
                        "AGE": 35,
                        "AMT_INCOME_TOTAL": 150000.0,
                        "AMT_CREDIT": 250000.0,
                        "AMT_ANNUITY": 12000.0,
                        "NAME_EDUCATION_TYPE": "Higher education",
                        "OCCUPATION_TYPE": "Laborers",
                        "EXT_SOURCE_1": 0.65,
                        "EXT_SOURCE_2": 0.55,
                        "EXT_SOURCE_3": 0.70,
                        "INCOME_GROUP": "Medium"
                    }
                }
            },
            {
                "name": "Edge Case — messy casing (auto-normalised)",
                "payload": {
                    **_base,
                    "features": {
                        "CODE_GENDER": "female",
                        "AGE": 25,
                        "AMT_INCOME_TOTAL": 45000.0,
                        "AMT_CREDIT": 80000.0,
                        "AMT_ANNUITY": 5000.0,
                        "NAME_EDUCATION_TYPE": "Incomplete higher",
                        "OCCUPATION_TYPE": "Laborers",
                        "EXT_SOURCE_1": 0.30,
                        "EXT_SOURCE_2": 0.40,
                        "EXT_SOURCE_3": 0.35,
                        "INCOME_GROUP": "medium"
                    }
                }
            }
        ]
    }


# ---------------------------------------------------------------------------
# MAIN AUDIT ENDPOINT  /v1/audit
# ---------------------------------------------------------------------------

@app.post("/v1/audit")
async def run_pipeline(request: AuditRequest):
    """
    Main orchestration endpoint for model inference, fairness auditing, and SHAP explainability.
    """
    start_time = time.time()
    logger.info(f"Received audit request for domain: {request.domain}")
    domain = request.domain.lower()

    # --- MODEL RESOLUTION ---
    if domain not in MODELS:
        logger.error(f"Domain '{domain}' requested but not loaded.")
        raise HTTPException(status_code=400, detail=f"Model for domain '{domain}' is not available.")
    MODEL_BUNDLE = MODELS[domain]

    # --- FEATURE EXTRACTION ---
    raw_features = _extract_raw_features(request)

    try:
        X_raw = pd.DataFrame([raw_features])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to convert features to DataFrame: {e}")

    # --- INFERENCE ---
    try:
        if request.apply_mitigation and f"fair_{domain}" in MODELS:
            logger.info(f"Applying Fairlearn mitigation for domain: {domain}")
            FAIR_BUNDLE = MODELS[f"fair_{domain}"]
            fair_model = FAIR_BUNDLE["fair_model"]

            X_processed, _, _ = preprocess_data(
                X_raw,
                training_columns=FAIR_BUNDLE.get("training_columns"),
                income_bins=FAIR_BUNDLE.get("income_bins")
            )

            sensitive = pd.Series([_build_sensitive_group_safe(raw_features)])
            pred_val = int(fair_model.predict(X_processed, sensitive_features=sensitive)[0])
            try:
                prob_val = float(fair_model.predict_proba(X_processed, sensitive_features=sensitive)[0][1])
            except Exception:
                prob_val = float(predict(MODEL_BUNDLE, X_raw)[1])

            prediction_str = "Rejected" if pred_val == 1 else "Approved"
            logger.info(f"Fair inference complete. Prediction: {prediction_str}, Probability: {prob_val:.4f}")
        else:
            pred_val, prob_val = predict(MODEL_BUNDLE, X_raw)
            prediction_str = "Rejected" if pred_val == 1 else "Approved"
            logger.info(f"Inference complete. Prediction: {prediction_str}, Probability: {float(prob_val):.4f}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise HTTPException(status_code=500, detail="Inference failed during preprocessing/prediction.")

    # --- COUNTERFACTUAL ---
    probability = round(float(prob_val), 4)
    confidence = "High" if probability > 0.8 else "Medium" if probability > 0.6 else "Low"

    logger.info(str({
        "event": "inference_completed",
        "domain": domain,
        "prediction": prediction_str,
        "probability": probability,
        "confidence": confidence,
        "threshold": round(float(MODEL_BUNDLE.get("optimal_threshold", 0.5)), 4),
        "model_version": MODEL_BUNDLE.get("version", "v1")
    }))

    recommendation = (
        generate_counterfactual_recommendation(MODEL_BUNDLE, X_raw, pred_val)
        if prediction_str == "Rejected"
        else "Application approved. No further action needed."
    )

    latency_ms = round((time.time() - start_time) * 1000, 2)
    if latency_ms > 500:
        logger.warning(f"Audit request took {latency_ms:.2f}ms (EXCEEDS 500ms SLA!)")
    else:
        logger.info(f"Audit request completed in {latency_ms:.2f}ms")

    # --- SHAP EXPLANATION ---
    explanation_dict = {}
    sensitive_feature_alert = False
    flagged_features = []
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
        PROTECTED_ATTRIBUTES = ["CODE_GENDER_M", "AGE"]
        for item in raw_explanation["top_features"]:
            if item["feature"] in PROTECTED_ATTRIBUTES and abs(item["shap_value"]) > 0.1:
                sensitive_feature_alert = True
                flagged_features.append(item["feature"])
    except Exception as e:
        logger.error(f"Error generating SHAP explanation: {e}")

    # --- FAIRNESS METRICS ---
    model_type_key = "fair_model" if request.apply_mitigation and f"fair_{domain}" in MODELS else "baseline_model"
    bias_metrics = {}
    fairness_score = 0.0
    bias_source = "Unknown"
    fairness_badge = "🔴 Risky"

    if FAIRNESS_REPORT:
        baseline_gap = FAIRNESS_REPORT.get("baseline_model", {}).get("selection_rate_gap", 1.0)
        fair_gap = FAIRNESS_REPORT.get("fair_model", {}).get("selection_rate_gap", 1.0)

        if model_type_key in FAIRNESS_REPORT:
            metrics = FAIRNESS_REPORT[model_type_key]
            bias_metrics = {
                "selection_rate_gap": metrics.get("selection_rate_gap", 0),
                "tpr_gap": metrics.get("tpr_gap", 0),
                "fpr_gap": metrics.get("fpr_gap", 0),
                "fnr_gap": metrics.get("fnr_gap", 0)
            }
            fairness_score = round((1.0 - metrics.get("selection_rate_gap", 0)) * 100, 1)

        if abs(baseline_gap - fair_gap) < 0.02:
            bias_source = "Historical Data Bias"
        else:
            bias_source = "Model Bias (Mitigated)" if request.apply_mitigation else "Model Bias (Detected)"

        if fairness_score > 85:
            fairness_badge = "🟢 Fair"
        elif fairness_score > 70:
            fairness_badge = "🟡 Moderate"
        else:
            fairness_badge = "🔴 Risky"

    # --- CONFIDENCE WARNING ---
    confidence_warning = None
    if 0.45 <= probability <= 0.55:
        confidence_warning = "⚠ Low confidence decision — human review recommended"

    # --- PHASE 2: DEBUG LAYER — gated by DEBUG_MODE env var, never crashes ---
    debug_info: Optional[Dict[str, Any]] = None
    if os.getenv("DEBUG_MODE", "false").lower() == "true":
        try:
            debug_info = {
                "input_validated": True,
                "sensitive_group": _build_sensitive_group_safe(raw_features),
                "gender_resolved": raw_features.get("CODE_GENDER_M"),
                "income_group_resolved": raw_features.get("INCOME_GROUP")
            }
        except Exception as de:
            logger.warning(f"Debug layer failed silently: {de}")
            debug_info = {"input_validated": True, "debug_error": "Could not build debug info"}

    return {
        "prediction": prediction_str,
        "probability": probability,
        "recommendation": recommendation,

        "fairness": {
            "score": fairness_score,
            "badge": fairness_badge,
            "bias_source": bias_source,
            "bias_metrics": bias_metrics,
            "sensitive_feature_alert": sensitive_feature_alert,
            "flagged_features": flagged_features
        },

        "explanation": explanation_dict,

        "governance": {
            "confidence": confidence,
            "confidence_warning": confidence_warning,
            "threshold": round(float(MODEL_BUNDLE.get("optimal_threshold", 0.5)), 4),
            "model_version": "fair_model" if request.apply_mitigation and f"fair_{domain}" in MODELS else MODEL_BUNDLE.get("version", "v1"),
            "mitigation_applied": request.apply_mitigation and f"fair_{domain}" in MODELS
        },

        "system": {
            "latency_ms": latency_ms,
            "domain": domain
        },

        # debug is None when DEBUG_MODE is off — omitted cleanly from JSON
        **(({"debug": debug_info}) if debug_info is not None else {})
    }


# ---------------------------------------------------------------------------
# COMPARE ENDPOINT  /v1/audit/compare
# ---------------------------------------------------------------------------

@app.post("/v1/audit/compare")
async def compare_audit(request: AuditRequest):
    """
    Runs the same applicant through BOTH the baseline (biased) and fair (mitigated)
    models, returning a side-by-side comparison. This is the 'wow moment' endpoint.
    """
    start_time = time.time()
    domain = request.domain.lower()

    if domain not in MODELS:
        raise HTTPException(status_code=400, detail=f"Model for domain '{domain}' is not available.")
    MODEL_BUNDLE = MODELS[domain]

    if f"fair_{domain}" not in MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Fair model for domain '{domain}' is not available. Run mitigation first."
        )

    FAIR_BUNDLE = MODELS[f"fair_{domain}"]
    raw_features = _extract_raw_features(request)

    try:
        X_raw = pd.DataFrame([raw_features])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to convert features: {e}")

    # --- BASELINE PREDICTION ---
    try:
        base_pred, base_prob = predict(MODEL_BUNDLE, X_raw)
        base_prediction_str = "Rejected" if base_pred == 1 else "Approved"
        base_prob = round(float(base_prob), 4)
    except Exception as e:
        logger.error(f"Baseline inference failed: {e}")
        raise HTTPException(status_code=500, detail="Baseline inference failed.")

    # --- FAIR PREDICTION ---
    try:
        fair_model = FAIR_BUNDLE["fair_model"]
        X_processed, _, _ = preprocess_data(
            X_raw,
            training_columns=FAIR_BUNDLE.get("training_columns"),
            income_bins=FAIR_BUNDLE.get("income_bins")
        )
        sensitive = pd.Series([_build_sensitive_group_safe(raw_features)])
        fair_pred = int(fair_model.predict(X_processed, sensitive_features=sensitive)[0])
        try:
            fair_prob = float(fair_model.predict_proba(X_processed, sensitive_features=sensitive)[0][1])
        except Exception:
            fair_prob = base_prob
        fair_prediction_str = "Rejected" if fair_pred == 1 else "Approved"
        fair_prob = round(fair_prob, 4)
    except Exception as e:
        logger.error(f"Fair inference failed: {e}")
        raise HTTPException(status_code=500, detail="Fair inference failed.")

    # --- FAIRNESS SCORES ---
    base_fairness = 0.0
    fair_fairness = 0.0
    if FAIRNESS_REPORT:
        base_gap = FAIRNESS_REPORT.get("baseline_model", {}).get("selection_rate_gap", 1.0)
        fair_gap = FAIRNESS_REPORT.get("fair_model", {}).get("selection_rate_gap", 1.0)
        base_fairness = round((1.0 - base_gap) * 100, 1)
        fair_fairness = round((1.0 - fair_gap) * 100, 1)

    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "baseline": {
            "prediction": base_prediction_str,
            "probability": base_prob,
            "fairness_score": base_fairness,
            "model_version": MODEL_BUNDLE.get("version", "v1")
        },
        "mitigated": {
            "prediction": fair_prediction_str,
            "probability": fair_prob,
            "fairness_score": fair_fairness,
            "model_version": "fair_model"
        },
        "improvement": {
            "fairness_gain": round(fair_fairness - base_fairness, 1),
            "decision_changed": base_prediction_str != fair_prediction_str
        },
        "system": {
            "latency_ms": latency_ms,
            "domain": domain
        }
    }


# ---------------------------------------------------------------------------
# FAIRNESS REPORT ENDPOINT
# ---------------------------------------------------------------------------

@app.get("/v1/fairness_report")
async def get_fairness_report():
    """Returns the full before/after fairness metrics report."""
    report_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "mitigation_report.json")
    if not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail="Fairness report not found. Run python_mitigation.py first."
        )
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)
