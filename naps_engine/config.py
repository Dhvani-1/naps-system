"""Application configuration and production delivery safety settings."""

import os
from zoneinfo import ZoneInfo

# Timezone settings (authoritative timezone is Asia/Kolkata)
TIMEZONE_NAME = "Asia/Kolkata"
APP_TIMEZONE = ZoneInfo(TIMEZONE_NAME)

# Normal target dispatch time (09:00:00 Asia/Kolkata)
NORMAL_DISPATCH_HOUR = 9
NORMAL_DISPATCH_MINUTE = 0
NORMAL_DISPATCH_SECOND = 0

# Worker and Lease configuration
DEFAULT_LEASE_DURATION_SECONDS = 300  # 5 minutes
MAX_AUTOMATIC_RETRIES = 1             # At most one automatic retry for transient failures

# Database configuration
DEFAULT_DB_PATH = os.environ.get("NAPS_DB_PATH", "naps_trainees.db")
DATABASE_URL: str = ""
POSTGRES_URL: str = ""

# Security & Cron settings
CRON_SECRET: str = "naps-cron-secret-change-in-production"
SESSION_SECRET: str = "naps-session-secret-change-in-production"

# Delivery mode: Strict simulation mode safeguard
# Even if someone accidentally misconfigures an env variable, live email transmission
# remains disabled unless ENABLE_LIVE_EMAIL_SENDING is explicitly set to 'true'.
ENABLE_LIVE_EMAIL_SENDING: bool = False
EMAIL_DRY_RUN: bool = True

# SMTP configuration (used only if simulation mode is ever explicitly unlocked)
SMTP_HOST: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
SMTP_USE_TLS: bool = True
DEFAULT_FROM_EMAIL: str = ""


def reload_config() -> None:
    """Reload environment variables from .env and refresh configuration variables."""
    global DATABASE_URL, POSTGRES_URL, CRON_SECRET, SESSION_SECRET
    global ENABLE_LIVE_EMAIL_SENDING, EMAIL_DRY_RUN
    global SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, DEFAULT_FROM_EMAIL

    try:
        import dotenv
        dotenv.load_dotenv(override=True)
    except Exception:
        pass

    # Database URLs for persistent cloud databases (Neon, Supabase, Vercel Postgres)
    DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()
    POSTGRES_URL = (os.environ.get("POSTGRES_URL") or "").strip()

    # Secrets
    CRON_SECRET = os.environ.get("CRON_SECRET", "naps-cron-secret-change-in-production").strip()
    SESSION_SECRET = os.environ.get("SESSION_SECRET", "naps-session-secret-change-in-production").strip()

    # Live email transmission safety lock:
    # Requires BOTH ENABLE_LIVE_EMAIL_SENDING=true AND EMAIL_DRY_RUN=false to enable live transmission.
    ENABLE_LIVE_EMAIL_SENDING = os.environ.get("ENABLE_LIVE_EMAIL_SENDING", "false").lower() in ("1", "true", "yes")
    dry_run_env = os.environ.get("EMAIL_DRY_RUN", "true").lower() in ("1", "true", "yes")

    # If ENABLE_LIVE_EMAIL_SENDING is false, force EMAIL_DRY_RUN to True for safety
    if not ENABLE_LIVE_EMAIL_SENDING:
        EMAIL_DRY_RUN = True
    else:
        EMAIL_DRY_RUN = dry_run_env

    # SMTP Settings
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "").strip()
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").strip()
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", SMTP_USER).strip()


# Initialize on import
reload_config()
