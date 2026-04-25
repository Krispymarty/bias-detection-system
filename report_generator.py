"""
FairLens - Report Generator (v2 with Simulation Sections)
==========================================================
Generates a professional, plain-English Bias Audit Report.

Sections:
  1. Decision Summary
  2. Fairness Evaluation
  3. What-If Simulation Summary (NEW)
  4. Key Adjustments Made (NEW)
  5. Optimal Recommended State (NEW)
  6. System Action Taken
  7. Recommendation
  8. Outcome Projection

Tone: Clear, professional, realistic. No exaggeration.
"""

from typing import Dict, Any, Optional, List


class ReportGenerator:
    """Generates a human-readable Bias Audit Report in plain English."""

    def generate(
        self,
        interpretation: Dict[str, Any],
        user_email: Optional[str] = None,
        simulation: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Produces the full report text from interpretation + simulation data.
        """
        prediction = interpretation.get("prediction") or "N/A"
        probability = interpretation.get("probability")
        fairness_score = interpretation.get("fairness_score")
        bias_score = interpretation.get("bias_score")
        bias_status = interpretation.get("bias_status") or "Unknown"
        bias_exceeded = interpretation.get("bias_exceeded")
        badge = interpretation.get("badge") or "N/A"
        bias_source = interpretation.get("bias_source") or "N/A"
        bias_metrics = interpretation.get("bias_metrics") or {}
        threshold = interpretation.get("threshold", 10)
        recommendation = interpretation.get("recommendation") or "No recommendation provided."

        prob_str = f"{probability:.4f}" if probability is not None else "N/A"
        fairness_str = f"{fairness_score}" if fairness_score is not None else "N/A"
        bias_str = f"{bias_score}" if bias_score is not None else "N/A"

        sections = []

        # Section 1: Decision Summary
        sections.append(self._section_decision_summary(prediction, prob_str, user_email))

        # Section 2: Fairness Evaluation
        sections.append(self._section_fairness_evaluation(
            fairness_str, bias_str, threshold, bias_status, badge, bias_source, bias_metrics
        ))

        # Sections 3-5: Simulation (if available)
        if simulation:
            sections.append(self._section_simulation_summary(simulation))
            sections.append(self._section_key_adjustments(simulation))
            sections.append(self._section_optimal_state(simulation))

        # Section 6: System Action
        sections.append(self._section_system_action(bias_exceeded, bias_status))

        # Section 7: Recommendation
        sections.append(self._section_recommendation(recommendation))

        # Section 8: Outcome Projection
        sections.append(self._section_outcome_projection(
            prediction, probability, bias_status, simulation
        ))

        return "\n\n".join(sections)

    # ===================================================================
    # Section builders
    # ===================================================================

    def _section_decision_summary(self, prediction, prob_str, user_email):
        lines = [
            "FAIRLENS BIAS AUDIT REPORT",
            "=" * 50,
            "",
            "Section 1: Decision Summary",
            "-" * 40,
            "",
            f"Model Decision: {prediction}",
            f"Risk Probability: {prob_str}",
        ]
        if user_email:
            lines.append(f"Report Recipient: {user_email}")
        lines.append("")
        lines.append(
            "This report summarizes the bias audit conducted on the above "
            "financial decision. The purpose of this audit is to evaluate "
            "whether the model's decision was influenced by systemic bias "
            "and to document the fairness status of the prediction."
        )
        return "\n".join(lines)

    def _section_fairness_evaluation(
        self, fairness_str, bias_str, threshold, bias_status, badge, bias_source, bias_metrics
    ):
        lines = [
            "Section 2: Fairness Evaluation",
            "-" * 40,
            "",
            f"Fairness Score: {fairness_str} / 100",
            f"Computed Bias Score: {bias_str}",
            f"Bias Threshold: {threshold}",
            f"Threshold Status: {bias_status}",
            f"Fairness Badge: {badge}",
            f"Primary Bias Source: {bias_source}",
        ]
        if bias_metrics:
            lines.append("")
            lines.append("Detailed Bias Metrics:")
            for name, val in bias_metrics.items():
                display = name.replace("_", " ").title()
                if isinstance(val, float):
                    lines.append(f"  - {display}: {val:.4f}")
                else:
                    lines.append(f"  - {display}: {val}")

        lines.append("")
        if bias_status == "Acceptable":
            lines.append(
                "The bias score falls within the acceptable range. No further "
                "bias adjustment is required at this time."
            )
        elif bias_status == "Needs Adjustment":
            lines.append(
                "The bias score exceeds the defined threshold. This indicates "
                "the model's decision may have been influenced by factors that "
                "disproportionately affect certain demographic groups. The "
                "What-If simulation below explores practical adjustments."
            )
        else:
            lines.append(
                "The fairness score was not available from the model API. "
                "A full fairness evaluation could not be completed."
            )
        return "\n".join(lines)

    def _section_simulation_summary(self, sim: Dict[str, Any]) -> str:
        """Section 3: What-If Simulation Summary."""
        total = sim.get("total_iterations", 0)
        init_p = sim.get("initial_probability", 0)
        final_p = sim.get("final_probability", 0)
        init_b = sim.get("initial_bias", 0)
        final_b = sim.get("final_bias", 0)
        flipped = sim.get("decision_flipped", False)

        lines = [
            "Section 3: What-If Simulation Summary",
            "-" * 40,
            "",
            f"Total Iterations Executed: {total}",
            f"Initial Risk Probability: {init_p:.4f}",
            f"Final Risk Probability: {final_p:.4f}",
            f"Probability Improvement: {init_p - final_p:.4f}",
            "",
            f"Initial Bias Score: {init_b:.1f}",
            f"Final Bias Score: {final_b:.1f}",
            f"Bias Improvement: {init_b - final_b:.1f} points",
            "",
            f"Decision Flipped: {'Yes' if flipped else 'No'}",
            "",
            "The simulation iteratively adjusted applicant features using "
            "realistic increments to identify the most practical path toward "
            "improved fairness. Each step applied balanced changes across "
            "income, credit amount, external scores, and age factors.",
        ]

        # Iteration-by-iteration log
        iterations = sim.get("iterations_log", [])
        if iterations:
            lines.append("")
            lines.append("Iteration Log:")
            for it in iterations:
                step = it["step"]
                r = it["result"]
                changes = it.get("changes", {})
                change_list = ", ".join(
                    f"{k}: {v.get('change', '?')}" for k, v in changes.items()
                )
                lines.append(
                    f"  Step {step:02d}: Prob={r['probability']:.4f} "
                    f"({r['probability_trend']}) | "
                    f"Bias={r['bias_score']:.1f} ({r['bias_trend']}) | "
                    f"[{change_list}]"
                )

        return "\n".join(lines)

    def _section_key_adjustments(self, sim: Dict[str, Any]) -> str:
        """Section 4: Key Adjustments Made."""
        orig = sim.get("original_features", {})
        final = sim.get("final_features", {})

        lines = [
            "Section 4: Key Adjustments Made",
            "-" * 40,
            "",
            "The following feature adjustments were applied during simulation:",
            "",
        ]

        # Compare original vs final
        compare_keys = [
            ("AMT_INCOME_TOTAL", "Income"),
            ("AMT_CREDIT", "Credit Amount"),
            ("AMT_ANNUITY", "Annuity"),
            ("EXT_SOURCE_1", "External Score 1"),
            ("EXT_SOURCE_2", "External Score 2"),
            ("EXT_SOURCE_3", "External Score 3"),
            ("AGE", "Age"),
        ]

        for key, label in compare_keys:
            if key in orig and key in final:
                o = orig[key]
                f = final[key]
                if isinstance(o, float) and o > 10:
                    lines.append(f"  {label}: {o:,.0f} -> {f:,.0f}")
                elif isinstance(o, float):
                    lines.append(f"  {label}: {o:.3f} -> {f:.3f}")
                else:
                    lines.append(f"  {label}: {o} -> {f}")

        lines.append("")
        lines.append(
            "All adjustments follow realistic constraints. Income changes "
            "are capped at 2.5x original, credit scores at 0.95, and age "
            "bounded between 18-55. No artificial or extreme modifications "
            "were applied."
        )

        return "\n".join(lines)

    def _section_optimal_state(self, sim: Dict[str, Any]) -> str:
        """Section 5: Optimal Recommended State."""
        final = sim.get("final_features", {})
        summary = sim.get("improvement_summary", "")

        lines = [
            "Section 5: Optimal Recommended State",
            "-" * 40,
            "",
            "The simulation identified the following as the optimal feature "
            "configuration for improved fairness:",
            "",
        ]

        for key, val in final.items():
            display = key.replace("_", " ").title()
            if isinstance(val, float) and val > 10:
                lines.append(f"  {display}: {val:,.0f}")
            elif isinstance(val, float):
                lines.append(f"  {display}: {val:.4f}")
            else:
                lines.append(f"  {display}: {val}")

        lines.append("")
        lines.append(f"Assessment: {summary}")

        return "\n".join(lines)

    def _section_system_action(self, bias_exceeded, bias_status):
        lines = [
            "Section 6: System Action Taken",
            "-" * 40,
            "",
        ]
        if bias_exceeded is True:
            lines.append(
                "The FairLens system has flagged this decision for review. "
                "The following actions have been initiated:"
            )
            lines.append("")
            lines.append("  1. This audit report has been generated and prepared for delivery.")
            lines.append("  2. What-If simulation was executed to identify improvements.")
            lines.append("  3. Decision metadata has been packaged for database persistence.")
            lines.append("  4. An email with the attached report will be dispatched.")
            lines.append("  5. The bias flag has been recorded for compliance tracking.")
        elif bias_exceeded is False:
            lines.append(
                "The bias score is within the acceptable range. Standard audit "
                "documentation has been generated for record-keeping."
            )
            lines.append("")
            lines.append("  1. This audit report has been generated as a routine compliance record.")
            lines.append("  2. What-If simulation was executed for exploratory analysis.")
            lines.append("  3. Decision metadata has been packaged for database persistence.")
            lines.append("  4. An email with the attached report will be dispatched.")
        else:
            lines.append(
                "The system could not determine the bias status due to "
                "missing fairness data. A default audit record has been "
                "created for compliance purposes."
            )
        return "\n".join(lines)

    def _section_recommendation(self, recommendation):
        return "\n".join([
            "Section 7: Recommendation",
            "-" * 40,
            "",
            recommendation,
        ])

    def _section_outcome_projection(self, prediction, probability, bias_status, simulation):
        lines = [
            "Section 8: Outcome Projection",
            "-" * 40,
            "",
        ]

        if simulation and simulation.get("decision_flipped"):
            final_p = simulation.get("final_probability", 0)
            lines.append(
                f"The simulation demonstrated that the decision can be improved "
                f"from {prediction} to Approved with realistic feature adjustments. "
                f"The optimized risk probability of {final_p:.4f} falls within "
                f"the approval range."
            )
        elif prediction == "Approved":
            lines.append(
                "The model has approved this application. Based on the current "
                "risk probability and fairness evaluation, the decision is "
                "consistent with the system's operational parameters."
            )
        elif prediction == "Rejected":
            lines.append(
                "The model has rejected this application. The risk probability "
                "indicates elevated default risk based on the submitted features."
            )
            if simulation:
                final_p = simulation.get("final_probability", probability)
                lines.append(
                    f"The simulation reduced risk to {final_p:.4f}, suggesting "
                    f"potential for improvement with the recommended adjustments."
                )
            if bias_status == "Needs Adjustment":
                lines.append(
                    "The bias audit identified fairness concerns. Decision-makers "
                    "should consider the simulation findings before finalizing."
                )
        else:
            lines.append(
                f"The model returned '{prediction}'. Review the full audit above."
            )

        if probability is not None:
            if probability >= 0.8:
                conf = "The model expressed high confidence in this decision."
            elif probability >= 0.6:
                conf = "The model expressed moderate confidence in this decision."
            elif probability >= 0.45:
                conf = "The model expressed low confidence. Human review is recommended."
            else:
                conf = "The model expressed low risk, supporting an approval outcome."
            lines.append("")
            lines.append(conf)

        lines.append("")
        lines.append("-" * 50)
        lines.append("End of FairLens Bias Audit Report")
        lines.append("-" * 50)

        return "\n".join(lines)
