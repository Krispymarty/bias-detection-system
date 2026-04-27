"""
FairSight AI — What-If Simulator Export System
Supports JSON, CSV, and PDF report generation.
"""

import json
import pandas as pd
from io import BytesIO
from typing import Dict, Any, Optional
from datetime import datetime


def _timestamp() -> str:
    """Current timestamp for reports."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_str(text) -> str:
    """Sanitize text for fpdf (latin-1 safe). Replace unicode chars that crash fpdf."""
    s = str(text)
    replacements = {
        "\u2014": "-",   # em-dash
        "\u2013": "-",   # en-dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u2022": "*",   # bullet
        "\u00a0": " ",   # non-breaking space
    }
    for orig, repl in replacements.items():
        s = s.replace(orig, repl)
    # Final fallback: strip anything non-latin-1
    return s.encode("latin-1", errors="replace").decode("latin-1")


def export_json(results: Dict[str, Any], input_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Export simulation results as formatted JSON.
    Includes both results and input configuration for reproducibility.
    """
    report = {
        "report_type": "FairSight AI — What-If Simulation Report",
        "generated_at": _timestamp(),
        "version": "2.0",
        "summary": {
            "fairness_score": results.get("fairness", 0),
            "accuracy": results.get("accuracy", 0),
            "bias_index": results.get("bias", 0),
            "risk_level": results.get("risk", "N/A"),
            "unbiased_percentage": results.get("unbiased", 0),
        },
        "detailed_metrics": results.get("details", {}),
    }
    if input_data:
        report["simulation_config"] = input_data

    return json.dumps(report, indent=4, default=str)


