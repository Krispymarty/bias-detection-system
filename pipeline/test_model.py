import pandas as pd
from model import load_model, predict

def test_inference():
    # 1. Load the trained model bundle
    print("Loading the production model...")
    model_bundle = load_model("pipeline/production_model.joblib")
    
    # 2. Create a mock dictionary (This is EXACTLY how Team 2's frontend will send data to you)
    mock_input = {
        "CODE_GENDER_M": 0,                    # 0 = Female, 1 = Male (Dataset is pre-encoded)
        "AGE": 41,                             # Using explicit AGE directly from UI input
        "OCCUPATION_TYPE": "Laborers",
        "NAME_EDUCATION_TYPE": "Secondary / secondary special",
        "AMT_INCOME_TOTAL": 150000.0,
        "AMT_CREDIT": 400000.0,
        "AMT_ANNUITY": 25000.0,
        "EXT_SOURCE_1": 0.5,
        "EXT_SOURCE_2": 0.6,
        "EXT_SOURCE_3": 0.4
    }
    
    print("\n--- 📝 Testing Single Applicant Input (Mocked from Frontend) ---")
    for key, val in mock_input.items():
        print(f"  {key}: {val}")
    
    # 3. Convert dictionary to DataFrame for the pipeline
    # Note: If training data has DAYS_BIRTH, pipeline handles `(-DAYS_BIRTH)//365`. 
    # But if the UI sends `AGE` directly like this, it seamlessly accepts it!
    input_df = pd.DataFrame([mock_input])
    
    # 4. Run prediction
    prediction, probability = predict(model_bundle, input_df)
    
    print("\n--- 🎯 Inference Results ---")
    # A prediction of 1 means the model thinks the person will DEFAULT on the loan
    # A prediction of 0 means the model thinks the person will PAY off the loan
    status = "REJECT LOAN (Default Risk)" if prediction == 1 else "APPROVE LOAN (Safe)"
    print(f"Prediction Result: {prediction} -> {status}")
    print(f"Confidence (Probability of Default Risk): {probability:.4f} ({probability * 100:.2f}%)")

if __name__ == "__main__":
    test_inference()