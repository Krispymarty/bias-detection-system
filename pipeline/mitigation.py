"""
pipeline/mitigation.py

PURPOSE: FastAPI module — loads the pre-trained fair_model.joblib
         (produced by running standalone mitigation.py once) and
         exposes prediction functions for the /v1/audit endpoint.

DO NOT RUN THIS DIRECTLY.
Run standalone mitigation.py first to generate outputs/fair_model.joblib.
Then FastAPI imports this module and calls predict_mitigated() per request.
"""

import os
import joblib
import numpy  as np
import pandas as pd

# Path to the fair model saved by standalone mitigation.py
FAIR_MODEL_PATH = "outputs/fair_model.joblib"


def load_fair_model() -> dict:
    """
    Loads the ThresholdOptimizer bundle saved by standalone mitigation.py.

    Returns:
        dict with keys 'fair_model' and 'training_columns'
        Returns None with warning if file doesn't exist yet.

    Called once at FastAPI startup in app/main.py:
        fair_bundle = load_fair_model()
    """
    if not os.path.exists(FAIR_MODEL_PATH):
        print(
            f"[mitigation] WARNING: {FAIR_MODEL_PATH} not found.\n"
            f"Run standalone mitigation.py first to generate it.\n"
            f"Command: python mitigation.py"
        )
        return None

    bundle = joblib.load(FAIR_MODEL_PATH)
    print(f"[mitigation] Fair model loaded OK from {FAIR_MODEL_PATH}")
    return bundle


def predict_mitigated(fair_bundle: dict,
                       X_input: pd.DataFrame,
                       gender_value: int) -> dict:
    """
    Run inference through the fairness-corrected ThresholdOptimizer model.

    How it works:
        ThresholdOptimizer does NOT retrain the model. It applies a
        DIFFERENT decision threshold per gender group so that True
        Positive Rate and False Positive Rate are equal across genders
        (EqualizedOdds constraint). This is the fair version of prediction.

    Args:
        fair_bundle  : bundle loaded by load_fair_model()
                       must have keys 'fair_model', 'training_columns'
        X_input      : preprocessed feature DataFrame
                       (same columns as the biased model expects)
        gender_value : int — 0 = Female, 1 = Male
                       (taken directly from the API request body)

    Returns:
        dict with keys:
            prediction  : 0 (approve) or 1 (reject)
            probability : float 0.0-1.0 or None if not available
            decision    : "APPROVED" or "REJECTED"
            model_type  : "fair"
            constraint  : "equalized_odds"
    """
    fair_model       = fair_bundle["fair_model"]       # ThresholdOptimizer object
    training_columns = fair_bundle["training_columns"]

    # Align input columns to exact training order
    X_aligned = X_input.reindex(columns=training_columns, fill_value=0)

    # ThresholdOptimizer was trained with string labels "Male"/"Female"
    # (see standalone mitigation.py line: .map({0: "Female", 1: "Male"}))
    # We must pass the same string format here
    gender_label = "Male" if gender_value == 1 else "Female"
    sensitive    = pd.Series([gender_label])

    # Get fair prediction
    prediction = int(fair_model.predict(X_aligned, sensitive_features=sensitive)[0])

    # Try to get probability — ThresholdOptimizer sometimes doesn't support this
    try:
        probability = float(
            fair_model.predict_proba(
                X_aligned, sensitive_features=sensitive
            )[0][1]
        )
    except Exception:
        # If predict_proba not available, return None
        # app/main.py will fall back to biased model's probability
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
    Compares Demographic Parity Difference before and after mitigation.

    Used by test_bias.py to verify the improvement.
    Note: The full report is already in outputs/mitigation_report.json
    from the standalone script — use that for presentation numbers.

    Args:
        y_test          : true labels from test set
        pred_original   : predictions from the original biased model
        pred_mitigated  : predictions from the fair ThresholdOptimizer
        sensitive_test  : Series of gender values for the test rows

    Returns:
        dict showing DPD before, after, and % improvement
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