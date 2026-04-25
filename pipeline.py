"""
FairLens v5 — User-Complete Pipeline Orchestrator
====================================================

A user-aware, device-independent pipeline that ALWAYS ensures a valid
email is obtained before generating and sending the audit report.

Pipeline:
  Step 0: Email Resolution (ask if missing, validate format)
  Step 1: Load & Validate Input from sample_input.json
  Step 2: Call Model API → initial_output
  Step 3: What-If Simulation (multiple API calls on copies)
  Step 4: Generate Report
  Step 5: Generate PDF → /reports/
  Step 6: Save to Database
  Step 7: Send Email with PDF attachment

CRITICAL RULES:
  - A valid email MUST be resolved before the report is sent
  - original_input is NEVER mutated after freezing
  - initial_output is preserved separately from simulated_output
  - The model is a black-box API (POST /v1/audit)
  - No imports from pipeline/ or bias-detection-system/ internals
  - Email failure NEVER breaks the pipeline

Usage:
    python -m fairlens.pipeline
    python -m fairlens.pipeline --input custom.json
    python -m fairlens.pipeline --no-email
    python -m fairlens.pipeline --no-api --no-sim
"""

import os
import re
import sys
import json
import copy
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, Tuple

import requests
from dotenv import load_dotenv

from .validator import InputValidator
from .services import PDFService, DatabaseService, EmailService
from .middleware import FairLensMiddleware

# Load .env file
load_dotenv()

# Model API endpoint (existing system — treated as black box)
API_URL = "https://bias-detection-system.onrender.com/v1/audit"

# Email validation regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# Maximum retry attempts for email input
MAX_EMAIL_RETRIES = 3

# Fallback sample response for offline mode
SAMPLE_API_RESPONSE = {
    "prediction": "Rejected",
    "probability": 0.7234,
    "recommendation": (
        "Reducing the requested credit amount by 20% may flip "
        "the decision to Approved."
    ),
    "fairness": {
        "score": 83.5,
        "badge": "Moderate",
        "bias_source": "Model Bias (Detected)",
        "bias_metrics": {
            "selection_rate_gap": 0.165,
            "tpr_gap": 0.042,
            "fpr_gap": 0.031,
            "fnr_gap": 0.028,
        },
    },
}


