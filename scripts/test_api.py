import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from fastapi.testclient import TestClient
from app.main import app, load_model_bundle, MODELS
import asyncio
import json
from unittest.mock import patch, MagicMock

# Mock model bundle
mock_bundle = {"model": "dummy", "training_columns": [], "income_bins": []}
MODELS["lending"] = mock_bundle
MODELS["hiring"] = mock_bundle

client = TestClient(app)

payload = {
    "domain": "lending",
    "features": {
        "CODE_GENDER": "M",
        "AGE": 30,
        "AMT_INCOME_TOTAL": 50000.0,
        "AMT_CREDIT": 100000.0,
        "AMT_ANNUITY": 5000.0,
        "NAME_EDUCATION_TYPE": "Higher education",
        "OCCUPATION_TYPE": "Laborers",
        "EXT_SOURCE_1": 0.5,
        "EXT_SOURCE_2": 0.5,
        "EXT_SOURCE_3": 0.5,
        "INCOME_GROUP": "Medium"
    }
}

@patch("app.main.predict")
@patch("app.main.get_shap_explanation")
def run_tests(mock_get_shap, mock_predict):
    mock_predict.return_value = (1, 0.85) # Predict Reject (1) with 0.85 prob
    mock_get_shap.return_value = {
        "top_features": [
            {"feature": "AGE", "shap_value": 0.15, "direction": "increases default risk", "is_protected": True},
            {"feature": "AMT_INCOME_TOTAL", "shap_value": -0.05, "direction": "decreases default risk", "is_protected": False}
        ],
        "base_value": 0.0
    }
    
    print("Testing lending domain:")
    response = client.post("/v1/audit", json=payload)
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print("Failed to decode JSON:", e)
        print(response.text)

    print("\nTesting hiring domain (fallback expected):")
    payload["domain"] = "hiring"
    response2 = client.post("/v1/audit", json=payload)
    print(f"Status Code: {response2.status_code}")
    try:
        print(json.dumps(response2.json(), indent=2))
    except Exception as e:
        print("Failed to decode JSON:", e)
        print(response2.text)

run_tests()
