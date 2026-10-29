"""Excel and CSV Import/Update engine with unified Email Stage Preferences, Idempotency, and Lifecycle Validation."""

from dataclasses import dataclass, field
from datetime import date, datetime
import io
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from naps_engine.audit import log_audit_event
from naps_engine.config import APP_TIMEZONE
from naps_engine.date_engine import calculate_all_stage_dates, calculate_default_lwd, validate_dates
from naps_engine.db import get_schedules_for_trainee, get_trainee, list_trainees
from naps_engine.models import (
    EmailSchedule,
    EmailStage,
    LwdMode,
    ScheduleStatus,
    Trainee,
    TraineeStatus,
    format_date_db,
    format_date_ui,
    parse_date,
    validate_email_syntax,
)
from naps_engine.reconciliation import (
    create_trainee_with_schedules,
    update_stage_preferences_and_dates,
    update_trainee_and_reconcile,
)

STAGE_COLUMN_MAP = {
    EmailStage.INITIAL: {
        "opt_out": "initial_email_opt_out",
        "scheduled_date": "initial_email_scheduled_date",
    },
    EmailStage.Q1: {
        "opt_out": "q1_opt_out",
        "scheduled_date": "q1_scheduled_date",
    },
    EmailStage.Q2: {
        "opt_out": "q2_opt_out",
        "scheduled_date": "q2_scheduled_date",
    },
    EmailStage.Q3: {
        "opt_out": "q3_opt_out",
        "scheduled_date": "q3_scheduled_date",
    },
    EmailStage.Q4: {
        "opt_out": "q4_opt_out",
        "scheduled_date": "q4_scheduled_date",
    },
    EmailStage.EXIT: {
        "opt_out": "exit_feedback_opt_out",
        "scheduled_date": "exit_feedback_scheduled_date",
    },
}

@dataclass
class RowImportResult:
    row_number: int
    trainee_id: Optional[str]
    success: bool
    action: str  # "CREATED", "UPDATED", "UNCHANGED", "FAILED"
    errors: List[Dict[str, str]] = field(default_factory=list)  # [{"field": ..., "reason": ...}]
    details: Optional[str] = None

@dataclass
class ImportSummary:
    total_rows: int
    created_count: int
    updated_count: int
    unchanged_count: int
    failed_count: int
    results: List[RowImportResult]

    @property
    def created(self) -> int:
        return self.created_count

    @property
    def updated(self) -> int:
        return self.updated_count

    @property
    def unchanged(self) -> int:
        return self.unchanged_count

    @property
    def failed(self) -> int:
        return self.failed_count

def normalize_column_name(col: str) -> str:
    """Normalize dataframe header string for flexible matching."""
    c = str(col).strip().lower().replace(" ", "_").replace("-", "_").replace(".", "_")
    mapping = {
        "id": "trainee_id",
        "trainee_id": "trainee_id",
        "name": "trainee_name",
        "trainee_name": "trainee_name",
        "email": "trainee_email",
        "trainee_email": "trainee_email",
        "doj": "date_of_joining",
        "date_of_joining": "date_of_joining",
        "joining_date": "date_of_joining",
        "manager": "manager_name",
        "manager_name": "manager_name",
        "manager_email": "manager_email",
        "department": "department",
        "location": "location",
        "status": "status",
        "lwd": "last_working_date",
        "last_working_date": "last_working_date",
        "confirmed_actual_lwd": "confirmed_actual_lwd",
        # Stage Opt-Out columns
        "initial_email_opt_out": "initial_email_opt_out",
        "initial_opt_out": "initial_email_opt_out",
        "opt_out_initial": "initial_email_opt_out",
        "welcome_email_opt_out": "initial_email_opt_out",
        "q1_opt_out": "q1_opt_out",
        "q1_email_opt_out": "q1_opt_out",
        "opt_out_q1": "q1_opt_out",
        "q2_opt_out": "q2_opt_out",
        "q2_email_opt_out": "q2_opt_out",
        "opt_out_q2": "q2_opt_out",
        "q3_opt_out": "q3_opt_out",
        "q3_email_opt_out": "q3_opt_out",
        "opt_out_q3": "q3_opt_out",
        "q4_opt_out": "q4_opt_out",
        "q4_email_opt_out": "q4_opt_out",
        "opt_out_q4": "q4_opt_out",
        "exit_feedback_opt_out": "exit_feedback_opt_out",
        "exit_opt_out": "exit_feedback_opt_out",
        "exit_email_opt_out": "exit_feedback_opt_out",
        "opt_out_exit": "exit_feedback_opt_out",
        # Stage Scheduled Date columns
        "initial_email_scheduled_date": "initial_email_scheduled_date",
        "initial_scheduled_date": "initial_email_scheduled_date",
        "welcome_email_scheduled_date": "initial_email_scheduled_date",
        "q1_scheduled_date": "q1_scheduled_date",
        "q1_email_scheduled_date": "q1_scheduled_date",
        "q2_scheduled_date": "q2_scheduled_date",
        "q2_email_scheduled_date": "q2_scheduled_date",
        "q3_scheduled_date": "q3_scheduled_date",
        "q3_email_scheduled_date": "q3_scheduled_date",
        "q4_scheduled_date": "q4_scheduled_date",
        "q4_email_scheduled_date": "q4_scheduled_date",
        "exit_feedback_scheduled_date": "exit_feedback_scheduled_date",
        "exit_scheduled_date": "exit_feedback_scheduled_date",
        "exit_email_scheduled_date": "exit_feedback_scheduled_date",
    }
    return mapping.get(c, c)

