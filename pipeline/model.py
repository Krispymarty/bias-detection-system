import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from typing import Tuple, List, Union, Any, Dict

# Selected features critical for fairness auditing and UI what-if simulators
SELECTED_FEATURES = [
    "CODE_GENDER_M",
    "AGE",
    "INCOME_GROUP",
    "OCCUPATION_TYPE",
    "NAME_EDUCATION_TYPE",
    "AMT_INCOME_TOTAL",  # Kept as requested, though INCOME_GROUP also exists 
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3"
]

def preprocess_data(X_raw: pd.DataFrame, training_columns: List[str] = None, income_bins: np.ndarray = None) -> Tuple[pd.DataFrame, List[str], np.ndarray]:
    """
    Preprocesses the data by engineering features, filling missing values, and one-hot encoding.
    Ensures that prediction data exactly matches training data structure.
    
    Args:
        X_raw (pd.DataFrame): Raw input data.
        training_columns (List[str], optional): Columns expected by the trained model.
        income_bins (np.ndarray, optional): Bin edges for INCOME_GROUP categorization.
        
    Returns:
        Tuple containing preprocessed DataFrame, final column list, and income bins.
    """
    X = X_raw.copy()
    
    # --- 1. FEATURE ENGINEERING ---
    # Convert DAYS_BIRTH to AGE
    if "DAYS_BIRTH" in X.columns:
        X["AGE"] = (-X["DAYS_BIRTH"]) // 365
        
    # Convert AMT_INCOME_TOTAL to INCOME_GROUP (using dynamic bucketing)
    if "AMT_INCOME_TOTAL" in X.columns:
        if income_bins is None:
            # Training phase: Calculate quantiles securely
            _, edges = pd.qcut(X["AMT_INCOME_TOTAL"], q=3, retbins=True, duplicates='drop')
            # Protect against extreme values in inference
            edges[0] = -np.inf
            edges[-1] = np.inf
            income_bins = edges
        
        # Apply strict bins for both train and inference
        X["INCOME_GROUP"] = pd.cut(X["AMT_INCOME_TOTAL"], bins=income_bins, labels=["Low", "Medium", "High"])
        
    # --- 2. SELECT FEATURES ---
    features_to_use = [f for f in SELECTED_FEATURES if f in X.columns]
    X_processed = X[features_to_use].copy()
    
    # --- 3. ENCODE CATEGORICALS ---
    # SUGGESTION 1: Mathematical Strictness. Ensure UI Strings perfectly map to numerical labels 
    # instead of depending on pandas fallback dummy logic that fills unknown strings with 0.
    if "OCCUPATION_TYPE" in X_processed.columns and pd.api.types.is_string_dtype(X_processed["OCCUPATION_TYPE"]):
        OCCUPATION_MAP = {
        "Accountants":          0.0,
        "Cleaning staff":       1.0,
        "Cooking staff":        2.0,
        "Core staff":           3.0,
        "Drivers":              4.0,
        "HR staff":             5.0,
        "High skill tech staff":6.0,
        "IT staff":             7.0,
        "Laborers":             8.0,
        "Low-skill Laborers":   9.0,
        "Managers":             10.0,
        "Medicine staff":       11.0,
        "Private service staff":12.0,
        "Realty agents":        13.0,
        "Sales staff":          14.0,
        "Secretaries":          15.0,
        "Security staff":       16.0,
        "Waiters/barmen staff": 17.0
        }
        X_processed["OCCUPATION_TYPE"] = X_processed["OCCUPATION_TYPE"].map(OCCUPATION_MAP).fillna(0.0)
        
    X_processed = pd.get_dummies(X_processed, drop_first=True)
    
    # --- 4. HANDLE MISSING VALUES ---
    # Median imputation for simplicity (ensuring it's numeric only)
    X_processed = X_processed.fillna(X_processed.median(numeric_only=True))
    
    # --- 5. ALIGN COLUMNS (CRITICAL FOR INFERENCE) ---
    if training_columns is not None:
        # Add missing columns with 0
        missing_cols = set(training_columns) - set(X_processed.columns)
        for c in missing_cols:
            X_processed[c] = 0
            
        # Keep only the training columns in exact order
        X_processed = X_processed[training_columns]
    else:
        # If no training_columns provided, we are training. Capture the final columns.
        training_columns = X_processed.columns.tolist()
        
    return X_processed, training_columns, income_bins


def train_model(X_train_raw: pd.DataFrame, y_train: pd.Series, **kwargs) -> Dict[str, Any]:
    """
    Trains an XGBoost classifier and captures the exact preprocessing structure.
    
    Args:
        X_train_raw (pd.DataFrame): Raw training features.
        y_train (pd.Series): Training labels.
        **kwargs: Optional hyperparameters for XGBClassifier.
        
    Returns:
        Dict: A bundle containing the model and the training requirements.
    """
    # Preprocess and capture structural invariants
    X_train, training_columns, income_bins = preprocess_data(X_train_raw)
    
    # Calculate scale_pos_weight to handle class imbalance
    neg_cases = (y_train == 0).sum()
    pos_cases = (y_train == 1).sum()
    scale_pos_weight = neg_cases / pos_cases if pos_cases > 0 else 1.0

    model = XGBClassifier(
        n_estimators=kwargs.get("n_estimators", 100),
        max_depth=kwargs.get("max_depth", 6),
        learning_rate=kwargs.get("learning_rate", 0.1),
        subsample=kwargs.get("subsample", 0.8),
        colsample_bytree=kwargs.get("colsample_bytree", 0.8),
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric="logloss"
    )
    
    model.fit(X_train, y_train)
    
    # Return bundle required for safe frontend inference
    return {
        "model": model,
        "training_columns": training_columns,
        "income_bins": income_bins
    }

def save_model(model_bundle: Dict[str, Any], filepath: str) -> None:
    """Saves the trained model bundle to disk."""
    joblib.dump(model_bundle, filepath)

def load_model(filepath: str) -> Dict[str, Any]:
    """Loads a trained model bundle from disk."""
    return joblib.load(filepath)

def predict(model_bundle: Dict[str, Any], X_raw: pd.DataFrame) -> Union[Tuple[int, float], Tuple[List[int], List[float]]]:
    """
    Predicts the target and probability using the precise pre-captured structure.
    """
    model = model_bundle["model"]
    training_columns = model_bundle["training_columns"]
    income_bins = model_bundle.get("income_bins", None)
    
    # Force strict architectural compliance via preprocessor
    X_processed, _, _ = preprocess_data(
        X_raw, 
        training_columns=training_columns, 
        income_bins=income_bins
    )
    
    probabilities = model.predict_proba(X_processed)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    
    if len(X_processed) == 1:
        return int(predictions[0]), float(probabilities[0])
    
    return predictions.tolist(), probabilities.tolist()