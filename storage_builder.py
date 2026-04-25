"""
FairLens - Storage Workflow Builder (v3 — Strict Output Format)
================================================================
Assembles structured output matching the strict JSON schema:

  original_input -> initial_output -> simulation -> file_metadata -> email_payload

CRITICAL: initial_output is NEVER overridden by simulation values.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class StorageWorkflowBuilder:
    """Builds structured storage workflow output for backend consumption."""

    REPORTS_DIR = "reports"
    EMAIL_SUBJECT = "FairLens Bias Audit Report"
    EMAIL_BODY = "Your report is attached."

    def build(
        self,
        interpretation: Dict[str, Any],
        report_text: str,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        simulation: Optional[Dict[str, Any]] = None,
        initial_output: Optional[Dict[str, Any]] = None,
        original_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assembles the complete FairLens output payload."""
        if timestamp is None:
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        else:
            ts = timestamp

        file_name = f"report_{ts}.pdf"
        file_path = f"{self.REPORTS_DIR}/{file_name}"

        file_metadata = {"file_name": file_name, "file_path": file_path}

        # Database record — uses INITIAL values only
        database_record = {
            "prediction": interpretation.get("prediction"),
            "probability": interpretation.get("probability"),
            "fairness_score": interpretation.get("fairness_score"),
            "bias_score": interpretation.get("bias_score"),
            "bias_status": interpretation.get("bias_status"),
            "recommendation": interpretation.get("recommendation"),
            "bias_source": interpretation.get("bias_source"),
            "user_email": user_email,
        }
        if user_id is not None:
            database_record["user_id"] = user_id

        # Email payload with mandatory send_required flag
        send_required = user_email is not None and len(user_email) > 0
        email_payload = {
            "to": user_email,
            "subject": self.EMAIL_SUBJECT,
            "body": self.EMAIL_BODY,
            "attachment_path": file_path,
            "send_required": send_required,
        }

        # Build result in strict schema order
        result = {}

        # 1. original_input (frozen, never modified)
        if original_input is not None:
            result["original_input"] = original_input

        # 2. initial_output (from first API call, preserved exactly)
        if initial_output is not None:
            result["initial_output"] = {
                "prediction": initial_output.get("prediction"),
                "probability": initial_output.get("probability"),
                "fairness": initial_output.get("fairness"),
                "recommendation": initial_output.get("recommendation"),
            }

        # 3. simulation block
        if simulation:
            sim_block = {
                "iterations_log": simulation.get("iterations_log", []),
                "final_features": simulation.get("final_features", {}),
                "final_output": simulation.get("final_output", {}),
                "improvement_summary": simulation.get(
                    "improvement_summary",
                    "Optimal improvement achieved without over-adjustment"
                ),
            }
            # Include best_output if available
            if "best_output" in simulation:
                sim_block["best_output"] = simulation["best_output"]
            result["simulation"] = sim_block

        # 4. Report text
        result["report_text"] = report_text

        # 5. File metadata
        result["file_metadata"] = file_metadata

        # 6. Database record
        result["database_record"] = database_record

        # 7. Email payload
        result["email_payload"] = email_payload

        return result
