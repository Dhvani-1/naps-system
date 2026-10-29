"""NAPS Apprenticeship Management System - Enterprise HR Frontend.

Automated date calculation, email scheduling, and trainee lifecycle management.
Backend integration: Deterministic date engine, SQLite WAL store, background worker,
audit trail, and idempotent Excel/CSV import/export.
"""

from datetime import date, datetime, timedelta
import importlib
import io
import json
import sqlite3
import sys
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st

# Invalidate and reload cached naps_engine modules in long-running Streamlit processes
for mod_name in ["naps_engine.config", "naps_engine.mailer", "naps_engine.worker", "naps_engine.excel_engine"]:
    if mod_name in sys.modules:
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception:
            pass

from naps_engine import config as naps_config
naps_config.reload_config()

from naps_engine.audit import log_audit_event
from naps_engine.auth import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    Permission,
    UserRole,
    enforce_permission,
    has_permission,
    verify_admin_credentials,
)
from naps_engine.config import (
    APP_TIMEZONE,
    DEFAULT_DB_PATH,
    DEFAULT_FROM_EMAIL,
    EMAIL_DRY_RUN,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)
from naps_engine.date_engine import (
    add_calendar_months,
    adjust_for_weekend,
    calculate_all_stage_dates,
    calculate_default_lwd,
    validate_dates,
)
from naps_engine.db import (
    archive_trainee,
    delete_trainee,
    get_db_connection,
    get_schedule_by_id,
    get_schedules_for_trainee,
    get_trainee,
    init_db,
    list_trainees,
)

try:
    from naps_engine.excel_engine import (
        ExcelImporter,
        STAGE_COLUMN_MAP,
        export_trainees_dataframe,
        generate_template_dataframe,
        preview_uploaded_schedules,
    )
