def clamp(val, lo, hi):
    return max(lo, min(val, hi))

def validate_input(input_data):
    return {
        "gender_ratio": clamp(input_data.get("gender_ratio", 50), 0, 100),
        "age_min": clamp(input_data.get("age_min", 25), 18, 100),
        "age_max": clamp(input_data.get("age_max", 55), 18, 100),
        "income_diversity": clamp(input_data.get("income_diversity", 5), 0, 10),
        "education_bias": clamp(input_data.get("education_bias", 5), 0, 10),
        "mitigation_toggle": bool(input_data.get("mitigation_toggle", False))
    }
