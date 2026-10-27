"""Data models, enums, state machine definitions, and validation helpers."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional, Set
import re

class TraineeStatus(str, Enum):
    ACTIVE = "Active"
    LEFT = "Left"
    COMPLETED = "Completed"
    ON_ROLL = "On Roll"

class LwdMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"

class EmailStage(str, Enum):
    INITIAL = "INITIAL"
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    EXIT = "EXIT"

STAGE_LABELS = {
    EmailStage.INITIAL: "Initial Trainee Email (Welcome)",
    EmailStage.Q1: "Quarterly Assessment 1",
    EmailStage.Q2: "Quarterly Assessment 2",
    EmailStage.Q3: "Quarterly Assessment 3",
    EmailStage.Q4: "Quarterly Assessment 4",
    EmailStage.EXIT: "Exit Feedback",
}

STAGE_RECIPIENT_ROLES = {
    EmailStage.INITIAL: "Trainee",
    EmailStage.Q1: "Manager",
    EmailStage.Q2: "Manager",
    EmailStage.Q3: "Manager",
    EmailStage.Q4: "Manager",
    EmailStage.EXIT: "Trainee",
}

class ScheduleStatus(str, Enum):
    SCHEDULED = "Scheduled"
    PROCESSING = "Processing"
    SENT = "Sent"
    CANCELLED = "Cancelled"
    FAILED = "Failed"
    RETRYING = "Retrying"
    UNCERTAIN = "Uncertain"

class DeliveryPhase(str, Enum):
    CLAIMED = "claimed"
    PREPARING = "preparing"
    TRANSMITTING = "transmitting"
    COMPLETED = "completed"

# Centralized State Machine Transition Rules
# Sent is strictly terminal and immutable.
PERMITTED_TRANSITIONS: dict[ScheduleStatus, Set[ScheduleStatus]] = {
    ScheduleStatus.SCHEDULED: {
        ScheduleStatus.PROCESSING,
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.PROCESSING: {
        ScheduleStatus.SENT,
        ScheduleStatus.RETRYING,
        ScheduleStatus.FAILED,
        ScheduleStatus.UNCERTAIN,
        ScheduleStatus.SCHEDULED,  # Recovered before transmission
        ScheduleStatus.CANCELLED,  # Cancelled before dispatch commitment
    },
    ScheduleStatus.RETRYING: {
        ScheduleStatus.PROCESSING,
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.UNCERTAIN: {
        ScheduleStatus.SENT,       # Admin confirmed delivery
        ScheduleStatus.SCHEDULED,  # Admin authorized retry
        ScheduleStatus.CANCELLED,  # Admin cancelled
    },
    ScheduleStatus.FAILED: {
        ScheduleStatus.SCHEDULED,  # Explicit manual retry
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.CANCELLED: {
        ScheduleStatus.SCHEDULED,  # Explicit authorized reactivation with selected date
    },
    ScheduleStatus.SENT: set(),    # IMMUTABLE! No transitions allowed out of Sent.
}

def validate_state_transition(current: ScheduleStatus, target: ScheduleStatus) -> bool:
    """Validate whether transitioning from current to target status is permitted.
    Sent schedules are strictly protected and immutable.
    """
    if current == ScheduleStatus.SENT:
        return False
    if current == target:
        return True
    allowed = PERMITTED_TRANSITIONS.get(current, set())
    return target in allowed

def validate_email_syntax(email: Optional[str]) -> bool:
    """Validate RFC-compliant email syntax."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def format_date_ui(d: Optional[date]) -> str:
    """Format date for user interface display as DD/MM/YYYY."""
    if d is None:
        return ""
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%d/%m/%Y")

def format_date_db(d: Optional[date]) -> str:
    """Format date for database storage as ISO YYYY-MM-DD."""
    if d is None:
        return ""
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%Y-%m-%d")

def parse_date(val) -> Optional[date]:
    """Parse date from ISO string, DD/MM/YYYY, date object, or datetime object."""
    if val is None or val == "":
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    
    val_str = str(val).strip()
    if not val_str:
        return None

    # Try ISO YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date string: '{val_str}'. Expected format DD/MM/YYYY or YYYY-MM-DD.")

@dataclass
class Trainee:
    trainee_id: str
    trainee_name: str
    trainee_email: str
    date_of_joining: date
    manager_name: str
    manager_email: str
    department: str
    location: str
    status: TraineeStatus = TraineeStatus.ACTIVE
    last_working_date: Optional[date] = None
    lwd_mode: LwdMode = LwdMode.AUTO
    is_archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class EmailSchedule:
    id: Optional[int]
    trainee_id: str
    stage: EmailStage
    recipient_role: str
    original_due_date: date
    scheduled_date: date
    custom_date: Optional[date] = None
    is_custom_date: bool = False
    is_opted_out: bool = False
    status: ScheduleStatus = ScheduleStatus.SCHEDULED
    attempt_count: int = 0
    claimed_at: Optional[datetime] = None
    lease_expires_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    delivery_phase: Optional[DeliveryPhase] = None
    last_attempt_at: Optional[datetime] = None
    last_error: Optional[str] = None
    sent_at: Optional[datetime] = None
    recipient_email_used: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class DeliveryAttempt:
    id: Optional[int]
    schedule_id: int
    trainee_id: str
    stage: EmailStage
    attempt_number: int
    attempt_at: datetime
    recipient_email: str
    status_outcome: str  # e.g., "SENT", "FAILED", "UNCERTAIN"
    failure_category: Optional[str] = None
    error_details: Optional[str] = None
    retry_decision: Optional[str] = None
    worker_id: Optional[str] = None
