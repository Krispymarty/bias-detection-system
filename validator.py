"""
FairLens - Input Validator
===========================
Validates user features BEFORE any API call or processing.

Ensures:
  - All required fields are present
  - All numeric fields are actual numbers (not strings)
  - Field names exactly match the API schema
  - No extra or renamed fields leak through
  - Values are within sane bounds
"""

import copy
from typing import Dict, Any, Tuple, List


# Exact API schema — field name -> (expected type, required)
API_SCHEMA = {
    "CODE_GENDER":           (str,   True),
    "AGE":                   ((int, float), True),
    "DAYS_BIRTH":            ((int, float), True),
    "OCCUPATION_TYPE":       (str,   True),
    "NAME_EDUCATION_TYPE":   (str,   True),
    "INCOME_GROUP":          (str,   True),
    "AMT_INCOME_TOTAL":      ((int, float), True),
    "AMT_CREDIT":            ((int, float), True),
    "AMT_ANNUITY":           ((int, float), True),
    "EXT_SOURCE_1":          ((int, float), True),
    "EXT_SOURCE_2":          ((int, float), True),
    "EXT_SOURCE_3":          ((int, float), True),
}

# Fields that MUST be numeric (catches string-encoded numbers)
NUMERIC_FIELDS = [
    "AGE", "DAYS_BIRTH", "AMT_INCOME_TOTAL", "AMT_CREDIT",
    "AMT_ANNUITY", "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3",
]

# Valid values for categorical fields
VALID_GENDER = {"M", "F"}
VALID_INCOME_GROUP = {"Low", "Medium", "High"}


class InputValidationError(Exception):
    """Raised when input validation fails."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Input validation failed: {'; '.join(errors)}")


class InputValidator:
    """Validates and freezes input features before any API call."""

    @staticmethod
    def validate(features: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates features against the API schema.

        Returns
        -------
        (is_valid, errors) : tuple
            is_valid: True if all checks pass.
            errors: List of human-readable error strings.
        """
        errors = []

        # 1. Check for missing required fields
        for field_name, (expected_type, required) in API_SCHEMA.items():
            if required and field_name not in features:
                errors.append(f"Missing required field: '{field_name}'")

        # 2. Check for extra/unknown fields
        known_fields = set(API_SCHEMA.keys())
        for field_name in features:
            if field_name not in known_fields:
                errors.append(
                    f"Unknown field: '{field_name}' — not in API schema"
                )

        # 3. Type validation — ensure numerics are numbers, not strings
        for field_name in NUMERIC_FIELDS:
            if field_name in features:
                val = features[field_name]
                if isinstance(val, str):
                    errors.append(
                        f"Type mismatch: '{field_name}' is a string ('{val}') "
                        f"but must be a number"
                    )
                elif not isinstance(val, (int, float)):
                    errors.append(
                        f"Type mismatch: '{field_name}' is {type(val).__name__} "
                        f"but must be int or float"
                    )

        # 4. Categorical field validation
        if "CODE_GENDER" in features:
            if features["CODE_GENDER"] not in VALID_GENDER:
                errors.append(
                    f"Invalid CODE_GENDER: '{features['CODE_GENDER']}' "
                    f"— must be 'M' or 'F'"
                )

        if "INCOME_GROUP" in features:
            if features["INCOME_GROUP"] not in VALID_INCOME_GROUP:
                errors.append(
                    f"Invalid INCOME_GROUP: '{features['INCOME_GROUP']}' "
                    f"— must be 'Low', 'Medium', or 'High'"
                )

        # 5. Range validation for numeric fields
        if "AGE" in features and isinstance(features["AGE"], (int, float)):
            age = features["AGE"]
            if age < 18 or age > 100:
                errors.append(f"AGE={age} out of valid range [18, 100]")

        if "EXT_SOURCE_1" in features and isinstance(features["EXT_SOURCE_1"], (int, float)):
            for src in ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]:
                if src in features and isinstance(features[src], (int, float)):
                    val = features[src]
                    if val < 0.0 or val > 1.0:
                        errors.append(f"{src}={val} out of valid range [0.0, 1.0]")

        if "AMT_INCOME_TOTAL" in features and isinstance(features["AMT_INCOME_TOTAL"], (int, float)):
            if features["AMT_INCOME_TOTAL"] < 0:
                errors.append("AMT_INCOME_TOTAL cannot be negative")

        if "AMT_CREDIT" in features and isinstance(features["AMT_CREDIT"], (int, float)):
            if features["AMT_CREDIT"] < 1000:
                errors.append(f"AMT_CREDIT={features['AMT_CREDIT']} below minimum (1000)")

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def validate_or_raise(features: Dict[str, Any]) -> None:
        """Validates features; raises InputValidationError on failure."""
        is_valid, errors = InputValidator.validate(features)
        if not is_valid:
            raise InputValidationError(errors)

    @staticmethod
    def freeze(features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a deep copy of the features dict.
        The returned copy is completely independent — mutations
        to the copy will NEVER affect the original.
        """
        return copy.deepcopy(features)

    @staticmethod
    def coerce_types(features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempts to coerce string-encoded numbers to actual numbers.
        Returns a NEW dict (does not modify the input).
        """
        result = copy.deepcopy(features)
        for field_name in NUMERIC_FIELDS:
            if field_name in result and isinstance(result[field_name], str):
                try:
                    # Try int first, then float
                    val = result[field_name].strip()
                    if "." in val:
                        result[field_name] = float(val)
                    else:
                        result[field_name] = int(val)
                except ValueError:
                    pass  # Leave as-is; validate() will catch it
        return result
