import json
import time
from fastapi.testclient import TestClient
import sys
import os

# Ensure the app module is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.main import app, load_model_bundle
import asyncio

# Create the test client
client = TestClient(app)

def run_demo():
    print("🚀 Starting AI Fairness Auditor Demonstration...")
    print("-" * 50)
    
    # Load Models as it usually happens on startup
    print("\n[Loading Model Bundle...]")
    asyncio.run(load_model_bundle())

    # 1. Test Health Endpoint
    print("\n[1] Checking API Health...")
    health_resp = client.get("/health")
    print("Status Code:", health_resp.status_code)
    print("Response:", json.dumps(health_resp.json(), indent=2))

    # 2. Test Audit Endpoint with an application that might be rejected
    print("\n[2] Testing '/v1/audit' endpoint (Expected to be rejected + counterfactuals)...")
    
    payload = {
        "domain": "lending",
        "features": {
            "CODE_GENDER": "M",
            "AGE": 25,
            "AMT_INCOME_TOTAL": 30000.0,
            "AMT_CREDIT": 500000.0,
            "AMT_ANNUITY": 25000.0,
            "NAME_EDUCATION_TYPE": "Secondary / secondary special",
            "OCCUPATION_TYPE": "Laborers",
            "EXT_SOURCE_1": 0.2,
            "EXT_SOURCE_2": 0.2,
            "EXT_SOURCE_3": 0.2,
            "INCOME_GROUP": "Low"
        },
        "apply_mitigation": False
    }

    try:
        start_time = time.time()
        audit_resp = client.post("/v1/audit", json=payload)
        end_time = time.time()
        
        print("Status Code:", audit_resp.status_code)
        print(f"Latency: {(end_time - start_time) * 1000:.2f} ms")
        print("\nResponse:")
        print(json.dumps(audit_resp.json(), indent=2))
    except Exception as e:
        print(f"❌ Error during /v1/audit request: {e}")

    # 3. Test Audit Endpoint with a strong application
    print("\n[3] Testing '/v1/audit' endpoint (Expected to be approved)...")
    
    payload_good = {
        "domain": "lending",
        "features": {
            "CODE_GENDER": "F",
            "AGE": 45,
            "AMT_INCOME_TOTAL": 150000.0,
            "AMT_CREDIT": 100000.0,
            "AMT_ANNUITY": 5000.0,
            "NAME_EDUCATION_TYPE": "Higher education",
            "OCCUPATION_TYPE": "Managers",
            "EXT_SOURCE_1": 0.8,
            "EXT_SOURCE_2": 0.8,
            "EXT_SOURCE_3": 0.8,
            "INCOME_GROUP": "High"
        },
        "apply_mitigation": False
    }

    try:
        start_time = time.time()
        audit_resp_good = client.post("/v1/audit", json=payload_good)
        end_time = time.time()
        
        print("Status Code:", audit_resp_good.status_code)
        print(f"Latency: {(end_time - start_time) * 1000:.2f} ms")
        print("\nResponse:")
        print(json.dumps(audit_resp_good.json(), indent=2))
    except Exception as e:
        print(f"❌ Error during /v1/audit request: {e}")

    print("\n" + "-" * 50)
    print("✅ Demonstration Complete!")

if __name__ == "__main__":
    run_demo()
