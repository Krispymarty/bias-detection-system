import pandas as pd
from pipeline.model import load_model, predict
from pipeline.bias import evaluate_bias

def test_fairlearn():
    print("Loading production model...")
    bundle = load_model("pipeline/production_model.joblib")
    
    # Load a small slice of data (e.g. 500 rows) just to test logic
    print("Loading a slice of testing data...")
    df = pd.read_csv("data/final_merged_cleaned.csv", nrows=1000)
    
    X_test_raw = df.copy()
    y_test = df["TARGET"]
    
    # We need the sensitive attribute explicitly
    if "CODE_GENDER_M" not in X_test_raw.columns:
        print("Missing CODE_GENDER_M! Bias check impossible.")
        return
        
    sensitive_features = X_test_raw["CODE_GENDER_M"]
    
    print("Making predictions using strict pipeline inference...")
    predictions, _ = predict(bundle, X_test_raw)
    
    print("Evaluating bias metrics via Fairlearn...")
    metrics = evaluate_bias(y_test, pd.Series(predictions, index=y_test.index), sensitive_features)
    
    print("\n--- FAIRNESS METRICS ---")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")

if __name__ == "__main__":
    test_fairlearn()