def parse_bool_field(val: Any) -> Optional[bool]:
    """Parse boolean representation strictly.
    Returns True for true/1/yes/opt_out/opted_out.
    Returns False for false/0/no/active/enabled.
    Returns None if blank or empty (preserves existing).
    Raises ValueError if unrecognized string.
    """
    if val is None or pd.isna(val):
        return None
    if isinstance(val, bool):
        return val
    
    val_str = str(val).strip().lower()
    if not val_str:
        return None
        
    if val_str in ("true", "1", "yes", "y", "t", "opt_out", "opted_out", "optout"):
        return True
    elif val_str in ("false", "0", "no", "n", "f", "active", "enabled", "opt_in", "optin"):
        return False
    else:
        raise ValueError(f"Invalid boolean value: '{val}'. Expected True/False, Yes/No, or 1/0.")

def parse_optional_date(val: Any) -> Optional[date]:
    """Parse date safely, returning None if empty, or raising ValueError if invalid."""
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    return parse_date(val_str)

class ExcelImporter:
    """Idempotent Excel/CSV Trainee and Schedule Preferences data importer."""

    def __init__(self, conn: sqlite3.Connection, actor: str = "importer"):
        self.conn = conn
        self.actor = actor

    def parse_file(self, file_path_or_buffer) -> pd.DataFrame:
        """Parse Excel (.xlsx, .xls) or CSV into a normalized DataFrame."""
        if isinstance(file_path_or_buffer, pd.DataFrame):
            df = file_path_or_buffer.copy()
        elif isinstance(file_path_or_buffer, str) and file_path_or_buffer.endswith(".csv"):
            df = pd.read_csv(file_path_or_buffer, dtype=str)
        else:
            try:
                # If multi-sheet workbook, detect Trainees_Import or sheet with trainee_id
                xl = pd.ExcelFile(file_path_or_buffer)
                target_sheet = 0
                for s in xl.sheet_names:
                    if s.lower() in ("trainees_import", "trainees", "import"):
                        target_sheet = s
                        break
                if target_sheet == 0 and len(xl.sheet_names) > 1:
                    for s in xl.sheet_names:
                        test_df = xl.parse(s, nrows=2)
                        norm_cols = [normalize_column_name(c) for c in test_df.columns]
                        if "trainee_id" in norm_cols:
                            target_sheet = s
                            break
                df = xl.parse(target_sheet, dtype=str)
            except Exception:
                # Fallback to CSV if reading as Excel fails
                if hasattr(file_path_or_buffer, "seek"):
                    file_path_or_buffer.seek(0)
                df = pd.read_csv(file_path_or_buffer, dtype=str)

        # Normalize column headers and deduplicate keeping the last specified value
        df.columns = [normalize_column_name(c) for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated(keep="last")]
        return df

    def import_trainees(
        self,
        file_path_or_buffer,
        clear_fields: bool = False,
        default_status: TraineeStatus = TraineeStatus.ACTIVE
    ) -> ImportSummary:
        """Execute transactional row-by-row import with partial failure isolation and full idempotency."""
        df = self.parse_file(file_path_or_buffer)
        total_rows = len(df)
        results: List[RowImportResult] = []

        created = 0
        updated = 0
        unchanged = 0
        failed = 0

        for idx, row in df.iterrows():
            row_num = idx + 2  # 1-indexed Excel row (header is row 1)
            raw_id = str(row.get("trainee_id", "")).strip() if pd.notna(row.get("trainee_id")) else ""
            if not raw_id:
                failed += 1
                results.append(
                    RowImportResult(
                        row_number=row_num,
                        trainee_id=None,
                        success=False,
                        action="FAILED",
                        errors=[{"field": "trainee_id", "reason": "trainee_id is mandatory and cannot be empty."}]
                    )
                )
                continue

            row_res = self._process_row(
                row_num=row_num,
                trainee_id=raw_id,
                row_data=row,
                clear_fields=clear_fields,
                default_status=default_status
            )
            results.append(row_res)

            if row_res.success:
                if row_res.action == "CREATED":
                    created += 1
                elif row_res.action == "UPDATED":
                    updated += 1
                elif row_res.action == "UNCHANGED":
                    unchanged += 1
            else:
                failed += 1

        summary = ImportSummary(
            total_rows=total_rows,
            created_count=created,
            updated_count=updated,
            unchanged_count=unchanged,
            failed_count=failed,
            results=results
        )

        log_audit_event(
            self.conn,
            entity_type="import",
            entity_id="EXCEL_IMPORT",
            action="IMPORT_BATCH",
            actor=self.actor,
            new_values={
                "total": total_rows,
                "created": created,
                "updated": updated,
                "unchanged": unchanged,
                "failed": failed
            },
            reason="Excel/CSV import operation completed"
        )
        return summary

    def _process_row(
        self,
        row_num: int,
        trainee_id: str,
        row_data: pd.Series,
        clear_fields: bool,
        default_status: TraineeStatus
    ) -> RowImportResult:
        """Process a single row transactionally, handling trainee fields, opt-outs, and dates."""
        existing = get_trainee(self.conn, trainee_id)
        errors: List[Dict[str, str]] = []

        def get_val(col_name: str) -> Optional[str]:
            v = row_data.get(col_name)
            if pd.isna(v) or v is None:
                return None
            s = str(v).strip()
            return s if s else None

        raw_name = get_val("trainee_name")
        raw_email = get_val("trainee_email")
        raw_doj = get_val("date_of_joining")
        raw_mgr_name = get_val("manager_name")
        raw_mgr_email = get_val("manager_email")
        raw_dept = get_val("department")
        raw_loc = get_val("location")
        raw_status = get_val("status")
        raw_lwd = get_val("last_working_date")
        raw_confirmed_lwd = get_val("confirmed_actual_lwd")

        confirmed_actual_lwd = False
        if raw_confirmed_lwd:
            confirmed_actual_lwd = raw_confirmed_lwd.lower() in ("true", "1", "yes", "confirmed")
        elif raw_lwd and str(raw_lwd).strip():
            # If the user explicitly provided an actual Last Working Date in the row, treat as confirmed
            confirmed_actual_lwd = True

        # Parse & Validate Status
        target_status: Optional[TraineeStatus] = None
        if raw_status:
            try:
                target_status = TraineeStatus(raw_status)
            except ValueError:
                errors.append({
                    "field": "status",
                    "reason": f"Invalid status '{raw_status}'. Must be Active, Left, Completed, or On Roll."
                })
        elif not existing:
            target_status = default_status

        # Parse Dates
        parsed_doj: Optional[date] = None
        if raw_doj:
            try:
                parsed_doj = parse_date(raw_doj)
            except Exception as e:
                errors.append({"field": "date_of_joining", "reason": f"Invalid DOJ format: {str(e)}"})
        elif not existing:
            errors.append({"field": "date_of_joining", "reason": "DOJ is mandatory for new trainees."})

        parsed_lwd: Optional[date] = None
        if raw_lwd:
            try:
                parsed_lwd = parse_date(raw_lwd)
            except Exception as e:
                errors.append({"field": "last_working_date", "reason": f"Invalid LWD format: {str(e)}"})

        # Email syntax validation if supplied
        if raw_email and not validate_email_syntax(raw_email):
            errors.append({"field": "trainee_email", "reason": f"Invalid email format: '{raw_email}'"})
        if raw_mgr_email and not validate_email_syntax(raw_mgr_email):
            errors.append({"field": "manager_email", "reason": f"Invalid manager email: '{raw_mgr_email}'"})

        # Parse Stage Opt-Out Preferences and Scheduled Dates
        parsed_stage_opt_outs: Dict[EmailStage, Optional[bool]] = {}
        parsed_stage_dates: Dict[EmailStage, Optional[date]] = {}

        for stage, cols in STAGE_COLUMN_MAP.items():
            opt_col = cols["opt_out"]
            date_col = cols["scheduled_date"]

            # 1. Parse Opt-out
            raw_opt = row_data.get(opt_col)
            try:
                opt_val = parse_bool_field(raw_opt)
                parsed_stage_opt_outs[stage] = opt_val
            except ValueError as e:
                errors.append({"field": opt_col, "reason": str(e)})

            # 2. Parse Scheduled Date
            raw_date = row_data.get(date_col)
            try:
                dt_val = parse_optional_date(raw_date)
                parsed_stage_dates[stage] = dt_val
            except Exception as e:
                errors.append({"field": date_col, "reason": str(e)})

        if errors:
            return RowImportResult(
                row_number=row_num,
                trainee_id=trainee_id,
                success=False,
                action="FAILED",
                errors=errors
            )

        # BRANCH A: NEW TRAINEE CREATION
        if not existing:
            if not raw_name:
                errors.append({"field": "trainee_name", "reason": "Mandatory for new trainee."})
            if not raw_email:
                errors.append({"field": "trainee_email", "reason": "Mandatory for new trainee."})
            if not parsed_doj:
                errors.append({"field": "date_of_joining", "reason": "Mandatory for new trainee."})
            if not raw_mgr_name:
                raw_mgr_name = "Manager"
            if not raw_mgr_email:
                raw_mgr_email = "manager@example.com"
            if not raw_dept:
                raw_dept = "General"
            if not raw_loc:
                raw_loc = "HQ"

            if errors:
                return RowImportResult(
                    row_number=row_num,
                    trainee_id=trainee_id,
                    success=False,
                    action="FAILED",
                    errors=errors
                )

            lwd_mode = LwdMode.MANUAL if parsed_lwd is not None else LwdMode.AUTO
            effective_lwd = parsed_lwd or calculate_default_lwd(parsed_doj)

            try:
                validate_dates(parsed_doj, effective_lwd)
            except Exception as e:
                return RowImportResult(
                    row_number=row_num,
                    trainee_id=trainee_id,
                    success=False,
                    action="FAILED",
                    errors=[{"field": "dates", "reason": str(e)}]
                )

            if target_status == TraineeStatus.LEFT and not confirmed_actual_lwd:
                return RowImportResult(
                    row_number=row_num,
                    trainee_id=trainee_id,
                    success=False,
                    action="FAILED",
                    errors=[{
                        "field": "status",
                        "reason": "Status 'Left' requires confirmed actual LWD. Blocked."
                    }]
                )

            new_trainee = Trainee(
                trainee_id=trainee_id,
                trainee_name=raw_name,
                trainee_email=raw_email,
                date_of_joining=parsed_doj,
                manager_name=raw_mgr_name,
                manager_email=raw_mgr_email,
                department=raw_dept,
                location=raw_loc,
                status=target_status or TraineeStatus.ACTIVE,
                last_working_date=effective_lwd,
                lwd_mode=lwd_mode
            )

            # Filter non-None stage custom dates and opt-out preferences
            filtered_custom_dates = {s: d for s, d in parsed_stage_dates.items() if d is not None}
            filtered_opt_outs = {s: o for s, o in parsed_stage_opt_outs.items() if o is not None}

            try:
                create_trainee_with_schedules(
                    conn=self.conn,
                    trainee=new_trainee,
                    custom_dates=filtered_custom_dates,
                    opt_out_preferences=filtered_opt_outs,
                    confirmed_actual_lwd=confirmed_actual_lwd,
                    actor=self.actor
                )
                return RowImportResult(
                    row_number=row_num,
                    trainee_id=trainee_id,
                    success=True,
                    action="CREATED",
                    details="Trainee and 6 email schedules created successfully with stage preferences."
                )
            except Exception as e:
                return RowImportResult(
                    row_number=row_num,
                    trainee_id=trainee_id,
                    success=False,
                    action="FAILED",
                    errors=[{"field": "database", "reason": str(e)}]
                )

        # BRANCH B: UPDATE EXISTING TRAINEE
        effective_name = raw_name if raw_name is not None else existing.trainee_name
        effective_email = raw_email if raw_email is not None else existing.trainee_email
        effective_mgr_name = raw_mgr_name if raw_mgr_name is not None else existing.manager_name
        effective_mgr_email = raw_mgr_email if raw_mgr_email is not None else existing.manager_email
        effective_dept = raw_dept if raw_dept is not None else existing.department
        effective_loc = raw_loc if raw_loc is not None else existing.location
        effective_status = target_status if target_status is not None else existing.status
        effective_doj = parsed_doj if parsed_doj is not None else existing.date_of_joining

        effective_lwd = parsed_lwd if parsed_lwd is not None else existing.last_working_date
        effective_lwd_mode = LwdMode.MANUAL if parsed_lwd is not None else existing.lwd_mode

        if effective_status == TraineeStatus.LEFT and existing.status != TraineeStatus.LEFT:
            if not confirmed_actual_lwd:
                return RowImportResult(
                    row_number=row_num,
                    trainee_id=trainee_id,
                    success=False,
                    action="FAILED",
                    errors=[{
                        "field": "status",
                        "reason": "Changing status to Left requires confirmed actual LWD. Blocked."
                    }]
                )

        trainee_has_changes = (
            effective_name != existing.trainee_name or
            effective_email != existing.trainee_email or
            effective_mgr_name != existing.manager_name or
            effective_mgr_email != existing.manager_email or
            effective_dept != existing.department or
            effective_loc != existing.location or
            effective_status != existing.status or
            effective_doj != existing.date_of_joining or
            effective_lwd != existing.last_working_date
        )

        try:
            # 1. Update core trainee and reconcile default dates if core fields changed
            if trainee_has_changes:
                update_trainee_and_reconcile(
                    conn=self.conn,
                    trainee_id=trainee_id,
                    name=effective_name,
                    email=effective_email,
                    manager_name=effective_mgr_name,
                    manager_email=effective_mgr_email,
                    department=effective_dept,
                    location=effective_loc,
                    new_doj=effective_doj,
                    new_lwd=effective_lwd,
                    new_lwd_mode=effective_lwd_mode,
                    new_status=effective_status,
                    confirmed_actual_lwd=confirmed_actual_lwd,
                    manual_lwd_reviewed=True,
                    actor=self.actor,
                    reason="Updated via Excel/CSV import"
                )

            # 2. Check if any stage preferences or custom dates were supplied
            has_stage_inputs = any(v is not None for v in parsed_stage_opt_outs.values()) or any(v is not None for v in parsed_stage_dates.values())
            stage_changes_detected = False

            if has_stage_inputs:
                current_schedules = get_schedules_for_trainee(self.conn, trainee_id)
                s_map = {s.stage: s for s in current_schedules}

                # Check if requested stage values actually differ from current
                for stg, opt_req in parsed_stage_opt_outs.items():
                    if opt_req is not None and stg in s_map and opt_req != s_map[stg].is_opted_out:
                        stage_changes_detected = True
                        break
                if not stage_changes_detected:
                    for stg, dt_req in parsed_stage_dates.items():
                        if dt_req is not None and stg in s_map and dt_req != s_map[stg].custom_date:
                            stage_changes_detected = True
                            break

                if stage_changes_detected:
                    update_stage_preferences_and_dates(
                        conn=self.conn,
                        trainee_id=trainee_id,
                        stage_preferences=parsed_stage_opt_outs,
                        stage_custom_dates=parsed_stage_dates,
                        actor=self.actor,
                        reason="Updated stage preferences via Excel/CSV import"
                    )

            if not trainee_has_changes and not stage_changes_detected:
                return RowImportResult(
                    row_number=row_num,
                    trainee_id=trainee_id,
                    success=True,
                    action="UNCHANGED",
                    details="Row values identical to existing database record. Preserved without modification."
                )

            return RowImportResult(
                row_number=row_num,
                trainee_id=trainee_id,
                success=True,
                action="UPDATED",
                details="Trainee and stage schedules updated and synchronized."
            )

        except Exception as e:
            return RowImportResult(
                row_number=row_num,
                trainee_id=trainee_id,
                success=False,
                action="FAILED",
                errors=[{"field": "reconciliation", "reason": str(e)}]
            )

