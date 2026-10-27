"""Vercel Serverless Application Entry Point & REST API.

Provides:
- FastAPI application mounted for Vercel Serverless Functions (@vercel/python).
- Administrative authentication and secure session token management.
- Trainee directory, lifecycle reconciliation, and milestone schedule management.
- Batch Excel & CSV import validation, staging, row deletion, and export.
- Safe Email Dispatch Worker execution (strictly in SIMULATION mode).
- Protected Vercel Cron endpoint (/api/cron/dispatch) with secret verification.
- Audit trail, exception resolution, and system diagnostics.
- Serves the unified client web portal interface.
"""

import hmac
import hashlib
import io
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

# Ensure naps_engine can be imported from root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Header,
    UploadFile,
    File,
    Form,
    Query,
    Request,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import pandas as pd

from naps_engine import config
from naps_engine.audit import log_audit_event
from naps_engine.auth import verify_admin_credentials, DEFAULT_ADMIN_USERNAME
from naps_engine.config import APP_TIMEZONE, TIMEZONE_NAME
from naps_engine.date_engine import (
    add_calendar_months,
    adjust_for_weekend,
    calculate_default_lwd,
    validate_dates,
)
from naps_engine.db import (
    archive_trainee,
    delete_trainee,
    get_db_connection,
    get_db_type,
    get_schedule_by_id,
    get_schedules_for_trainee,
    get_trainee,
    init_db,
    list_trainees,
    row_to_schedule,
    row_to_trainee,
)
from naps_engine.excel_engine import (
    ExcelImporter,
    STAGE_COLUMN_MAP,
    export_trainees_dataframe,
    generate_template_dataframe,
    normalize_column_name,
    preview_uploaded_schedules,
)
from naps_engine.mailer import Mailer
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
    validate_state_transition,
)
from naps_engine.reconciliation import (
    create_trainee_with_schedules,
    update_stage_preferences_and_dates,
    update_trainee_and_reconcile,
)
from naps_engine.worker import DispatchWorker

# Initialize FastAPI App
app = FastAPI(
    title="NAPS Apprentice Lifecycle & Email Scheduling System",
    description="Production-grade HR Apprentice Management & Milestone Scheduling Web Application",
    version="2.0.0",
)

# Enable CORS for local testing and Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled exception handler to return structured JSON instead of plain-text 500."""
    import traceback
    traceback.print_exc()
    status_code = 500
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        detail = exc.detail
    else:
        detail = f"Internal server error: {str(exc)}"
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "type": type(exc).__name__},
    )

# ------------------------------------------------------------------------------
# AUTHENTICATION & SESSION MANAGEMENT
# ------------------------------------------------------------------------------

def _generate_session_token(username: str) -> str:
    """Generate a tamper-proof HMAC-SHA256 signed session token (24h validity)."""
    ts = int(time.time())
    secret = config.SESSION_SECRET.encode("utf-8")
    payload = f"{username}:{ts}".encode("utf-8")
    sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return f"{username}:{ts}:{sig}"


def _verify_session_token(token: Optional[str]) -> Optional[str]:
    """Verify HMAC signature and timestamp of session token."""
    if not token:
        return None
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        username, ts_str, sig = parts
        ts = int(ts_str)
        # Token valid for 24 hours (86400 seconds)
        if time.time() - ts > 86400 or time.time() < ts - 60:
            return None
        secret = config.SESSION_SECRET.encode("utf-8")
        payload = f"{username}:{ts}".encode("utf-8")
        expected_sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, expected_sig):
            return username
        return None
    except Exception:
        return None


def get_current_admin(authorization: Optional[str] = Header(None)) -> str:
    """Dependency that enforces administrator authentication on protected routes."""
    token = None
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()

    username = _verify_session_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in as administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


# ------------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# ------------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class TraineeCreateRequest(BaseModel):
    trainee_id: str
    trainee_name: str
    trainee_email: str
    date_of_joining: str
    manager_name: str
    manager_email: str
    department: str
    location: str
    status: Optional[str] = "Active"
    last_working_date: Optional[str] = None
    stage_preferences: Optional[Dict[str, Dict[str, Any]]] = None


class TraineeUpdateRequest(BaseModel):
    trainee_name: Optional[str] = None
    trainee_email: Optional[str] = None
    date_of_joining: Optional[str] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    last_working_date: Optional[str] = None
    confirmed_actual_lwd: Optional[str] = None


class ScheduleUpdateRequest(BaseModel):
    stages: Dict[str, Dict[str, Any]]  # { "q1": { "opt_out": bool, "scheduled_date": "DD/MM/YYYY" } }


class ExceptionResolveRequest(BaseModel):
    schedule_id: int
    action: str  # "MARK_SENT" or "RETRY"
    reason: str


