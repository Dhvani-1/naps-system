"""Background dispatch worker engine with atomic claiming, lease crash recovery, and retry safeguards."""

from datetime import date, datetime, timedelta
import sqlite3
from typing import Dict, List, Optional, Tuple
import uuid

from naps_engine.audit import log_audit_event
from naps_engine.config import (
    APP_TIMEZONE,
    DEFAULT_LEASE_DURATION_SECONDS,
    MAX_AUTOMATIC_RETRIES,
)
from naps_engine.db import get_schedule_by_id, get_trainee, row_to_schedule
from naps_engine.mailer import (
    DeliveryResultStatus,
    EmailFailureCategory,
    MailDispatchResult,
    Mailer,
)
from naps_engine.models import (
    DeliveryAttempt,
    DeliveryPhase,
    EmailSchedule,
    EmailStage,
    ScheduleStatus,
    STAGE_LABELS,
    Trainee,
    TraineeStatus,
    format_date_db,
    format_date_ui,
    validate_email_syntax,
)

class DispatchWorker:
    """Automated dispatch worker for HR Trainee email schedules."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        worker_id: Optional[str] = None,
        lease_seconds: int = DEFAULT_LEASE_DURATION_SECONDS,
        mailer: Optional[Mailer] = None
    ):
        self.conn = conn
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.lease_seconds = lease_seconds
        self.mailer = mailer or Mailer()

    def get_today_kolkata(self) -> date:
        """Evaluate today's operational date explicitly in Asia/Kolkata."""
        return datetime.now(APP_TIMEZONE).date()

    def recover_expired_leases(self) -> int:
        """Scan for abandoned 'Processing' schedules whose lease has expired.
        
        Guarantees:
        - If phase is 'transmitting', we cannot know if remote server accepted it -> mark UNCERTAIN.
        - If phase is 'claimed' or 'preparing', MTA was never contacted -> safely revert to SCHEDULED.
        """
        now = datetime.now(APP_TIMEZONE)
        now_iso = now.isoformat()
        recovered_count = 0

        self.conn.execute("BEGIN IMMEDIATE")
        try:
            cursor = self.conn.execute(
                """
                SELECT id, delivery_phase, stage, trainee_id, attempt_count
                FROM email_schedules
                WHERE status = 'Processing'
                  AND lease_expires_at IS NOT NULL
                  AND lease_expires_at < ?
                """,
                (now_iso,)
            )
            expired_rows = cursor.fetchall()

            for row in expired_rows:
                schedule_id = row["id"]
                phase = row["delivery_phase"]
                stage = row["stage"]
                trainee_id = row["trainee_id"]

                if phase == "transmitting":
                    # Ambiguous: could have sent before worker crash
                    self.conn.execute(
                        """
                        UPDATE email_schedules SET
                            status = ?,
                            last_error = ?,
                            lease_expires_at = NULL,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (
                            ScheduleStatus.UNCERTAIN.value,
                            "Worker crashed during transmission lease. Outcome is uncertain.",
                            now_iso,
                            schedule_id
                        )
                    )
                    log_audit_event(
                        self.conn,
                        entity_type="schedule",
                        entity_id=str(schedule_id),
                        action="LEASE_RECOVERY_UNCERTAIN",
                        actor=self.worker_id,
                        reason="Lease expired during active email transmission phase"
                    )
                else:
                    # Safe to revert to Scheduled (or Retrying if prior attempts)
                    target_status = ScheduleStatus.RETRYING if row["attempt_count"] > 0 else ScheduleStatus.SCHEDULED
                    self.conn.execute(
                        """
                        UPDATE email_schedules SET
                            status = ?,
                            worker_id = NULL,
                            delivery_phase = NULL,
                            claimed_at = NULL,
                            lease_expires_at = NULL,
                            updated_at = ?
                        WHERE id = ?
                        """,
                        (target_status.value, now_iso, schedule_id)
                    )
                    log_audit_event(
                        self.conn,
                        entity_type="schedule",
                        entity_id=str(schedule_id),
                        action="LEASE_RECOVERY_REVERT",
                        actor=self.worker_id,
                        reason="Lease expired before transmission commitment point. Reverted safely."
                    )
                recovered_count += 1

            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

        return recovered_count

    def claim_schedule(self, schedule_id: int) -> Optional[EmailSchedule]:
        """Atomically claim a due schedule with an operational lease.
        Two workers cannot claim the same schedule concurrently.
        """
        now = datetime.now(APP_TIMEZONE)
        now_iso = now.isoformat()
        lease_expires = (now + timedelta(seconds=self.lease_seconds)).isoformat()

        self.conn.execute("BEGIN IMMEDIATE")
        try:
            # Atomic update: must be in Scheduled or Retrying and not opted out
            cursor = self.conn.execute(
                """
                UPDATE email_schedules SET
                    status = 'Processing',
                    worker_id = ?,
                    claimed_at = ?,
                    lease_expires_at = ?,
                    delivery_phase = 'claimed',
                    updated_at = ?
                WHERE id = ?
                  AND status IN ('Scheduled', 'Retrying')
                  AND is_opted_out = 0
                """,
                (self.worker_id, now_iso, lease_expires, now_iso, schedule_id)
            )
            if cursor.rowcount == 0:
                self.conn.execute("ROLLBACK")
                return None

            claimed_sched = get_schedule_by_id(self.conn, schedule_id)
            self.conn.execute("COMMIT")
            return claimed_sched
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def find_due_schedules(self, target_date: Optional[date] = None) -> List[int]:
        """Find candidate schedule IDs whose scheduled_date <= target_date."""
        eval_date = target_date or self.get_today_kolkata()
        date_str = format_date_db(eval_date)

        cursor = self.conn.execute(
            """
            SELECT s.id
            FROM email_schedules s
            JOIN trainees t ON s.trainee_id = t.trainee_id
            WHERE s.scheduled_date <= ?
              AND s.status IN ('Scheduled', 'Retrying')
              AND s.is_opted_out = 0
              AND t.is_archived = 0
            ORDER BY s.scheduled_date ASC, s.id ASC
            """,
            (date_str,)
        )
        return [row["id"] for row in cursor.fetchall()]

    def resolve_recipient(self, sched: EmailSchedule, trainee: Trainee) -> Tuple[Optional[str], Optional[str]]:
        """Resolve authoritative recipient email address dynamically from latest trainee record.
        
        - Initial: latest valid trainee_email
        - Q1-Q4: latest valid manager_email
        - Exit: latest valid trainee_email
        """
        if sched.stage in (EmailStage.INITIAL, EmailStage.EXIT):
            recipient = (trainee.trainee_email or "").strip()
            if not validate_email_syntax(recipient):
                return None, f"Trainee email '{recipient}' is missing or has invalid syntax."
            return recipient, None
        elif sched.stage in (EmailStage.Q1, EmailStage.Q2, EmailStage.Q3, EmailStage.Q4):
            recipient = (trainee.manager_email or "").strip()
            if not validate_email_syntax(recipient):
                return None, f"Manager email '{recipient}' is missing or has invalid syntax."
            return recipient, None
        else:
            return None, f"Unknown stage: {sched.stage}"

    def process_schedule(self, schedule_id: int) -> Dict[str, str]:
        """Process a single schedule through atomic claiming, safety checks, and dispatch."""
        claimed = self.claim_schedule(schedule_id)
        if not claimed:
            return {"status": "SKIPPED", "reason": "Could not claim (already claimed, sent, or cancelled)"}

        # Load fresh trainee data
        trainee = get_trainee(self.conn, claimed.trainee_id)
        now = datetime.now(APP_TIMEZONE)
        now_iso = now.isoformat()

        # Check 1: Trainee exists and not archived
        if not trainee or trainee.is_archived:
            self._cancel_claimed(schedule_id, "Trainee is archived or missing")
            return {"status": "CANCELLED", "reason": "Trainee archived"}

        # Check 2: Lifecycle rules enforcement immediately before dispatch
        if trainee.status in (TraineeStatus.LEFT, TraineeStatus.COMPLETED, TraineeStatus.ON_ROLL):
            if claimed.stage != EmailStage.EXIT:
                self._cancel_claimed(schedule_id, f"Ineligible under lifecycle status {trainee.status.value}")
                return {"status": "CANCELLED", "reason": f"Lifecycle status {trainee.status.value}"}

        # Check 3: Opt-out preference check
        if claimed.is_opted_out:
            self._cancel_claimed(schedule_id, "Stage opted out by user preference")
            return {"status": "CANCELLED", "reason": "Opted out"}

        # Check 4: Recipient resolution
        recipient, error_msg = self.resolve_recipient(claimed, trainee)
        if error_msg or not recipient:
            self._record_failure(
                schedule=claimed,
                attempt_num=claimed.attempt_count + 1,
                recipient_email=recipient or "UNKNOWN",
                category="recipient_invalid",
                error_details=error_msg or "Recipient address invalid",
                is_permanent=True
            )
            return {"status": "FAILED", "reason": error_msg or "Invalid recipient"}

        # Phase update callback helper
        def update_phase(phase: str):
            self.conn.execute(
                "UPDATE email_schedules SET delivery_phase = ?, updated_at = ? WHERE id = ?",
                (phase, datetime.now(APP_TIMEZONE).isoformat(), schedule_id)
            )

        # Dispatch via mailer
        subject = f"[NAPS HR] {STAGE_LABELS.get(claimed.stage, claimed.stage.value)} - {trainee.trainee_name}"
        body = (
            f"Dear {trainee.trainee_name if claimed.stage in (EmailStage.INITIAL, EmailStage.EXIT) else trainee.manager_name},\n\n"
            f"Notification for {STAGE_LABELS.get(claimed.stage, claimed.stage.value)} regarding trainee {trainee.trainee_name} (ID: {trainee.trainee_id}).\n"
            f"Scheduled Date: {format_date_ui(claimed.scheduled_date)}\n"
        )

        result: MailDispatchResult = self.mailer.send_email(
            to_email=recipient,
            subject=subject,
            body=body,
            on_phase_callback=update_phase
        )

        attempt_num = claimed.attempt_count + 1

        if result.status == DeliveryResultStatus.SUCCESS:
            self._record_success(claimed, recipient, attempt_num, result.details)
            return {"status": "SENT", "recipient": recipient}

        elif result.status == DeliveryResultStatus.TRANSIENT_FAILURE:
            if attempt_num <= MAX_AUTOMATIC_RETRIES:
                self._record_transient_retry(claimed, recipient, attempt_num, result.error_message)
                return {"status": "RETRYING", "error": result.error_message}
            else:
                self._record_failure(
                    schedule=claimed,
                    attempt_num=attempt_num,
                    recipient_email=recipient,
                    category=result.category.value if result.category else "transient_exhausted",
                    error_details=result.error_message or "Transient error retry exhausted",
                    is_permanent=True
                )
                return {"status": "FAILED", "error": result.error_message}

        elif result.status == DeliveryResultStatus.AMBIGUOUS:
            self._record_ambiguous(claimed, recipient, attempt_num, result.error_message)
            return {"status": "UNCERTAIN", "error": result.error_message}

        else:  # PERMANENT_FAILURE
            self._record_failure(
                schedule=claimed,
                attempt_num=attempt_num,
                recipient_email=recipient,
                category=result.category.value if result.category else "permanent_smtp",
                error_details=result.error_message or "Permanent delivery failure",
                is_permanent=True
            )
            return {"status": "FAILED", "error": result.error_message}

    def run_worker_cycle(self, target_date: Optional[date] = None) -> Dict[str, int]:
        """Execute one complete worker dispatch cycle.
        
        1. Recover expired leases.
        2. Find all eligible due schedules (scheduled_date <= target_date).
        3. Dispatch each schedule atomically.
        """
        recovered = self.recover_expired_leases()
        due_ids = self.find_due_schedules(target_date)

        summary = {
            "recovered": recovered,
            "due": len(due_ids),
            "claimed": len(due_ids),
            "sent": 0,
            "failed": 0,
            "retrying": 0,
            "uncertain": 0,
            "cancelled": 0,
            "skipped": 0,
        }

        for sid in due_ids:
            res = self.process_schedule(sid)
            status = res["status"].lower()
            if status in summary:
                summary[status] += 1

        return summary

    def _cancel_claimed(self, schedule_id: int, reason: str):
        now_iso = datetime.now(APP_TIMEZONE).isoformat()
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute(
                """
                UPDATE email_schedules SET
                    status = 'Cancelled',
                    cancellation_reason = ?,
                    delivery_phase = NULL,
                    lease_expires_at = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (reason, now_iso, schedule_id)
            )
            log_audit_event(
                self.conn,
                entity_type="schedule",
                entity_id=str(schedule_id),
                action="WORKER_CANCEL",
                actor=self.worker_id,
                reason=reason
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def _record_success(self, schedule: EmailSchedule, recipient: str, attempt_num: int, details: Optional[str]):
        now_iso = datetime.now(APP_TIMEZONE).isoformat()
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            # Mark Sent - Sent is IMMUTABLE!
            self.conn.execute(
                """
                UPDATE email_schedules SET
                    status = 'Sent',
                    sent_at = ?,
                    recipient_email_used = ?,
                    delivery_phase = 'completed',
                    lease_expires_at = NULL,
                    attempt_count = ?,
                    last_attempt_at = ?,
                    last_error = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (now_iso, recipient, attempt_num, now_iso, now_iso, schedule.id)
            )
            details_str = details or "Dispatched successfully"
            is_sim = ("[SIMULATION]" in details_str or "[DRY-RUN]" in details_str or getattr(self.mailer, "dry_run", True))
            outcome = "SIMULATED_SUCCESS" if is_sim else "SENT"
            failure_cat = "simulated_delivery" if is_sim else None

            self.conn.execute(
                """
                INSERT INTO delivery_attempts (
                    schedule_id, trainee_id, stage, attempt_number, attempt_at,
                    recipient_email, status_outcome, failure_category, error_details,
                    retry_decision, worker_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'NONE', ?)
                """,
                (schedule.id, schedule.trainee_id, schedule.stage.value, attempt_num, now_iso, recipient, outcome, failure_cat, details_str, self.worker_id)
            )
            log_audit_event(
                self.conn,
                entity_type="schedule",
                entity_id=str(schedule.id),
                action="DISPATCH_SIMULATED_SUCCESS" if is_sim else "DISPATCH_SENT",
                actor=self.worker_id,
                new_values={"status": "Sent", "recipient": recipient, "attempt": attempt_num, "is_simulated": is_sim},
                reason=details_str
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def _record_transient_retry(self, schedule: EmailSchedule, recipient: str, attempt_num: int, error_msg: Optional[str]):
        now_iso = datetime.now(APP_TIMEZONE).isoformat()
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute(
                """
                UPDATE email_schedules SET
                    status = 'Retrying',
                    delivery_phase = NULL,
                    lease_expires_at = NULL,
                    attempt_count = ?,
                    last_attempt_at = ?,
                    last_error = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (attempt_num, now_iso, error_msg, now_iso, schedule.id)
            )
            self.conn.execute(
                """
                INSERT INTO delivery_attempts (
                    schedule_id, trainee_id, stage, attempt_number, attempt_at,
                    recipient_email, status_outcome, failure_category, error_details,
                    retry_decision, worker_id
                ) VALUES (?, ?, ?, ?, ?, ?, 'RETRYING', 'transient_smtp', ?, 'SCHEDULE_RETRY', ?)
                """,
                (schedule.id, schedule.trainee_id, schedule.stage.value, attempt_num, now_iso, recipient, error_msg, self.worker_id)
            )
            log_audit_event(
                self.conn,
                entity_type="schedule",
                entity_id=str(schedule.id),
                action="DISPATCH_TRANSIENT_RETRY",
                actor=self.worker_id,
                reason=f"Attempt {attempt_num} encountered transient failure. Scheduled 1 automatic retry."
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def _record_ambiguous(self, schedule: EmailSchedule, recipient: str, attempt_num: int, error_msg: Optional[str]):
        now_iso = datetime.now(APP_TIMEZONE).isoformat()
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute(
                """
                UPDATE email_schedules SET
                    status = 'Uncertain',
                    delivery_phase = 'transmitting',
                    lease_expires_at = NULL,
                    attempt_count = ?,
                    last_attempt_at = ?,
                    last_error = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (attempt_num, now_iso, error_msg, now_iso, schedule.id)
            )
            self.conn.execute(
                """
                INSERT INTO delivery_attempts (
                    schedule_id, trainee_id, stage, attempt_number, attempt_at,
                    recipient_email, status_outcome, failure_category, error_details,
                    retry_decision, worker_id
                ) VALUES (?, ?, ?, ?, ?, ?, 'UNCERTAIN', 'ambiguous_timeout', ?, 'MANUAL_RESOLUTION_REQUIRED', ?)
                """,
                (schedule.id, schedule.trainee_id, schedule.stage.value, attempt_num, now_iso, recipient, error_msg, self.worker_id)
            )
            log_audit_event(
                self.conn,
                entity_type="schedule",
                entity_id=str(schedule.id),
                action="DISPATCH_UNCERTAIN",
                actor=self.worker_id,
                reason="Transmission interrupted or timed out. Delivery outcome uncertain."
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def _record_failure(
        self,
        schedule: EmailSchedule,
        attempt_num: int,
        recipient_email: str,
        category: str,
        error_details: str,
        is_permanent: bool
    ):
        now_iso = datetime.now(APP_TIMEZONE).isoformat()
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute(
                """
                UPDATE email_schedules SET
                    status = 'Failed',
                    delivery_phase = NULL,
                    lease_expires_at = NULL,
                    attempt_count = ?,
                    last_attempt_at = ?,
                    last_error = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (attempt_num, now_iso, error_details, now_iso, schedule.id)
            )
            self.conn.execute(
                """
                INSERT INTO delivery_attempts (
                    schedule_id, trainee_id, stage, attempt_number, attempt_at,
                    recipient_email, status_outcome, failure_category, error_details,
                    retry_decision, worker_id
                ) VALUES (?, ?, ?, ?, ?, ?, 'FAILED', ?, ?, 'NO_RETRY', ?)
                """,
                (schedule.id, schedule.trainee_id, schedule.stage.value, attempt_num, now_iso, recipient_email, category, error_details, self.worker_id)
            )
            log_audit_event(
                self.conn,
                entity_type="schedule",
                entity_id=str(schedule.id),
                action="DISPATCH_FAILED",
                actor=self.worker_id,
                reason=f"Dispatch failed permanently: {error_details}"
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