def generate_template_dataframe() -> pd.DataFrame:
    """Generate sample template dataframe with all trainee fields and stage opt-out/scheduled-date columns."""
    sample_rows = [
        {
            "trainee_id": "TR-9001",
            "trainee_name": "Aarav Sharma",
            "trainee_email": "trainee@example.com",
            "date_of_joining": "15/01/2025",
            "manager_name": "Vikram Malhotra",
            "manager_email": "manager@example.com",
            "department": "Engineering",
            "location": "Bangalore",
            "status": "Active",
            "last_working_date": "",  # Blank = Auto LWD (DOJ + 12m)
            "confirmed_actual_lwd": "",
            "initial_email_opt_out": "False",
            "initial_email_scheduled_date": "30/01/2025",
            "q1_opt_out": "False",
            "q1_scheduled_date": "15/04/2025",
            "q2_opt_out": "False",
            "q2_scheduled_date": "15/07/2025",
            "q3_opt_out": "False",
            "q3_scheduled_date": "15/10/2025",
            "q4_opt_out": "False",
            "q4_scheduled_date": "15/01/2026",
            "exit_feedback_opt_out": "False",
            "exit_feedback_scheduled_date": "15/04/2026",
        },
        {
            "trainee_id": "TR-9002",
            "trainee_name": "Pooja Patel",
            "trainee_email": "safetest@company.com",
            "date_of_joining": "29/02/2024",
            "manager_name": "Anita Sen",
            "manager_email": "manager@example.com",
            "department": "Operations",
            "location": "Mumbai",
            "status": "Active",
            "last_working_date": "",
            "confirmed_actual_lwd": "",
            "initial_email_opt_out": "False",
            "initial_email_scheduled_date": "",
            "q1_opt_out": "False",
            "q1_scheduled_date": "",
            "q2_opt_out": "False",
            "q2_scheduled_date": "",
            "q3_opt_out": "False",
            "q3_scheduled_date": "",
            "q4_opt_out": "False",
            "q4_scheduled_date": "",
            "exit_feedback_opt_out": "True",  # Opted out
            "exit_feedback_scheduled_date": "",
        }
    ]
    return pd.DataFrame(sample_rows)

