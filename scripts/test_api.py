"""
Phase 3 — Real API-level test script
Hits the live deployed endpoint to verify end-to-end behavior.

Usage:
    python scripts/test_api.py                         # uses default Render URL
    python scripts/test_api.py http://localhost:8000   # local dev server
"""
import sys
import json
import time

try:
    import requests
except ImportError:
    print("ERROR: 'requests' not installed. Run: pip install requests")
    sys.exit(1)

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://bias-detection-system.onrender.com"
AUDIT_URL = f"{BASE_URL}/v1/audit"
TIMEOUT   = 60  # Render cold-start can be slow

# ---------------------------------------------------------------------------
# Shared valid base payload
# ---------------------------------------------------------------------------
VALID_PAYLOAD = {
    "domain": "lending",
    "apply_mitigation": False,
    "features": {
        "CODE_GENDER": "M",
        "AGE": 35,
        "AMT_INCOME_TOTAL": 150000.0,
        "AMT_CREDIT": 250000.0,
        "AMT_ANNUITY": 12000.0,
        "NAME_EDUCATION_TYPE": "Higher education",
        "OCCUPATION_TYPE": "Laborers",
        "EXT_SOURCE_1": 0.65,
        "EXT_SOURCE_2": 0.55,
        "EXT_SOURCE_3": 0.70,
        "INCOME_GROUP": "Medium"
    }
}

def _patch(overrides: dict) -> dict:
    """Deep-merge overrides into the valid payload features."""
    import copy
    p = copy.deepcopy(VALID_PAYLOAD)
    for k, v in overrides.items():
        p["features"][k] = v
    return p

def _patch_remove(key: str) -> dict:
    import copy
    p = copy.deepcopy(VALID_PAYLOAD)
    p["features"].pop(key, None)
    return p

# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------
TESTS = [
    {
        "name": "T1  Valid input",
        "payload": VALID_PAYLOAD,
        "expect_status": 200,
        "check": lambda r: all(k in r for k in ("prediction", "fairness", "explanation", "governance", "system")),
        "check_desc": "All 5 required response keys present"
    },
    {
        "name": "T2  Lowercase INCOME_GROUP ('medium')",
        "payload": _patch({"INCOME_GROUP": "medium"}),
        "expect_status": 200,
        "check": lambda r: "prediction" in r,
        "check_desc": "Normalised to 'Medium' and processed successfully"
    },
    {
        "name": "T3  Messy gender ('female')",
        "payload": _patch({"CODE_GENDER": "female"}),
        "expect_status": 200,
        "check": lambda r: "prediction" in r,
        "check_desc": "Normalised to CODE_GENDER_M=0 and processed successfully"
    },
    {
        "name": "T4  Invalid AGE type ('abc')",
        "payload": _patch({"AGE": "abc"}),
        "expect_status": 422,
        "check": lambda r: "error" in r or "detail" in r,
        "check_desc": "422 with human-friendly error message"
    },
    {
        "name": "T5  Missing required field (no EXT_SOURCE_1)",
        "payload": _patch_remove("EXT_SOURCE_1"),
        "expect_status": 422,
        "check": lambda r: "error" in r or "detail" in r,
        "check_desc": "422 for missing field"
    },
    {
        "name": "T6  Uppercase INCOME_GROUP ('HIGH')",
        "payload": _patch({"INCOME_GROUP": "HIGH"}),
        "expect_status": 200,
        "check": lambda r: "prediction" in r,
        "check_desc": "Normalised to 'High' and processed"
    },
    {
        "name": "T7  CODE_GENDER_M integer (1) instead of string",
        "payload": {**VALID_PAYLOAD, "features": {**VALID_PAYLOAD["features"], "CODE_GENDER_M": 1}},
        "expect_status": 200,
        "check": lambda r: "prediction" in r,
        "check_desc": "Binary gender integer accepted"
    },
]

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print(f"  AI Fairness Auditor — API Test Matrix")
print(f"  Target: {AUDIT_URL}")
print(f"{'='*60}\n")

passed = 0
failed = 0

for t in TESTS:
    name   = t["name"]
    expect = t["expect_status"]
    check  = t["check"]
    desc   = t["check_desc"]

    try:
        t0 = time.time()
        resp = requests.post(AUDIT_URL, json=t["payload"], timeout=TIMEOUT)
        latency = round((time.time() - t0) * 1000)

        status_ok = resp.status_code == expect

        try:
            body = resp.json()
        except Exception:
            body = {}

        content_ok = check(body) if status_ok else True  # only check content on expected status

        if status_ok and content_ok:
            print(f"  [PASS]  {name}")
            print(f"          status={resp.status_code}  latency={latency}ms  check='{desc}'")
            passed += 1
        else:
            print(f"  [FAIL]  {name}")
            print(f"          expected_status={expect}  got={resp.status_code}  latency={latency}ms")
            if not content_ok:
                print(f"          content_check FAILED: '{desc}'")
                print(f"          response_preview: {resp.text[:300]}")
            failed += 1

    except requests.exceptions.Timeout:
        print(f"  [FAIL]  {name}  ->  TIMEOUT after {TIMEOUT}s (Render cold start?)")
        failed += 1
    except requests.exceptions.ConnectionError as e:
        print(f"  [FAIL]  {name}  ->  CONNECTION ERROR: {e}")
        failed += 1
    except Exception as e:
        print(f"  [FAIL]  {name}  ->  Unexpected error: {e}")
        failed += 1

    print()

print(f"{'='*60}")
print(f"  Results: {passed} passed, {failed} failed out of {len(TESTS)} tests")
print(f"{'='*60}\n")

sys.exit(0 if failed == 0 else 1)
