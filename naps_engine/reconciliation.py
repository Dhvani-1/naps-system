"""Lifecycle reconciliation engine and email schedule management.

Enforces:
- Deterministic schedule generation for all 6 stages.
- Lifecycle state transitions (Active, Left, Completed, On Roll).
- Sent-history immutability.
- Opt-out enforcement in all backend pathways.
- Explicit LWD requirement when changing status to Left.
- Preservation of cancelled stages on reactivation to Active.
"""

from datetime import date, datetime
import sqlite3
from typing import Dict, List, Optional, Tuple

from naps_engine.audit import log_audit_event
from naps_engine.config import APP_TIMEZONE
from naps_engine.date_engine import (
    add_calendar_months,
    adjust_for_weekend,
    calculate_all_stage_dates,
    calculate_default_lwd,
    calculate_stage_math_due_date,
    validate_dates,
)
from naps_engine.db import (
    get_schedule_by_id,
    get_schedules_for_trainee,
    get_trainee,
    row_to_schedule,
    row_to_trainee,
)
from naps_engine.models import (
    DeliveryAttempt,
    DeliveryPhase,
    EmailSchedule,
    EmailStage,
    LwdMode,
    ScheduleStatus,
    STAGE_RECIPIENT_ROLES,
    Trainee,
    TraineeStatus,
    format_date_db,
    format_date_ui,
    validate_email_syntax,
)

