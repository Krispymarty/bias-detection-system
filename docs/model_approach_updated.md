# Rigorous Hyperparameter Tuning & Selection Walkthrough

I have successfully executed the end-to-end competition pipeline that you designed. The system now flawlessly treats both **XGBoost** and **Random Forest** as identical citizens, searches for their optimal hyper-parameters using early stopping, and picks the ultimate winner for deployment!

## What Changed

### 1. The Pipeline Competition (`pipeline/model.py`)
I overhauled `train_model()` to act as an automated tournament:
1. **Data Splits:** It cleanly splits off 15% of the data exclusively for early stopping and threshold validation to prevent data leakage.
2. **StratifiedKFold + RandomizedSearchCV:** It uses a 3-fold stratified split to search through our expanded parameter dictionaries (covering deeper trees and different subsample rates).
3. **Early Stopping:** The XGBoost classifier enforces `early_stopping_rounds=10`. This means if a specific parameter guess is terrible, XGBoost will kill the training early instead of wasting your CPU.

### 2. Optimal F1-Based Threshold
We officially killed the naive `0.5` probability threshold.
After finding the "Best Model" (whether it's XGB or RF), the code uses the 15% validation slice we held back to plot precision-recall curves. It calculates the exact probability threshold that maximizes the mathematical F1-score across the dataset. 

This **`optimal_threshold`** (often not exactly 0.5) is now natively embedded inside the `model_bundle` object!

### 3. Smart Inference
Your FastAPI backend relies on `predict()` inside `pipeline/model.py`. 
I dynamically updated this function:
```python
# Before
predictions = (probabilities >= 0.5).astype(int)

# After: Extracts your tuned threshold directly from the bundle
optimal_threshold = model_bundle.get("optimal_threshold", 0.5)
predictions = (probabilities >= optimal_threshold).astype(int)
```

## Validation Results

I completely re-ran `python train_final.py` which executed this tournament!

It successfully loaded the full `final_merged_cleaned.csv` dataset, evaluated the parameters using K-Folds, found the absolute peak performance, calculated the optimized threshold, and securely saved the new master bundle as `pipeline/production_model.joblib`. 

> [!WARNING]
> Because the `production_model.joblib` bundle was just rebuilt on your hard drive, your currently running FastAPI server (`uvicorn` terminal process) doesn't know about it yet! You will need to press `Ctrl + C` in your terminal to stop the server, and rerun `uvicorn app.main:app --reload` so it loads the brand new tuned bundle into memory.
