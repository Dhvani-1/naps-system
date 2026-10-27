"""Deterministic calendar arithmetic and weekend adjustment engine.

Follows the NAPS Apprenticeship Program specification:
- Deterministic calendar-month addition with month-end clamping.
- Independent milestone calculations from original DOJ.
- Welcome email calculation using DOJ + 15 calendar days.
- Exit feedback calculation using effective LWD + 3 calendar months.
- Weekend adjustments: Saturday -> Monday (+2 days), Sunday -> Monday (+1 day).
- Public holidays do not trigger shifting.
"""

import calendar
from datetime import date, timedelta
from typing import Dict, Tuple

from naps_engine.models import EmailStage

def add_calendar_months(d: date, n: int) -> date:
    """Add n calendar months to date d with deterministic month-end clamping.
    
    1. Calculate target year and month.
    2. Preserve original day of month where possible.
    3. If that day does not exist in target month, clamp to the target month's last valid day.
    
    Examples:
    - 31 January + 3 months = 30 April
    - 31 January + 6 months = 31 July
    - 31 January + 9 months = 31 October
    - 31 January 2025 + 12 months = 31 January 2026
    - 29 February 2024 + 12 months = 28 February 2025
    - 31 August + 6 months = last valid day of February in target year (28 or 29 Feb)
    """
    if not isinstance(d, date):
        raise TypeError(f"Expected date instance, got {type(d)}")
    
    # Target month and year
    total_months = (d.year * 12) + (d.month - 1) + n
    target_year = total_months // 12
    target_month = (total_months % 12) + 1
    
    # Clamp day to max valid day in target month
    _, max_days_in_target_month = calendar.monthrange(target_year, target_month)
    target_day = min(d.day, max_days_in_target_month)
    
    return date(target_year, target_month, target_day)

def adjust_for_weekend(d: date) -> date:
    """Adjust date for operational delivery:
    - Monday through Friday: leave unchanged
    - Saturday (weekday == 5): move forward two calendar days to Monday (+2)
    - Sunday (weekday == 6): move forward one calendar day to Monday (+1)
    
    Public holidays do NOT trigger additional shifting.
    """
    if not isinstance(d, date):
        raise TypeError(f"Expected date instance, got {type(d)}")
    
    weekday = d.weekday()  # Monday is 0, Sunday is 6
    if weekday == 5:  # Saturday
        return d + timedelta(days=2)
    elif weekday == 6:  # Sunday
        return d + timedelta(days=1)
    return d

def calculate_default_lwd(doj: date) -> date:
    """Calculate the default Last Working Date (LWD):
    LWD = DOJ + 12 calendar months with month-end clamping.
    """
    if not isinstance(doj, date):
        raise TypeError(f"Expected date instance for DOJ, got {type(doj)}")
    return add_calendar_months(doj, 12)

def validate_dates(doj: date, lwd: date) -> None:
    """Validate DOJ and LWD relationship:
    - Both must be valid date objects.
    - LWD must not be earlier than DOJ.
    """
    if not isinstance(doj, date):
        raise ValueError("DOJ is mandatory and must be a valid date.")
    if not isinstance(lwd, date):
        raise ValueError("LWD must be a valid date.")
    if lwd < doj:
        raise ValueError(
            f"Invalid dates: Last Working Date ({lwd.strftime('%d/%m/%Y')}) "
            f"cannot be earlier than Date of Joining ({doj.strftime('%d/%m/%Y')})."
        )

def calculate_stage_math_due_date(stage: EmailStage, doj: date, effective_lwd: date) -> date:
    """Calculate the independent mathematical due date for a specific stage:
    - INITIAL: DOJ + 15 calendar days (not business days)
    - Q1: DOJ + 3 calendar months (independent from DOJ, not Q0)
    - Q2: DOJ + 6 calendar months (independent from DOJ, not Q1)
    - Q3: DOJ + 9 calendar months (independent from DOJ, not Q2)
    - Q4: DOJ + 12 calendar months (independent from DOJ, not Q3)
    - EXIT: effective LWD + 3 calendar months
    """
    if stage == EmailStage.INITIAL:
        return doj + timedelta(days=15)
    elif stage == EmailStage.Q1:
        return add_calendar_months(doj, 3)
    elif stage == EmailStage.Q2:
        return add_calendar_months(doj, 6)
    elif stage == EmailStage.Q3:
        return add_calendar_months(doj, 9)
    elif stage == EmailStage.Q4:
        return add_calendar_months(doj, 12)
    elif stage == EmailStage.EXIT:
        return add_calendar_months(effective_lwd, 3)
    else:
        raise ValueError(f"Unknown stage: {stage}")

def calculate_all_stage_dates(doj: date, effective_lwd: date) -> Dict[EmailStage, Tuple[date, date]]:
    """Compute (original_due_date, operational_scheduled_date) for all six stages."""
    validate_dates(doj, effective_lwd)
    
    stages = [
        EmailStage.INITIAL,
        EmailStage.Q1,
        EmailStage.Q2,
        EmailStage.Q3,
        EmailStage.Q4,
        EmailStage.EXIT,
    ]
    
    result = {}
    for stage in stages:
        orig = calculate_stage_math_due_date(stage, doj, effective_lwd)
        sched = adjust_for_weekend(orig)
        result[stage] = (orig, sched)
        
    return result