def create_trainee_with_schedules(
    conn: sqlite3.Connection,
    trainee: Trainee,
    custom_dates: Optional[Dict[EmailStage, date]] = None,
    opt_out_preferences: Optional[Dict[EmailStage, bool]] = None,
    confirmed_actual_lwd: bool = False,
    actor: str = "system"
) -> Tuple[Trainee, List[EmailSchedule]]:
    """Create a new trainee and generate initial schedules transactionally.
    
    Invariants:
    - DOJ is mandatory.
    - Status 'Left' requires confirmed actual LWD.
    - All 6 stages generated with independent math due dates.
    - Weekend adjustment applied.
    - Idempotent and rollback safe.
    """
    # Validation
    if not trainee.trainee_id or not trainee.trainee_id.strip():
        raise ValueError("trainee_id is mandatory.")
    trainee_id = trainee.trainee_id.strip()
    
    if not trainee.trainee_name or not trainee.trainee_name.strip():
        raise ValueError("trainee_name is mandatory.")
    
    if not validate_email_syntax(trainee.trainee_email):
        raise ValueError(f"Invalid trainee email address: '{trainee.trainee_email}'")
        
    if not validate_email_syntax(trainee.manager_email):
        raise ValueError(f"Invalid manager email address: '{trainee.manager_email}'")

    if not isinstance(trainee.date_of_joining, date):
        raise ValueError("DOJ is mandatory and must be a valid date.")
    
    # LWD resolution
    if trainee.last_working_date is None:
        trainee.last_working_date = calculate_default_lwd(trainee.date_of_joining)
        trainee.lwd_mode = LwdMode.AUTO
    else:
        validate_dates(trainee.date_of_joining, trainee.last_working_date)

    # Status Left special rule
    if trainee.status == TraineeStatus.LEFT and not confirmed_actual_lwd:
        raise ValueError(
            "Changing status to 'Left' requires user to explicitly provide or confirm "
            "the actual Last Working Date (LWD). Default DOJ + 12 months cannot be silently assumed."
        )

    # Compute dates for all 6 stages
    stage_dates = calculate_all_stage_dates(trainee.date_of_joining, trainee.last_working_date)
    
    now_iso = datetime.now(APP_TIMEZONE).isoformat()
    trainee.created_at = datetime.now(APP_TIMEZONE)
    trainee.updated_at = trainee.created_at

    conn.execute("BEGIN IMMEDIATE")
    try:
        # Check existing
        existing = get_trainee(conn, trainee_id)
        if existing:
            raise ValueError(f"Trainee with ID '{trainee_id}' already exists.")

        conn.execute(
            """
            INSERT INTO trainees (
                trainee_id, trainee_name, trainee_email, date_of_joining,
                manager_name, manager_email, department, location,
                status, last_working_date, lwd_mode, is_archived,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trainee.trainee_id,
                trainee.trainee_name.strip(),
                trainee.trainee_email.strip(),
                format_date_db(trainee.date_of_joining),
                trainee.manager_name.strip(),
                trainee.manager_email.strip(),
                trainee.department.strip(),
                trainee.location.strip(),
                trainee.status.value,
                format_date_db(trainee.last_working_date),
                trainee.lwd_mode.value,
                0,
                now_iso,
                now_iso
            )
        )
        
        custom_dates = custom_dates or {}
        opt_out_preferences = opt_out_preferences or {}

        created_schedules = []
        for stage in [
            EmailStage.INITIAL,
            EmailStage.Q1,
            EmailStage.Q2,
            EmailStage.Q3,
            EmailStage.Q4,
            EmailStage.EXIT,
        ]:
            orig_due, auto_sched = stage_dates[stage]
            custom_date = custom_dates.get(stage)
            is_custom = custom_date is not None
            
            if is_custom:
                effective_sched = adjust_for_weekend(custom_date)
            else:
                effective_sched = auto_sched
                
            is_opted_out = opt_out_preferences.get(stage, False)
            
            # Initial status based on lifecycle
            initial_status = ScheduleStatus.SCHEDULED
            cancellation_reason = None
            
            if is_opted_out:
                initial_status = ScheduleStatus.CANCELLED
                cancellation_reason = "Opted out by user preference"
            elif trainee.status in (TraineeStatus.LEFT, TraineeStatus.COMPLETED, TraineeStatus.ON_ROLL):
                if stage != EmailStage.EXIT:
                    initial_status = ScheduleStatus.CANCELLED
                    cancellation_reason = f"Lifecycle status is {trainee.status.value}"

            cursor = conn.execute(
                """
                INSERT INTO email_schedules (
                    trainee_id, stage, recipient_role, original_due_date,
                    custom_date, scheduled_date, is_custom_date, is_opted_out,
                    status, cancellation_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trainee.trainee_id,
                    stage.value,
                    STAGE_RECIPIENT_ROLES[stage],
                    format_date_db(orig_due),
                    format_date_db(custom_date) if custom_date else None,
                    format_date_db(effective_sched),
                    1 if is_custom else 0,
                    1 if is_opted_out else 0,
                    initial_status.value,
                    cancellation_reason,
                    now_iso,
                    now_iso
                )
            )
            created_schedules.append(
                EmailSchedule(
                    id=cursor.lastrowid,
                    trainee_id=trainee.trainee_id,
                    stage=stage,
                    recipient_role=STAGE_RECIPIENT_ROLES[stage],
                    original_due_date=orig_due,
                    custom_date=custom_date,
                    scheduled_date=effective_sched,
                    is_custom_date=is_custom,
                    is_opted_out=is_opted_out,
                    status=initial_status,
                    cancellation_reason=cancellation_reason,
                    created_at=trainee.created_at,
                    updated_at=trainee.updated_at
                )
            )

        log_audit_event(
            conn,
            entity_type="trainee",
            entity_id=trainee.trainee_id,
            action="CREATE",
            actor=actor,
            new_values={
                "trainee_name": trainee.trainee_name,
                "doj": format_date_db(trainee.date_of_joining),
                "lwd": format_date_db(trainee.last_working_date),
                "status": trainee.status.value,
                "lwd_mode": trainee.lwd_mode.value
            }
        )
        conn.execute("COMMIT")
        return trainee, created_schedules
    except Exception:
        conn.execute("ROLLBACK")
        raise

