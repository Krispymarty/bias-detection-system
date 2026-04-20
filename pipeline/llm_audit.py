"""
pipeline/llm_audit.py
Converts SHAP output into plain-English audit log using Gemini 2.5 Flash.
Extracted and adapted from shap_llm_explainer.py.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # loads GEMINI_API_KEY from .env file


def generate_audit_log(prediction: str,
                        shap_explanation: dict,
                        bias_metrics: dict,
                        domain: str = "lending") -> str:
    """
    Converts structured model output (SHAP + bias metrics) into a
    plain-English 3-paragraph audit log using Gemini 2.5 Flash.

    Args:
        prediction       : "APPROVED" or "REJECTED"
        shap_explanation : output from get_shap_explanation() in explainability.py
        bias_metrics     : output from evaluate_bias() in bias.py
        domain           : "lending" or "hiring"

    Returns:
        Natural language audit log string.
        Returns a fallback message if GEMINI_API_KEY not configured.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "Audit log unavailable: GEMINI_API_KEY not set in .env file."

    try:
        from google import genai
    except ImportError:
        return "Audit log unavailable: google-genai package not installed. Run: pip install google-genai"

    client = genai.Client(api_key=api_key)

    # Format SHAP features as readable lines for the prompt
    shap_lines = "\n".join([
        f"  - {f['feature']}: {f['shap_value']:+.4f}  ({f['direction']})"
        + ("  *** PROTECTED ATTRIBUTE ***" if f.get("is_protected") else "")
        for f in shap_explanation.get("top_features", [])
    ])

    dpd = bias_metrics.get("demographic_parity_difference", "N/A")
    eod = bias_metrics.get("equalized_odds_difference",     "N/A")

    prompt = f"""You are an AI fairness auditor reviewing a {domain} decision.

Decision: {prediction}
Model baseline (log-odds): {shap_explanation.get('base_value', 'N/A')}

Top features that influenced this decision (SHAP values):
{shap_lines}

Fairness metrics:
- Demographic Parity Difference (gender): {dpd}
- Equalized Odds Difference: {eod}

Write exactly 3 paragraphs with these headings:
Paragraph 1 - DECISION REASON: Explain why the decision was made. Name the top 2-3 features and their direction.
Paragraph 2 - BIAS CHECK: State whether gender or age appear in top features. Flag as SIGNIFICANT if Demographic Parity Difference exceeds 0.10.
Paragraph 3 - RECOMMENDATION: Give one concrete, actionable step to reduce bias.

Be factual, plain-English, concise. No bullet points."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text