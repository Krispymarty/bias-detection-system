"""
FairLens - Main Middleware Orchestrator (v2.1 — Input Integrity)
================================================================
Orchestrates the full pipeline with strict input preservation:

  1. Validate input format/types
  2. FREEZE original_input (immutable deep copy)
  3. Send ORIGINAL to interpreter (never modified)
  4. Store initial_output from API
  5. ONLY THEN run What-If on a COPY
  6. Clearly separate initial_output from simulated_outputs

CRITICAL RULES:
  - original_input is NEVER overwritten
  - First API evaluation uses EXACT input received
  - Simulation operates on independent copies only
"""

import copy
import json
from typing import Dict, Any, Optional, Callable
from .validator import InputValidator, InputValidationError
from .interpreter import FairnessInterpreter
from .simulator import WhatIfSimulator
from .report_generator import ReportGenerator
from .formatter import PDFContentFormatter
from .storage_builder import StorageWorkflowBuilder


class FairLensMiddleware:
    """
    Ethical AI middleware with strict input integrity guarantees.

    Pipeline:
        Validate -> Freeze -> Interpret (original) -> Simulate (copy)
        -> Report -> Format -> Storage Assembly
    """

    def __init__(self, bias_threshold: float = 10, predict_fn: Callable = None):
        self.bias_threshold = bias_threshold
        self.interpreter = FairnessInterpreter(threshold=bias_threshold)
        self.simulator = WhatIfSimulator(predict_fn=predict_fn)
        self.report_generator = ReportGenerator()
        self.formatter = PDFContentFormatter()
        self.storage_builder = StorageWorkflowBuilder()

    def process(
        self,
        api_response: Dict[str, Any],
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        user_features: Optional[Dict[str, Any]] = None,
        run_simulation: bool = True,
    ) -> Dict[str, Any]:
        """
        Full pipeline execution with input integrity guarantees.

        Parameters
        ----------
        api_response : dict
            JSON response from the FIRST model API call (initial_output).
            This is PRESERVED as-is in the output — never overwritten.
        user_email : str, optional
            Recipient email for the audit report.
        user_id : str, optional
            User identifier for database tracking.
        timestamp : str, optional
            Override timestamp (format: YYYYMMDD_HHMMSS).
        user_features : dict, optional
            Original user features. FROZEN immediately on receipt.
            Simulation runs on a COPY, never on this object.
        run_simulation : bool
            Whether to run the What-If simulation loop (default True).

        Returns
        -------
        dict
            Structured output with clearly separated initial_output
            and simulated_outputs.
        """
        # ============================================================
        # STEP 0: VALIDATE & FREEZE INPUT
        # ============================================================
        frozen_input = None
        if user_features is not None:
            # Attempt type coercion for string-encoded numbers
            coerced = InputValidator.coerce_types(user_features)

            # Validate against API schema
            is_valid, errors = InputValidator.validate(coerced)
            if not is_valid:
                print("[VALIDATION] Input validation warnings:")
                for err in errors:
                    print(f"  - {err}")
                # Non-fatal: log warnings but continue with best-effort
                # Fatal errors (missing fields) will surface downstream

            # FREEZE: create an immutable deep copy
            # This is the canonical original_input — NEVER modified
            frozen_input = InputValidator.freeze(coerced)

        # ============================================================
        # STEP 1: INTERPRET INITIAL API RESPONSE (from original input)
        # ============================================================
        # This api_response was generated from the ORIGINAL input
        # by the caller. We preserve it exactly as initial_output.
        initial_output = copy.deepcopy(api_response)
        interpretation = self.interpreter.interpret(initial_output)

        # ============================================================
        # STEP 2: WHAT-IF SIMULATION (on a COPY of frozen input)
        # ============================================================
        simulation_result = None
        if run_simulation and frozen_input is not None:
            # Pass a COPY to the simulator — frozen_input stays untouched
            simulation_copy = copy.deepcopy(frozen_input)
            simulation_result = self.simulator.simulate(
                original_features=simulation_copy,
                initial_api_response=initial_output,
                bias_threshold=self.bias_threshold,
            )

        # ============================================================
        # STEP 3: GENERATE REPORT
        # ============================================================
        raw_report = self.report_generator.generate(
            interpretation, user_email, simulation_result
        )

        # ============================================================
        # STEP 4: FORMAT FOR PDF
        # ============================================================
        pdf_report = self.formatter.format(raw_report)
        if not self.formatter.validate(pdf_report):
            pdf_report = self.formatter.format(pdf_report)

        # ============================================================
        # STEP 5: BUILD STORAGE OUTPUT
        # ============================================================
        result = self.storage_builder.build(
            interpretation=interpretation,
            report_text=pdf_report,
            user_email=user_email,
            user_id=user_id,
            timestamp=timestamp,
            simulation=simulation_result,
            initial_output=initial_output,
            original_input=frozen_input,
        )

        # ============================================================
        # INTEGRITY CHECK: verify original was not mutated
        # ============================================================
        if frozen_input is not None and user_features is not None:
            coerced_check = InputValidator.coerce_types(user_features)
            for key in frozen_input:
                if key in coerced_check:
                    if frozen_input[key] != coerced_check[key]:
                        print(
                            f"[INTEGRITY VIOLATION] original_input['{key}'] "
                            f"was mutated: {frozen_input[key]} != {coerced_check[key]}"
                        )

        return result

    def process_json(
        self,
        api_response_json: str,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        user_features: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Convenience method that accepts/returns JSON strings."""
        api_response = json.loads(api_response_json)
        result = self.process(api_response, user_email, user_id,
                              user_features=user_features)
        return json.dumps(result, indent=2, ensure_ascii=False)