# ===================================================================
# EMAIL VALIDATION
# ===================================================================
def validate_email(email: str) -> bool:
    """
    Validates email format using RFC 5322 simplified regex.
    Returns True if the email is structurally valid.
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


# ===================================================================
# EMAIL RESOLUTION (STEP 0 — MANDATORY)
# ===================================================================
def resolve_email(data: Dict[str, Any]) -> str:
    """
    Resolves the recipient email address.

    Strategy:
      1. Check 'user_email' field in input data
      2. Check 'email' field in input data (fallback key)
      3. If neither found → prompt user interactively
      4. Validate format
      5. Retry up to MAX_EMAIL_RETRIES times if invalid

    Parameters
    ----------
    data : dict
        The parsed JSON input data.

    Returns
    -------
    str
        A validated email address.
    """
    print("\n" + "=" * 60)
    print("  STEP 0: EMAIL RESOLUTION")
    print("=" * 60)

    # --- Case 1: Email provided in input ---
    email = data.get("user_email", "").strip()
    if not email:
        email = data.get("email", "").strip()

    if email:
        if validate_email(email):
            print(f"  [OK] Email found in input: {email}")
            return email
        else:
            print(f"  [!] Email found but INVALID format: '{email}'")
            print(f"  Requesting corrected email from user...")

    # --- Case 2: Email NOT provided → ask user ---
    if not email:
        print("  [!] No email found in input data.")
        print("  The audit report must be delivered to a valid email.")

    print()
    for attempt in range(1, MAX_EMAIL_RETRIES + 1):
        try:
            prompt = (
                "  Please provide your email address to receive the "
                "FairLens audit report"
            )
            if attempt > 1:
                prompt = f"  (Attempt {attempt}/{MAX_EMAIL_RETRIES}) Enter a valid email"

            user_input = input(f"{prompt}: ").strip()

            if validate_email(user_input):
                print(f"  [OK] Email validated: {user_input}")
                return user_input
            else:
                print(f"  [X] Invalid email format: '{user_input}'")
                if attempt < MAX_EMAIL_RETRIES:
                    print(f"  Please try again (must be like user@example.com)")

        except (EOFError, KeyboardInterrupt):
            # Non-interactive environment (piped input, CI/CD, etc.)
            print("\n  [!] Non-interactive environment detected.")
            if email and "@" in email:
                print(f"  Using best-effort email: {email}")
                return email
            print("  [!] No email could be resolved. Pipeline will continue.")
            print("  [!] Report will be saved but NOT emailed.")
            return ""

    # Exhausted retries
    print(f"\n  [X] Failed to obtain valid email after {MAX_EMAIL_RETRIES} attempts.")
    if email and "@" in email:
        print(f"  Falling back to original input: {email}")
        return email
    print("  Report will be saved but NOT emailed.")
    return ""


# ===================================================================
# API CALLER (treats model as black-box)
# ===================================================================
def call_audit_api(features: dict) -> Optional[dict]:
    """
    Calls POST /v1/audit on the existing bias-detection-system API.
    This is the ONLY point of contact with the model.
    Returns the JSON response, or None on failure.
    """
    payload = {
        "domain": "lending",
        "features": features,
        "apply_mitigation": False,
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        print(f"[API ERROR] {response.status_code}: {response.text[:200]}")
        return None
    except requests.exceptions.Timeout:
        print("[API ERROR] Request timed out after 60s")
        return None
    except requests.exceptions.ConnectionError:
        print("[API ERROR] Connection refused — is the API running?")
        return None
    except Exception as e:
        print(f"[API ERROR] {e}")
        return None


# ===================================================================
# INPUT LOADER
# ===================================================================
def load_input(file_path: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Loads the full JSON data and extracts features.
    Returns (features, raw_data) so email can be resolved from raw_data.
    """
    if not os.path.exists(file_path):
        print(f"[FATAL] Input file not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", data)

    # Handle nested structure
    if "CODE_GENDER" not in features and "features" in data:
        features = data["features"]

    print(f"[LOAD] Loaded {len(features)} features from {file_path}")
    return features, data