def update_trainee_and_reconcile(
    conn: sqlite3.Connection,
    trainee_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    manager_name: Optional[str] = None,
    manager_email: Optional[str] = None,
    department: Optional[str] = None,
    location: Optional[str] = None,
    new_doj: Optional[date] = None,
    new_lwd: Optional[date] = None,
    new_lwd_mode: Optional[LwdMode] = None,
    new_status: Optional[TraineeStatus] = None,
    confirmed_actual_lwd: bool = False,
    manual_lwd_reviewed: bool = False,
    actor: str = "system",
    reason: Optional[str] = None
) -> Tuple[Trainee, List[EmailSchedule]]:
    """Update trainee fields and reconcile schedules transactionally.
    
    Enforces all business rules:
    - DOJ change recalculates automatic LWD, prompts review for manual LWD.
    - Status change to Left requires confirmed actual LWD.
    - Lifecycle cancellations for Left, Completed, On Roll cancel unsent Initial & Q1-Q4.
    - Sent schedules are completely untouched and immutable.
    - Cancelled schedules remain cancelled when status moves to Active.
    - Custom dates survive DOJ/LWD changes.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        current_trainee = get_trainee(conn, trainee_id)
        if not current_trainee:
            raise ValueError(f"Trainee {trainee_id} not found.")

        old_values = {
            "name": current_trainee.trainee_name,
            "email": current_trainee.trainee_email,
            "manager_name": current_trainee.manager_name,
            "manager_email": current_trainee.manager_email,
            "department": current_trainee.department,
            "location": current_trainee.location,
            "doj": format_date_db(current_trainee.date_of_joining),
            "lwd": format_date_db(current_trainee.last_working_date),
            "lwd_mode": current_trainee.lwd_mode.value,
            "status": current_trainee.status.value,
        }

        updated_name = name.strip() if name is not None else current_trainee.trainee_name
        updated_email = email.strip() if email is not None else current_trainee.trainee_email
        updated_manager_name = manager_name.strip() if manager_name is not None else current_trainee.manager_name
        updated_manager_email = manager_email.strip() if manager_email is not None else current_trainee.manager_email
        updated_department = department.strip() if department is not None else current_trainee.department
        updated_location = location.strip() if location is not None else current_trainee.location
        
        if not validate_email_syntax(updated_email):
            raise ValueError(f"Invalid trainee email: '{updated_email}'")
        if not validate_email_syntax(updated_manager_email):
            raise ValueError(f"Invalid manager email: '{updated_manager_email}'")

        doj_changed = (new_doj is not None) and (new_doj != current_trainee.date_of_joining)
        updated_doj = new_doj if doj_changed else current_trainee.date_of_joining

        # LWD determination
        status_changing_to_left = (new_status == TraineeStatus.LEFT) and (current_trainee.status != TraineeStatus.LEFT)
        
        if status_changing_to_left and not confirmed_actual_lwd:
            raise ValueError(
                "Changing status to 'Left' requires user to explicitly provide or confirm "
                "the actual Last Working Date (LWD). Status transition is blocked."
            )

        updated_lwd_mode = new_lwd_mode if new_lwd_mode is not None else current_trainee.lwd_mode
        
        if new_lwd is not None:
            updated_lwd = new_lwd
            if new_lwd_mode is None:
                updated_lwd_mode = LwdMode.MANUAL
        elif doj_changed:
            if current_trainee.lwd_mode == LwdMode.AUTO:
                updated_lwd = calculate_default_lwd(updated_doj)
                updated_lwd_mode = LwdMode.AUTO
            else:
                # Manual LWD requires user review confirmation when DOJ changes
                if not manual_lwd_reviewed:
                    raise ValueError(
                        f"DOJ changed for trainee {trainee_id} with manually entered LWD "
                        f"({format_date_ui(current_trainee.last_working_date)}). "
                        f"User must review and confirm whether LWD should change."
                    )
                updated_lwd = current_trainee.last_working_date
        else:
            updated_lwd = current_trainee.last_working_date

        validate_dates(updated_doj, updated_lwd)

        status_changed = (new_status is not None) and (new_status != current_trainee.status)
        updated_status = new_status if new_status is not None else current_trainee.status

        lwd_changed = (updated_lwd != current_trainee.last_working_date)

        now_iso = datetime.now(APP_TIMEZONE).isoformat()
        
        # Save trainee updates
        conn.execute(
            """
            UPDATE trainees SET
                trainee_name = ?,
                trainee_email = ?,
                manager_name = ?,
                manager_email = ?,
                department = ?,
                location = ?,
                date_of_joining = ?,
                last_working_date = ?,
                lwd_mode = ?,
                status = ?,
                updated_at = ?
            WHERE trainee_id = ?
            """,
            (
                updated_name,
                updated_email,
                updated_manager_name,
                updated_manager_email,
                updated_department,
                updated_location,
                format_date_db(updated_doj),
                format_date_db(updated_lwd),
                updated_lwd_mode.value,
                updated_status.value,
                now_iso,
                trainee_id
            )
        )

        # Reconcile schedules
        schedules = get_schedules_for_trainee(conn, trainee_id)
        stage_map = {s.stage: s for s in schedules}

        # Ensure all 6 stages exist (in case Exit or another was missing)
        for stage in [
            EmailStage.INITIAL,
            EmailStage.Q1,
            EmailStage.Q2,
            EmailStage.Q3,
            EmailStage.Q4,
            EmailStage.EXIT
        ]:
            if stage not in stage_map:
                orig = calculate_stage_math_due_date(stage, updated_doj, updated_lwd)
                sched = adjust_for_weekend(orig)
                init_status = ScheduleStatus.SCHEDULED
                c_reason = None
                if updated_status in (TraineeStatus.LEFT, TraineeStatus.COMPLETED, TraineeStatus.ON_ROLL) and stage != EmailStage.EXIT:
                    init_status = ScheduleStatus.CANCELLED
                    c_reason = f"Lifecycle status is {updated_status.value}"

                c = conn.execute(
                    """
                    INSERT INTO email_schedules (
                        trainee_id, stage, recipient_role, original_due_date,
                        scheduled_date, is_custom_date, is_opted_out,
                        status, cancellation_reason, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
                    """,
                    (
                        trainee_id,
                        stage.value,
                        STAGE_RECIPIENT_ROLES[stage],
                        format_date_db(orig),
                        format_date_db(sched),
                        init_status.value,
                        c_reason,
                        now_iso,
                        now_iso
                    )
                )
                stage_map[stage] = get_schedule_by_id(conn, c.lastrowid)

        # Process each schedule according to lifecycle & date rules
        for stage, sched in stage_map.items():
            # RULE: Sent schedules are IMMUTABLE. Never modify them!
            if sched.status == ScheduleStatus.SENT:
                continue

            # Update dates if DOJ or LWD changed
            new_math_due = calculate_stage_math_due_date(stage, updated_doj, updated_lwd)
            
            sched_is_custom = sched.is_custom_date
            custom_date = sched.custom_date
            
            if sched_is_custom and custom_date:
                # Custom date survives DOJ or LWD changes. Re-apply weekend adjustment.
                effective_sched = adjust_for_weekend(custom_date)
            else:
                effective_sched = adjust_for_weekend(new_math_due)

            current_status = sched.status
            cancellation_reason = sched.cancellation_reason

            # Lifecycle status updates
            if status_changed:
                if updated_status in (TraineeStatus.LEFT, TraineeStatus.COMPLETED, TraineeStatus.ON_ROLL):
                    if stage != EmailStage.EXIT:
                        # Cancel unsent Initial and Q1-Q4
                        if current_status in (
                            ScheduleStatus.SCHEDULED,
                            ScheduleStatus.RETRYING,
                            ScheduleStatus.PROCESSING,
                            ScheduleStatus.FAILED
                        ):
                            current_status = ScheduleStatus.CANCELLED
                            cancellation_reason = f"Cancelled due to trainee status {updated_status.value}"
                    else:
                        # Exit Feedback schedule must exist and be retained
                        if current_status == ScheduleStatus.CANCELLED and not sched.is_opted_out:
                            # If Exit was previously cancelled not by opt-out, ensure it exists
                            pass
                elif updated_status == TraineeStatus.ACTIVE:
                    # RULE: "If a trainee changes back to Active, previously cancelled stages must remain cancelled until manually re-enabled."
                    # Do NOT change current_status from CANCELLED to SCHEDULED!
                    pass

            # Update schedule record
            conn.execute(
                """
                UPDATE email_schedules SET
                    original_due_date = ?,
                    custom_date = ?,
                    scheduled_date = ?,
                    is_custom_date = ?,
                    status = ?,
                    cancellation_reason = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    format_date_db(new_math_due),
                    format_date_db(custom_date) if custom_date else None,
                    format_date_db(effective_sched),
                    1 if sched_is_custom else 0,
                    current_status.value,
                    cancellation_reason,
                    now_iso,
                    sched.id
                )
            )

        new_values = {
            "name": updated_name,
            "email": updated_email,
            "manager_name": updated_manager_name,
            "manager_email": updated_manager_email,
            "department": updated_department,
            "location": updated_location,
            "doj": format_date_db(updated_doj),
            "lwd": format_date_db(updated_lwd),
            "lwd_mode": updated_lwd_mode.value,
            "status": updated_status.value,
        }

        # Check if actual changes occurred
        has_changes = any(old_values[k] != new_values[k] for k in old_values)
        if has_changes:
            log_audit_event(
                conn,
                entity_type="trainee",
                entity_id=trainee_id,
                action="UPDATE",
                actor=actor,
                old_values=old_values,
                new_values=new_values,
                reason=reason or "Trainee update and schedule reconciliation"
            )
        else:
            log_audit_event(
                conn,
                entity_type="trainee",
                entity_id=trainee_id,
                action="SAVE_UNCHANGED",
                actor=actor,
                reason="Save called without field changes"
            )

        conn.execute("COMMIT")
        updated_trainee = get_trainee(conn, trainee_id)
        refreshed_schedules = get_schedules_for_trainee(conn, trainee_id)
        return updated_trainee, refreshed_schedules
    except Exception:
        conn.execute("ROLLBACK")
        raise

