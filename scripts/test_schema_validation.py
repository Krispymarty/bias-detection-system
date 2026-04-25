"""
Phase 4 — Validation Test Matrix
Tests the FeatureSet schema directly (no server required).
Run: python scripts/test_schema_validation.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError

# Import the schema from app.main
# We can't import app.main directly (it imports pipeline), so we replicate just the schema here.
# ---------------------------------------------------------------------------
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any

_INCOME_GROUP_MAP = {"low": "Low", "medium": "Medium", "high": "High"}

def _normalize_income_group(val: Any) -> str:
    try:
        return _INCOME_GROUP_MAP.get(str(val).strip().lower(), "Medium")
    except Exception:
        return "Medium"

class FeatureSet(BaseModel):
    CODE_GENDER_M: Optional[int] = Field(None, ge=0, le=1)
    CODE_GENDER: Optional[str] = Field(None)
    AGE: int = Field(..., ge=18, le=100)
    AMT_INCOME_TOTAL: float = Field(..., ge=0.0)
    AMT_CREDIT: float = Field(..., ge=1000.0, le=10_000_000.0)
    AMT_ANNUITY: float = Field(..., ge=0.0)
    NAME_EDUCATION_TYPE: str
    OCCUPATION_TYPE: str
    EXT_SOURCE_1: float = Field(..., ge=0.0, le=1.0)
    EXT_SOURCE_2: float = Field(..., ge=0.0, le=1.0)
    EXT_SOURCE_3: float = Field(..., ge=0.0, le=1.0)
    INCOME_GROUP: str

    @model_validator(mode="before")
    @classmethod
    def normalize_inputs(cls, values: dict) -> dict:
        try:
            cgm = values.get("CODE_GENDER_M")
            cg  = values.get("CODE_GENDER")
            if cgm is None:
                if isinstance(cg, str):
                    normalised = cg.strip().upper()
                    values["CODE_GENDER_M"] = 1 if normalised in ("M", "MALE") else 0
                elif isinstance(cg, (int, float)):
                    values["CODE_GENDER_M"] = int(cg)
                else:
                    values["CODE_GENDER_M"] = 0
            if values.get("CODE_GENDER") is None and values.get("CODE_GENDER_M") is not None:
                values["CODE_GENDER"] = "M" if int(values["CODE_GENDER_M"]) == 1 else "F"
        except Exception:
            values.setdefault("CODE_GENDER_M", 0)
        return values
# ---------------------------------------------------------------------------

VALID_BASE = {
    "CODE_GENDER": "M",
    "AGE": 30,
    "AMT_INCOME_TOTAL": 120000.0,
    "AMT_CREDIT": 200000.0,
    "AMT_ANNUITY": 10000.0,
    "NAME_EDUCATION_TYPE": "Higher education",
    "OCCUPATION_TYPE": "Laborers",
    "EXT_SOURCE_1": 0.6,
    "EXT_SOURCE_2": 0.7,
    "EXT_SOURCE_3": 0.5,
    "INCOME_GROUP": "Medium"
}

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"

def run(name, payload, expect_valid: bool, extra_check=None):
    try:
        obj = FeatureSet(**payload)
        if expect_valid:
            result = PASS
            if extra_check:
                check_result, msg = extra_check(obj)
                result = PASS if check_result else FAIL
                print(f"[{'OK' if check_result else 'FAIL'}] {name}: {msg}")
                return
        else:
            result = FAIL  # expected 422 but got valid
        print(f"[{'OK' if expect_valid else 'FAIL'}] {name}: model built successfully")
    except ValidationError as e:
        if not expect_valid:
            result = PASS
            print(f"[OK]{PASS} {name}: got ValidationError as expected → {e.errors()[0]['msg']}")
            return
        else:
            print(f"[FAIL]{FAIL} {name}: unexpected ValidationError → {e.errors()}")
            return
    print(f"[OK]{result} {name}")


print("\n=== Phase 4 — Validation Test Matrix ===\n")

# Test 1 — Valid input → expect success
run("Test 1  Valid input (AGE=30)",
    {**VALID_BASE},
    expect_valid=True)

# Test 2 — Wrong type (AGE="abc") → expect 422
run("Test 2  Wrong type (AGE='abc')",
    {**VALID_BASE, "AGE": "abc"},
    expect_valid=False)

# Test 3 — Missing required field (EXT_SOURCE_1) → expect 422
payload3 = {k: v for k, v in VALID_BASE.items() if k != "EXT_SOURCE_1"}
run("Test 3  Missing EXT_SOURCE_1",
    payload3,
    expect_valid=False)

# Test 4 — Messy gender string → should normalise to CODE_GENDER_M=0
def check_gender(obj):
    ok = obj.CODE_GENDER_M == 0
    return ok, f"CODE_GENDER_M={obj.CODE_GENDER_M} (expected 0)"

run("Test 4  Messy gender CODE_GENDER='female'",
    {**VALID_BASE, "CODE_GENDER": "female"},
    expect_valid=True,
    extra_check=check_gender)

# Test 5 — Lowercase INCOME_GROUP → normalised in _extract_raw_features
# (schema accepts any str; normalisation happens at extraction time)
def check_income(obj):
    normalised = _normalize_income_group(obj.INCOME_GROUP)
    ok = normalised == "Medium"
    return ok, f"_normalize_income_group('{obj.INCOME_GROUP}') → '{normalised}' (expected 'Medium')"

run("Test 5  Lowercase INCOME_GROUP='medium'",
    {**VALID_BASE, "INCOME_GROUP": "medium"},
    expect_valid=True,
    extra_check=check_income)

print("\n=== Done ===\n")