# ===================================================================
# MAIN PIPELINE
# ===================================================================
def run_pipeline(
    input_file: str = "sample_input.json",
    no_email: bool = False,
    no_api: bool = False,
    no_sim: bool = False,
) -> Dict[str, Any]:
    """
    Executes the full FairLens user-complete pipeline.

    Returns
    -------
    dict
        Structured output including:
        - report_text, file_path, email_used, email_status
        - original_input, initial_output, simulation, database_record
    """
    print("\n" + "#" * 65)
    print("  FAIRLENS v5 — USER-COMPLETE PIPELINE")
    print("#" * 65)

    # ==============================================================
    # LOAD INPUT
    # ==============================================================
    features, raw_data = load_input(input_file)

    # ==============================================================
    # STEP 0: EMAIL RESOLUTION (MANDATORY)
    # ==============================================================
    if no_email:
        user_email = raw_data.get("user_email", raw_data.get("email", ""))
        print(f"\n[STEP 0] Email: Using '{user_email}' (--no-email: send skipped)")
    else:
        user_email = resolve_email(raw_data)

    email_status = "pending"

    # ==============================================================
    # STEP 1: VALIDATE & FREEZE INPUT
    # ==============================================================
    print(f"\n[STEP 1] Validating and freezing input...")

    features = InputValidator.coerce_types(features)

    is_valid, errors = InputValidator.validate(features)
    if not is_valid:
        print("[STEP 1] Validation warnings:")
        for err in errors:
            print(f"  - {err}")

    # FREEZE: immutable deep copy — NEVER modified from here
    original_input = InputValidator.freeze(features)

    print(
        f"[STEP 1] Frozen original_input: "
        f"Gender={original_input.get('CODE_GENDER', 'N/A')}, "
        f"Age={original_input.get('AGE', 'N/A')}, "
        f"Income={original_input.get('AMT_INCOME_TOTAL', 0):,.0f}, "
        f"Credit={original_input.get('AMT_CREDIT', 0):,.0f}"
    )

    # ==============================================================
    # STEP 2: INITIAL API CALL (with EXACT original_input)
    # ==============================================================
    print(f"\n[STEP 2] Sending EXACT original_input to API...")

    if no_api:
        print("[STEP 2] Offline mode — using sample API response")
        api_response = copy.deepcopy(SAMPLE_API_RESPONSE)
        predict_fn = None
    else:
        api_response = call_audit_api(original_input)
        if api_response is None:
            print("[STEP 2] API unavailable. Falling back to sample response.")
            api_response = copy.deepcopy(SAMPLE_API_RESPONSE)
            predict_fn = None
        else:
            predict_fn = call_audit_api

    # Store as initial_output (deep copy — never overwritten)
    initial_output = copy.deepcopy(api_response)

    print(
        f"[STEP 2] initial_output => "
        f"Prediction: {initial_output['prediction']} | "
        f"Probability: {initial_output['probability']} | "
        f"Fairness: {initial_output.get('fairness', {}).get('score', 'N/A')}"
    )

    # ==============================================================
    # STEP 3: FAIRLENS MIDDLEWARE (interpret + simulate + report)
    # ==============================================================
    print(f"\n[STEP 3] Running FairLens middleware...")

    middleware = FairLensMiddleware(
        bias_threshold=10,
        predict_fn=predict_fn if not no_api else None,
    )

    result = middleware.process(
        api_response=initial_output,
        user_email=user_email,
        user_features=original_input,
        run_simulation=not no_sim,
    )

    print(f"\n[STEP 3] Bias Score: {result['database_record']['bias_score']}")
    print(f"[STEP 3] Status: {result['database_record']['bias_status']}")

    if "simulation" in result:
        sim = result["simulation"]
        n_iter = len(sim.get("iterations_log", []))
        print(f"[STEP 3] Simulation: {n_iter} iterations")
        summary = sim.get("improvement_summary", "")
        print(f"[STEP 3] Summary: {summary[:80]}...")

    # ==============================================================
    # STEP 4: GENERATE REPORT TEXT (already done by middleware)
    # ==============================================================
    print(f"\n[STEP 4] Report: {len(result.get('report_text', ''))} chars")

    # ==============================================================
    # STEP 5: GENERATE PDF → /reports/
    # ==============================================================
    print("\n[STEP 5] Generating PDF report...")
    reports_dir = os.getenv("REPORTS_DIR", "reports")
    pdf_service = PDFService(reports_dir=reports_dir)
    pdf_path = pdf_service.generate(
        report_text=result["report_text"],
        file_name=result["file_metadata"]["file_name"],
    )
    if not pdf_path:
        print("[FATAL] PDF generation failed. Aborting.")
        sys.exit(1)

    # ==============================================================
    # STEP 6: STORE IN DATABASE
    # ==============================================================
    print("\n[STEP 6] Saving audit record...")
    db_path = os.getenv("DB_PATH", "fairlens_reports.db")
    db_service = DatabaseService(db_path=db_path)
    row_id = db_service.save(
        database_record=result["database_record"],
        pdf_path=pdf_path,
    )

    # ==============================================================
    # STEP 7: EMAIL DISPATCH (MANDATORY)
    # ==============================================================
    email_sent = False

    if no_email:
        print("\n[STEP 7] Email: Skipped (--no-email flag)")
        email_status = "skipped"

    elif not user_email:
        print("\n[STEP 7] Email: CANNOT SEND — no valid email resolved")
        print("         Report saved to PDF and database for manual retrieval.")
        email_status = "no_email"

    elif not validate_email(user_email):
        print(f"\n[STEP 7] Email: CANNOT SEND — invalid format: '{user_email}'")
        email_status = "invalid_email"

    else:
        sender_email = os.getenv("EMAIL_USER", "").strip()
        sender_pass = os.getenv("EMAIL_PASS", "").strip()

        # --- EMAIL DEBUG BLOCK ---
        print(f"\n[STEP 7] Email Dispatch:")
        print(f"  Sender:    '{sender_email}'")
        print(f"  Password:  {'*' * len(sender_pass)} ({len(sender_pass)} chars)")
        print(f"  Recipient: '{user_email}'")
        print(f"  PDF:       '{pdf_path}'")
        print(f"  PDF exists: {os.path.exists(pdf_path) if pdf_path else False}")
        print(f"  PDF size:  {os.path.getsize(pdf_path):,} bytes" if pdf_path and os.path.exists(pdf_path) else "")

        if not sender_email or not sender_pass:
            print("[STEP 7] Email: FAILED — SMTP not configured in .env")
            print("         Set EMAIL_USER=your@gmail.com and EMAIL_PASS=your_app_password")
            email_status = "failed"
        elif "@" not in sender_email:
            print(f"[STEP 7] Email: FAILED — Invalid sender: '{sender_email}'")
            email_status = "failed"
        elif not pdf_path or not os.path.exists(pdf_path):
            print(f"[STEP 7] Email: FAILED — PDF not found: {pdf_path}")
            email_status = "failed"
        else:
            print(f"[STEP 7] Sending to {user_email}...")
            try:
                email_service = EmailService(sender_email, sender_pass)
                email_sent = email_service.send(
                    recipient_email=user_email,
                    pdf_path=pdf_path,
                    subject=result["email_payload"]["subject"],
                )
                if email_sent:
                    print(f"[STEP 7] Email: SENT successfully to {user_email}")
                    email_status = "sent"
                else:
                    print(f"[STEP 7] Email: FAILED — check error logs above")
                    print("         Common fixes:")
                    print("         1. Enable 2FA on Gmail")
                    print("         2. Generate App Password: https://myaccount.google.com/apppasswords")
                    print("         3. Set EMAIL_PASS to the 16-char App Password (no spaces)")
                    email_status = "failed"
            except Exception as e:
                print(f"[STEP 7] Email: FAILED with exception: {e}")
                email_status = "failed"

    # ==============================================================
    # INTEGRITY CHECK
    # ==============================================================
    coerced_check = InputValidator.coerce_types(features)
    for key in original_input:
        if key in coerced_check and original_input[key] != coerced_check[key]:
            print(f"[INTEGRITY VIOLATION] original_input['{key}'] was mutated!")

    # ==============================================================
    # BUILD FINAL OUTPUT
    # ==============================================================
    result["email_used"] = user_email
    result["email_status"] = email_status
    result["file_path"] = pdf_path

    # ==============================================================
    # SUMMARY
    # ==============================================================
    print("\n" + "=" * 65)
    print("  PIPELINE COMPLETE")
    print("=" * 65)
    print(f"  Input:        {input_file} (unchanged)")
    print(f"  Email Used:   {user_email or '(none)'}")
    print(f"  Email Status: {email_status}")
    print(f"  PDF:          {pdf_path}")
    print(f"  Database:     Row #{row_id} in {db_path}")
    if "simulation" in result:
        n = len(result["simulation"].get("iterations_log", []))
        print(f"  Simulation:   {n} iterations")
        if "final_output" in result["simulation"]:
            fo = result["simulation"]["final_output"]
            print(
                f"  Best:         {fo.get('prediction')} | "
                f"Prob: {fo.get('probability')} | "
                f"Fairness: {fo.get('fairness_score')}"
            )
    print("=" * 65)

    # Save full JSON output
    output_file = "fairlens_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] Structured output: {output_file}")

    return result


# ===================================================================
# CLI ENTRYPOINT
# ===================================================================
def main():
    parser = argparse.ArgumentParser(
        description="FairLens v5 — User-Complete Pipeline"
    )
    parser.add_argument(
        "--input", type=str, default="sample_input.json",
        help="Path to JSON input file (default: sample_input.json)",
    )
    parser.add_argument(
        "--no-email", action="store_true",
        help="Skip email sending (report saved to PDF/DB only)",
    )
    parser.add_argument(
        "--no-api", action="store_true",
        help="Offline mode (use sample response)",
    )
    parser.add_argument(
        "--no-sim", action="store_true",
        help="Skip What-If simulation",
    )
    args = parser.parse_args()

    run_pipeline(
        input_file=args.input,
        no_email=args.no_email,
        no_api=args.no_api,
        no_sim=args.no_sim,
    )


if __name__ == "__main__":
    main()