class RunWorkerRequest(BaseModel):
    target_date: Optional[str] = None  # YYYY-MM-DD or DD/MM/YYYY


# ------------------------------------------------------------------------------
# DATABASE AUTO-INITIALIZATION HOOK
# ------------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """Ensure database schema is initialized on serverless function spin-up."""
    try:
        conn = get_db_connection()
        init_db(conn)
        conn.close()
    except Exception as e:
        print(f"[STARTUP ERROR] Database initialization failed: {e}")


# ------------------------------------------------------------------------------
# AUTHENTICATION ENDPOINTS
# ------------------------------------------------------------------------------

@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Authenticate administrator and return signed session token."""
    config.reload_config()
    is_valid = verify_admin_credentials(req.username.strip(), req.password.strip())
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials. Access denied.",
        )
    token = _generate_session_token(req.username.strip())
    return {
        "status": "success",
        "token": token,
        "username": req.username.strip(),
        "delivery_mode": "SIMULATION",
        "database_engine": get_db_type(),
        "timezone": TIMEZONE_NAME,
    }


@app.get("/api/auth/me")
def get_current_user_profile(user: str = Depends(get_current_admin)):
    """Return authenticated administrator profile and system diagnostics."""
    return {
        "authenticated": True,
        "username": user,
        "delivery_mode": "SIMULATION (Safe Mode - Live SMTP Disabled)",
        "is_simulation_mode": True,
        "database_engine": get_db_type(),
        "timezone": TIMEZONE_NAME,
        "current_time_ist": datetime.now(APP_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


@app.post("/api/auth/logout")
def logout():
    """Sign out administrator."""
    return {"status": "success", "message": "Signed out successfully."}


# ------------------------------------------------------------------------------
# DASHBOARD & METRICS ENDPOINTS
# ------------------------------------------------------------------------------

@app.get("/api/dashboard/stats")
def get_dashboard_stats(user: str = Depends(get_current_admin)):
    """Compute live dashboard KPIs from persistent database."""
    conn = get_db_connection()
    try:
        init_db(conn)
        trainees = list_trainees(conn)
        total_trainees = len(trainees)
        active_count = sum(1 for t in trainees if t.status == TraineeStatus.ACTIVE)
        completed_count = sum(1 for t in trainees if t.status == TraineeStatus.COMPLETED)
        on_roll_count = sum(1 for t in trainees if t.status == TraineeStatus.ON_ROLL)
        left_count = sum(1 for t in trainees if t.status == TraineeStatus.LEFT)

        # Email schedule status counts
        cur = conn.execute(
            """
            SELECT status, COUNT(*) as cnt
            FROM email_schedules
            GROUP BY status
            """
        )
        status_counts = {r["status"]: r["cnt"] for r in cur.fetchall()}

        simulated_sent_count = status_counts.get("Sent", 0)
        pending_queue_count = status_counts.get("Scheduled", 0) + status_counts.get("Retrying", 0)
        exceptions_count = status_counts.get("Uncertain", 0) + status_counts.get("Failed", 0)

        # Department breakdown
        dept_counts: Dict[str, int] = {}
        for t in trainees:
            dept = t.department or "Unassigned"
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        # Recent audit logs
        log_cur = conn.execute(
            "SELECT id, timestamp, actor, entity_type, entity_id, action, reason FROM audit_logs ORDER BY id DESC LIMIT 10"
        )
        recent_logs = [dict(r) for r in log_cur.fetchall()]

        # Exceptions list
        exc_cur = conn.execute(
            """
            SELECT s.id, s.trainee_id, t.trainee_name, s.stage, s.status, s.last_error
            FROM email_schedules s
            JOIN trainees t ON s.trainee_id = t.trainee_id
            WHERE s.status IN ('Uncertain', 'Failed')
            ORDER BY s.id DESC
            LIMIT 5
            """
        )
        exceptions = [dict(r) for r in exc_cur.fetchall()]

        return {
            "total_trainees": total_trainees,
            "active_count": active_count,
            "completed_count": completed_count,
            "on_roll_count": on_roll_count,
            "left_count": left_count,
            "simulated_sent_count": simulated_sent_count,
            "pending_queue_count": pending_queue_count,
            "exceptions_count": exceptions_count,
            "department_breakdown": dept_counts,
            "recent_activity": recent_logs,
            "exceptions": exceptions,
            "delivery_mode": "SIMULATION (Safe Mode - Live SMTP Disabled)",
            "is_simulation_mode": True,
            "database_engine": get_db_type(),
        }
    finally:
        conn.close()


@app.get("/api/dashboard/queue")
def get_dashboard_queue(user: str = Depends(get_current_admin)):
    """Retrieve upcoming and overdue email dispatch items."""
    conn = get_db_connection()
    try:
        today_kolkata = datetime.now(APP_TIMEZONE).date()
        cur = conn.execute(
            """
            SELECT s.id, s.trainee_id, t.trainee_name, s.stage, s.scheduled_date, s.status, s.attempt_count
            FROM email_schedules s
            JOIN trainees t ON s.trainee_id = t.trainee_id
            WHERE s.status IN ('Scheduled', 'Retrying')
              AND s.is_opted_out = 0
              AND t.is_archived = 0
            ORDER BY s.scheduled_date ASC, s.id ASC
            LIMIT 50
            """
        )
        queue_items = []
        for r in cur.fetchall():
            s_date = parse_date(r["scheduled_date"])
            due_status = "Due Today" if s_date == today_kolkata else ("Overdue" if s_date and s_date < today_kolkata else "Upcoming")
            queue_items.append({
                "queue_id": r["id"],
                "trainee_id": r["trainee_id"],
                "trainee_name": r["trainee_name"],
                "stage": r["stage"],
                "scheduled_date": format_date_ui(s_date),
                "scheduled_date_raw": r["scheduled_date"],
                "due_status": due_status,
                "status": r["status"],
                "attempt_count": r["attempt_count"],
            })
        return {"queue": queue_items, "today_ist": format_date_ui(today_kolkata)}
    finally:
        conn.close()


# ------------------------------------------------------------------------------
# WORKER DISPATCH & VERCEL CRON ENDPOINTS
# ------------------------------------------------------------------------------

@app.post("/api/worker/run")
def run_worker_cycle(req: RunWorkerRequest, user: str = Depends(get_current_admin)):
    """Manually trigger background dispatch cycle in SIMULATION mode."""
    conn = get_db_connection()
    try:
        init_db(conn)
        target_d = None
        if req.target_date:
            target_d = parse_date(req.target_date)

        # Mailer strictly initialized in simulation mode
        mailer = Mailer(dry_run=True)
        worker = DispatchWorker(conn=conn, worker_id=f"admin-{user}", mailer=mailer)
        summary = worker.run_worker_cycle(target_date=target_d)

        return {
            "status": "success",
            "message": "Dispatch cycle executed safely in SIMULATION mode.",
            "is_simulation_mode": True,
            "summary": summary,
            "target_date_evaluated": format_date_ui(target_d or datetime.now(APP_TIMEZONE).date()),
        }
    finally:
        conn.close()


@app.get("/api/cron/dispatch")
def cron_dispatch(
    authorization: Optional[str] = Header(None),
    x_vercel_cron: Optional[str] = Header(None),
    secret: Optional[str] = Query(None),
):
    """Protected Vercel Cron endpoint scheduled daily at 09:00:00 Asia/Kolkata.
    
    Processes due milestone schedules strictly in SIMULATION mode.
    Secured by CRON_SECRET or Vercel platform headers.
    """
    config.reload_config()
    is_authorized = False

    # Check 1: Authorization: Bearer <CRON_SECRET>
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if hmac.compare_digest(token, config.CRON_SECRET):
            is_authorized = True

    # Check 2: ?secret=<CRON_SECRET> query param
    if secret and hmac.compare_digest(secret, config.CRON_SECRET):
        is_authorized = True

    # Check 3: Vercel automated cron header (present when triggered by Vercel infrastructure)
    if x_vercel_cron:
        is_authorized = True

    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized cron invocation. Valid CRON_SECRET required.",
        )

    conn = get_db_connection()
    try:
        init_db(conn)
        now_ist = datetime.now(APP_TIMEZONE)
        today_date = now_ist.date()

        # Strict simulation mailer
        mailer = Mailer(dry_run=True)
        worker = DispatchWorker(conn=conn, worker_id="vercel-cron-daemon", mailer=mailer)
        summary = worker.run_worker_cycle(target_date=today_date)

        return {
            "status": "success",
            "mode": "SIMULATION",
            "timestamp": now_ist.isoformat(),
            "target_date": format_date_ui(today_date),
            "results": summary,
        }
    finally:
        conn.close()


# ------------------------------------------------------------------------------
# TRAINEE DIRECTORY & CRUD ENDPOINTS
# ------------------------------------------------------------------------------

@app.get("/api/trainees")
def list_all_trainees(
    status_filter: Optional[str] = Query(None),
    dept_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: str = Depends(get_current_admin),
):
    """List trainees with filter, search, and full 6-stage milestone timelines."""
    conn = get_db_connection()
    try:
        init_db(conn)
        trainees = list_trainees(conn)
        out = []
        for t in trainees:
            # Apply filters
            if status_filter and status_filter != "All" and t.status.value != status_filter:
                continue
            if dept_filter and dept_filter != "All" and t.department != dept_filter:
                continue
            if search:
                match_fields = [
                    t.trainee_id or "",
                    t.trainee_name or "",
                    t.trainee_email or "",
                    t.department or "",
                    t.location or "",
                    t.manager_name or "",
                    t.manager_email or "",
                ]
                if not any(q in f.lower() for f in match_fields):
                    continue

            # Load schedules
            scheds = get_schedules_for_trainee(conn, t.trainee_id)
            sched_map = {s.stage.value: s for s in scheds}

            stages_out = {}
            for stg in [EmailStage.INITIAL, EmailStage.Q1, EmailStage.Q2, EmailStage.Q3, EmailStage.Q4, EmailStage.EXIT]:
                s_obj = sched_map.get(stg.value)
                if s_obj:
                    stg_dict = {
                        "id": s_obj.id,
                        "scheduled_date": format_date_ui(s_obj.scheduled_date),
                        "scheduled_date_raw": format_date_db(s_obj.scheduled_date),
                        "status": s_obj.status.value,
                        "is_opted_out": s_obj.is_opted_out,
                        "is_custom_date": s_obj.is_custom_date,
                        "attempt_count": s_obj.attempt_count,
                        "last_error": s_obj.last_error,
                        "sent_at": s_obj.sent_at.isoformat() if s_obj.sent_at else None,
                    }
                    stages_out[stg.value] = stg_dict
                    stages_out[stg.value.lower()] = stg_dict

            out.append({
                "trainee_id": t.trainee_id,
                "trainee_name": t.trainee_name,
                "trainee_email": t.trainee_email,
                "date_of_joining": format_date_ui(t.date_of_joining),
                "date_of_joining_raw": format_date_db(t.date_of_joining),
                "manager_name": t.manager_name,
                "manager_email": t.manager_email,
                "department": t.department,
                "location": t.location,
                "status": t.status.value,
                "last_working_date": format_date_ui(t.last_working_date),
                "last_working_date_raw": format_date_db(t.last_working_date),
                "lwd_mode": t.lwd_mode.value,
                "stages": stages_out,
            })

        return {"count": len(out), "trainees": out}
    finally:
        conn.close()


@app.get("/api/trainees/{trainee_id}")
def get_single_trainee(trainee_id: str, user: str = Depends(get_current_admin)):
    """Retrieve detailed trainee record with full milestone schedule history."""
    conn = get_db_connection()
    try:
        t = get_trainee(conn, trainee_id)
        if not t:
            raise HTTPException(status_code=404, detail=f"Trainee '{trainee_id}' not found.")
        scheds = get_schedules_for_trainee(conn, trainee_id)

        # Delivery attempts history
        att_cur = conn.execute(
            """
            SELECT id, schedule_id, stage, attempt_number, attempt_at, recipient_email,
                   status_outcome, failure_category, error_details, worker_id
            FROM delivery_attempts
            WHERE trainee_id = ?
            ORDER BY id DESC
            """,
            (trainee_id,)
        )
        attempts = [dict(r) for r in att_cur.fetchall()]

        return {
            "trainee": {
                "trainee_id": t.trainee_id,
                "trainee_name": t.trainee_name,
                "trainee_email": t.trainee_email,
                "date_of_joining": format_date_ui(t.date_of_joining),
                "date_of_joining_raw": format_date_db(t.date_of_joining),
                "manager_name": t.manager_name,
                "manager_email": t.manager_email,
                "department": t.department,
                "location": t.location,
                "status": t.status.value,
                "last_working_date": format_date_ui(t.last_working_date),
                "last_working_date_raw": format_date_db(t.last_working_date),
                "lwd_mode": t.lwd_mode.value,
            },
            "schedules": [
                {
                    "id": s.id,
                    "stage": s.stage.value,
                    "scheduled_date": format_date_ui(s.scheduled_date),
                    "scheduled_date_raw": format_date_db(s.scheduled_date),
                    "status": s.status.value,
                    "is_opted_out": s.is_opted_out,
                    "is_custom_date": s.is_custom_date,
                    "attempt_count": s.attempt_count,
                    "last_error": s.last_error,
                    "sent_at": s.sent_at.isoformat() if s.sent_at else None,
                }
                for s in scheds
            ],
            "delivery_attempts": attempts,
        }
    finally:
        conn.close()


@app.post("/api/trainees")
def create_new_trainee(req: TraineeCreateRequest, user: str = Depends(get_current_admin)):
    """Register a new trainee with auto-calculated LWD and all 6 milestone schedules."""
    conn = get_db_connection()
    try:
        init_db(conn)
        # Check duplicate
        existing = get_trainee(conn, req.trainee_id.strip())
        if existing:
            raise HTTPException(status_code=400, detail=f"Trainee ID '{req.trainee_id}' already exists.")

        doj = parse_date(req.date_of_joining)
        if not doj:
            raise HTTPException(status_code=400, detail="Invalid Date of Joining format. Use DD/MM/YYYY or YYYY-MM-DD.")

        lwd = parse_date(req.last_working_date) if req.last_working_date else None
        lwd_mode = LwdMode.MANUAL if lwd else LwdMode.AUTO
        if not lwd:
            lwd = calculate_default_lwd(doj)

        status_val = TraineeStatus(req.status) if req.status in [s.value for s in TraineeStatus] else TraineeStatus.ACTIVE

        trainee = Trainee(
            trainee_id=req.trainee_id.strip(),
            trainee_name=req.trainee_name.strip(),
            trainee_email=req.trainee_email.strip(),
            date_of_joining=doj,
            manager_name=req.manager_name.strip(),
            manager_email=req.manager_email.strip(),
            department=req.department.strip(),
            location=req.location.strip(),
            status=status_val,
            last_working_date=lwd,
            lwd_mode=lwd_mode,
        )

        custom_dates = {}
        opt_outs = {}
        if req.stage_preferences:
            for stg_key, pref in req.stage_preferences.items():
                try:
                    stg_enum = EmailStage(str(stg_key).strip().upper())
                    if isinstance(pref, dict):
                        if pref.get("custom_date"):
                            c_date = parse_date(pref.get("custom_date"))
                            if c_date:
                                custom_dates[stg_enum] = c_date
                        if "opt_out" in pref:
                            opt_outs[stg_enum] = bool(pref.get("opt_out"))
                        elif "opted_out" in pref:
                            opt_outs[stg_enum] = bool(pref.get("opted_out"))
                    elif isinstance(pref, bool):
                        opt_outs[stg_enum] = pref
                except Exception as ex:
                    logger.warning(f"Error parsing stage preference for '{stg_key}': {ex}")

        t_obj, scheds = create_trainee_with_schedules(
            conn=conn,
            trainee=trainee,
            custom_dates=custom_dates if custom_dates else None,
            opt_out_preferences=opt_outs if opt_outs else None,
            actor=user,
        )

        return {
            "status": "success",
            "message": f"Trainee '{t_obj.trainee_id}' created with {len(scheds)} milestone schedules.",
            "trainee_id": t_obj.trainee_id,
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.put("/api/trainees/{trainee_id}")
def update_trainee_details(
    trainee_id: str,
    req: TraineeUpdateRequest,
    user: str = Depends(get_current_admin),
):
    """Update trainee fields, status transition, or Last Working Date."""
    conn = get_db_connection()
    try:
        t = get_trainee(conn, trainee_id)
        if not t:
            raise HTTPException(status_code=404, detail=f"Trainee '{trainee_id}' not found.")

        updates: Dict[str, Any] = {}
        if req.trainee_name:
            updates["trainee_name"] = req.trainee_name.strip()
        if req.trainee_email:
            updates["trainee_email"] = req.trainee_email.strip()
        if req.manager_name:
            updates["manager_name"] = req.manager_name.strip()
        if req.manager_email:
            updates["manager_email"] = req.manager_email.strip()
        if req.department:
            updates["department"] = req.department.strip()
        if req.location:
            updates["location"] = req.location.strip()
        if req.date_of_joining:
            doj = parse_date(req.date_of_joining)
            if doj:
                updates["date_of_joining"] = doj
        if req.status:
            updates["status"] = TraineeStatus(req.status)
        if req.last_working_date:
            lwd = parse_date(req.last_working_date)
            if lwd:
                updates["last_working_date"] = lwd
        if req.confirmed_actual_lwd:
            c_lwd = parse_date(req.confirmed_actual_lwd)
            if c_lwd:
                updates["confirmed_actual_lwd"] = c_lwd

        updated_t = update_trainee_and_reconcile(
            conn=conn,
            trainee_id=trainee_id,
            updates=updates,
            actor=user,
        )

        return {
            "status": "success",
            "message": f"Trainee '{trainee_id}' updated successfully.",
            "trainee": {
                "trainee_id": updated_t.trainee_id,
                "status": updated_t.status.value,
                "last_working_date": format_date_ui(updated_t.last_working_date),
            },
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.put("/api/trainees/{trainee_id}/schedules")
def update_trainee_schedules(
    trainee_id: str,
    req: ScheduleUpdateRequest,
    user: str = Depends(get_current_admin),
):
    """Update custom scheduled dates or toggle opt-out preferences across milestone stages."""
    conn = get_db_connection()
    try:
        stage_prefs: Dict[EmailStage, Optional[bool]] = {}
        stage_dates: Dict[EmailStage, Optional[date]] = {}
        for stg_str, data in req.stages.items():
            try:
                stg_enum = EmailStage(stg_str.upper())
                if "opt_out" in data:
                    stage_prefs[stg_enum] = bool(data["opt_out"])
                if "scheduled_date" in data and data["scheduled_date"]:
                    stage_dates[stg_enum] = parse_date(data["scheduled_date"])
            except Exception as ex:
                print(f"[STAGE PREF NOTICE] {stg_str}: {ex}")

        update_stage_preferences_and_dates(
            conn=conn,
            trainee_id=trainee_id,
            stage_preferences=stage_prefs,
            stage_custom_dates=stage_dates,
            actor=user,
            reason="Updated via administrator portal",
        )

        return {"status": "success", "message": f"Schedules updated for trainee '{trainee_id}'."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.delete("/api/trainees/{trainee_id}")
def delete_single_trainee(trainee_id: str, user: str = Depends(get_current_admin)):
    """Hard delete trainee. Strictly blocked if any Sent delivery history exists."""
    conn = get_db_connection()
    try:
        delete_trainee(conn, trainee_id=trainee_id, actor=user)
        return {"status": "success", "message": f"Trainee '{trainee_id}' deleted."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    finally:
        conn.close()


@app.post("/api/trainees/{trainee_id}/archive")
def archive_single_trainee(trainee_id: str, user: str = Depends(get_current_admin)):
    """Soft delete / archive trainee while preserving all schedules and delivery history."""
    conn = get_db_connection()
    try:
        archive_trainee(conn, trainee_id=trainee_id, actor=user, reason="Archived by administrator")
        return {"status": "success", "message": f"Trainee '{trainee_id}' archived."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# ------------------------------------------------------------------------------
# EXCEL / CSV BATCH IMPORT & EXPORT ENDPOINTS
# ------------------------------------------------------------------------------

@app.get("/api/templates/download")
def download_template(format: str = Query("xlsx")):
    """Download official 23-column import template in Excel (.xlsx) or CSV format."""
    df_tmpl = generate_template_dataframe()
    if format.lower() == "csv":
        buf = io.StringIO()
        df_tmpl.to_csv(buf, index=False)
        buf.seek(0)
        return StreamingResponse(
            io.BytesIO(buf.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=naps_trainee_import_template.csv"},
        )
    else:
        buf = io.BytesIO()
        df_tmpl.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=naps_trainee_import_template.xlsx"},
        )


@app.post("/api/import/preview")
async def preview_import_file(
    file: UploadFile = File(...),
    user: str = Depends(get_current_admin),
):
    """Upload and validate Excel/CSV file.
    
    Returns:
    - Staged valid rows with calculated milestone dates.
    - Isolated error rows with field-level reason breakdown.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        filename = (file.filename or "").lower()
        if not (filename.endswith(".xlsx") or filename.endswith(".xls") or filename.endswith(".csv")):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload an Excel (.xlsx, .xls) or CSV file.",
            )

        conn = get_db_connection()
        try:
            importer = ExcelImporter(conn=conn, actor=user)
            df_norm = importer.parse_file(io.BytesIO(content))

            if df_norm.empty:
                raise HTTPException(status_code=400, detail="The uploaded sheet contains no data rows.")

            preview_items = preview_uploaded_schedules(df_norm, conn)

            staged_items = []
            error_items = []

            for idx, item in enumerate(preview_items):
                orig_row = df_norm.iloc[idx].to_dict()
                row_num = item.get("row_number", idx + 2)
                trainee_id = str(item.get("trainee_id", "")).strip()
                trainee_name = str(item.get("trainee_name", "")).strip()

                # Row-level validation
                row_errors = []
                if not trainee_id or trainee_id.startswith("Row-"):
                    row_errors.append({"field": "trainee_id", "reason": "Trainee ID is required."})
                if not trainee_name or trainee_name == "Unnamed":
                    row_errors.append({"field": "trainee_name", "reason": "Trainee Name is required."})
                if not item.get("date_of_joining"):
                    row_errors.append({"field": "date_of_joining", "reason": "Valid Date of Joining is required (DD/MM/YYYY or YYYY-MM-DD)."})

                if row_errors:
                    error_items.append({
                        "row_number": row_num,
                        "trainee_id": trainee_id or f"Row {row_num}",
                        "trainee_name": trainee_name or "Unnamed",
                        "errors": row_errors,
                    })
                    continue

                stages_dict = {}
                for stg, s_data in item.get("stages", {}).items():
                    stg_key = stg.value if hasattr(stg, "value") else str(stg)
                    stages_dict[stg_key] = {
                        "date": format_date_ui(s_data.get("scheduled_date")),
                        "opt_out": s_data.get("is_opted_out", False),
                        "is_custom": s_data.get("is_custom", False),
                    }

                # Ensure all 6 stage keys always exist
                for stage_code in ["initial", "q1", "q2", "q3", "q4", "exit"]:
                    if stage_code not in stages_dict:
                        stages_dict[stage_code] = {"date": "-", "opt_out": False, "is_custom": False}

                staged_items.append({
                    "trainee_id": item["trainee_id"],
                    "trainee_name": item["trainee_name"],
                    "trainee_email": str(orig_row.get("trainee_email") or ""),
                    "date_of_joining": format_date_ui(item.get("date_of_joining")),
                    "date_of_joining_raw": format_date_db(item.get("date_of_joining")),
                    "manager_name": str(orig_row.get("manager_name") or ""),
                    "manager_email": str(orig_row.get("manager_email") or ""),
                    "department": str(orig_row.get("department") or ""),
                    "location": str(orig_row.get("location") or ""),
                    "status": item.get("status", "Active"),
                    "last_working_date": format_date_ui(item.get("last_working_date")) if item.get("last_working_date") else "-",
                    "is_existing": item.get("is_existing", False),
                    "stages": stages_dict,
                    "raw_row": {k: (str(v) if pd.notna(v) else "") for k, v in orig_row.items()}
                })

            return {
                "total_rows": len(df_norm),
                "valid_count": len(staged_items),
                "error_count": len(error_items),
                "staged_rows": staged_items,
                "error_rows": error_items,
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parsing error: {str(e)}")


class CommitImportRequest(BaseModel):
    trainee_ids_to_commit: List[str]
    staged_rows: List[Dict[str, Any]]


@app.post("/api/import/commit")
def commit_import_rows(
    req: CommitImportRequest,
    user: str = Depends(get_current_admin),
):
    """Commit verified staged rows to database idempotently.
    
    Rows deleted by user from staging are excluded.
    """
    conn = get_db_connection()
    try:
        init_db(conn)
        allowed_ids = set(req.trainee_ids_to_commit)
        rows_to_process = [r for r in req.staged_rows if r.get("trainee_id") in allowed_ids]

        if not rows_to_process:
            raise HTTPException(status_code=400, detail="No rows selected for commit.")

        importer = ExcelImporter(conn=conn, actor=user)
        commit_dicts = []
        for r in rows_to_process:
            raw = r.get("raw_row")
            raw_dict = dict(raw) if (raw and isinstance(raw, dict)) else {}
            # Pre-normalize raw column names to prevent duplicate columns in DataFrame
            commit_row = {}
            for k, v in raw_dict.items():
                norm_k = normalize_column_name(k)
                commit_row[norm_k] = str(v).strip() if (v is not None and pd.notna(v)) else ""

            # Overlay core profile attributes from staged row
            for fld in ["trainee_id", "trainee_name", "trainee_email", "manager_name", "manager_email", "department", "location", "status"]:
                if r.get(fld):
                    commit_row[fld] = str(r[fld]).strip()

            # Overlay edited tenure dates
            if r.get("date_of_joining") and r.get("date_of_joining") != "-":
                commit_row["date_of_joining"] = str(r["date_of_joining"]).strip()
            if r.get("last_working_date") and r.get("last_working_date") != "-":
                commit_row["last_working_date"] = str(r["last_working_date"]).strip()

            # Overlay edited milestone stage dates and opt-out preferences
            stages_map = r.get("stages", {})
            for stage_enum, col_names in STAGE_COLUMN_MAP.items():
                stg_key = stage_enum.value if hasattr(stage_enum, "value") else str(stage_enum)
                stg_val = stages_map.get(stg_key) or stages_map.get(stg_key.lower()) or stages_map.get(stg_key.upper())
                if stg_val and isinstance(stg_val, dict):
                    d_str = stg_val.get("date")
                    norm_date_col = normalize_column_name(col_names["scheduled_date"])
                    norm_opt_col = normalize_column_name(col_names["opt_out"])
                    if d_str and d_str != "-":
                        commit_row[norm_date_col] = str(d_str).strip()
                    opt_val = stg_val.get("opt_out") if "opt_out" in stg_val else stg_val.get("opted_out")
                    if opt_val is not None:
                        commit_row[norm_opt_col] = "True" if bool(opt_val) else "False"

            commit_dicts.append(commit_row)

        df_commit = pd.DataFrame(commit_dicts)
        summary = importer.import_trainees(df_commit)

        created_val = getattr(summary, "created_count", getattr(summary, "created", 0))
        updated_val = getattr(summary, "updated_count", getattr(summary, "updated", 0))
        unchanged_val = getattr(summary, "unchanged_count", getattr(summary, "unchanged", 0))
        failed_val = getattr(summary, "failed_count", getattr(summary, "failed", 0))

        return {
            "status": "success",
            "message": f"Successfully processed: {created_val} created, {updated_val} updated, {unchanged_val} unchanged, {failed_val} failed.",
            "details": {
                "created": created_val,
                "updated": updated_val,
                "unchanged": unchanged_val,
                "failed": failed_val,
            },
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/api/export/directory")
def export_directory(format: str = Query("csv"), user: str = Depends(get_current_admin)):
    """Export current apprentice roster with milestone schedules."""
    conn = get_db_connection()
    try:
        df = export_trainees_dataframe(conn)
        if format.lower() == "xlsx":
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine="openpyxl")
            buf.seek(0)
            return StreamingResponse(
                buf,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=naps_trainee_roster.xlsx"},
            )
        else:
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            buf.seek(0)
            return StreamingResponse(
                io.BytesIO(buf.getvalue().encode("utf-8")),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=naps_trainee_roster.csv"},
            )
    finally:
        conn.close()


# ------------------------------------------------------------------------------
# EXCEPTIONS & AUDIT LOGS ENDPOINTS
# ------------------------------------------------------------------------------

@app.get("/api/exceptions")
def get_exceptions(user: str = Depends(get_current_admin)):
    """Retrieve all schedules in Uncertain or Failed status with attempt logs."""
    conn = get_db_connection()
    try:
        cur = conn.execute(
            """
            SELECT s.id, s.trainee_id, t.trainee_name, s.stage, s.status, s.scheduled_date,
                   s.attempt_count, s.last_attempt_at, s.last_error
            FROM email_schedules s
            JOIN trainees t ON s.trainee_id = t.trainee_id
            WHERE s.status IN ('Uncertain', 'Failed')
            ORDER BY s.id DESC
            """
        )
        exceptions = [dict(r) for r in cur.fetchall()]
        return {"exceptions": exceptions}
    finally:
        conn.close()


@app.post("/api/exceptions/resolve")
def resolve_exception(req: ExceptionResolveRequest, user: str = Depends(get_current_admin)):
    """Administratively resolve an Uncertain or Failed dispatch with audit reason."""
    conn = get_db_connection()
    try:
        sched = get_schedule_by_id(conn, req.schedule_id)
        if not sched:
            raise HTTPException(status_code=404, detail="Schedule not found.")

        now_iso = datetime.now(APP_TIMEZONE).isoformat()
        if req.action == "MARK_SENT":
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                UPDATE email_schedules SET
                    status = 'Sent',
                    sent_at = ?,
                    delivery_phase = 'completed',
                    lease_expires_at = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (now_iso, now_iso, req.schedule_id)
            )
            log_audit_event(
                conn,
                entity_type="schedule",
                entity_id=str(req.schedule_id),
                action="MANUAL_RESOLVE_MARK_SENT",
                actor=user,
                reason=req.reason,
            )
            conn.execute("COMMIT")
        elif req.action == "RETRY":
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                UPDATE email_schedules SET
                    status = 'Scheduled',
                    delivery_phase = NULL,
                    lease_expires_at = NULL,
                    updated_at = ?
                WHERE id = ?
                """,
                (now_iso, req.schedule_id)
            )
            log_audit_event(
                conn,
                entity_type="schedule",
                entity_id=str(req.schedule_id),
                action="MANUAL_RESOLVE_RETRY",
                actor=user,
                reason=req.reason,
            )
            conn.execute("COMMIT")
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use MARK_SENT or RETRY.")

        return {"status": "success", "message": f"Schedule #{req.schedule_id} resolved as {req.action}."}
    finally:
        conn.close()


@app.get("/api/audit-logs")
def get_audit_logs(user: str = Depends(get_current_admin)):
    """Retrieve full append-only system audit trail."""
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT id, timestamp, actor, entity_type, entity_id, action, old_values, new_values, reason FROM audit_logs ORDER BY id DESC LIMIT 100"
        )
        logs = [dict(r) for r in cur.fetchall()]
        return {"logs": logs}
    finally:
        conn.close()


@app.post("/api/database/prune")
def prune_database(user: str = Depends(get_current_admin)):
    """Safely prune un-sent apprentice records while strictly protecting Sent history."""
    conn = get_db_connection()
    try:
        cur = conn.execute("SELECT trainee_id FROM trainees WHERE is_archived = 0")
        all_ids = [r["trainee_id"] for r in cur.fetchall()]
        deleted = 0
        preserved = 0
        for tid in all_ids:
            scheds = get_schedules_for_trainee(conn, tid)
            has_sent = any(s.status == ScheduleStatus.SENT for s in scheds)
            if has_sent:
                preserved += 1
            else:
                delete_trainee(conn, tid, actor=user)
                deleted += 1

        return {
            "status": "success",
            "message": f"Pruned {deleted} trainee(s). Preserved {preserved} trainee(s) with Sent history.",
        }
    finally:
        conn.close()


# ------------------------------------------------------------------------------
# CLIENT WEB PORTAL UI (EMBEDDED CLIENT APPLICATION)
# ------------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
@app.get("/{full_path:path}", response_class=HTMLResponse)
def serve_client_web_app(request: Request, full_path: str = ""):
    """Serve the complete client web portal application."""
    # If API route not found, return 404 JSON instead of HTML
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found.")

    from api.ui_html import get_client_ui_html
    return HTMLResponse(content=get_client_ui_html())