except (ImportError, AttributeError):
    if "naps_engine.excel_engine" in sys.modules:
        del sys.modules["naps_engine.excel_engine"]
    import naps_engine.excel_engine
    importlib.reload(naps_engine.excel_engine)
    try:
        from naps_engine.excel_engine import (
            ExcelImporter,
            STAGE_COLUMN_MAP,
            export_trainees_dataframe,
            generate_template_dataframe,
            preview_uploaded_schedules,
        )
    except (ImportError, AttributeError):
        from naps_engine.excel_engine import (
            ExcelImporter,
            STAGE_COLUMN_MAP,
            export_trainees_dataframe,
            generate_template_dataframe,
            parse_optional_date,
            parse_bool_field,
        )

        def preview_uploaded_schedules(df: pd.DataFrame, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
            """Fallback preview generator guaranteeing seamless operation in cached Streamlit sessions."""
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

from naps_engine.mailer import DeliveryResultStatus, Mailer
from naps_engine.models import (
    EmailSchedule,
    EmailStage,
    LwdMode,
    ScheduleStatus,
    STAGE_LABELS,
    STAGE_RECIPIENT_ROLES,
    Trainee,
    TraineeStatus,
    format_date_db,
    format_date_ui,
    parse_date,
    validate_email_syntax,
)
from naps_engine.reconciliation import (
    create_trainee_with_schedules,
    reenable_cancelled_stage,
    resolve_uncertain_schedule,
    set_stage_preference,
    update_schedule_custom_date,
    update_stage_preferences_and_dates,
    update_trainee_and_reconcile,
)
from naps_engine.worker import DispatchWorker

# -------------------------------------------------------------
# PAGE CONFIGURATION & THEME STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="NAPS Apprenticeship Management System",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* High-contrast Enterprise Base Typography */
    html, body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Enterprise Headers */
    .app-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.025em;
        margin-bottom: 0.2rem;
    }

    .app-subtitle {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.25rem;
        line-height: 1.5;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.015em;
        margin-top: 0.75rem;
        margin-bottom: 0.25rem;
    }

    .section-caption {
        font-size: 0.875rem;
        color: #64748B;
        margin-bottom: 1rem;
    }

    /* Card Panels */
    .metric-panel {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }

    .metric-panel-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }

    .metric-panel-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
    }

    .metric-panel-detail {
        font-size: 0.8rem;
        color: #475569;
        margin-top: 0.35rem;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border: 1px solid transparent;
    }

    .badge-active { background-color: #ECFDF5; color: #065F46; border-color: #A7F3D0; }
    .badge-left { background-color: #FFF1F2; color: #9F1239; border-color: #FECDD3; }
    .badge-completed { background-color: #EFF6FF; color: #1E40AF; border-color: #BFDBFE; }
    .badge-onroll { background-color: #F5F3FF; color: #5B21B6; border-color: #DDD6FE; }

    .badge-sent { background-color: #ECFDF5; color: #065F46; border-color: #A7F3D0; }
    .badge-scheduled { background-color: #F1F5F9; color: #334155; border-color: #CBD5E1; }
    .badge-processing { background-color: #FEF3C7; color: #92400E; border-color: #FDE68A; }
    .badge-cancelled { background-color: #F8FAFC; color: #64748B; border-color: #E2E8F0; }
    .badge-failed { background-color: #FFF1F2; color: #9F1239; border-color: #FECDD3; }
    .badge-retrying { background-color: #FFF7ED; color: #C2410C; border-color: #FFEDD5; }
    .badge-uncertain { background-color: #FEF3C7; color: #B45309; border-color: #FDE68A; }
    .badge-admin { background-color: #0F172A; color: #FFFFFF; border-color: #0F172A; font-weight: 700; letter-spacing: 0.06em; }

    /* Enterprise Administrator Login Page */
    .login-container-box {
        margin-top: 1.5rem;
        margin-bottom: 2rem;
    }

    .login-brand-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .login-brand-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem;
    }

    .login-brand-sub {
        font-size: 0.95rem;
        color: #64748B;
        line-height: 1.5;
    }

    .login-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 2.25rem 2.25rem 1.5rem 2.25rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03);
        margin-bottom: 1.25rem;
    }

    .login-card-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin-bottom: 0.35rem;
    }

    .login-card-desc {
        font-size: 0.875rem;
        color: #64748B;
        margin-bottom: 1.5rem;
        line-height: 1.45;
    }

    .login-security-notice {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        margin-top: 1.5rem;
        font-size: 0.825rem;
        color: #475569;
        line-height: 1.5;
    }

    /* Clean Enterprise Buttons */
    .stButton button[kind="primary"] {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.5rem 1.25rem !important;
        transition: background-color 0.15s ease-in-out;
    }

    .stButton button[kind="primary"]:hover {
        background-color: #1E293B !important;
        border-color: #1E293B !important;
    }

    .stButton button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }

    .stButton button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
    }

    /* Sidebar Clean Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }

    .sidebar-brand-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
    }

    .sidebar-brand-sub {
        font-size: 0.775rem;
        color: #64748B;
        margin-bottom: 1.25rem;
    }

    .sidebar-section-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    /* Tab Label Styling */
    button[data-baseweb="tab"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: #475569 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0F172A !important;
        font-weight: 600 !important;
        border-bottom-color: #0F172A !important;
    }

    /* Table Container */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# DATABASE & SESSION STATE
# -------------------------------------------------------------
conn = get_db_connection(DEFAULT_DB_PATH)
init_db(conn)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_role" not in st.session_state:
    st.session_state.current_role = UserRole.ADMIN if st.session_state.authenticated else None
if "current_user" not in st.session_state:
    st.session_state.current_user = "admin@company.com" if st.session_state.authenticated else None

today_kolkata = datetime.now(APP_TIMEZONE).date()

# -------------------------------------------------------------
# AUTHENTICATION GATEWAY (ADMINISTRATOR LOGIN REQUIRED)
# -------------------------------------------------------------
if not st.session_state.get("authenticated", False):
    with st.sidebar:
        st.markdown('<div class="sidebar-brand-title">NAPS Enterprise</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-brand-sub">Apprenticeship Lifecycle & Scheduling</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown('<div class="sidebar-section-label">Access Control</div>', unsafe_allow_html=True)
        st.info("System access restricted to authorized administrators. Please sign in to proceed.")
        st.divider()
        st.write(f"**System Timezone:** `Asia/Kolkata`")
        st.write(f"**System Date (IST):** `{format_date_ui(today_kolkata)}`")

    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.markdown(
            """
            <div class="login-container-box">
                <div class="login-brand-header">
                    <div class="login-brand-title">NAPS Enterprise Portal</div>
                    <div class="login-brand-sub">Apprenticeship Email Scheduling, Date Calculation & Lifecycle Engine</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="login-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="badge badge-admin">ADMINISTRATOR ONLY</span>
                    <span style="font-size: 0.775rem; color: #64748B; font-weight: 500;">Protected Access</span>
                </div>
                <div class="login-card-title">Administrator Sign In</div>
                <div class="login-card-desc">Enter your administrator credentials to access trainee management, milestone timelines, and email dispatch queues.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("admin_login_form"):
            login_username = st.text_input(
                "Administrator Username or Email",
                placeholder="e.g. admin or admin@company.com",
                key="input_login_username"
            )
            login_password = st.text_input(
                "Administrator Password",
                type="password",
                placeholder="Enter administrator password",
                key="input_login_password"
            )
            st.write("")
            submit_login = st.form_submit_button("Sign In as Administrator", type="primary", use_container_width=True)

            if submit_login:
                if not login_username.strip() or not login_password:
                    st.error("Please enter both username and password.")
                elif verify_admin_credentials(login_username, login_password):
                    st.session_state.authenticated = True
                    st.session_state.current_role = UserRole.ADMIN
                    st.session_state.current_user = "admin@company.com"
                    log_audit_event(
                        conn,
                        entity_type="auth",
                        entity_id="admin",
                        action="LOGIN_SUCCESS",
                        actor="admin@company.com",
                        reason="Administrator signed in successfully"
                    )
                    st.success("Authentication successful! Loading system...")
                    st.rerun()
                else:
                    log_audit_event(
                        conn,
                        entity_type="auth",
                        entity_id=login_username.strip() or "anonymous",
                        action="LOGIN_FAILED",
                        actor=login_username.strip() or "anonymous",
                        reason="Failed administrator sign-in attempt"
                    )
                    st.error("Access denied: Invalid administrator username or password.")

        st.markdown(
            """
            <div class="login-security-notice">
                <div style="font-weight: 600; color: #0F172A; margin-bottom: 0.25rem;">Administrator Credentials:</div>
                <div>Username: <code>admin</code> (or <code>admin@company.com</code>) &bull; Password: <code>Admin@123</code></div>
                <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.35rem;">
                    Configurable via <code>NAPS_ADMIN_USERNAME</code> and <code>NAPS_ADMIN_PASSWORD</code> environment variables.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()

# -------------------------------------------------------------
# SIDEBAR NAVIGATION & SYSTEM CONTEXT (AUTHENTICATED)
# -------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-brand-title">NAPS Enterprise</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-brand-sub">Apprenticeship Lifecycle & Scheduling</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)
    menu = st.radio(
        "Navigation Menu",
        [
            "Dashboard",
            "Trainee Directory",
            "Add Trainee",
            "Worker & Dispatch",
            "Excel / CSV Import",
            "Audit & Exceptions",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown('<div class="sidebar-section-label">Authenticated Session</div>', unsafe_allow_html=True)
    st.markdown('<span class="badge badge-admin">ADMINISTRATOR</span>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: 0.85rem; color: #0F172A; font-weight: 600; margin-top: 0.4rem; margin-bottom: 0.2rem;">{st.session_state.current_user}</div>', unsafe_allow_html=True)
    st.caption("Full Administrative Authorization")
    st.write("")
    if st.button("Log Out", type="secondary", use_container_width=True, key="btn_logout"):
        log_audit_event(
            conn,
            entity_type="auth",
            entity_id="admin",
            action="LOGOUT",
            actor=st.session_state.current_user,
            reason="Administrator logged out"
        )
        st.session_state.authenticated = False
        st.session_state.current_role = None
        st.session_state.current_user = None
        st.rerun()

    st.divider()

    st.markdown('<div class="sidebar-section-label">System Environment</div>', unsafe_allow_html=True)
    st.write(f"**Delivery Mode:** `{'Simulation (Dry-Run)' if naps_config.EMAIL_DRY_RUN else 'Live SMTP Dispatch'}`")
    st.write(f"**Timezone:** `Asia/Kolkata`")
    st.write(f"**System Date (IST):** `{format_date_ui(today_kolkata)}`")


# -------------------------------------------------------------
# APPLICATION HEADER
# -------------------------------------------------------------
st.markdown('<div class="app-title">NAPS Trainee Email & Lifecycle Engine</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Automated milestone calculation, weekend adjustment, opt-out enforcement, and immutable delivery safeguards.</div>',
    unsafe_allow_html=True,
)

# =============================================================
# VIEW 1: OPERATIONS DASHBOARD
# =============================================================
if menu == "Dashboard":
    all_trainees = list_trainees(conn, include_archived=False)
    active_count = sum(1 for t in all_trainees if t.status == TraineeStatus.ACTIVE)
    left_count = sum(1 for t in all_trainees if t.status == TraineeStatus.LEFT)
    completed_count = sum(1 for t in all_trainees if t.status == TraineeStatus.COMPLETED)
    on_roll_count = sum(1 for t in all_trainees if t.status == TraineeStatus.ON_ROLL)

    # Schedules KPI
    sched_summary = conn.execute(
        """
        SELECT
            SUM(CASE WHEN status IN ('Scheduled', 'Processing', 'Retrying') THEN 1 ELSE 0 END) AS pending_cnt,
            SUM(CASE WHEN status = 'Sent' THEN 1 ELSE 0 END) AS sent_cnt,
            SUM(CASE WHEN status IN ('Uncertain', 'Failed') THEN 1 ELSE 0 END) AS exc_cnt,
            SUM(CASE WHEN status IN ('Scheduled', 'Processing', 'Retrying') AND scheduled_date <= ? THEN 1 ELSE 0 END) AS overdue_cnt
        FROM email_schedules
        """,
        (format_date_db(today_kolkata),)
    ).fetchone()

    pending_cnt = sched_summary["pending_cnt"] or 0
    sent_cnt = sched_summary["sent_cnt"] or 0
    exc_cnt = sched_summary["exc_cnt"] or 0
    overdue_cnt = sched_summary["overdue_cnt"] or 0

    # 4 Top KPI Cards
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.markdown(
            f"""
            <div class="metric-panel">
                <div class="metric-panel-label">Total Trainees</div>
                <div class="metric-panel-value">{len(all_trainees)}</div>
                <div class="metric-panel-detail">{active_count} Active &bull; {left_count} Left &bull; {completed_count} Completed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_k2:
        overdue_note = f"<span style='color: #B91C1C; font-weight: 600;'>{overdue_cnt} Due/Overdue</span>" if overdue_cnt > 0 else "All queues on schedule"
        st.markdown(
            f"""
            <div class="metric-panel">
                <div class="metric-panel-label">Pending Schedules</div>
                <div class="metric-panel-value">{pending_cnt}</div>
                <div class="metric-panel-detail">{overdue_note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_k3:
        st.markdown(
            f"""
            <div class="metric-panel">
                <div class="metric-panel-label">Delivered Milestones</div>
                <div class="metric-panel-value">{sent_cnt}</div>
                <div class="metric-panel-detail">Immutable audit-recorded deliveries</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_k4:
        exc_color = "#991B1B" if exc_cnt > 0 else "#065F46"
        st.markdown(
            f"""
            <div class="metric-panel">
                <div class="metric-panel-label">Delivery Exceptions</div>
                <div class="metric-panel-value" style="color: {exc_color};">{exc_cnt}</div>
                <div class="metric-panel-detail">{'Attention required' if exc_cnt > 0 else 'All channels healthy'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Queue Operations & Dispatch Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Monitor upcoming milestones, execute dispatch batches, and review exceptions.</div>', unsafe_allow_html=True)

    dash_col_left, dash_col_right = st.columns([5, 4])

    with dash_col_left:
        st.markdown("**Upcoming & Due Email Schedules**")
        due_cursor = conn.execute(
            """
            SELECT s.id, s.trainee_id, t.trainee_name, s.stage, s.scheduled_date, s.status, s.attempt_count
            FROM email_schedules s
            JOIN trainees t ON s.trainee_id = t.trainee_id
            WHERE s.status IN ('Scheduled', 'Retrying', 'Processing')
            ORDER BY s.scheduled_date ASC
            LIMIT 15
            """
        )
        due_rows = due_cursor.fetchall()
        if due_rows:
            dash_queue_rows = []
            for r in due_rows:
                s_date = parse_date(r["scheduled_date"])
                is_due_now = s_date <= today_kolkata
                due_status = "Due Today / Overdue" if is_due_now else f"Scheduled (In {(s_date - today_kolkata).days}d)"
                dash_queue_rows.append({
                    "Queue ID": r["id"],
                    "Trainee ID": r["trainee_id"],
                    "Employee Name": r["trainee_name"],
                    "Stage": STAGE_LABELS.get(EmailStage(r["stage"]), r["stage"]),
                    "Scheduled Date": format_date_ui(s_date),
                    "Dispatch Eligibility": due_status,
                    "Status": r["status"],
                })
            st.dataframe(pd.DataFrame(dash_queue_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No pending schedules currently in queue.")

        # Quick Dispatch Action
        with st.expander("Execute Background Worker Dispatch Cycle"):
            st.caption("Processes all schedules whose scheduled_date <= Target Evaluation Date.")
            c_d1, c_d2 = st.columns([2, 1])
            with c_d1:
                dash_worker_date = st.date_input("Target Evaluation Date", value=today_kolkata, key="dash_worker_date")
            with c_d2:
                st.write("")
                st.write("")
                run_dash_worker = st.button("Run Dispatch Now", type="primary", key="btn_run_dash_worker")
            if run_dash_worker:
                worker = DispatchWorker(conn=conn, worker_id=f"dash-{st.session_state.current_user}")
                with st.spinner("Dispatching eligible schedules..."):
                    res = worker.run_worker_cycle(target_date=dash_worker_date)
                    st.success(f"Cycle completed: {res.get('sent', 0)} sent, {res.get('claimed', res.get('due', 0))} processed, {res.get('failed', 0)} failed.")
                    st.rerun()

    with dash_col_right:
        st.markdown("**Exceptions Requiring Attention**")
        exc_rows = conn.execute(
            """
            SELECT s.id, s.trainee_id, t.trainee_name, s.stage, s.status, s.last_error
            FROM email_schedules s
            JOIN trainees t ON s.trainee_id = t.trainee_id
            WHERE s.status IN ('Uncertain', 'Failed')
            ORDER BY s.id DESC
            LIMIT 5
            """
        ).fetchall()

        if exc_rows:
            for ex in exc_rows:
                st.error(f"Schedule #{ex['id']} &bull; Trainee {ex['trainee_id']} ({ex['trainee_name']}) &bull; {ex['stage']}: {ex['status']}")
                st.caption(f"Error Details: {ex['last_error']}")
        else:
            st.success("No delivery exceptions currently requiring attention.")

        st.markdown("---")
        st.markdown("**Recent System Activity Feed**")
        recent_logs = conn.execute("SELECT timestamp, actor, entity_type, entity_id, action, reason FROM audit_logs ORDER BY id DESC LIMIT 5").fetchall()
        if recent_logs:
            for l in recent_logs:
                st.caption(f"**{l['timestamp']}** &bull; `{l['action']}` on {l['entity_type']} ({l['entity_id']}) by {l['actor']}")
                if l["reason"]:
                    st.write(f"&nbsp;&nbsp;*Reason: {l['reason']}*")
        else:
            st.caption("No audit activity logged yet.")

# =============================================================
# VIEW 2: TRAINEE DIRECTORY & DETAILS
# =============================================================
elif menu == "Trainee Directory":
    trainees = list_trainees(conn, include_archived=False)

    col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
    with col_s1:
        search_query = st.text_input("Search Trainees", placeholder="Filter by Trainee ID, Name, Department, or Email...")
    with col_s2:
        status_filter = st.selectbox("Status Filter", ["All", "Active", "Left", "Completed", "On Roll"])
    with col_s3:
        all_depts = sorted(list({t.department for t in trainees if t.department}))
        dept_filter = st.selectbox("Department Filter", ["All"] + all_depts)

    filtered_trainees = []
    for t in trainees:
        if status_filter != "All" and t.status.value != status_filter:
            continue
        if dept_filter != "All" and t.department != dept_filter:
            continue
        if search_query:
            q = search_query.lower()
            if not (q in t.trainee_id.lower() or q in t.trainee_name.lower() or q in t.department.lower() or q in t.trainee_email.lower()):
                continue
        filtered_trainees.append(t)

    st.caption(f"Showing {len(filtered_trainees)} of {len(trainees)} registered apprentices.")

    if not filtered_trainees:
        st.warning("No trainees found matching current criteria.")
    else:
        # 1. Master Trainee Directory & Scheduled Email Milestones Table
        st.markdown('<div class="section-title">Master Trainee Directory & Milestone Schedule Timeline</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">Authoritative scheduled milestone dispatch dates and statuses for all trainees across all 6 stages. Synchronized with database and worker.</div>',
            unsafe_allow_html=True,
        )

        master_rows = []
        for t in filtered_trainees:
            t_scheds = get_schedules_for_trainee(conn, t.trainee_id)
            s_map = {s.stage: s for s in t_scheds}

            eff_lwd = t.last_working_date or (calculate_default_lwd(t.date_of_joining) if t.date_of_joining else None)
            auto_stage_map = calculate_all_stage_dates(t.date_of_joining, eff_lwd) if (t.date_of_joining and eff_lwd) else {}

            def _format_stage_cell(stage: EmailStage) -> str:
                s = s_map.get(stage)
                auto_pair = auto_stage_map.get(stage, (None, None))
                auto_sched = auto_pair[1]
                auto_dt_str = format_date_ui(auto_sched) if auto_sched else "-"

                if not s:
                    return f"{auto_dt_str} [Scheduled]" if auto_dt_str != "-" else "-"
                dt_str = format_date_ui(s.scheduled_date) if s.scheduled_date else auto_dt_str
                if s.status == ScheduleStatus.SENT:
                    return f"{dt_str} [Sent]"
                elif s.is_opted_out:
                    return f"{dt_str} [Opted Out]"
                elif s.status == ScheduleStatus.CANCELLED:
                    return f"{dt_str} [Cancelled]"
                elif s.status == ScheduleStatus.UNCERTAIN:
                    return f"{dt_str} [Uncertain]"
                elif s.status == ScheduleStatus.PROCESSING:
                    return f"{dt_str} [Processing]"
                elif s.is_custom_date:
                    return f"{dt_str} [Custom Override]"
                else:
                    return f"{dt_str} [Scheduled]"

            master_rows.append({
                "Trainee ID": t.trainee_id,
                "Name": t.trainee_name,
                "Status": t.status.value,
                "DOJ": format_date_ui(t.date_of_joining),
                "LWD": format_date_ui(t.last_working_date),
                "Initial Email (DOJ+15d)": _format_stage_cell(EmailStage.INITIAL),
                "Q1 Milestone (DOJ+3m)": _format_stage_cell(EmailStage.Q1),
                "Q2 Milestone (DOJ+6m)": _format_stage_cell(EmailStage.Q2),
                "Q3 Milestone (DOJ+9m)": _format_stage_cell(EmailStage.Q3),
                "Q4 Milestone (DOJ+12m)": _format_stage_cell(EmailStage.Q4),
                "Exit Feedback (LWD+3m)": _format_stage_cell(EmailStage.EXIT),
                "Department": t.department,
                "Manager": t.manager_name,
            })

        df_master = pd.DataFrame(master_rows)
        st.dataframe(df_master, use_container_width=True, hide_index=True)
        st.caption("Status Indicators: [Scheduled] Normal Automated Date &bull; [Custom Override] Manual Date &bull; [Opted Out] Stage Inactive &bull; [Sent] Delivered &bull; [Cancelled] Lifecycle Inactive &bull; [Uncertain] Exception")

        st.markdown("---")
        st.markdown('<div class="section-title">Trainee Details & Configuration</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">Select an apprentice to inspect full profile details, update lifecycle status, or customize specific milestone schedules.</div>', unsafe_allow_html=True)

        trainee_options = {f"{t.trainee_id} - {t.trainee_name} ({t.status.value})": t.trainee_id for t in filtered_trainees}
        selected_display = st.selectbox("Select Trainee for Profile & Schedules", options=list(trainee_options.keys()))
        selected_id = trainee_options[selected_display]

        trainee = get_trainee(conn, selected_id)
        schedules = get_schedules_for_trainee(conn, selected_id)

        tab_schedules, tab_profile, tab_edit = st.tabs([
            "Milestone Schedules & Opt-Outs",
            "Profile Information",
            "Edit Trainee & Lifecycle",
        ])

        # TAB: MILESTONE SCHEDULES & OPT-OUTS
        with tab_schedules:
            st.subheader("Email Stage Schedule Dates & Opt-Out Preferences")
            st.caption(
                "Authoritative email stages and dispatch dates. Synchronized in real time across the database, "
                "worker, and import engine. Sent stages are strictly immutable."
            )

            stage_rows = []
            for s in schedules:
                stage_rows.append({
                    "Stage": f"{STAGE_LABELS.get(s.stage, s.stage.value)} ({s.stage.value})",
                    "Recipient": s.recipient_role,
                    "Math Due Date": format_date_ui(s.original_due_date),
                    "Effective Scheduled Date": format_date_ui(s.scheduled_date),
                    "Date Mode": "Custom Override" if s.is_custom_date else "Automatic (Weekend Adjusted)",
                    "Opt-out Preference": "Opted Out" if s.is_opted_out else "Active (Enabled)",
                    "Status": s.status.value,
                    "Attempts": s.attempt_count,
                    "Details": s.last_error or s.cancellation_reason or (f"Sent to {s.recipient_email_used}" if s.sent_at else "-")
                })
            st.dataframe(stage_rows, use_container_width=True)

            st.markdown("---")
            st.markdown("**Update Email Stage Schedule Dates & Opt-Outs**")
            st.caption("Modifications are validated, audited, and synchronized across all views immediately.")

            with st.form(f"sync_stages_form_{trainee.trainee_id}"):
                cols_form = st.columns(2)
                form_opt_outs: Dict[EmailStage, bool] = {}
                form_dates: Dict[EmailStage, date] = {}
                form_clears: Dict[EmailStage, bool] = {}

                for i, sched in enumerate(schedules):
                    col = cols_form[i % 2]
                    with col:
                        st.markdown(f"**{STAGE_LABELS.get(sched.stage, sched.stage.value)}** (`{sched.stage.value}`)")
                        badge_class = f"badge-{sched.status.value.lower()}"
                        st.markdown(f'<span class="badge {badge_class}">{sched.status.value}</span>', unsafe_allow_html=True)
                        st.caption(f"Recipient: {sched.recipient_role} &bull; Math Due: {format_date_ui(sched.original_due_date)}")

                        if sched.status == ScheduleStatus.SENT:
                            sent_str = format_date_ui(sched.sent_at.date()) if sched.sent_at else ""
                            st.info(f"Delivered on {sent_str} to {sched.recipient_email_used}. Record is immutable.")
                            form_opt_outs[sched.stage] = sched.is_opted_out
                            form_dates[sched.stage] = sched.scheduled_date
                            form_clears[sched.stage] = False
                        else:
                            opt_val = st.checkbox(
                                "Opt Out (Disable stage)",
                                value=sched.is_opted_out,
                                key=f"sync_opt_{trainee.trainee_id}_{sched.stage.value}",
                            )
                            form_opt_outs[sched.stage] = opt_val

                            date_val = st.date_input(
                                "Scheduled Date",
                                value=sched.scheduled_date,
                                key=f"sync_date_{trainee.trainee_id}_{sched.stage.value}",
                            )
                            form_dates[sched.stage] = date_val

                            if date_val < today_kolkata and not opt_val:
                                st.caption("Notice: Scheduled date is earlier than today; eligible for immediate dispatch on next worker run.")
                            if date_val.weekday() in (5, 6):
                                st.caption(f"Weekend Adjustment: Automatically shifts to Monday ({format_date_ui(adjust_for_weekend(date_val))}).")

                            clear_val = False
                            if sched.is_custom_date:
                                clear_val = st.checkbox(
                                    "Reset to automatic calculated date",
                                    value=False,
                                    key=f"sync_clear_{trainee.trainee_id}_{sched.stage.value}",
                                )
                            form_clears[sched.stage] = clear_val

                        st.divider()

                sync_submit = st.form_submit_button("Save & Synchronize Email Stages", type="primary")

                if sync_submit:
                    try:
                        update_stage_preferences_and_dates(
                            conn=conn,
                            trainee_id=trainee.trainee_id,
                            stage_preferences=form_opt_outs,
                            stage_custom_dates=form_dates,
                            clear_custom_dates=form_clears,
                            actor=st.session_state.current_user,
                            reason="Updated via Trainee Directory interface",
                        )
                        st.success(f"Email stages for trainee {trainee.trainee_id} synchronized and saved to database!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving stage preferences: {str(e)}")

        # TAB: PROFILE INFORMATION
        with tab_profile:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.write(f"**Trainee ID:** `{trainee.trainee_id}`")
                st.write(f"**Full Name:** {trainee.trainee_name}")
                st.write(f"**Email Address:** `{trainee.trainee_email}`")
                st.write(f"**Status:** `{trainee.status.value}`")
            with col_b:
                st.write(f"**Date of Joining (DOJ):** {format_date_ui(trainee.date_of_joining)}")
                lwd_str = format_date_ui(trainee.last_working_date)
                mode_str = "Auto (DOJ + 12m)" if trainee.lwd_mode == LwdMode.AUTO else "Manual Override"
                st.write(f"**Last Working Date (LWD):** {lwd_str} *({mode_str})*")
                st.write(f"**Department:** {trainee.department}")
                st.write(f"**Location:** {trainee.location}")
            with col_c:
                st.write(f"**Reporting Manager:** {trainee.manager_name}")
                st.write(f"**Manager Email:** `{trainee.manager_email}`")
                st.write(f"**Registration Date:** {format_date_ui(trainee.created_at.date()) if trainee.created_at else 'N/A'}")
                st.write(f"**Last Updated:** {format_date_ui(trainee.updated_at.date()) if trainee.updated_at else 'N/A'}")

        # TAB: EDIT TRAINEE & LIFECYCLE
        with tab_edit:
            st.subheader("Edit Trainee Details & Lifecycle Status")
            with st.form("edit_trainee_form"):
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    edit_name = st.text_input("Trainee Name", value=trainee.trainee_name)
                    edit_email = st.text_input("Trainee Email", value=trainee.trainee_email)
                    edit_mgr_name = st.text_input("Manager Name", value=trainee.manager_name)
                    edit_mgr_email = st.text_input("Manager Email", value=trainee.manager_email)
                    edit_dept = st.text_input("Department", value=trainee.department)
                    edit_loc = st.text_input("Location", value=trainee.location)

                with e_col2:
                    edit_doj = st.date_input("Date of Joining (DOJ)", value=trainee.date_of_joining)

                    status_options = [TraineeStatus.ACTIVE.value, TraineeStatus.LEFT.value, TraineeStatus.COMPLETED.value, TraineeStatus.ON_ROLL.value]
                    status_idx = status_options.index(trainee.status.value)
                    edit_status = st.selectbox("Lifecycle Status", options=status_options, index=status_idx)

                    st.markdown("**Last Working Date (LWD) Management:**")
                    lwd_mode_choice = st.radio(
                        "LWD Mode",
                        ["Automatic (DOJ + 12 calendar months)", "Manual Override Date"],
                        index=0 if trainee.lwd_mode == LwdMode.AUTO else 1,
                    )

                    default_calc_lwd = calculate_default_lwd(edit_doj)
                    current_lwd_val = trainee.last_working_date or default_calc_lwd
                    edit_lwd = st.date_input(
                        "Last Working Date (LWD)",
                        value=current_lwd_val,
                        help="Must be on or after Date of Joining.",
                    )

                    confirmed_actual_lwd = False
                    if edit_status == TraineeStatus.LEFT.value:
                        st.warning("Confirmation Required: Status is 'Left'. You must explicitly confirm the actual Last Working Date. Default DOJ + 12 months cannot be silently assumed.")
                        confirmed_actual_lwd = st.checkbox("I confirm that the above Last Working Date is the trainee's actual departure date.")

                    manual_reviewed = True
                    if edit_doj != trainee.date_of_joining and trainee.lwd_mode == LwdMode.MANUAL:
                        st.info(f"Notice: DOJ changed from {format_date_ui(trainee.date_of_joining)} to {format_date_ui(edit_doj)}. Please review the manual LWD.")
                        manual_reviewed = st.checkbox("I have reviewed and confirmed the manual LWD.")

                submit_edit = st.form_submit_button("Save Trainee & Reconcile Schedules", type="primary")

                if submit_edit:
                    try:
                        resolved_mode = LwdMode.AUTO if "Automatic" in lwd_mode_choice else LwdMode.MANUAL
                        resolved_lwd = default_calc_lwd if resolved_mode == LwdMode.AUTO and edit_doj != trainee.date_of_joining else edit_lwd

                        update_trainee_and_reconcile(
                            conn=conn,
                            trainee_id=trainee.trainee_id,
                            name=edit_name,
                            email=edit_email,
                            manager_name=edit_mgr_name,
                            manager_email=edit_mgr_email,
                            department=edit_dept,
                            location=edit_loc,
                            new_doj=edit_doj,
                            new_lwd=resolved_lwd,
                            new_lwd_mode=resolved_mode,
                            new_status=TraineeStatus(edit_status),
                            confirmed_actual_lwd=confirmed_actual_lwd,
                            manual_lwd_reviewed=manual_reviewed,
                            actor=st.session_state.current_user,
                        )
                        st.success(f"Trainee {trainee.trainee_id} updated and schedules reconciled successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating trainee: {str(e)}")

            st.markdown("---")
            with st.expander("Archive Trainee Record"):
                st.caption("Archiving deactivates the trainee record while strictly preserving all email schedules and Sent delivery history.")
                if st.button("Archive Trainee Record", type="secondary"):
                    try:
                        archive_trainee(conn, trainee.trainee_id, actor=st.session_state.current_user)
                        st.success(f"Trainee {trainee.trainee_id} archived successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

# =============================================================
# VIEW 3: ADD NEW TRAINEE
# =============================================================
elif menu == "Add Trainee":
    st.markdown('<div class="section-title">Enroll New NAPS Apprentice</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">All milestone dates are deterministically computed with calendar month clamping and automatic weekend adjustments.</div>', unsafe_allow_html=True)

    with st.form("create_trainee_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_id = st.text_input("Trainee ID (Mandatory, Unique)*", placeholder="e.g. TR-5001")
            new_name = st.text_input("Trainee Full Name*", placeholder="e.g. Priyanshu Roy")
            new_email = st.text_input("Trainee Email Address*", placeholder="e.g. trainee@example.com")
            new_doj = st.date_input("Date of Joining (DOJ)*", value=today_kolkata)
            new_dept = st.text_input("Department*", value="Engineering")
            new_loc = st.text_input("Location*", value="Bangalore")

        with col2:
            new_mgr_name = st.text_input("Manager Name*", value="Project Manager")
            new_mgr_email = st.text_input("Manager Email Address*", value="manager@example.com")
            new_status = st.selectbox("Status", [TraineeStatus.ACTIVE.value, TraineeStatus.LEFT.value, TraineeStatus.COMPLETED.value, TraineeStatus.ON_ROLL.value], index=0)

            auto_lwd_calc = calculate_default_lwd(new_doj)
            st.markdown(f"**Default LWD (DOJ + 12m):** `{format_date_ui(auto_lwd_calc)}`")

            use_custom_lwd = st.checkbox("Provide Manual Last Working Date Override")
            custom_lwd = None
            if use_custom_lwd:
                custom_lwd = st.date_input("Manual Last Working Date", value=auto_lwd_calc)

            confirmed_lwd = False
            if new_status == TraineeStatus.LEFT.value:
                st.warning("Confirmation Required: Status is 'Left'. You must explicitly confirm the actual Last Working Date.")
                confirmed_lwd = st.checkbox("Confirm actual LWD for status Left*")

        st.markdown("---")
        st.markdown("**Initial Email Stage Schedule Dates & Opt-Outs**")
        st.caption("All 6 stages are enabled by default for new apprentices. You may customize dates or opt out.")

        effective_lwd_preview = custom_lwd if use_custom_lwd and custom_lwd else auto_lwd_calc
        preview_dates = calculate_all_stage_dates(new_doj, effective_lwd_preview)

        custom_dates_input = {}
        opt_out_input = {}

        cols = st.columns(3)
        stages = [EmailStage.INITIAL, EmailStage.Q1, EmailStage.Q2, EmailStage.Q3, EmailStage.Q4, EmailStage.EXIT]
        for i, stage in enumerate(stages):
            with cols[i % 3]:
                orig_d, sched_d = preview_dates[stage]
                enabled = st.checkbox(f"Enable {STAGE_LABELS[stage]}", value=True, key=f"new_opt_{stage.value}")
                opt_out_input[stage] = not enabled

                chosen_d = st.date_input(
                    f"Scheduled Date ({stage.value})",
                    value=sched_d,
                    key=f"new_date_{stage.value}",
                    help=f"Math Due: {format_date_ui(orig_d)}",
                )
                if chosen_d != sched_d:
                    custom_dates_input[stage] = chosen_d

        submit_new = st.form_submit_button("Register Trainee & Generate Schedules", type="primary")

        if submit_new:
            try:
                trainee_obj = Trainee(
                    trainee_id=new_id.strip(),
                    trainee_name=new_name.strip(),
                    trainee_email=new_email.strip(),
                    date_of_joining=new_doj,
                    manager_name=new_mgr_name.strip(),
                    manager_email=new_mgr_email.strip(),
                    department=new_dept.strip(),
                    location=new_loc.strip(),
                    status=TraineeStatus(new_status),
                    last_working_date=custom_lwd if use_custom_lwd else auto_lwd_calc,
                    lwd_mode=LwdMode.MANUAL if use_custom_lwd else LwdMode.AUTO,
                )
                create_trainee_with_schedules(
                    conn=conn,
                    trainee=trainee_obj,
                    custom_dates=custom_dates_input,
                    opt_out_preferences=opt_out_input,
                    confirmed_actual_lwd=confirmed_lwd,
                    actor=st.session_state.current_user,
                )
                st.success(f"Trainee {new_id} and 6 schedules created successfully!")
            except Exception as e:
                st.error(f"Validation error: {str(e)}")

# =============================================================
# VIEW 4: WORKER & DISPATCH ENGINE
# =============================================================
elif menu == "Worker & Dispatch":
    st.markdown('<div class="section-title">Automated Dispatch Worker & Engine Controls</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">The background worker processes eligible schedules whose scheduled_date <= Target Evaluation Date in Asia/Kolkata.</div>', unsafe_allow_html=True)

    # SMTP & Dispatch Configuration Overview
    with st.expander("SMTP & Dispatch Configuration", expanded=True):
        naps_config.reload_config()
        clean_pwd = (naps_config.SMTP_PASSWORD or "").replace(" ", "").strip()
        has_pwd = bool(clean_pwd)
        status_pwd_html = '<span style="color: #065F46; font-weight: 600;">Configured</span>' if has_pwd else '<span style="color: #B91C1C; font-weight: 600;">Not Set &bull; Configure in .env</span>'
        delivery_mode_html = '<span style="color: #B45309; font-weight: 600;">Simulation (Dry-Run Enabled)</span>' if naps_config.EMAIL_DRY_RUN else '<span style="color: #065F46; font-weight: 600;">Live SMTP Transmission</span>'

        sender_display = naps_config.DEFAULT_FROM_EMAIL or naps_config.SMTP_USER or "Not configured"
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 0.5rem;">
                <div style="font-weight: 700; color: #0F172A; margin-bottom: 0.5rem; font-size: 0.95rem;">
                    Active Dispatch Settings:
                </div>
                <div style="font-size: 0.85rem; color: #334155; line-height: 1.6;">
                    &bull; <b>Sender Email:</b> <code>{sender_display}</code><br/>
                    &bull; <b>SMTP Server:</b> <code>{naps_config.SMTP_HOST}:{naps_config.SMTP_PORT}</code> (STARTTLS)<br/>
                    &bull; <b>SMTP Authentication:</b> {status_pwd_html}<br/>
                    &bull; <b>Delivery Mode:</b> {delivery_mode_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Delivery Mode", "Simulation (Dry-Run)" if naps_config.EMAIL_DRY_RUN else "Live SMTP Dispatch")
    with col2:
        st.metric("Target Dispatch Hour", "09:00:00 Asia/Kolkata")
    with col3:
        st.metric("Automatic Retries", "1 Transient Retry Allowed")

    st.markdown("---")
    c_a, c_b = st.columns([2, 1])
    with c_a:
        run_date = st.date_input("Target Evaluation Date (Asia/Kolkata)", value=today_kolkata)
    with c_b:
        st.write("")
        st.write("")
        run_btn = st.button("Run Dispatch Worker Cycle", type="primary")

    worker = DispatchWorker(conn=conn, worker_id=f"manual-{st.session_state.current_user}")

    if run_btn:
        with st.spinner("Executing worker cycle (recovering leases, claiming, safety checks, dispatch)..."):
            res = worker.run_worker_cycle(target_date=run_date)
            st.success("Worker cycle completed successfully.")
            st.json(res)

    st.markdown("---")
    st.markdown('<div class="section-title">Queue Status: Pending & In-Flight Schedules</div>', unsafe_allow_html=True)
    due_cursor = conn.execute(
        """
        SELECT s.id, s.trainee_id, t.trainee_name, s.stage, s.scheduled_date, s.status, s.attempt_count
        FROM email_schedules s
        JOIN trainees t ON s.trainee_id = t.trainee_id
        WHERE s.status IN ('Scheduled', 'Retrying', 'Processing')
        ORDER BY s.scheduled_date ASC
        """
    )
    due_rows = due_cursor.fetchall()
    if due_rows:
        due_table = [
            {
                "ID": r["id"],
                "Trainee ID": r["trainee_id"],
                "Name": r["trainee_name"],
                "Stage": r["stage"],
                "Scheduled Date": format_date_ui(parse_date(r["scheduled_date"])),
                "Status": r["status"],
                "Attempts": r["attempt_count"],
            }
            for r in due_rows
        ]
        st.dataframe(due_table, use_container_width=True)
    else:
        st.info("No pending schedules currently queued.")

# =============================================================
# VIEW 5: EXCEL / CSV IMPORT & EXPORT
# =============================================================
elif menu == "Excel / CSV Import":
    st.markdown('<div class="section-title">Idempotent Trainee & Email Stage Import / Export</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">Upload .xlsx or .csv files with trainee fields and stage preferences. Re-importing unchanged data preserves custom dates, opt-outs, and Sent history.</div>',
        unsafe_allow_html=True,
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**Download Import Template:**")
        tmpl_df = generate_template_dataframe()

        buf_xlsx = io.BytesIO()
        tmpl_df.to_excel(buf_xlsx, index=False)
        buf_xlsx.seek(0)

        csv_str = tmpl_df.to_csv(index=False)

        st.download_button(
            "Download Excel Template (.xlsx)",
            data=buf_xlsx.getvalue(),
            file_name="naps_trainee_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.download_button(
            "Download CSV Template (.csv)",
            data=csv_str,
            file_name="naps_trainee_import_template.csv",
            mime="text/csv",
        )

    with col_t2:
        st.markdown("**Export Current Database:**")
        exp_df = export_trainees_dataframe(conn)
        buf_exp = io.BytesIO()
        exp_df.to_excel(buf_exp, index=False)
        buf_exp.seek(0)

        st.download_button(
            "Export Current Trainees & Schedules (.xlsx)",
            data=buf_exp.getvalue(),
            file_name="naps_current_trainees_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.download_button(
            "Export Current Trainees & Schedules (.csv)",
            data=exp_df.to_csv(index=False),
            file_name="naps_current_trainees_export.csv",
            mime="text/csv",
        )

    st.markdown("---")
    with st.expander("Documented Column Specifications & Validation Rules"):
        st.markdown(
            """
            **Trainee Core Fields:**
            `trainee_id`, `trainee_name`, `trainee_email`, `date_of_joining` (DD/MM/YYYY), `manager_name`, `manager_email`, `department`, `location`, `status`, `last_working_date`, `confirmed_actual_lwd`

            **Stage Opt-Out Columns (True/False):**
            `initial_email_opt_out`, `q1_opt_out`, `q2_opt_out`, `q3_opt_out`, `q4_opt_out`, `exit_feedback_opt_out`

            **Stage Scheduled Date Columns (DD/MM/YYYY):**
            `initial_email_scheduled_date`, `q1_scheduled_date`, `q2_scheduled_date`, `q3_scheduled_date`, `q4_scheduled_date`, `exit_feedback_scheduled_date`

            *Rules:*
            - For new trainees, omitted stage dates are automatically calculated and weekend-adjusted.
            - For update imports, blank cells preserve existing preferences and dates by default.
            """
        )

    uploaded_file = st.file_uploader("Select Trainee Excel or CSV File", type=["xlsx", "xls", "csv"])

    if uploaded_file is not None:
        importer = ExcelImporter(conn=conn, actor=st.session_state.current_user)
        try:
            if "import_file_id" not in st.session_state or st.session_state.import_file_id != uploaded_file.name:
                st.session_state.import_file_id = uploaded_file.name
                st.session_state.import_df = importer.parse_file(uploaded_file)
                st.session_state.import_overrides = {}

            if "import_df" not in st.session_state or st.session_state.import_df is None:
                st.session_state.import_df = importer.parse_file(uploaded_file)
                st.session_state.import_overrides = {}

            df_curr = st.session_state.import_df
            if df_curr is None or len(df_curr) == 0:
                st.info("The staged import is currently empty (all rows were removed or cleared).")
                if st.button("Reload Original File Rows", key="btn_reload_orig_staged"):
                    st.session_state.import_df = importer.parse_file(uploaded_file)
                    st.session_state.import_overrides = {}
                    st.rerun()
                st.stop()

            preview_items = preview_uploaded_schedules(df_curr, conn)

            total_emps = len(preview_items)
            new_emps = sum(1 for item in preview_items if not item["is_existing"])
            upd_emps = sum(1 for item in preview_items if item["is_existing"])
            overrides_cnt = len(st.session_state.import_overrides)

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Total Records in File", total_emps)
            m_col2.metric("New Registrations", new_emps)
            m_col3.metric("Existing Trainee Updates", upd_emps)
            m_col4.metric("Configured Schedule Overrides", overrides_cnt)

            st.markdown("---")
            st.markdown('<div class="section-title">Milestone Schedule Calculations for Uploaded Records</div>', unsafe_allow_html=True)
            st.caption(
                "Authoritative email milestone schedule dates calculated deterministically from Date of Joining (DOJ) "
                "and Last Working Date (LWD). Dates falling on Saturdays or Sundays are automatically shifted to Monday. "
                "Custom dates and opt-outs specified in the spreadsheet or configured below are highlighted."
            )

            sched_preview_rows = []
            for item in preview_items:
                stg_map = item.get("stages", {})

                def _fmt_preview_col(stage: EmailStage) -> str:
                    stg = stg_map.get(stage)
                    d_val = stg.get("scheduled_date") if stg else None
                    if not d_val:
                        eff_doj = item.get("date_of_joining")
                        eff_lwd = item.get("last_working_date") or (calculate_default_lwd(eff_doj) if eff_doj else None)
                        if eff_doj and eff_lwd:
                            calc_map = calculate_all_stage_dates(eff_doj, eff_lwd)
                            d_val = calc_map[stage][1]
                    d_str = format_date_ui(d_val) if d_val else "-"
                    if stg and stg.get("is_opted_out"):
                        return f"{d_str} [Opted Out]"
                    elif stg and stg.get("is_custom"):
                        return f"{d_str} [Custom Override]"
                    elif d_val and d_val.weekday() == 0 and stg and stg.get("math_due_date") and stg.get("math_due_date").weekday() in (5, 6):
                        return f"{d_str} [Weekend Shifted]"
                    else:
                        return f"{d_str} [Scheduled]"

                sched_preview_rows.append({
                    "Row #": item["row_number"],
                    "Trainee ID": item["trainee_id"],
                    "Employee Name": item["trainee_name"],
                    "Type": "Update (Existing)" if item["is_existing"] else "New Registration",
                    "DOJ": format_date_ui(item["date_of_joining"]) if item["date_of_joining"] else "Missing",
                    "LWD": format_date_ui(item["last_working_date"]) if item["last_working_date"] else "Missing",
                    "Status": item["status"],
                    "Initial Email (DOJ+15d)": _fmt_preview_col(EmailStage.INITIAL),
                    "Q1 Milestone (DOJ+3m)": _fmt_preview_col(EmailStage.Q1),
                    "Q2 Milestone (DOJ+6m)": _fmt_preview_col(EmailStage.Q2),
                    "Q3 Milestone (DOJ+9m)": _fmt_preview_col(EmailStage.Q3),
                    "Q4 Milestone (DOJ+12m)": _fmt_preview_col(EmailStage.Q4),
                    "Exit Feedback (LWD+3m)": _fmt_preview_col(EmailStage.EXIT),
                })

            st.dataframe(pd.DataFrame(sched_preview_rows), use_container_width=True, hide_index=True)
            st.caption("Status Indicators: [Scheduled] Normal (Weekend Adjusted) &bull; [Custom Override] Manual Date &bull; [Opted Out] Inactive")

            # ROW MANAGEMENT & DELETION FOR STAGED IMPORT
            with st.expander("Delete / Remove Rows from Staging Table", expanded=False):
                st.caption("Remove specific rows from this upload preview so they will not be imported into the database.")
                del_choices = {
                    f"Row {idx + 1}: {item['trainee_id']} - {item['trainee_name']} ({item['status']})": df_curr.index[idx]
                    for idx, item in enumerate(preview_items)
                }
                del_c1, del_c2 = st.columns([3, 1])
                with del_c1:
                    selected_rows_to_del = st.multiselect(
                        "Select Rows to Remove from Staging",
                        options=list(del_choices.keys()),
                        key="multi_select_delete_staged_rows",
                        placeholder="Choose rows to delete from staging...",
                    )
                with del_c2:
                    st.write("")
                    st.write("")
                    btn_del_rows = st.button("Delete Selected Rows", type="secondary", key="btn_execute_delete_staged")

                if btn_del_rows:
                    if selected_rows_to_del:
                        indices_to_drop = [del_choices[lbl] for lbl in selected_rows_to_del]
                        for lbl in selected_rows_to_del:
                            t_id = lbl.split(":")[1].split("-")[0].strip()
                            st.session_state.import_overrides.pop(t_id, None)
                        st.session_state.import_df = st.session_state.import_df.drop(index=indices_to_drop).reset_index(drop=True)
                        st.success(f"Removed {len(indices_to_drop)} row(s) from staged import.")
                        st.rerun()
                    else:
                        st.warning("Please select at least one row to remove.")

                st.write("")
                if st.button("Clear / Discard Entire Uploaded File", key="btn_clear_staged_upload"):
                    st.session_state.import_df = pd.DataFrame()
                    st.session_state.import_file_id = None
                    st.session_state.import_overrides = {}
                    st.success("Staged upload discarded.")
                    st.rerun()

            # INTERACTIVE CONFIGURATOR PER EMPLOYEE
            st.markdown("---")
            st.markdown('<div class="section-title">Employee Milestone Schedule Configuration & Overrides</div>', unsafe_allow_html=True)
            st.caption("Review or customize specific email milestone schedule dates and opt-out preferences for any employee before saving to database.")

            if total_emps > 0:
                emp_choices = {
                    f"Row {item['row_number']}: {item['trainee_id']} - {item['trainee_name']} ({'Update' if item['is_existing'] else 'New'})": idx
                    for idx, item in enumerate(preview_items)
                }
                selected_choice = st.selectbox(
                    "Select Employee to View / Adjust Schedule Dates",
                    options=list(emp_choices.keys()),
                    key="select_emp_import_schedule",
                )
                sel_idx = emp_choices[selected_choice]
                target_emp = preview_items[sel_idx]
                target_id = target_emp["trainee_id"]
                target_stages = target_emp.get("stages", {})

                with st.form(f"adjust_import_schedule_form_{target_id}_{sel_idx}"):
                    st.markdown(f"**Configuring Email Stage Schedules for:** `{target_id}` &mdash; **{target_emp['trainee_name']}**")
                    if target_emp["is_existing"]:
                        st.info("Notice: Existing trainee in database. Any milestone emails already sent in history are strictly immutable.")

                    stg_cols = st.columns(2)
                    form_opt_outs: Dict[EmailStage, bool] = {}
                    form_dates: Dict[EmailStage, date] = {}

                    all_stages_list = [
                        EmailStage.INITIAL,
                        EmailStage.Q1,
                        EmailStage.Q2,
                        EmailStage.Q3,
                        EmailStage.Q4,
                        EmailStage.EXIT,
                    ]

                    for s_i, stg in enumerate(all_stages_list):
                        col = stg_cols[s_i % 2]
                        stg_info = target_stages.get(stg, {})
                        curr_date = stg_info.get("scheduled_date") or today_kolkata
                        curr_opt = stg_info.get("is_opted_out", False)
                        math_due = stg_info.get("math_due_date")

                        with col:
                            st.markdown(f"**{STAGE_LABELS.get(stg, stg.value)}** (`{stg.value}`)")
                            st.caption(f"Role: {STAGE_RECIPIENT_ROLES.get(stg, 'Trainee')} &bull; Due: {format_date_ui(math_due) if math_due else 'N/A'}")

                            is_already_sent = False
                            if target_emp["is_existing"]:
                                s_row = conn.execute(
                                    "SELECT status, sent_at, recipient_email_used FROM email_schedules WHERE trainee_id = ? AND stage = ?",
                                    (target_id, stg.value),
                                ).fetchone()
                                if s_row and s_row["status"] == ScheduleStatus.SENT.value:
                                    is_already_sent = True
                                    sent_str = format_date_ui(parse_date(s_row['sent_at']))
                                    st.info(f"Delivered on {sent_str} to {s_row['recipient_email_used']}. Record is immutable.")
                                    form_opt_outs[stg] = False
                                    form_dates[stg] = curr_date

                            if not is_already_sent:
                                opt_val = st.checkbox(
                                    "Opt Out (Disable stage)",
                                    value=curr_opt,
                                    key=f"cfg_opt_{target_id}_{stg.value}_{sel_idx}",
                                )
                                form_opt_outs[stg] = opt_val

                                date_val = st.date_input(
                                    "Scheduled Date",
                                    value=curr_date,
                                    key=f"cfg_dt_{target_id}_{stg.value}_{sel_idx}",
                                )
                                form_dates[stg] = date_val

                                if date_val.weekday() in (5, 6):
                                    st.caption(f"Weekend Adjustment: Automatically shifts to Monday ({format_date_ui(adjust_for_weekend(date_val))}).")
                                if date_val < today_kolkata and not opt_val:
                                    st.caption("Notice: Scheduled date is in the past; worker will dispatch immediately upon next cycle.")

                            st.divider()

                    c_save_emp, c_del_emp = st.columns([3, 1])
                    with c_save_emp:
                        save_emp_schedules = st.form_submit_button(
                            f"Save Schedule Configuration for {target_id}",
                            type="primary",
                            use_container_width=True,
                        )
                    with c_del_emp:
                        del_single_staged_row = st.form_submit_button(
                            f"Delete Row {target_id}",
                            type="secondary",
                            use_container_width=True,
                        )

                    if del_single_staged_row:
                        target_df_idx = df_curr.index[sel_idx]
                        st.session_state.import_df = st.session_state.import_df.drop(index=[target_df_idx]).reset_index(drop=True)
                        st.session_state.import_overrides.pop(target_id, None)
                        st.success(f"Removed row for {target_id} from staged import.")
                        st.rerun()

                    if save_emp_schedules:
                        if target_id not in st.session_state.import_overrides:
                            st.session_state.import_overrides[target_id] = {}

                        row_pos = target_emp["row_number"] - 2
                        for stg in all_stages_list:
                            st.session_state.import_overrides[target_id][stg] = {
                                "scheduled_date": form_dates[stg],
                                "opt_out": form_opt_outs[stg],
                            }
                            cols = STAGE_COLUMN_MAP[stg]
                            if cols["scheduled_date"] not in st.session_state.import_df.columns:
                                st.session_state.import_df[cols["scheduled_date"]] = ""
                            if cols["opt_out"] not in st.session_state.import_df.columns:
                                st.session_state.import_df[cols["opt_out"]] = ""

                            st.session_state.import_df.at[row_pos, cols["scheduled_date"]] = format_date_ui(form_dates[stg])
                            st.session_state.import_df.at[row_pos, cols["opt_out"]] = "True" if form_opt_outs[stg] else "False"

                        st.success(f"Schedule preferences and dates updated for {target_id}. Reflected in preview table.")
                        st.rerun()

                if st.session_state.import_overrides:
                    c_rst1, c_rst2 = st.columns([1, 3])
                    with c_rst1:
                        if st.button("Reset All Overrides to Original File"):
                            st.session_state.import_df = importer.parse_file(uploaded_file)
                            st.session_state.import_overrides = {}
                            st.success("Reverted all schedule dates to original file contents.")
                            st.rerun()

            # DATABASE COMMIT
            st.markdown("---")
            st.markdown('<div class="section-title">Database Synchronization & Persistence</div>', unsafe_allow_html=True)
            st.caption("Commit all rows and synchronized schedule dates directly into the database.")

            col_btn1, col_btn2 = st.columns([2, 1])
            with col_btn1:
                confirm_import = st.button("Commit Valid Records & Synchronize Schedules", type="primary", use_container_width=True)

            if confirm_import:
                summary = importer.import_trainees(st.session_state.import_df)

                if st.session_state.import_overrides:
                    for ov_id, stg_map in st.session_state.import_overrides.items():
                        pref_opts = {stg: data["opt_out"] for stg, data in stg_map.items()}
                        pref_dates = {stg: data["scheduled_date"] for stg, data in stg_map.items()}
                        try:
                            update_stage_preferences_and_dates(
                                conn=conn,
                                trainee_id=ov_id,
                                stage_preferences=pref_opts,
                                stage_custom_dates=pref_dates,
                                actor=st.session_state.current_user,
                                reason="Configured via Import Section Schedule Dates Option",
                            )
                        except Exception:
                            pass

                st.session_state.import_overrides = {}
                st.success(
                    f"Import Completed: {summary.created_count} Created, {summary.updated_count} Updated, "
                    f"{summary.unchanged_count} Unchanged, {summary.failed_count} Failed."
                )

                if summary.failed_count > 0:
                    st.error("Partial Failures / Errors Reported:")
                    for r in summary.results:
                        if not r.success:
                            err_msg = ", ".join([f"{e['field']}: {e['reason']}" for e in r.errors])
                            st.write(f"- Row {r.row_number} (ID: `{r.trainee_id}`): {err_msg}")
                else:
                    st.info("Records committed successfully. You may view and manage them in the Trainee Directory.")

            with st.expander("Raw Normalized Spreadsheet Columns"):
                st.dataframe(st.session_state.import_df, use_container_width=True)

        except Exception as e:
            st.error(f"Error parsing file: {str(e)}")

    st.markdown("---")
    # UTILITY: DELETE / CLEAN UP IMPORTED TRAINEES FROM DATABASE
    with st.expander("Delete / Clean Up Trainees from Database", expanded=False):
        st.markdown('<div class="section-title">Database Clean Up Utility</div>', unsafe_allow_html=True)
        st.caption(
            "Delete registered trainees and their unsent schedules directly from the database. "
            "Note: Trainees with already 'Sent' milestone emails are protected and cannot be hard deleted to preserve audit logs."
        )
        all_db_trainees = list_trainees(conn, include_archived=False)
        if all_db_trainees:
            db_del_options = {
                f"{t.trainee_id} - {t.trainee_name} ({t.department}, {t.status.value})": t.trainee_id
                for t in all_db_trainees
            }
            db_del_selected = st.multiselect(
                "Select Trainees to Delete from Database",
                options=list(db_del_options.keys()),
                key="db_clean_up_multiselect",
                placeholder="Choose one or more trainees to delete from database...",
            )
            c_db_del1, c_db_del2 = st.columns([3, 1])
            with c_db_del1:
                confirm_chk = st.checkbox(
                    "I confirm that I want to permanently delete the selected trainee(s) and their unsent schedules",
                    key="chk_confirm_delete_from_db",
                )
            with c_db_del2:
                btn_delete_from_db = st.button("Delete from Database", type="secondary", key="btn_exec_db_delete_import")

            if btn_delete_from_db:
                if not db_del_selected:
                    st.warning("Please select at least one trainee to delete.")
                elif not confirm_chk:
                    st.error("Please confirm the deletion by checking the box.")
                else:
                    deleted_cnt = 0
                    errors_list = []
                    for label in db_del_selected:
                        t_id = db_del_options[label]
                        try:
                            delete_trainee(conn, t_id, actor=st.session_state.current_user)
                            deleted_cnt += 1
                        except Exception as e:
                            errors_list.append(f"{t_id}: {str(e)}")
                    if deleted_cnt > 0:
                        st.success(f"Successfully deleted {deleted_cnt} trainee(s) and their unsent schedules from database.")
                    if errors_list:
                        for err in errors_list:
                            st.error(f"Cannot delete: {err}")
                    st.rerun()
        else:
            st.info("No active trainees currently exist in the database.")

# =============================================================
# VIEW 6: AUDIT TRAIL & EXCEPTIONS
# =============================================================
elif menu == "Audit & Exceptions":
    tab_audit, tab_exc = st.tabs(["Activity Audit Trail", "Delivery Exceptions & Uncertain Deliveries"])

    with tab_audit:
        st.subheader("Append-Only System Audit Trail")
        st.caption("Comprehensive log of entity changes, status updates, overrides, worker actions, and exception resolutions.")

        filter_entity = st.selectbox("Filter Entity Type", ["All", "trainee", "schedule", "import", "worker"])

        query = "SELECT * FROM audit_logs"
        params = []
        if filter_entity != "All":
            query += " WHERE entity_type = ?"
            params.append(filter_entity)
        query += " ORDER BY id DESC LIMIT 100"

        logs = conn.execute(query, params).fetchall()
        if logs:
            log_data = [
                {
                    "ID": l["id"],
                    "Timestamp (IST)": l["timestamp"],
                    "Actor": l["actor"],
                    "Entity": f"{l['entity_type']} ({l['entity_id']})",
                    "Action": l["action"],
                    "Reason": l["reason"] or "-",
                    "Old Values": l["old_values"] or "-",
                    "New Values": l["new_values"] or "-",
                }
                for l in logs
            ]
            st.dataframe(log_data, use_container_width=True)
        else:
            st.info("No audit records found.")

    with tab_exc:
        st.subheader("Exception Management & Uncertain Delivery Resolution")
        st.caption("When SMTP timeouts or ambiguities occur during transmission, schedules are placed into Uncertain status. Admin authorization is required.")

        unc_cursor = conn.execute(
            """
            SELECT s.id, s.trainee_id, t.trainee_name, s.stage, s.scheduled_date, s.status, s.last_error, s.delivery_phase
            FROM email_schedules s
            JOIN trainees t ON s.trainee_id = t.trainee_id
            WHERE s.status IN ('Uncertain', 'Failed')
            ORDER BY s.id DESC
            """
        )
        unc_rows = unc_cursor.fetchall()

        if not unc_rows:
            st.success("No uncertain or failed schedules currently requiring attention.")
        else:
            for r in unc_rows:
                with st.container():
                    st.markdown(f"**Schedule #{r['id']} &bull; Trainee `{r['trainee_id']}` ({r['trainee_name']}) &bull; Stage: {r['stage']}**")
                    badge_cls = f"badge-{r['status'].lower()}"
                    st.markdown(f'Status: <span class="badge {badge_cls}">{r["status"]}</span> &bull; Phase: `{r["delivery_phase"]}`', unsafe_allow_html=True)
                    st.caption(f"Error / Details: {r['last_error']}")

                    if r["status"] == "Uncertain":
                        if has_permission(st.session_state.current_role, Permission.RESOLVE_UNCERTAIN):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                reason_txt = st.text_input("Resolution Justification*", key=f"res_txt_{r['id']}")
                            with col2:
                                if st.button("Mark as Confirmed Sent", key=f"btn_cs_{r['id']}"):
                                    if not reason_txt.strip():
                                        st.error("Justification is mandatory.")
                                    else:
                                        resolve_uncertain_schedule(conn, r["id"], "confirm_sent", actor=st.session_state.current_user, reason=reason_txt)
                                        st.success("Resolved as Sent.")
                                        st.rerun()
                            with col3:
                                if st.button("Authorize Retry", key=f"btn_ar_{r['id']}"):
                                    if not reason_txt.strip():
                                        st.error("Justification is mandatory.")
                                    else:
                                        resolve_uncertain_schedule(conn, r["id"], "authorize_retry", actor=st.session_state.current_user, reason=reason_txt)
                                        st.success("Authorized for retry.")
                                        st.rerun()
                        else:
                            st.warning("Admin authorization required to resolve Uncertain deliveries.")
                    st.divider()