def export_trainees_dataframe(conn: sqlite3.Connection) -> pd.DataFrame:
    """Export current trainees and their latest stage schedules as a standardized DataFrame."""
    trainees = list_trainees(conn, include_archived=False)
    rows = []

    for t in trainees:
        schedules = get_schedules_for_trainee(conn, t.trainee_id)
        s_map = {s.stage: s for s in schedules}

        row = {
            "trainee_id": t.trainee_id,
            "trainee_name": t.trainee_name,
            "trainee_email": t.trainee_email,
            "date_of_joining": format_date_ui(t.date_of_joining),
            "manager_name": t.manager_name,
            "manager_email": t.manager_email,
            "department": t.department,
            "location": t.location,
            "status": t.status.value,
            "last_working_date": format_date_ui(t.last_working_date),
            "confirmed_actual_lwd": "True" if t.status == TraineeStatus.LEFT else "False",
        }

        eff_lwd = t.last_working_date or (calculate_default_lwd(t.date_of_joining) if t.date_of_joining else None)
        auto_calc = calculate_all_stage_dates(t.date_of_joining, eff_lwd) if (t.date_of_joining and eff_lwd) else {}

        for stage, cols in STAGE_COLUMN_MAP.items():
            sched = s_map.get(stage)
            if sched and sched.scheduled_date:
                row[cols["opt_out"]] = "True" if sched.is_opted_out else "False"
                row[cols["scheduled_date"]] = format_date_ui(sched.scheduled_date)
            elif sched:
                row[cols["opt_out"]] = "True" if sched.is_opted_out else "False"
                auto_sched = auto_calc.get(stage, (None, None))[1]
                row[cols["scheduled_date"]] = format_date_ui(auto_sched) if auto_sched else ""
            else:
                row[cols["opt_out"]] = "False"
                auto_sched = auto_calc.get(stage, (None, None))[1]
                row[cols["scheduled_date"]] = format_date_ui(auto_sched) if auto_sched else ""

        rows.append(row)

    if not rows:
        return generate_template_dataframe()
    return pd.DataFrame(rows)

