import requests
import os

API_BASE = os.getenv("API_BASE_URL", "https://bias-detection-system.onrender.com")

def run_audit(payload):
    try:
        res = requests.post(
            f"{API_BASE}/v1/audit",
            json=payload,
            timeout=15
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}


def compare_audit(run1, run2):
    try:
        res = requests.post(
            f"{API_BASE}/v1/audit/compare",
            json={
                "run_1": run1,
                "run_2": run2
            },
            timeout=15
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}


def get_fairness_report():
    try:
        res = requests.get(
            f"{API_BASE}/v1/fairness_report",
            timeout=15
        )
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}
