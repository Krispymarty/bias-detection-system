"""
FairSight AI — What-If Simulator Backend
Payload builder, API service, and response parser.
No pandas. No DataFrames. Pure JSON + requests.
"""
import requests
import time
from .validators import validate_input

API_BASE = "https://bias-detection-system.onrender.com"


# ──────────────────────────────────────────────
# Payload Builder (strict Swagger schema)
# ──────────────────────────────────────────────
def build_payload(input_data):
    """
    Maps UI slider values → exact AuditRequest JSON
    per OpenAPI /v1/audit schema.
    """
    data = validate_input(input_data)

    # CODE_GENDER: string "M" or "F" (regex ^(M|F)$)
    code_gender = "F" if data["gender_ratio"] >= 50 else "M"

    # AGE: integer 18–100
    age = int((data["age_min"] + data["age_max"]) / 2)
    age = max(18, min(age, 100))

    # AMT_INCOME_TOTAL: number >= 0
    amt_income_total = float(50000 + data["income_diversity"] * 10000)

    # AMT_CREDIT: number 1000–10000000
    amt_credit = 500000.0

    # AMT_ANNUITY: number >= 0
    amt_annuity = 25000.0

    # EXT_SOURCE_*: number 0–1
    ext = round(0.3 + (data["education_bias"] / 10) * 0.6, 2)
    ext = max(0.0, min(ext, 1.0))

    payload = {
        "domain": "lending",
        "features": {
            "CODE_GENDER": code_gender,
            "AGE": age,
            "AMT_INCOME_TOTAL": amt_income_total,
            "AMT_CREDIT": amt_credit,
            "AMT_ANNUITY": amt_annuity,
            "NAME_EDUCATION_TYPE": "Higher education",
            "OCCUPATION_TYPE": "Laborers",
            "EXT_SOURCE_1": ext,
            "EXT_SOURCE_2": ext,
            "EXT_SOURCE_3": ext,
            "INCOME_GROUP": "Medium"
        },
        "apply_mitigation": data["mitigation_toggle"]
    }
    return payload


# ──────────────────────────────────────────────
# API Service: POST /v1/audit (3 retries)
# ──────────────────────────────────────────────
def run_audit(payload):
    """Send audit request with retry logic."""
    url = f"{API_BASE}/v1/audit"
    last_err = None

    for attempt in range(3):
        try:
            res = requests.post(url, json=payload, timeout=120)
            if res.status_code == 200:
                return {"ok": True, "data": res.json(), "status": 200}
            else:
                return {
                    "ok": False,
                    "error": res.text,
                    "status": res.status_code
                }
        except Exception as e:
            last_err = str(e)
            if attempt < 2:
                time.sleep(2)

    return {"ok": False, "error": last_err or "Unknown error", "status": 0}


# ──────────────────────────────────────────────
# API Service: POST /v1/audit/compare
# Same AuditRequest schema — compares baseline vs fair model
# ──────────────────────────────────────────────
def compare_runs(payload):
    """
    Compare baseline vs mitigated model for the same applicant.
    Uses the same AuditRequest schema as /v1/audit.
    """
    url = f"{API_BASE}/v1/audit/compare"
    try:
        res = requests.post(url, json=payload, timeout=120)
        if res.status_code == 200:
            return {"ok": True, "data": res.json()}
        return {"ok": False, "error": res.text, "status": res.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e), "status": 0}


# ──────────────────────────────────────────────
# API Service: GET /v1/fairness_report
# ──────────────────────────────────────────────
def get_fairness_report():
    """Fetch the full before/after fairness metrics report."""
    url = f"{API_BASE}/v1/fairness_report"
    try:
        res = requests.get(url, timeout=120)
        if res.status_code == 200:
            return {"ok": True, "data": res.json()}
        return {"ok": False, "error": res.text, "status": res.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e), "status": 0}


# ──────────────────────────────────────────────
# Response Parser (defensive — keys may vary)
# ──────────────────────────────────────────────
def parse_audit_response(api_json):
    """Normalize API response into a consistent dict for UI rendering."""
    prediction = api_json.get("prediction", "N/A")
    probability = api_json.get("probability", 0)

    fairness = api_json.get("fairness") or {}
    fairness_score = fairness.get("score", 0)
    badge = fairness.get("badge", "Unknown")
    bias_source = fairness.get("bias_source", "")
    bias_metrics = fairness.get("bias_metrics") or {}
    selection_rate_gap = bias_metrics.get("selection_rate_gap", 0)

    governance = api_json.get("governance") or {}
    confidence = governance.get("confidence", "Unknown")
    mitigation_applied = governance.get("mitigation_applied", False)

    # Map badge to a simple risk level for the UI
    if "Risky" in badge or "🔴" in badge:
        risk = "High"
    elif "Warning" in badge or "🟡" in badge or "⚠" in badge:
        risk = "Medium"
    elif "Fair" in badge or "🟢" in badge or "✅" in badge:
        risk = "Low"
    else:
        risk = "Unknown"

    return {
        "prediction": prediction,
        "probability": probability,
        "fairness_score": fairness_score,
        "fairness_badge": badge,
        "bias": selection_rate_gap,
        "bias_source": bias_source,
        "risk": risk,
        "confidence": confidence,
        "mitigation_applied": mitigation_applied,
        "raw": api_json
    }
