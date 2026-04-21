"""
pipeline/mitigation.py
Loads the pre-trained fair_model.joblib (produced by standalone mitigation.py)
and exposes prediction functions for the FastAPI /v1/audit endpoint.
"""

import joblib
import os
import numpy  as np
import pandas as pd


# Path to the fair model saved by standalone mitigation.py
FAIR_MODEL_PATH = "outputs/fair_model.joblib"


def load_fair_model():
    """
    Loads the ThresholdOptimizer bundle saved by mitigation.py.
    Returns None with a warning if file doesn't exist yet.
    """
    if not os.path.exists(FAIR_MODEL_PATH):
        print(f"[mitigation] WARNING: {FAIR_MODEL_PATH} not found. "
              f"Run standalone mitigation.py first to generate it.")
        return None
    bundle = joblib.load(FAIR_MODEL_PATH)
    print(f"[mitigation] Fair model loaded from {FAIR_MODEL_PATH}")
    return bundle


def predict_mitigated(fair_bundle: dict,
                       X_input: pd.DataFrame,
                       gender_value: int) -> dict:
    """
    Run inference through the fairness-corrected ThresholdOptimizer model.

    Args:
        fair_bundle  : bundle loaded by load_fair_model()
        X_input      : preprocessed feature DataFrame (same columns as biased model)
        gender_value : 0 = Female, 1 = Male (from the API request)

    Returns:
        dict with prediction, probability, and constraint info
    """
    fair_model       = fair_bundle["fair_model"]        # ThresholdOptimizer
    training_columns = fair_bundle["training_columns"]

    # Align columns
    X_aligned = X_input.reindex(columns=training_columns, fill_value=0)

    # ThresholdOptimizer needs gender label as string — same as how it was trained
    gender_label = "Male" if gender_value == 1 else "Female"
    sensitive    = pd.Series([gender_label])

    prediction = int(fair_model.predict(X_aligned, sensitive_features=sensitive)[0])

    # Try to get probability — ThresholdOptimizer may not support predict_proba
    try:
        probability = float(
            fair_model.predict_proba(X_aligned, sensitive_features=sensitive)[0][1]
        )
    except Exception:
        # Fallback: use the original biased model's probability as reference
        probability = None

    return {
        "prediction":  prediction,
        "probability": probability,
        "decision":    "REJECTED" if prediction == 1 else "APPROVED",
        "model_type":  "fair",
        "constraint":  "equalized_odds"
    }


def compare_bias_before_after(y_test,
                               pred_original: np.ndarray,
                               pred_mitigated: np.ndarray,
                               sensitive_test: pd.Series) -> dict:
    """
    Returns DPD before/after mitigation. Used by test_bias.py to
    verify improvement. Numbers come from mitigation_report.json
    if you want to avoid recomputing.
    """
    from fairlearn.metrics import demographic_parity_difference

    dpd_before  = demographic_parity_difference(
        y_test, pred_original,  sensitive_features=sensitive_test
    )
    dpd_after   = demographic_parity_difference(
        y_test, pred_mitigated, sensitive_features=sensitive_test
    )
    improvement = (abs(dpd_before) - abs(dpd_after)) / abs(dpd_before) * 100

    return {
        "dpd_before_mitigation": round(float(dpd_before), 4),
        "dpd_after_mitigation":  round(float(dpd_after), 4),
        "improvement_pct":       round(improvement, 2)
    }