def update_schedule_custom_date(
    conn: sqlite3.Connection,
    schedule_id: int,
    custom_date: date,
    actor: str = "system",
    reason: Optional[str] = None
) -> EmailSchedule:
    """Explicitly set a custom scheduled date for an email stage.
    
    Invariants:
    - Sent schedules are immutable.
    - Weekend adjustment applies to all custom dates.
    - Persists custom_date, is_custom_date = 1, and weekend-adjusted scheduled_date.
    - Overdue warning condition checked by caller/UI.
    - Custom date does NOT override lifecycle cancellation or opt-out.
    """
    if not isinstance(custom_date, date):
        raise TypeError("custom_date must be a valid date.")
        
    conn.execute("BEGIN IMMEDIATE")
    try:
        sched = get_schedule_by_id(conn, schedule_id)
        if not sched:
            raise ValueError(f"Schedule with id {schedule_id} not found.")

        # SENT IS IMMUTABLE
        if sched.status == ScheduleStatus.SENT:
            raise ValueError(
                f"Cannot modify schedule {schedule_id}: stage {sched.stage.value} is already SENT. "
                "Sent schedules are strictly immutable."
            )

        adjusted_date = adjust_for_weekend(custom_date)
        now_iso = datetime.now(APP_TIMEZONE).isoformat()

        old_values = {
            "custom_date": format_date_db(sched.custom_date),
            "scheduled_date": format_date_db(sched.scheduled_date),
            "is_custom_date": sched.is_custom_date
        }

        conn.execute(
            """
            UPDATE email_schedules SET
                custom_date = ?,
                scheduled_date = ?,
                is_custom_date = 1,
                updated_at = ?
            WHERE id = ?
            """,
            (format_date_db(custom_date), format_date_db(adjusted_date), now_iso, schedule_id)
        )

        log_audit_event(
            conn,
            entity_type="schedule",
            entity_id=str(schedule_id),
            action="UPDATE_CUSTOM_DATE",
            actor=actor,
            old_values=old_values,
            new_values={
                "custom_date": format_date_db(custom_date),
                "scheduled_date": format_date_db(adjusted_date),
                "is_custom_date": True
            },
            reason=reason or "User manually updated scheduled date"
        )
        conn.execute("COMMIT")
        return get_schedule_by_id(conn, schedule_id)
    except Exception:
        conn.execute("ROLLBACK")
        raise

