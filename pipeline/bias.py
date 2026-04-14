import pandas as pd
from typing import Dict, Any

def evaluate_bias(y_true: pd.Series, y_pred: pd.Series, sensitive_features: pd.Series) -> Dict[str, float]:
    """
    Evaluates fairness metrics using Fairlearn.
    
    Args:
        y_true (pd.Series): Actual target labels.
        y_pred (pd.Series): Predicted labels (0 or 1).
        sensitive_features (pd.Series): The sensitive feature column (e.g., CODE_GENDER).
        
    Returns:
        dict: A structured dictionary with fairness metrics.
    """
    # Import locally to avoid crashing if fairlearn isn't installed yet
    from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference
    
    # Calculate Demographic Parity Difference
    # It measures if the selection rate (e.g., getting a loan) is equal across groups.
    dp_diff = demographic_parity_difference(
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_features
    )
    
    # Calculate Equalized Odds Difference
    # It measures if True Positive Rates and False Positive Rates are equal across groups.
    eo_diff = equalized_odds_difference(
        y_true=y_true,
        y_pred=y_pred,
        sensitive_features=sensitive_features
    )
    
    return {
        "demographic_parity_difference": float(dp_diff),
        "equalized_odds_difference": float(eo_diff)
    }

def run_bias_audit(model_bundle: Dict[str, Any], X_test_raw: pd.DataFrame, y_test: pd.Series, sensitive_col: str = "CODE_GENDER_M") -> Dict[str, Any]:
    """
    Wrapper to easily audit a trained model.
    Pass raw data to extract accurate sensitive attributes before preprocessing wipes them out (e.g., converting 'F'/'M' to 1s and 0s).
    """
    from pipeline.model import predict
    
    if sensitive_col not in X_test_raw.columns:
        raise ValueError(f"Sensitive feature '{sensitive_col}' missing from the test data. Cannot audit bias.")
        
    # Isolate exact sensitive attributes directly from RAW data dynamically
    sensitive_features = X_test_raw[sensitive_col]
    
    # Run the standard production inference to get predicted labels
    predictions, probabilities = predict(model_bundle, X_test_raw)
    
    # Convert predictions to pd.Series for fairlearn
    y_pred_series = pd.Series(predictions, index=y_test.index)
    
    # Output structured dictionary exactly as requested
    bias_metrics = evaluate_bias(y_test, y_pred_series, sensitive_features)
    
    return bias_metrics
