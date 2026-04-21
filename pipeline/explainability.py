"""
pipeline/explainability.py
Single-row SHAP explanation for FastAPI /v1/audit endpoint.
Extracted and adapted from shap_llm_explainer.py.
"""

import shap
import numpy as np
import pandas as pd

# Features that should not legally influence loan decisions
PROTECTED_ATTRIBUTES = ["CODE_GENDER_M", "AGE"]


def get_shap_explanation(bundle: dict, X_input: pd.DataFrame, top_n: int = 5) -> dict:
    """
    Generates SHAP-based feature explanations for a single applicant row.
    Sliced to top_n features to maintain <500ms API latency SLA.

    Positive SHAP value → feature pushes toward DEFAULT (higher risk)
    Negative SHAP value → feature pushes toward REPAYMENT (lower risk)

    Args:
        bundle  : model bundle dict with keys 'model', 'training_columns', 'income_bins'
        X_input : single-row DataFrame already preprocessed by preprocess_data()
        top_n   : number of top features to return (default 5)

    Returns:
        dict with 'top_features' list and 'base_value'
    """
    model            = bundle["model"]
    training_columns = bundle["training_columns"]

    # Align input exactly to training column order — fill any missing with 0
    X_aligned = X_input.reindex(columns=training_columns, fill_value=0)

    # TreeExplainer is specifically optimised for XGBoost
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(X_aligned)

    # Fix for SHAP 0.51+ — expected_value returned as numpy array not scalar
    ev       = explainer.expected_value
    base_val = ev.item() if hasattr(ev, "item") else float(ev)

    # For a single row, shap_vals is shape (1, n_features) — take row 0
    shap_row = shap_vals[0] if shap_vals.ndim > 1 else shap_vals

    # Sort by absolute contribution, take top N
    shap_pairs  = list(zip(training_columns, shap_row))
    shap_sorted = sorted(shap_pairs, key=lambda x: abs(x[1]), reverse=True)
    top_feats   = shap_sorted[:top_n]

    return {
        "top_features": [
            {
                "feature":      feat,
                "shap_value":   round(float(val), 4),
                "direction":    "increases default risk" if val > 0 else "decreases default risk",
                "is_protected": feat in PROTECTED_ATTRIBUTES
            }
            for feat, val in top_feats
        ],
        "base_value": round(base_val, 4)
    }
