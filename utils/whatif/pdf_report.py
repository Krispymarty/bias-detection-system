"""
FairSight AI — PDF Report Generator
Generates comparison reports from audit results.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ── Brand Colors ──
CYAN_HEX = "#00CCA6"
DARK_BG = "#0a0f1e"
PURPLE_HEX = "#A855F7"
RED_HEX = "#FF5050"
YELLOW_HEX = "#FFD700"


def _build_styles():
    """Create branded paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=22, textColor=HexColor("#111827"),
        spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#666666"),
        spaceAfter=20, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        "SectionHead", parent=styles["Heading2"],
        fontSize=13, textColor=HexColor(CYAN_HEX),
        spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "BodyText2", parent=styles["Normal"],
        fontSize=9.5, textColor=HexColor("#333333"),
        leading=14, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        "InsightBullet", parent=styles["Normal"],
        fontSize=9.5, textColor=HexColor("#444444"),
        leading=14, leftIndent=16, spaceAfter=4, bulletIndent=6
    ))
    return styles


def generate_explanation(results, report, comparison=None):
    """Generate dynamic explanation points based on real data."""
    points = []

    # From audit results
    prediction = results.get("prediction", "N/A")
    fairness_score = results.get("fairness_score", 0) or 0
    bias = results.get("bias", 0) or 0
    risk = results.get("risk", "Unknown")
    probability = results.get("probability", 0) or 0
    confidence = results.get("confidence", "N/A")
    mitigation = results.get("mitigation_applied", False)

    if prediction == "Approved":
        points.append(f"The applicant was APPROVED with a probability of {probability:.2%}.")
    else:
        points.append(f"The applicant was REJECTED with a probability of {probability:.2%}.")

    if fairness_score >= 80:
        points.append(f"Fairness score of {fairness_score}% indicates strong equitable treatment across demographic groups.")
    elif fairness_score >= 60:
        points.append(f"Fairness score of {fairness_score}% shows moderate equity — some bias mitigation may be beneficial.")
    else:
        points.append(f"Fairness score of {fairness_score}% is below acceptable thresholds — significant bias detected.")

    if bias > 0.3:
        points.append(f"Selection rate gap of {bias:.4f} reveals substantial disparity between demographic groups.")
    elif bias > 0.1:
        points.append(f"Selection rate gap of {bias:.4f} indicates moderate disparity between groups.")
    else:
        points.append(f"Selection rate gap of {bias:.4f} is within acceptable fairness bounds.")

    if mitigation:
        points.append("Bias mitigation was applied using Fairlearn ThresholdOptimizer with equalized odds constraint.")
    else:
        points.append("No bias mitigation was applied. Consider enabling mitigation for fairer outcomes.")

    points.append(f"Model confidence: {confidence}. Risk assessment: {risk}.")

    # From fairness report
    if isinstance(report, dict) and "improvement" in report:
        imp = report["improvement"]
        gap_change = imp.get("selection_rate_gap_change", 0)
        acc_change = imp.get("accuracy_change", 0)
        if gap_change < -0.1:
            points.append(f"Bias gap improved by {abs(gap_change):.4f} after mitigation — a significant reduction in discrimination.")
        if acc_change < -0.05:
            points.append(f"Accuracy decreased by {abs(acc_change):.4f} — a typical trade-off when optimizing for fairness.")

    return points