def set_stage_preference(
    conn: sqlite3.Connection,
    schedule_id: int,
    is_opted_out: bool,
    chosen_date: Optional[date] = None,
    actor: str = "system",
    reason: Optional[str] = None
) -> EmailSchedule:
    """Update email stage opt-out preference.
    
    Rules:
    - Opting out cancels unsent schedule and marks is_opted_out = 1.
    - Re-enabling requires user to choose a scheduled date explicitly.
    - Lifecycle rules govern eligibility on re-enabling.
    - Sent schedules are immutable.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        sched = get_schedule_by_id(conn, schedule_id)
        if not sched:
            raise ValueError(f"Schedule with id {schedule_id} not found.")

        if sched.status == ScheduleStatus.SENT:
            raise ValueError(
                f"Cannot alter preferences for schedule {schedule_id}: stage {sched.stage.value} is already SENT."
            )

        trainee = get_trainee(conn, sched.trainee_id)
        now_iso = datetime.now(APP_TIMEZONE).isoformat()

        if is_opted_out:
            # Cancel unsent schedule
            conn.execute(
                """
                UPDATE email_schedules SET
                    is_opted_out = 1,
                    status = ?,
                    cancellation_reason = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (ScheduleStatus.CANCELLED.value, "User opted out", now_iso, schedule_id)
            )
            log_audit_event(
                conn,
                entity_type="schedule",
                entity_id=str(schedule_id),
                action="OPT_OUT",
                actor=actor,
                old_values={"is_opted_out": sched.is_opted_out, "status": sched.status.value},
                new_values={"is_opted_out": True, "status": ScheduleStatus.CANCELLED.value},
                reason=reason or "Stage opted out by user"
            )
        else:
            # Rechecking requires explicit date choice
            if chosen_date is None:
                raise ValueError(
                    "Re-enabling an opted-out stage requires an explicit scheduled date choice."
                )

            # Check lifecycle eligibility
            if trainee.status in (TraineeStatus.LEFT, TraineeStatus.COMPLETED, TraineeStatus.ON_ROLL):
                if sched.stage != EmailStage.EXIT:
                    raise ValueError(
                        f"Cannot re-enable {sched.stage.value} for trainee with status {trainee.status.value}. "
                        "Only Exit Feedback is eligible for non-Active trainees."
                    )

            effective_sched = adjust_for_weekend(chosen_date)
            conn.execute(
                """
                UPDATE email_schedules SET
                    is_opted_out = 0,
                    status = ?,
                    custom_date = ?,
                    scheduled_date = ?,
                    is_custom_date = 1,
                    cancellation_reason = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    ScheduleStatus.SCHEDULED.value,
                    format_date_db(chosen_date),
                    format_date_db(effective_sched),
                    now_iso,
                    schedule_id
                )
            )
            log_audit_event(
                conn,
                entity_type="schedule",
                entity_id=str(schedule_id),
                action="OPT_IN",
                actor=actor,
                old_values={"is_opted_out": sched.is_opted_out, "status": sched.status.value},
                new_values={
                    "is_opted_out": False,
                    "status": ScheduleStatus.SCHEDULED.value,
                    "scheduled_date": format_date_db(effective_sched)
                },
                reason=reason or "Stage re-enabled by user with explicit date"
            )

        conn.execute("COMMIT")
        return get_schedule_by_id(conn, schedule_id)
    except Exception:
        conn.execute("ROLLBACK")
        raise

def reenable_cancelled_stage(
    conn: sqlite3.Connection,
    schedule_id: int,
    explicit_date: date,
    actor: str = "admin",
    reason: Optional[str] = None
) -> EmailSchedule:
    """Authorized manual reactivation of a previously cancelled schedule.
    
    Requires an explicit date choice (calculated default or custom date).
    Sent history is never modified.
    Lifecycle rules still govern eligibility.
    """
    if not isinstance(explicit_date, date):
        raise TypeError("explicit_date must be a valid date.")
        
    conn.execute("BEGIN IMMEDIATE")
    try:
        sched = get_schedule_by_id(conn, schedule_id)
        if not sched:
            raise ValueError(f"Schedule with id {schedule_id} not found.")

        if sched.status == ScheduleStatus.SENT:
            raise ValueError("Sent schedules cannot be reactivated or modified.")

        trainee = get_trainee(conn, sched.trainee_id)
        if trainee.status in (TraineeStatus.LEFT, TraineeStatus.COMPLETED, TraineeStatus.ON_ROLL):
            if sched.stage != EmailStage.EXIT:
                raise ValueError(
                    f"Lifecycle conflict: Trainee is '{trainee.status.value}'. "
                    f"Stage '{sched.stage.value}' is ineligible under lifecycle rules."
                )

        effective_sched = adjust_for_weekend(explicit_date)
        now_iso = datetime.now(APP_TIMEZONE).isoformat()

        conn.execute(
            """
            UPDATE email_schedules SET
                status = ?,
                custom_date = ?,
                scheduled_date = ?,
                is_custom_date = 1,
                is_opted_out = 0,
                cancellation_reason = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (
                ScheduleStatus.SCHEDULED.value,
                format_date_db(explicit_date),
                format_date_db(effective_sched),
                now_iso,
                schedule_id
            )
        )

        log_audit_event(
            conn,
            entity_type="schedule",
            entity_id=str(schedule_id),
            action="MANUAL_REACTIVATE",
            actor=actor,
            old_values={"status": sched.status.value},
            new_values={
                "status": ScheduleStatus.SCHEDULED.value,
                "scheduled_date": format_date_db(effective_sched)
            },
            reason=reason or "Administrator explicitly re-enabled cancelled schedule"
        )
        conn.execute("COMMIT")
        return get_schedule_by_id(conn, schedule_id)
    except Exception:
        conn.execute("ROLLBACK")
        raise

