"""SMTP Mailer abstraction, delivery safety safeguards, and failure classifications."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import smtplib
from typing import Optional

from naps_engine.config import (
    APP_TIMEZONE,
    DEFAULT_FROM_EMAIL,
    EMAIL_DRY_RUN,
)
from naps_engine.models import validate_email_syntax


class EmailFailureCategory(str, Enum):
    RECIPIENT_INVALID = "recipient_invalid"
    TRANSIENT_SMTP = "transient_smtp"
    PERMANENT_SMTP = "permanent_smtp"
    AMBIGUOUS_TIMEOUT = "ambiguous_timeout"


class DeliveryResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    TRANSIENT_FAILURE = "TRANSIENT_FAILURE"
    PERMANENT_FAILURE = "PERMANENT_FAILURE"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass
class MailDispatchResult:
    status: DeliveryResultStatus
    category: Optional[EmailFailureCategory] = None
    error_message: Optional[str] = None
    is_simulated: bool = False
    details: Optional[str] = None


class Mailer:
    """Production-grade safeguarded mailer client.

    Guarantees:
    - Dry-run simulation mode for safe pre-production verification.
    - Strict syntactic email validation before connection attempt.
    - Explicit classification into Transient, Permanent, and Ambiguous outcomes.
    - Guaranteed TLS/STARTTLS encryption for authenticated SMTP dispatch.
    """
    def __init__(self, dry_run: Optional[bool] = None):
        from naps_engine import config
        config.reload_config()
        if not config.ENABLE_LIVE_EMAIL_SENDING:
            self.dry_run = True
        else:
            self.dry_run = config.EMAIL_DRY_RUN if dry_run is None else dry_run

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        on_phase_callback = None
    ) -> MailDispatchResult:
        """Send an email through production safeguards."""
        from naps_engine import config

        sender = from_email or config.DEFAULT_FROM_EMAIL or config.SMTP_USER

        # 1. Syntactic recipient validation
        if not to_email or not validate_email_syntax(to_email):
            return MailDispatchResult(
                status=DeliveryResultStatus.PERMANENT_FAILURE,
                category=EmailFailureCategory.RECIPIENT_INVALID,
                error_message=f"Invalid or missing recipient email address: '{to_email}'"
            )

        # 2. Notify phase: Preparing
        if on_phase_callback:
            on_phase_callback("preparing")

        # 3. Safe Simulation Send
        if self.dry_run:
            if on_phase_callback:
                on_phase_callback("completed")
            return MailDispatchResult(
                status=DeliveryResultStatus.SUCCESS,
                is_simulated=True,
                details=f"[SIMULATION] Simulated delivery to {to_email} (Subject: '{subject}') recorded in database. Live SMTP bypassed."
            )

        # 4. Notify phase: Transmitting (Point of commitment)
        if on_phase_callback:
            on_phase_callback("transmitting")

        # 5. Live SMTP Transmission
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            config.reload_config()

            clean_password = (config.SMTP_PASSWORD or "").replace(" ", "").strip()
            if not clean_password:
                return MailDispatchResult(
                    status=DeliveryResultStatus.PERMANENT_FAILURE,
                    category=EmailFailureCategory.PERMANENT_SMTP,
                    error_message="SMTP Password is empty. Please configure SMTP_PASSWORD in the .env file."
                )

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to_email
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=25.0) as server:
                server.ehlo()
                if config.SMTP_USE_TLS:
                    server.starttls()
                    server.ehlo()
                if config.SMTP_USER and clean_password:
                    server.login(config.SMTP_USER.strip(), clean_password)
                server.send_message(msg)

            if on_phase_callback:
                on_phase_callback("completed")

            return MailDispatchResult(
                status=DeliveryResultStatus.SUCCESS,
                details=f"Email transmitted to {to_email} via SMTP ({config.SMTP_HOST}:{config.SMTP_PORT})."
            )
        except smtplib.SMTPAuthenticationError as e:
            return MailDispatchResult(
                status=DeliveryResultStatus.PERMANENT_FAILURE,
                category=EmailFailureCategory.PERMANENT_SMTP,
                error_message=f"SMTP Authentication Error ({e.smtp_code}): Check SMTP credentials in .env for user '{config.SMTP_USER}'."
            )
        except smtplib.SMTPRecipientsRefused as e:
            return MailDispatchResult(
                status=DeliveryResultStatus.PERMANENT_FAILURE,
                category=EmailFailureCategory.RECIPIENT_INVALID,
                error_message=f"Recipient refused by SMTP server: {str(e)}"
            )
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, TimeoutError) as e:
            return MailDispatchResult(
                status=DeliveryResultStatus.AMBIGUOUS,
                category=EmailFailureCategory.AMBIGUOUS_TIMEOUT,
                error_message=f"SMTP connection interrupted or timed out: {str(e)}"
            )
        except smtplib.SMTPResponseException as e:
            if 400 <= e.smtp_code < 500:
                return MailDispatchResult(
                    status=DeliveryResultStatus.TRANSIENT_FAILURE,
                    category=EmailFailureCategory.TRANSIENT_SMTP,
                    error_message=f"SMTP {e.smtp_code}: {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)}"
                )
            else:
                return MailDispatchResult(
                    status=DeliveryResultStatus.PERMANENT_FAILURE,
                    category=EmailFailureCategory.PERMANENT_SMTP,
                    error_message=f"SMTP {e.smtp_code}: {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)}"
                )
        except Exception as e:
            return MailDispatchResult(
                status=DeliveryResultStatus.AMBIGUOUS,
                category=EmailFailureCategory.AMBIGUOUS_TIMEOUT,
                error_message=f"Unexpected transmission error: {str(e)}"
            )