def export_csv(results: Dict[str, Any], input_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Export simulation results as CSV with metrics and details.
    """
    details = results.get("details", {})

    rows = [
        {"Category": "Summary", "Metric": "Fairness Score", "Value": results.get("fairness", 0), "Unit": "%"},
        {"Category": "Summary", "Metric": "Accuracy", "Value": results.get("accuracy", 0), "Unit": "%"},
        {"Category": "Summary", "Metric": "Bias Index", "Value": results.get("bias", 0), "Unit": "ratio"},
        {"Category": "Summary", "Metric": "Risk Level", "Value": results.get("risk", "N/A"), "Unit": "—"},
        {"Category": "Summary", "Metric": "Unbiased %", "Value": results.get("unbiased", 0), "Unit": "%"},
        {"Category": "Disparity", "Metric": "Demographic Parity Diff", "Value": details.get("demographic_parity_diff", "—"), "Unit": "ratio"},
        {"Category": "Disparity", "Metric": "Equalized Odds Diff", "Value": details.get("equalized_odds_diff", "—"), "Unit": "ratio"},
        {"Category": "Group", "Metric": "Male Approval Rate", "Value": details.get("male_approval_rate", "—"), "Unit": "%"},
        {"Category": "Group", "Metric": "Female Approval Rate", "Value": details.get("female_approval_rate", "—"), "Unit": "%"},
        {"Category": "Group", "Metric": "Male Accuracy", "Value": details.get("male_accuracy", "—"), "Unit": "%"},
        {"Category": "Group", "Metric": "Female Accuracy", "Value": details.get("female_accuracy", "—"), "Unit": "%"},
        {"Category": "Model", "Metric": "Sample Size", "Value": details.get("sample_size", "—"), "Unit": "records"},
        {"Category": "Model", "Metric": "Positive Rate", "Value": details.get("positive_rate", "—"), "Unit": "%"},
        {"Category": "Model", "Metric": "Model Type", "Value": details.get("model_type", "—"), "Unit": "—"},
    ]

    if input_data:
        rows.extend([
            {"Category": "Config", "Metric": "Gender Ratio (% Female)", "Value": input_data.get("gender_ratio", "—"), "Unit": "%"},
            {"Category": "Config", "Metric": "Age Range", "Value": f"{input_data.get('age_min', '—')}–{input_data.get('age_max', '—')}", "Unit": "years"},
            {"Category": "Config", "Metric": "Income Diversity", "Value": input_data.get("income_diversity", "—"), "Unit": "/10"},
            {"Category": "Config", "Metric": "Education Bias", "Value": input_data.get("education_bias", "—"), "Unit": "/10"},
        ])

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def export_pdf(results: Dict[str, Any], input_data: Optional[Dict[str, Any]] = None) -> BytesIO:
    """
    Export simulation results as a PDF audit report.
    Uses fpdf if available, falls back to plain text.
    """
    details = results.get("details", {})
    buf = BytesIO()

    try:
        from fpdf import FPDF # type: ignore

        class AuditPDF(FPDF):
            def header(self):
                self.set_font("Arial", "B", 18)
                self.set_text_color(0, 200, 166)
                self.cell(0, 12, "FairSight AI", 0, 1, "C")
                self.set_font("Arial", "", 10)
                self.set_text_color(120, 120, 120)
                self.cell(0, 6, "AI Fairness Simulation Audit Report", 0, 1, "C")
                self.cell(0, 6, f"Generated: {_timestamp()}", 0, 1, "C")
                self.ln(8)
                self.set_draw_color(0, 200, 166)
                self.line(10, self.get_y(), 200, self.get_y())
                self.ln(6)

            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", "I", 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f"FairSight AI v2.0 | Page {self.page_no()}", 0, 0, "C")

        pdf = AuditPDF()
        pdf.add_page()

        # Summary Section
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 10, "Executive Summary", 0, 1)
        pdf.ln(2)

        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(60, 60, 60)

        risk = results.get("risk", "N/A")
        risk_color = {"Low": (0, 180, 0), "Medium": (200, 150, 0), "High": (200, 50, 50)}
        r, g, b = risk_color.get(risk, (100, 100, 100))

        summary_items = [
            ("Fairness Score", f"{results.get('fairness', 0)}%"),
            ("Model Accuracy", f"{results.get('accuracy', 0)}%"),
            ("Bias Index", f"{results.get('bias', 0)}"),
            ("Unbiased Percentage", f"{results.get('unbiased', 0)}%"),
        ]

        for label, value in summary_items:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(80, 8, _safe_str(f"  {label}:"), 0, 0)
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 8, _safe_str(value), 0, 1)

        pdf.set_font("Arial", "B", 11)
        pdf.cell(80, 8, "  Risk Level:", 0, 0)
        pdf.set_text_color(r, g, b)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, risk, 0, 1)
        pdf.set_text_color(60, 60, 60)

        # Detailed Metrics
        pdf.ln(6)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 10, "Detailed Metrics", 0, 1)
        pdf.ln(2)

        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(60, 60, 60)

        detail_items = [
            ("Demographic Parity Diff", details.get("demographic_parity_diff", "N/A")),
            ("Equalized Odds Diff", details.get("equalized_odds_diff", "N/A")),
            ("Male Approval Rate", f"{details.get('male_approval_rate', 'N/A')}%"),
            ("Female Approval Rate", f"{details.get('female_approval_rate', 'N/A')}%"),
            ("Male Accuracy", f"{details.get('male_accuracy', 'N/A')}%"),
            ("Female Accuracy", f"{details.get('female_accuracy', 'N/A')}%"),
            ("Sample Size", details.get("sample_size", "N/A")),
            ("Model Type", details.get("model_type", "N/A")),
        ]

        for label, value in detail_items:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(80, 7, _safe_str(f"  {label}:"), 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 7, _safe_str(value), 0, 1)

        # Configuration
        if input_data:
            pdf.ln(6)
            pdf.set_font("Arial", "B", 14)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 10, "Simulation Configuration", 0, 1)
            pdf.ln(2)

            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(60, 60, 60)
            config_items = [
                ("Gender Ratio (% Female)", f"{input_data.get('gender_ratio', 'N/A')}%"),
                ("Age Range", f"{input_data.get('age_min', 'N/A')} - {input_data.get('age_max', 'N/A')}"),
                ("Income Diversity", f"{input_data.get('income_diversity', 'N/A')}/10"),
                ("Education Bias", f"{input_data.get('education_bias', 'N/A')}/10"),
                ("Sample Size", input_data.get("sample_size", "N/A")),
                ("Model", input_data.get("model_type", "N/A")),
            ]
            for label, value in config_items:
                pdf.set_font("Arial", "B", 10)
                pdf.cell(80, 7, _safe_str(f"  {label}:"), 0, 0)
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 7, _safe_str(value), 0, 1)

        pdf_bytes = pdf.output(dest="S")
        if isinstance(pdf_bytes, str):
            buf.write(pdf_bytes.encode("latin1"))
        else:
            buf.write(pdf_bytes)

    except ImportError:
        # Fallback: plain text report
        lines = [
            "=" * 50,
            "FAIRSIGHT AI - SIMULATION AUDIT REPORT",
            "=" * 50,
            f"Generated: {_timestamp()}",
            "",
            "SUMMARY",
            "-" * 30,
            f"Fairness Score:      {results.get('fairness', 0)}%",
            f"Model Accuracy:      {results.get('accuracy', 0)}%",
            f"Bias Index:          {results.get('bias', 0)}",
            f"Risk Level:          {results.get('risk', 'N/A')}",
            f"Unbiased %:          {results.get('unbiased', 0)}%",
            "",
            "DETAILED METRICS",
            "-" * 30,
            f"DP Difference:       {details.get('demographic_parity_diff', 'N/A')}",
            f"EO Difference:       {details.get('equalized_odds_diff', 'N/A')}",
            f"Male Approval Rate:  {details.get('male_approval_rate', 'N/A')}%",
            f"Female Approval Rate:{details.get('female_approval_rate', 'N/A')}%",
            "",
            "=" * 50,
        ]
        buf.write("\n".join(lines).encode("utf-8"))

    buf.seek(0)
    return buf


def generate_mitigation_report(input_data: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a smart AI fairness mitigation report based on inputs and simulation results.
    """
    gender_ratio = input_data.get("gender_ratio", 50)
    education_bias = input_data.get("education_bias", 3)
    income_diversity = input_data.get("income_diversity", 5)
    
    fairness = results.get("fairness", 0)
    bias = results.get("bias", 0)
    risk = results.get("risk", "Unknown")
    
    # 1. Summary
    summary = {
        "fairness_score": fairness,
        "bias_score": bias,
        "risk_level": risk
    }
    
    # 2. Bias Analysis
    bias_analysis = {
        "gender_imbalance": "High" if gender_ratio < 40 or gender_ratio > 60 else "Low",
        "age_skew": "Moderate",  # Placeholder if age wasn't strictly analyzed for bias gap
        "income_imbalance": "High" if income_diversity < 5 else "Low",
        "education_bias_impact": "High" if education_bias > 5 else "Low"
    }
    
    # 3. Root Cause Analysis
    root_causes = []
    if education_bias > 5:
        root_causes.append("Low fairness due to high education bias factor.")
    if gender_ratio < 40 or gender_ratio > 60:
        root_causes.append("Gender ratio imbalance causing demographic disparity.")
    if income_diversity < 5:
        root_causes.append("Low income diversity restricting equitable approval rates.")
    
    root_cause_str = " ".join(root_causes) if root_causes else "Model shows natural disparity not strongly linked to a single demographic parameter."
    
    # 4. Mitigation Suggestions
    recommendations = []
    if gender_ratio < 40 or gender_ratio > 60:
        recommendations.append("Balance gender distribution closer to 50% in the training data.")
    if education_bias > 5:
        recommendations.append("Reduce education bias weight to improve equalized odds.")
    if income_diversity < 5:
        recommendations.append("Increase income diversity sampling to capture a broader socioeconomic baseline.")
    if fairness < 70:
        recommendations.append("Use fairness-aware model or adversarial debiasing preprocessing.")
        
    if not recommendations:
        recommendations.append("Maintain current configuration as fairness metrics are within acceptable thresholds.")
        
    # 5. Improvement Estimate
    if fairness < 80:
        expected_improvement = "Fairness may increase by 10-15% if recommendations are applied."
    else:
        expected_improvement = "Marginal improvements (1-3%) expected; model is already highly fair."
        
    # 6. Group Fairness
    group_fairness = {}
    if "group_analysis" in results:
        ga = results["group_analysis"]
        male = ga.get("male", {})
        female = ga.get("female", {})
        m_app = male.get("approval_rate", 0)
        f_app = female.get("approval_rate", 0)
        m_acc = male.get("accuracy", 0)
        f_acc = female.get("accuracy", 0)
        group_fairness = {
            "male_approval_rate": m_app,
            "female_approval_rate": f_app,
            "approval_disparity": abs(m_app - f_app),
            "male_accuracy": m_acc,
            "female_accuracy": f_acc,
            "accuracy_gap": abs(m_acc - f_acc)
        }
        
    # 7. Final Output
    return {
        "summary": summary,
        "bias_analysis": bias_analysis,
        "root_cause": root_cause_str,
        "recommendations": recommendations,
        "expected_improvement": expected_improvement,
        "group_analysis": group_fairness,
        "timestamp": _timestamp()
    }
