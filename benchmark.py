import pandas as pd
import numpy as np
import time
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Define algorithms to test
models = {
    "LogisticRegression": LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42),
    "RandomForest": RandomForestClassifier(n_estimators=50, max_depth=10, class_weight='balanced', random_state=42, n_jobs=-1),
    "XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, eval_metric="logloss", n_jobs=-1)
}

# Not using a hardcoded feature list, will use all features dynamically

datasets = {
    "application_train": "data/application_train_cleaned.csv",
    "final_merged": "data/final_merged_cleaned.csv"
}

results = []

for name, path in datasets.items():
    print(f"\n{'='*50}\nEvaluating Dataset: {name}\n{'='*50}")
    
    # Verify file exists
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
        
    # Read the dataset
    print("Loading data...")
    df = pd.read_csv(path)
    
    # Ensure TARGET is present
    if "TARGET" not in df.columns:
        print("Missing 'TARGET' column in dataset. Skipping.")
        continue
    
    print(f"Total Rows: {len(df)}")
    
    # Select all features except TARGET and any ID columns
    drop_cols = ["TARGET", "SK_ID_CURR"]
    feature_cols = [c for c in df.columns if c not in drop_cols]
    X = df[feature_cols].copy()
    y = df["TARGET"].copy()
    
    print("Preprocessing data (Missing Values, One-Hot)...")
    X = pd.get_dummies(X, drop_first=True)
    X = X.fillna(X.median())
    
    # For fair comparison and Logistic Regression suitability, apply standard scaling
    print("Scaling numeric features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Calculate pos weight for XGBoost
    neg = (y_train == 0).sum()
    pos = (y_train == 1).sum()
    scale_pos_wt = neg / pos if pos > 0 else 1.0
    models["XGBoost"].set_params(scale_pos_weight=scale_pos_wt)
    
    for model_name, model in models.items():
        print(f"\n-> Training {model_name}...")
        start_time = time.time()
        
        model.fit(X_train, y_train)
        
        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)
        
        auc = roc_auc_score(y_test, y_prob)
        acc = accuracy_score(y_test, y_pred)
        elapsed = time.time() - start_time
        
        print(f"   ROC-AUC: {auc:.4f} | Accuracy: {acc:.4f} | Time: {elapsed:.1f}s")
        
        results.append({
            "Dataset": name,
            "Model": model_name,
            "ROC-AUC": auc,
            "Accuracy": acc,
            "Time (s)": round(elapsed, 1)
        })

print("\n\n" + "="*50)
print("FINAL BENCHMARK SUMMARY")
print("="*50)
df_res = pd.DataFrame(results)
print(df_res.sort_values(by="ROC-AUC", ascending=False).to_string(index=False))
df_res.to_json("benchmark_summary.json", orient='records')