def resolve_uncertain_schedule(
    conn: sqlite3.Connection,
    schedule_id: int,
    resolution: str,  # 'confirm_sent' or 'authorize_retry' or 'cancel'
    actor: str = "admin",
    reason: Optional[str] = None
) -> EmailSchedule:
    """Authorized manual resolution of an Uncertain delivery schedule.
    
    Resolution records actor, timestamp, reason, and action without rewriting attempt history.
    """
    if resolution not in ("confirm_sent", "authorize_retry", "cancel"):
        raise ValueError(f"Invalid resolution '{resolution}'. Must be confirm_sent, authorize_retry, or cancel.")

    conn.execute("BEGIN IMMEDIATE")
    try:
        sched = get_schedule_by_id(conn, schedule_id)
        if not sched:
            raise ValueError(f"Schedule {schedule_id} not found.")

        if sched.status != ScheduleStatus.UNCERTAIN:
            raise ValueError(f"Schedule {schedule_id} status is '{sched.status.value}', expected 'Uncertain'.")

        now_iso = datetime.now(APP_TIMEZONE).isoformat()

        if resolution == "confirm_sent":
            target_status = ScheduleStatus.SENT
            conn.execute(
                """
                UPDATE email_schedules SET
                    status = ?,
                    sent_at = ?,
                    delivery_phase = 'completed',
                    lease_expires_at = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (target_status.value, now_iso, now_iso, schedule_id)
            )
        elif resolution == "authorize_retry":
            target_status = ScheduleStatus.SCHEDULED
            conn.execute(
                """
                UPDATE email_schedules SET
                    status = ?,
                    delivery_phase = NULL,
                    lease_expires_at = NULL,
                    claimed_at = NULL,
                    worker_id = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (target_status.value, now_iso, schedule_id)
            )
        elif resolution == "cancel":
            target_status = ScheduleStatus.CANCELLED
            conn.execute(
                """
                UPDATE email_schedules SET
                    status = ?,
                    cancellation_reason = 'Cancelled by administrator resolution',
                    delivery_phase = NULL,
                    lease_expires_at = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (target_status.value, now_iso, schedule_id)
            )

        log_audit_event(
            conn,
            entity_type="schedule",
            entity_id=str(schedule_id),
            action=f"RESOLVE_UNCERTAIN_{resolution.upper()}",
            actor=actor,
            old_values={"status": ScheduleStatus.UNCERTAIN.value},
            new_values={"status": target_status.value},
            reason=reason or f"Admin resolved uncertain delivery via {resolution}"
        )
        conn.execute("COMMIT")
        return get_schedule_by_id(conn, schedule_id)
    except Exception:
        conn.execute("ROLLBACK")
        raise

def update_stage_preferences_and_dates(
    conn: sqlite3.Connection,
    trainee_id: str,
    stage_preferences: Optional[Dict[EmailStage, Optional[bool]]] = None,
    stage_custom_dates: Optional[Dict[EmailStage, Optional[date]]] = None,
    clear_custom_dates: Optional[Dict[EmailStage, bool]] = None,
    actor: str = "system",
    reason: Optional[str] = None
) -> List[EmailSchedule]:
    """Unified service for updating email stage preferences and scheduled dates.

    Guarantees:
    - Single source of truth: directly persists and reconciles database schedules.
    - Sent schedules are strictly immutable (rejects any attempt to change opt-out or date).
    - Lifecycle rules are strictly enforced (e.g. non-Exit stages cannot be re-enabled for Left/Completed/On Roll trainees).
    - Lifecycle cancellation takes precedence over custom dates (setting a custom date on a lifecycle-cancelled schedule does not revive it).
    - Weekend adjustment applies to all custom dates.
    - Transactional execution with immediate locking and rollback on error.
    - Append-only audit logging for every changed value.
    """
    stage_preferences = stage_preferences or {}
    stage_custom_dates = stage_custom_dates or {}
    clear_custom_dates = clear_custom_dates or {}

    conn.execute("BEGIN IMMEDIATE")
    try:
        trainee = get_trainee(conn, trainee_id)
        if not trainee:
            raise ValueError(f"Trainee '{trainee_id}' not found.")

        current_schedules = get_schedules_for_trainee(conn, trainee_id)
        stage_map = {s.stage: s for s in current_schedules}

        now_iso = datetime.now(APP_TIMEZONE).isoformat()
        ordered_stages = [
            EmailStage.INITIAL,
            EmailStage.Q1,
            EmailStage.Q2,
            EmailStage.Q3,
            EmailStage.Q4,
            EmailStage.EXIT
        ]

        for stage in ordered_stages:
            if stage not in stage_map:
                continue

            sched = stage_map[stage]
            req_opt_out = stage_preferences.get(stage)
            req_custom_date = stage_custom_dates.get(stage)
            req_clear_custom = clear_custom_dates.get(stage, False)

            # Skip if nothing requested for this stage
            if req_opt_out is None and req_custom_date is None and not req_clear_custom:
                continue

            # SENT IS IMMUTABLE
            if sched.status == ScheduleStatus.SENT:
                if req_opt_out is not None and req_opt_out != sched.is_opted_out:
                    raise ValueError(f"Cannot modify preference for stage '{stage.value}': it is already SENT and strictly immutable.")
                if req_custom_date is not None and req_custom_date != sched.custom_date:
                    raise ValueError(f"Cannot modify scheduled date for stage '{stage.value}': it is already SENT and strictly immutable.")
                if req_clear_custom and sched.is_custom_date:
                    raise ValueError(f"Cannot clear custom date for stage '{stage.value}': it is already SENT and strictly immutable.")
                continue

            new_is_opted_out = sched.is_opted_out
            new_status = sched.status
            new_cancellation_reason = sched.cancellation_reason
            new_custom_date = sched.custom_date
            new_scheduled_date = sched.scheduled_date
            new_is_custom = sched.is_custom_date

            # 1. Process Date Update if requested
            if req_clear_custom:
                new_is_custom = False
                new_custom_date = None
                new_scheduled_date = adjust_for_weekend(sched.original_due_date)
            elif req_custom_date is not None:
                new_is_custom = True
                new_custom_date = req_custom_date
                new_scheduled_date = adjust_for_weekend(req_custom_date)

            # 2. Process Opt-Out preference if requested
            if req_opt_out is not None:
                if req_opt_out is True:
                    # Opting out
                    new_is_opted_out = True
                    new_status = ScheduleStatus.CANCELLED
                    new_cancellation_reason = "Opted out by user preference"
                else:
                    # Opting in / Re-enabling
                    # Lifecycle check
                    if trainee.status in (TraineeStatus.LEFT, TraineeStatus.COMPLETED, TraineeStatus.ON_ROLL):
                        if stage != EmailStage.EXIT:
                            raise ValueError(
                                f"Lifecycle conflict: Trainee is '{trainee.status.value}'. "
                                f"Stage '{stage.value}' cannot be re-enabled under lifecycle rules."
                            )
                    new_is_opted_out = False
                    if sched.status == ScheduleStatus.CANCELLED:
                        new_status = ScheduleStatus.SCHEDULED
                        new_cancellation_reason = None
            else:
                # If opt-out was not specified, but custom date was:
                # Lifecycle cancellation rule: A custom date must NOT reactivate a stage cancelled due to lifecycle status or opt-out!
                if sched.status == ScheduleStatus.CANCELLED:
                    new_status = ScheduleStatus.CANCELLED

            # Check if any changes
            has_changes = (
                new_is_opted_out != sched.is_opted_out or
                new_is_custom != sched.is_custom_date or
                new_custom_date != sched.custom_date or
                new_scheduled_date != sched.scheduled_date or
                new_status != sched.status or
                new_cancellation_reason != sched.cancellation_reason
            )

            if has_changes:
                old_vals = {
                    "is_opted_out": sched.is_opted_out,
                    "is_custom_date": sched.is_custom_date,
                    "custom_date": format_date_db(sched.custom_date),
                    "scheduled_date": format_date_db(sched.scheduled_date),
                    "status": sched.status.value,
                }
                new_vals = {
                    "is_opted_out": new_is_opted_out,
                    "is_custom_date": new_is_custom,
                    "custom_date": format_date_db(new_custom_date),
                    "scheduled_date": format_date_db(new_scheduled_date),
                    "status": new_status.value,
                }

                conn.execute(
                    """
                    UPDATE email_schedules SET
                        is_opted_out = ?,
                        is_custom_date = ?,
                        custom_date = ?,
                        scheduled_date = ?,
                        status = ?,
                        cancellation_reason = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        1 if new_is_opted_out else 0,
                        1 if new_is_custom else 0,
                        format_date_db(new_custom_date) if new_custom_date else None,
                        format_date_db(new_scheduled_date),
                        new_status.value,
                        new_cancellation_reason,
                        now_iso,
                        sched.id
                    )
                )

                log_audit_event(
                    conn,
                    entity_type="schedule",
                    entity_id=str(sched.id),
                    action="UPDATE_STAGE_SYNC",
                    actor=actor,
                    old_values=old_vals,
                    new_values=new_vals,
                    reason=reason or f"Synchronized update for stage {stage.value}"
                )

        conn.execute("COMMIT")
        return get_schedules_for_trainee(conn, trainee_id)
    except Exception:
        conn.execute("ROLLBACK")
        raise

