import pandas as pd
import numpy as np
import joblib
import logging
import os
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV, train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve
from typing import Tuple, List, Union, Any, Dict, Optional

logger = logging.getLogger(__name__)

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

def preprocess_data(
    X_raw: pd.DataFrame, 
    training_columns: Optional[List[str]] = None, 
    income_bins: Optional[np.ndarray] = None
) -> Tuple[pd.DataFrame, List[str], np.ndarray]:
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
    logger.debug(f"Starting preprocessing for {len(X)} records.")
    
    # --- 1. FEATURE ENGINEERING ---
    # Convert DAYS_BIRTH to AGE
    if "DAYS_BIRTH" in X.columns:
        X["AGE"] = (-X["DAYS_BIRTH"]) // 365
        
    # Translate API string payload to expected CSV integer column securely
    if "CODE_GENDER" in X.columns:
        X["CODE_GENDER_M"] = (X["CODE_GENDER"] == "M").astype(float)
        X = X.drop(columns=["CODE_GENDER"])
        
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
        # Member B: Please expand this mapping dictionary based on final_merged_cleaned.csv labels!
        OCCUPATION_MAP = {"Laborers": 8.0} 
        X_processed["OCCUPATION_TYPE"] = X_processed["OCCUPATION_TYPE"].map(OCCUPATION_MAP).fillna(0.0)
        
    X_processed = pd.get_dummies(X_processed)
    
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
        logger.info(f"Captured {len(training_columns)} struct columns during training.")
        
    return X_processed, training_columns, income_bins


def train_model(X_train_raw: pd.DataFrame, y_train: pd.Series, **kwargs) -> Dict[str, Any]:
    """
    Trains an XGBoost and RF classifier using RandomizedSearchCV, selects the best, 
    and optimizes the threshold using the validation set.
    """
    # Preprocess and capture structural invariants
    X_train, training_columns, income_bins = preprocess_data(X_train_raw)
    
    # 1. Split a validation set specifically for early stopping & threshold tuning (prevent leakage)
    X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.15, stratify=y_train, random_state=42)
    
    # Calculate scale_pos_weight to handle class imbalance for XGBoost
    neg_cases = (y_tr == 0).sum()
    pos_cases = (y_tr == 1).sum()
    scale_pos_weight = neg_cases / pos_cases if pos_cases > 0 else 1.0

    # 2. StratifiedKFold for robust validation
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    
    # 3. XGBoost Tuning (with early_stopping_rounds in new XGB API)
    logger.info("Tuning XGBoost...")
    xgb_model = XGBClassifier(
        scale_pos_weight=scale_pos_weight, 
        eval_metric="logloss",
        early_stopping_rounds=10,
        random_state=42,
        n_jobs=-1
    )
    xgb_params = {
        "n_estimators": [100, 200, 300, 500],
        "max_depth": [4, 6, 8, 10],
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "subsample": [0.6, 0.8, 1.0],
        "colsample_bytree": [0.6, 0.8, 1.0],
        "min_child_weight": [1, 3, 5]
    }
    xgb_search = RandomizedSearchCV(xgb_model, xgb_params, n_iter=20, scoring="roc_auc", cv=skf, random_state=42, n_jobs=1)
    # Provide the external eval_set to fit() so the internal XGB estimators can use early stopping
    xgb_search.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
    
    # 4. Random Forest Tuning
    logger.info("Tuning Random Forest...")
    rf_model = RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1)
    rf_params = {
        "n_estimators": [100, 200],
        "max_depth": [6, 10, 15]
    }
    rf_search = RandomizedSearchCV(rf_model, rf_params, n_iter=4, scoring="roc_auc", cv=skf, random_state=42, n_jobs=1)
    rf_search.fit(X_tr, y_tr)
    
    logger.info(f"XGBoost Best CV AUC: {xgb_search.best_score_:.4f}")
    logger.info(f"Random Forest Best CV AUC: {rf_search.best_score_:.4f}")
    
    # 5. Select Best Model
    if xgb_search.best_score_ >= rf_search.best_score_:
        logger.info("XGBoost selected as the ultimate production model.")
        best_model = xgb_search.best_estimator_
        model_type = "xgboost"
        final_auc = xgb_search.best_score_
    else:
        logger.info("Random Forest selected as the ultimate production model.")
        best_model = rf_search.best_estimator_
        model_type = "random_forest"
        final_auc = rf_search.best_score_

    # 6. F1-based Threshold Optimization (on Validation set only)
    logger.info("Optimizing probability threshold using validation set...")
    y_val_prob = best_model.predict_proba(X_val)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_val, y_val_prob)
    
    # Calculate F1 score for each threshold, avoiding division by zero
    f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds[optimal_idx] if optimal_idx < len(thresholds) else 0.5
    
    logger.info(f"Optimal Validation F1 Score: {f1_scores[optimal_idx]:.4f}")
    logger.info(f"Optimal Threshold Shifted From 0.5 to: {optimal_threshold:.4f}")
    
    # Extract Feature Importances
    try:
        importances = best_model.feature_importances_
        top_idx = np.argsort(importances)[::-1][:5]
        top_features = {training_columns[i]: float(importances[i]) for i in top_idx}
    except Exception as e:
        logger.warning(f"Could not extract feature importances: {e}")
        top_features = {}
        
    # User Requested Final Log Overview
    print("\n" + "="*50)
    print("== TRAINING SUMMARY ==")
    print(f"Best Model: {model_type.upper()}")
    print(f"ROC-AUC: {final_auc:.4f}")
    print(f"Threshold: {optimal_threshold:.2f}")
    if top_features:
        print(f"Top Feature: {list(top_features.keys())[0]} ({list(top_features.values())[0]:.4f})")
    print("="*50 + "\n")

    # 7. Save advanced bundle metadata
    return {
        "model": best_model,
        "model_type": model_type,
        "version": "v1",
        "roc_auc": float(final_auc),
        "features": training_columns, # Standardized name
        "feature_importances": top_features,
        "training_columns": training_columns, # Legacy support
        "income_bins": income_bins,
        "optimal_threshold": float(optimal_threshold),
        "training_config": {
            "cv_folds": 3,
            "search_type": "randomized_search",
            "early_stopping_rounds": 10,
            "validation_split": 0.15
        }
    }

def save_model(model_bundle: Dict[str, Any], filepath: str) -> None:
    """Saves the trained model bundle to disk safely."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump(model_bundle, filepath)
        logger.info(f"Model successfully saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save model to {filepath}: {e}")
        raise

def load_model(filepath: str) -> Dict[str, Any]:
    """Loads a trained model bundle from disk securely."""
    try:
        model = joblib.load(filepath)
        logger.info(f"Model successfully loaded from {filepath}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model from {filepath}: {e}")
        raise

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
    
    logger.debug(f"Running exact strict schema inference for {len(X_processed)} records.")
    
    probabilities = model.predict_proba(X_processed)[:, 1]
    
    # Use the optimized threshold instead of the naive 0.5
    optimal_threshold = model_bundle.get("optimal_threshold", 0.5)
    predictions = (probabilities >= optimal_threshold).astype(int)
    
    if len(X_processed) == 1:
        return int(predictions[0]), float(probabilities[0])
    
    return predictions.tolist(), probabilities.tolist()