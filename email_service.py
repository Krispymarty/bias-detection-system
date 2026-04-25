"""
FairLens — Email Service (with Full Debugging)
================================================

Standalone email module that sends PDF audit reports via Gmail SMTP.
This addresses the CRITICAL email debugging requirement.

DEBUGGING CHECKLIST (applied automatically):
  1. Validates SMTP credentials are present and correctly formatted
  2. Validates sender email contains '@'
  3. Validates recipient email is non-empty
  4. Validates PDF file exists at the given path
  5. Validates attachment read before sending
  6. Logs every step for traceability
  7. NEVER breaks the pipeline — all errors are caught and logged

Usage:
    from fairlens.email_service import EmailService

    service = EmailService(sender_email="...", sender_password="...")
    success = service.send(
        recipient_email="user@example.com",
        pdf_path="/path/to/report.pdf",
    )

Troubleshooting:
    - Gmail requires an App Password (not your regular password)
    - Enable 2FA: https://myaccount.google.com/security
    - Generate App Password: https://myaccount.google.com/apppasswords
    - Use the 16-character password WITHOUT spaces
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional


class EmailService:
    """
    Production email service with comprehensive error logging.

    Every step is logged so that email failures can be traced
    to the exact point of failure without breaking the pipeline.
    """

    DEFAULT_SUBJECT = "FairLens Bias Audit Report"
    DEFAULT_BODY = (
        "Hello,\n\n"
        "Your FairLens Bias Audit Report has been generated and is attached "
        "to this email.\n\n"
        "Please review the report for details on the fairness evaluation, "
        "bias score analysis, and recommended actions.\n\n"
        "This is an automated message from FairLens."
    )

    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
    ):
        # Strip whitespace from credentials (common .env issue)
        self.sender_email = sender_email.strip() if sender_email else ""
        self.sender_password = sender_password.strip() if sender_password else ""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send(
        self,
        recipient_email: str,
        pdf_path: str,
        subject: Optional[str] = None,
        body: Optional[str] = None,
    ) -> bool:
        """
        Sends an email with the PDF audit report attached.

        Returns True on success, False on failure.
        NEVER raises — all errors are caught and logged.
        """
        subject = subject or self.DEFAULT_SUBJECT
        body = body or self.DEFAULT_BODY

        # ============================================================
        # PRE-FLIGHT CHECKS (validate everything before attempting send)
        # ============================================================

        # Check 1: Sender email
        if not self.sender_email:
            print("[EMAIL ERROR] Sender email is empty.")
            print("  FIX: Set EMAIL_USER in your .env file")
            return False

        if "@" not in self.sender_email:
            print(f"[EMAIL ERROR] Invalid sender email: '{self.sender_email}'")
            print(f"  FIX: EMAIL_USER must contain '@' (e.g., aiauditor@gmail.com)")
            return False

        # Check 2: Sender password
        if not self.sender_password:
            print("[EMAIL ERROR] Sender password is empty.")
            print("  FIX: Set EMAIL_PASS in your .env file")
            print("  NOTE: Use a Gmail App Password, NOT your regular password")
            return False

        if len(self.sender_password) < 8:
            print(f"[EMAIL ERROR] Password too short ({len(self.sender_password)} chars).")
            print("  FIX: Gmail App Passwords are 16 characters. Check EMAIL_PASS.")
            return False

        # Check 3: Recipient email
        if not recipient_email or "@" not in recipient_email:
            print(f"[EMAIL ERROR] Invalid recipient: '{recipient_email}'")
            return False

        # Check 4: PDF file
        if not pdf_path:
            print("[EMAIL ERROR] No PDF path provided.")
            return False

        if not os.path.exists(pdf_path):
            print(f"[EMAIL ERROR] PDF file not found at: {pdf_path}")
            print(f"  FIX: Check that PDF generation completed successfully")
            return False

        pdf_size = os.path.getsize(pdf_path)
        if pdf_size == 0:
            print(f"[EMAIL ERROR] PDF file is empty (0 bytes): {pdf_path}")
            return False

        print(f"[EMAIL] Pre-flight checks passed:")
        print(f"  From:    {self.sender_email}")
        print(f"  To:      {recipient_email}")
        print(f"  PDF:     {pdf_path} ({pdf_size:,} bytes)")
        print(f"  Subject: {subject}")

        # ============================================================
        # BUILD EMAIL MESSAGE
        # ============================================================
        try:
            msg = MIMEMultipart()
            msg["From"] = f"FairLens Audit System <{self.sender_email}>"
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to build message: {e}")
            return False

        # ============================================================
        # ATTACH PDF
        # ============================================================
        try:
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()

            if len(pdf_data) == 0:
                print("[EMAIL ERROR] PDF read returned 0 bytes")
                return False

            part = MIMEBase("application", "octet-stream")
            part.set_payload(pdf_data)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(pdf_path)}",
            )
            msg.attach(part)
            print(f"[EMAIL] PDF attached successfully ({len(pdf_data):,} bytes)")
        except PermissionError:
            print(f"[EMAIL ERROR] Permission denied reading: {pdf_path}")
            return False
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to attach PDF: {e}")
            return False

        # ============================================================
        # SEND VIA SMTP
        # ============================================================
        try:
            print(f"[EMAIL] Connecting to {self.smtp_server}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                print("[EMAIL] Starting TLS...")
                server.starttls()
                print(f"[EMAIL] Logging in as {self.sender_email}...")
                server.login(self.sender_email, self.sender_password)
                print(f"[EMAIL] Sending to {recipient_email}...")
                server.send_message(msg)
            print(f"[EMAIL] SUCCESS — Report sent to {recipient_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"[EMAIL ERROR] Authentication FAILED: {e}")
            print("  DIAGNOSIS: Your credentials were rejected by Gmail.")
            print("  FIX:")
            print("    1. Enable 2-Factor Authentication on your Gmail account")
            print("    2. Go to https://myaccount.google.com/apppasswords")
            print("    3. Generate a new App Password for 'Mail'")
            print("    4. Copy the 16-character password (no spaces)")
            print("    5. Set EMAIL_PASS=<that password> in your .env file")
            return False

        except smtplib.SMTPRecipientsRefused as e:
            print(f"[EMAIL ERROR] Recipient refused: {e}")
            print(f"  FIX: Verify that '{recipient_email}' is a valid email address")
            return False

        except smtplib.SMTPConnectError as e:
            print(f"[EMAIL ERROR] Connection failed: {e}")
            print("  FIX: Check your internet connection and firewall settings")
            return False

        except smtplib.SMTPException as e:
            print(f"[EMAIL ERROR] SMTP error: {e}")
            return False

        except TimeoutError:
            print("[EMAIL ERROR] Connection timed out after 15 seconds")
            print("  FIX: Check your internet connection")
            return False

        except Exception as e:
            print(f"[EMAIL ERROR] Unexpected error: {type(e).__name__}: {e}")
            return False

    def validate_credentials(self) -> bool:
        """
        Tests SMTP credentials without sending an email.
        Useful for debugging .env configuration.

        Returns True if login succeeds, False otherwise.
        """
        if not self.sender_email or "@" not in self.sender_email:
            print(f"[EMAIL VALIDATE] Invalid email: '{self.sender_email}'")
            return False
        if not self.sender_password:
            print("[EMAIL VALIDATE] No password configured")
            return False

        try:
            print(f"[EMAIL VALIDATE] Testing login for {self.sender_email}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            print("[EMAIL VALIDATE] Login successful!")
            return True
        except smtplib.SMTPAuthenticationError:
            print("[EMAIL VALIDATE] Authentication FAILED")
            print("  Use a Gmail App Password, not your regular password")
            return False
        except Exception as e:
            print(f"[EMAIL VALIDATE] Connection error: {e}")
            return False