def generate_pdf_report(results, report, input_payload, comparison=None):
    """
    Generate a professional PDF report.
    Returns bytes buffer ready for st.download_button.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20*mm, bottomMargin=15*mm,
        leftMargin=18*mm, rightMargin=18*mm
    )
    styles = _build_styles()
    elements = []

    # ── Title ──
    elements.append(Paragraph("FairSight AI", styles["ReportTitle"]))
    elements.append(Paragraph("Bias Comparison Report", styles["ReportSubtitle"]))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}",
        styles["ReportSubtitle"]
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor(CYAN_HEX)))
    elements.append(Spacer(1, 8*mm))

    # ── Section 1: Input Summary ──
    elements.append(Paragraph("1. Input Configuration", styles["SectionHead"]))
    if isinstance(input_payload, dict):
        features = input_payload.get("features", {})
        input_rows = [
            ["Parameter", "Value"],
            ["Domain", input_payload.get("domain", "N/A")],
            ["Gender", features.get("CODE_GENDER", "N/A")],
            ["Age", str(features.get("AGE", "N/A"))],
            ["Income", f"${features.get('AMT_INCOME_TOTAL', 0):,.0f}"],
            ["Credit Amount", f"${features.get('AMT_CREDIT', 0):,.0f}"],
            ["Education", features.get("NAME_EDUCATION_TYPE", "N/A")],
            ["Occupation", features.get("OCCUPATION_TYPE", "N/A")],
            ["EXT Source Avg", f"{features.get('EXT_SOURCE_1', 0):.2f}"],
            ["Mitigation", "Enabled" if input_payload.get("apply_mitigation") else "Disabled"],
        ]
        t = Table(input_rows, colWidths=[140, 280])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(CYAN_HEX)),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F9F9F9"), HexColor("#FFFFFF")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)
    elements.append(Spacer(1, 6*mm))

    # ── Section 2: Audit Results ──
    elements.append(Paragraph("2. Audit Results", styles["SectionHead"]))
    if isinstance(results, dict):
        result_rows = [
            ["Metric", "Value"],
            ["Prediction", str(results.get("prediction", "N/A"))],
            ["Probability", f"{(results.get('probability', 0) or 0):.2%}"],
            ["Fairness Score", f"{results.get('fairness_score', 0) or 0}%"],
            ["Bias Gap", f"{results.get('bias', 0) or 0:.4f}"],
            ["Risk Level", str(results.get("risk", "Unknown"))],
            ["Confidence", str(results.get("confidence", "N/A"))],
            ["Mitigation Applied", "Yes" if results.get("mitigation_applied") else "No"],
        ]
        t = Table(result_rows, colWidths=[140, 280])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(PURPLE_HEX)),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F9F9F9"), HexColor("#FFFFFF")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)
    elements.append(Spacer(1, 6*mm))

    # ── Section 3: Fairness Report Comparison ──
    if isinstance(report, dict) and "baseline_model" in report:
        elements.append(Paragraph("3. Model Comparison: Baseline vs Fair", styles["SectionHead"]))
        baseline = report.get("baseline_model", {})
        fair = report.get("fair_model", {})
        improvement = report.get("improvement", {})

        comp_rows = [
            ["Metric", "Baseline", "Fair (Mitigated)", "Change"],
            ["Accuracy",
             f"{baseline.get('accuracy', 0):.4f}",
             f"{fair.get('accuracy', 0):.4f}",
             f"{improvement.get('accuracy_change', 0):+.4f}"],
            ["ROC AUC",
             f"{baseline.get('roc_auc', 0):.4f}",
             f"{fair.get('roc_auc', 0):.4f}",
             f"{improvement.get('auc_change', 0):+.4f}"],
            ["Selection Rate Gap",
             f"{baseline.get('selection_rate_gap', 0):.4f}",
             f"{fair.get('selection_rate_gap', 0):.4f}",
             f"{improvement.get('selection_rate_gap_change', 0):+.4f}"],
            ["TPR Gap",
             f"{baseline.get('tpr_gap', 0):.4f}",
             f"{fair.get('tpr_gap', 0):.4f}",
             f"{improvement.get('tpr_gap_change', 0):+.4f}"],
            ["FPR Gap",
             f"{baseline.get('fpr_gap', 0):.4f}",
             f"{fair.get('fpr_gap', 0):.4f}",
             f"{improvement.get('fpr_gap_change', 0):+.4f}"],
        ]
        t = Table(comp_rows, colWidths=[120, 100, 100, 100])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#111827")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F9F9F9"), HexColor("#FFFFFF")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 6*mm))

    # ── Section 4: AI Explanation ──
    section_num = "4" if isinstance(report, dict) and "baseline_model" in report else "3"
    elements.append(Paragraph(f"{section_num}. AI-Generated Explanation", styles["SectionHead"]))
    explanations = generate_explanation(results, report, comparison)
    for exp in explanations:
        elements.append(Paragraph(f"• {exp}", styles["InsightBullet"]))
    elements.append(Spacer(1, 6*mm))

    # ── Footer ──
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#CCCCCC")))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(
        "This report was auto-generated by FairSight AI. "
        "All metrics are based on real-time API responses from the bias-detection-system.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7.5,
                        textColor=HexColor("#999999"), alignment=TA_CENTER)
    ))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()