def preview_uploaded_schedules(
    df: pd.DataFrame,
    conn: sqlite3.Connection
) -> List[Dict[str, Any]]:
    """Generate an interactive preview of each uploaded employee with their 6 calculated/specified email stage dates."""
    from naps_engine.date_engine import calculate_all_stage_dates, adjust_for_weekend
    preview_items = []

    for idx, row in df.iterrows():
        raw_id = str(row.get("trainee_id", "")).strip() if pd.notna(row.get("trainee_id")) else f"Row-{idx+2}"
        raw_name = str(row.get("trainee_name", "")).strip() if pd.notna(row.get("trainee_name")) else "Unnamed"
        raw_doj = row.get("date_of_joining")
        raw_lwd = row.get("last_working_date")
        raw_status = str(row.get("status", "Active")).strip() if pd.notna(row.get("status")) else "Active"

        parsed_doj = None
        try:
            parsed_doj = parse_optional_date(raw_doj)
        except Exception:
            pass

        parsed_lwd = None
        try:
            parsed_lwd = parse_optional_date(raw_lwd)
        except Exception:
            pass

        existing_trainee = get_trainee(conn, raw_id) if raw_id and not raw_id.startswith("Row-") else None
        effective_doj = parsed_doj or (existing_trainee.date_of_joining if existing_trainee else None)
        effective_lwd = parsed_lwd or (existing_trainee.last_working_date if existing_trainee else None)

        if effective_doj and not effective_lwd:
            effective_lwd = calculate_default_lwd(effective_doj)

        calculated_stages = {}
        if effective_doj and effective_lwd:
            calc_map = calculate_all_stage_dates(effective_doj, effective_lwd)

            for stage, cols in STAGE_COLUMN_MAP.items():
                orig_due, auto_sched = calc_map[stage]
                raw_stage_date = row.get(cols["scheduled_date"])
                parsed_stage_date = None
                try:
                    parsed_stage_date = parse_optional_date(raw_stage_date)
                except Exception:
                    pass

                raw_stage_opt = row.get(cols["opt_out"])
                parsed_stage_opt = False
                try:
                    opt_res = parse_bool_field(raw_stage_opt)
                    parsed_stage_opt = bool(opt_res) if opt_res is not None else False
                except Exception:
                    pass

                if parsed_stage_date:
                    sched_date = adjust_for_weekend(parsed_stage_date)
                    is_custom = True
                else:
                    sched_date = auto_sched
                    is_custom = False

                calculated_stages[stage] = {
                    "math_due_date": orig_due,
                    "scheduled_date": sched_date,
                    "is_custom": is_custom,
                    "is_opted_out": parsed_stage_opt,
                }

        preview_items.append({
            "row_number": idx + 2,
            "trainee_id": raw_id,
            "trainee_name": raw_name,
            "date_of_joining": effective_doj,
            "last_working_date": effective_lwd,
            "status": raw_status,
            "is_existing": existing_trainee is not None,
            "stages": calculated_stages
        })

    return preview_items

