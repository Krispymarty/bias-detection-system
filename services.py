"""
FairLens Backend Services
=========================
Production services that execute the storage workflow:
  - PDFService:    Generates actual PDF files from report_text
  - DatabaseService: Stores audit records in SQLite
  - EmailService:  Sends reports via Gmail SMTP
"""

import os
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, Any, Optional

from fpdf import FPDF


# ===================================================================
# 1. PDF SERVICE
# ===================================================================
class PDFService:
    """Generates a styled PDF from the FairLens report_text."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate(self, report_text: str, file_name: str) -> Optional[str]:
        """
        Creates a PDF file from plain report text.

        Returns the absolute path to the generated PDF, or None on failure.
        """
        # Safety net: strip any characters outside latin-1 range
        # fpdf2's built-in Helvetica font only supports latin-1 encoding
        safe_text = report_text.encode("latin-1", errors="ignore").decode("latin-1")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        left_margin = 10
        content_width = 190  # 210 - 2*10 margins

        # --- Header bar ---
        pdf.set_fill_color(30, 39, 73)  # Dark navy
        pdf.rect(0, 0, 210, 30, "F")
        pdf.set_xy(left_margin, 5)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(content_width, 12, txt="FAIRLENS BIAS AUDIT REPORT", ln=True, align="C")
        pdf.set_x(left_margin)
        pdf.set_font("Helvetica", size=9)
        pdf.cell(content_width, 8, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        pdf.set_y(35)

        # --- Body ---
        pdf.set_text_color(30, 30, 30)

        for line in safe_text.split("\n"):
            stripped = line.strip()

            # Section headings (lines starting with "Section")
            if stripped.startswith("Section "):
                pdf.ln(4)
                pdf.set_x(left_margin)
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(30, 39, 73)
                pdf.cell(content_width, 8, txt=stripped, ln=True)
                pdf.set_text_color(30, 30, 30)
                continue

            # Divider lines
            if stripped and all(c in "-=" for c in stripped):
                pdf.set_draw_color(180, 180, 180)
                pdf.line(left_margin, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(2)
                continue

            # Title line (already rendered in header)
            if stripped == "FAIRLENS BIAS AUDIT REPORT":
                continue

            # "End of" footer line
            if stripped.startswith("End of FairLens"):
                pdf.ln(2)
                pdf.set_x(left_margin)
                pdf.set_font("Helvetica", "I", 10)
                pdf.cell(content_width, 6, txt=stripped, ln=True, align="C")
                continue

            # Empty lines
            if not stripped:
                pdf.ln(3)
                continue

            # Regular text
            pdf.set_x(left_margin)
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(content_width, 5, txt=stripped)

        # Save
        file_path = os.path.join(self.reports_dir, file_name)
        try:
            pdf.output(file_path)
            abs_path = os.path.abspath(file_path)
            print(f"[PDF] Report saved: {abs_path}")
            return abs_path
        except Exception as e:
            print(f"[PDF ERROR] {e}")
            return None


# ===================================================================
# 2. DATABASE SERVICE (SQLite)
# ===================================================================
class DatabaseService:
    """Stores FairLens audit records in a SQLite database."""

    def __init__(self, db_path: str = "fairlens_reports.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Creates the reports table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fairlens_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction TEXT,
                    probability REAL,
                    fairness_score REAL,
                    bias_score REAL,
                    bias_status TEXT,
                    recommendation TEXT,
                    bias_source TEXT,
                    user_email TEXT,
                    pdf_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        print(f"[DB] Connected to {self.db_path}")

    def save(self, database_record: Dict[str, Any], pdf_path: str) -> int:
        """
        Inserts a record and returns the row ID.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO fairlens_reports 
                   (prediction, probability, fairness_score, bias_score,
                    bias_status, recommendation, bias_source, user_email, pdf_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    database_record.get("prediction"),
                    database_record.get("probability"),
                    database_record.get("fairness_score"),
                    database_record.get("bias_score"),
                    database_record.get("bias_status"),
                    database_record.get("recommendation"),
                    database_record.get("bias_source"),
                    database_record.get("user_email"),
                    pdf_path,
                ),
            )
            row_id = cursor.lastrowid
        print(f"[DB] Record saved (ID: {row_id})")
        return row_id

    def get_all(self):
        """Returns all stored reports."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM fairlens_reports ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]


# ===================================================================
# 3. EMAIL SERVICE (Gmail SMTP)
# ===================================================================
class EmailService:
    """Sends the PDF audit report via Gmail SMTP."""

    def __init__(self, sender_email: str, sender_password: str):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send(self, recipient_email: str, pdf_path: str, subject: str = None, body: str = None) -> bool:
        """
        Sends an email with the PDF attached.
        Returns True on success, False on failure.
        """
        if not self.sender_email or not self.sender_password:
            print("[EMAIL ERROR] SMTP credentials not configured. Set EMAIL_USER and EMAIL_PASS in .env")
            return False

        if not os.path.exists(pdf_path):
            print(f"[EMAIL ERROR] PDF not found at: {pdf_path}")
            return False

        subject = subject or "Your FairLens Bias Audit Report"
        body = body or (
            "Hello,\n\n"
            "Your FairLens Bias Audit Report has been generated and is attached to this email.\n\n"
            "Please review the report for details on the fairness evaluation, "
            "bias score analysis, and recommended actions.\n\n"
            "This is an automated message from FairLens."
        )

        msg = MIMEMultipart()
        msg["From"] = f"FairLens Audit System <{self.sender_email}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Attach PDF
        try:
            with open(pdf_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(pdf_path)}",
                )
                msg.attach(part)
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to attach PDF: {e}")
            return False

        # Send via SMTP
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print(f"[EMAIL] Report sent to {recipient_email}")
            return True
        except smtplib.SMTPAuthenticationError:
            print("[EMAIL ERROR] Authentication failed. Check your App Password.")
            print("             Go to https://myaccount.google.com/apppasswords to generate one.")
            return False
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
            return False
