"""Database initialization, schema management, and multi-engine transactional repository methods.

Supports:
1. Persistent PostgreSQL databases (Neon, Supabase, Vercel Postgres, AWS RDS) via DATABASE_URL or POSTGRES_URL.
2. Embedded SQLite (with WAL mode, busy timeout, and foreign keys) when running locally or during testing.
"""

import json
import os
import sqlite3
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from naps_engine.audit import log_audit_event
from naps_engine.config import APP_TIMEZONE, DEFAULT_DB_PATH
from naps_engine.date_engine import adjust_for_weekend
from naps_engine.models import (
    DeliveryAttempt,
    DeliveryPhase,
    EmailSchedule,
    EmailStage,
    LwdMode,
    ScheduleStatus,
    Trainee,
    TraineeStatus,
    format_date_db,
    parse_date,
    validate_state_transition,
)

# ------------------------------------------------------------------------------
# SQL SCHEMAS
# ------------------------------------------------------------------------------

SQLITE_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS trainees (
    trainee_id TEXT PRIMARY KEY,
    trainee_name TEXT NOT NULL,
    trainee_email TEXT NOT NULL,
    date_of_joining TEXT NOT NULL,
    manager_name TEXT NOT NULL,
    manager_email TEXT NOT NULL,
    department TEXT NOT NULL,
    location TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    last_working_date TEXT NOT NULL,
    lwd_mode TEXT NOT NULL DEFAULT 'auto',
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS email_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainee_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    recipient_role TEXT NOT NULL,
    original_due_date TEXT NOT NULL,
    custom_date TEXT NULL,
    scheduled_date TEXT NOT NULL,
    is_custom_date INTEGER NOT NULL DEFAULT 0,
    is_opted_out INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Scheduled',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    claimed_at TEXT NULL,
    lease_expires_at TEXT NULL,
    worker_id TEXT NULL,
    delivery_phase TEXT NULL,
    last_attempt_at TEXT NULL,
    last_error TEXT NULL,
    sent_at TEXT NULL,
    recipient_email_used TEXT NULL,
    cancellation_reason TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CONSTRAINT uq_trainee_stage UNIQUE (trainee_id, stage),
    FOREIGN KEY (trainee_id) REFERENCES trainees(trainee_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS delivery_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    trainee_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    attempt_at TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    status_outcome TEXT NOT NULL,
    failure_category TEXT NULL,
    error_details TEXT NULL,
    retry_decision TEXT NULL,
    worker_id TEXT NULL,
    FOREIGN KEY (schedule_id) REFERENCES email_schedules(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'system',
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    old_values TEXT NULL,
    new_values TEXT NULL,
    reason TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_schedules_dispatch 
    ON email_schedules (scheduled_date, status, is_opted_out);

CREATE INDEX IF NOT EXISTS idx_schedules_lease 
    ON email_schedules (status, lease_expires_at);

CREATE INDEX IF NOT EXISTS idx_schedules_trainee 
    ON email_schedules (trainee_id);
"""

POSTGRES_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trainees (
    trainee_id VARCHAR(100) PRIMARY KEY,
    trainee_name VARCHAR(255) NOT NULL,
    trainee_email VARCHAR(255) NOT NULL,
    date_of_joining VARCHAR(20) NOT NULL,
    manager_name VARCHAR(255) NOT NULL,
    manager_email VARCHAR(255) NOT NULL,
    department VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Active',
    last_working_date VARCHAR(20) NOT NULL,
    lwd_mode VARCHAR(20) NOT NULL DEFAULT 'auto',
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at VARCHAR(50) NOT NULL,
    updated_at VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS email_schedules (
    id SERIAL PRIMARY KEY,
    trainee_id VARCHAR(100) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    recipient_role VARCHAR(50) NOT NULL,
    original_due_date VARCHAR(20) NOT NULL,
    custom_date VARCHAR(20) NULL,
    scheduled_date VARCHAR(20) NOT NULL,
    is_custom_date INTEGER NOT NULL DEFAULT 0,
    is_opted_out INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'Scheduled',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    claimed_at VARCHAR(50) NULL,
    lease_expires_at VARCHAR(50) NULL,
    worker_id VARCHAR(100) NULL,
    delivery_phase VARCHAR(50) NULL,
    last_attempt_at VARCHAR(50) NULL,
    last_error TEXT NULL,
    sent_at VARCHAR(50) NULL,
    recipient_email_used VARCHAR(255) NULL,
    cancellation_reason TEXT NULL,
    created_at VARCHAR(50) NOT NULL,
    updated_at VARCHAR(50) NOT NULL,
    CONSTRAINT uq_trainee_stage UNIQUE (trainee_id, stage),
    FOREIGN KEY (trainee_id) REFERENCES trainees(trainee_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS delivery_attempts (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL,
    trainee_id VARCHAR(100) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    attempt_number INTEGER NOT NULL,
    attempt_at VARCHAR(50) NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    status_outcome VARCHAR(50) NOT NULL,
    failure_category VARCHAR(100) NULL,
    error_details TEXT NULL,
    retry_decision VARCHAR(100) NULL,
    worker_id VARCHAR(100) NULL,
    FOREIGN KEY (schedule_id) REFERENCES email_schedules(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp VARCHAR(50) NOT NULL,
    actor VARCHAR(100) NOT NULL DEFAULT 'system',
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    old_values TEXT NULL,
    new_values TEXT NULL,
    reason TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_schedules_dispatch 
    ON email_schedules (scheduled_date, status, is_opted_out);

CREATE INDEX IF NOT EXISTS idx_schedules_lease 
    ON email_schedules (status, lease_expires_at);

CREATE INDEX IF NOT EXISTS idx_schedules_trainee 
    ON email_schedules (trainee_id);
"""

# Backwards compatibility
SCHEMA_SQL = SQLITE_SCHEMA_SQL

# ------------------------------------------------------------------------------
# PLACEHOLDER CONVERSION HELPER
# ------------------------------------------------------------------------------

def _convert_qmark_to_percent_s(sql: str) -> str:
    """Convert '?' parameter placeholders to '%s' for PostgreSQL."""
    parts = []
    in_str = False
    str_char = ''
    i = 0
    while i < len(sql):
        c = sql[i]
        if in_str:
            parts.append(c)
            if c == str_char:
                if i + 1 < len(sql) and sql[i+1] == str_char:
                    parts.append(sql[i+1])
                    i += 1
                else:
                    in_str = False
        else:
            if c in ("'", '"'):
                in_str = True
                str_char = c
                parts.append(c)
            elif c == '?':
                parts.append('%s')
            else:
                parts.append(c)
        i += 1
    return "".join(parts)


# ------------------------------------------------------------------------------
# UNIFIED ROW & CURSOR WRAPPERS
# ------------------------------------------------------------------------------

class RowWrapper(dict):
    """Unified row wrapper providing dictionary mapping and sequence index access."""
    def __init__(self, col_names: List[str], values: Any):
        super().__init__(zip(col_names, values))
        self._values = tuple(values)

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, int):
            return self._values[item]
        return super().__getitem__(item)

    def get(self, key: Any, default: Any = None) -> Any:
        if isinstance(key, int):
            return self._values[key] if 0 <= key < len(self._values) else default
        return super().get(key, default)


class PostgresCursorWrapper:
    """Cursor wrapper delivering sqlite3.Row-like column and index access."""
    def __init__(self, raw_cursor, lastrowid: Optional[int] = None):
        self._cursor = raw_cursor
        self._lastrowid = lastrowid
        self._col_names = [col[0] for col in raw_cursor.description] if raw_cursor.description else []

    def fetchone(self) -> Optional[Any]:
        row = self._cursor.fetchone()
        if row is None:
            return None
        return RowWrapper(self._col_names, row)

    def fetchall(self) -> List[Any]:
        rows = self._cursor.fetchall()
        return [RowWrapper(self._col_names, r) for r in rows]

    def fetchmany(self, size: Optional[int] = None) -> List[Any]:
        rows = self._cursor.fetchmany(size) if size is not None else self._cursor.fetchmany()
        return [RowWrapper(self._col_names, r) for r in rows]

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def lastrowid(self) -> Optional[int]:
        return self._lastrowid

    def __iter__(self):
        return iter(self.fetchall())

    def close(self):
        try:
            self._cursor.close()
        except Exception:
            pass


class PostgresConnectionWrapper:
    """Connection wrapper presenting a unified DB-API interface compatible with sqlite3."""
    def __init__(self, pg_conn):
        self._conn = pg_conn
        self._conn.autocommit = False

    def execute(self, sql: str, params: Any = None) -> PostgresCursorWrapper:
        sql_clean = sql.strip()
        sql_upper = sql_clean.upper()

        # Handle explicit transaction directives
        if sql_upper.startswith("BEGIN"):
            return PostgresCursorWrapper(self._conn.cursor())
        elif sql_upper == "COMMIT":
            self._conn.commit()
            return PostgresCursorWrapper(self._conn.cursor())
        elif sql_upper == "ROLLBACK":
            self._conn.rollback()
            return PostgresCursorWrapper(self._conn.cursor())

        pg_sql = _convert_qmark_to_percent_s(sql)
        cursor = self._conn.cursor()
        lastrowid = None

        # Check if INSERT without RETURNING on table with serial id
        sql_trim = pg_sql.strip().rstrip(";")
        is_insert = sql_trim.upper().startswith("INSERT INTO")
        has_returning = "RETURNING" in sql_trim.upper()
        target_tables = ("email_schedules", "delivery_attempts", "audit_logs")
        needs_returning = is_insert and not has_returning and any(tbl in sql_trim for tbl in target_tables)

        if needs_returning:
            sql_trim += " RETURNING id"
            if params is not None:
                cursor.execute(sql_trim, tuple(params) if isinstance(params, (list, tuple)) else params)
            else:
                cursor.execute(sql_trim)
            try:
                ret = cursor.fetchone()
                if ret:
                    lastrowid = ret[0]
            except Exception:
                pass
            return PostgresCursorWrapper(cursor, lastrowid=lastrowid)
        else:
            if params is not None:
                cursor.execute(pg_sql, tuple(params) if isinstance(params, (list, tuple)) else params)
            else:
                cursor.execute(pg_sql)
            return PostgresCursorWrapper(cursor)

    def commit(self):
        try:
            self._conn.commit()
        except Exception:
            pass

    def rollback(self):
        try:
            self._conn.rollback()
        except Exception:
            pass

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass

    def executescript(self, script: str):
        statements = [s.strip() for s in script.split(";") if s.strip()]
        for stmt in statements:
            if stmt.upper().startswith("PRAGMA"):
                continue
            cursor = self._conn.cursor()
            try:
                cursor.execute(_convert_qmark_to_percent_s(stmt))
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                if "already exists" not in str(e).lower():
                    print(f"[DB SCHEMA NOTICE] {e}")
            finally:
                cursor.close()


# ------------------------------------------------------------------------------
# CONNECTION FACTORY
# ------------------------------------------------------------------------------

_schema_initialized: bool = False


def get_sqlite_path(db_path: Optional[str] = None) -> str:
    """Determine writable SQLite path, automatically defaulting to /tmp on serverless environments."""
    if db_path:
        return db_path
    env_path = os.environ.get("NAPS_DB_PATH")
    if env_path:
        return env_path
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "/tmp/naps_trainees.db"
    try:
        test_file = f".test_write_{os.getpid()}"
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return DEFAULT_DB_PATH
    except Exception:
        return "/tmp/naps_trainees.db"


def get_db_type() -> str:
    """Return active database engine type ('postgres' or 'sqlite')."""
    db_url = (os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or "").strip()
    return "postgres" if db_url else "sqlite"


def init_db(conn: Union[sqlite3.Connection, PostgresConnectionWrapper]) -> None:
    """Initialize database tables, foreign keys, and indexes for active engine."""
    if isinstance(conn, PostgresConnectionWrapper) or get_db_type() == "postgres":
        conn.executescript(POSTGRES_SCHEMA_SQL)
    else:
        conn.executescript(SQLITE_SCHEMA_SQL)


def ensure_db_initialized(conn: Union[sqlite3.Connection, PostgresConnectionWrapper]) -> None:
    """Ensure database schema is initialized at least once per process container."""
    global _schema_initialized
    if not _schema_initialized:
        try:
            init_db(conn)
            _schema_initialized = True
        except Exception as e:
            print(f"[DB WARNING] Schema initialization warning: {e}")


def get_db_connection(db_path: Optional[str] = None) -> Union[sqlite3.Connection, PostgresConnectionWrapper]:
    """Obtain an authoritative database connection.
    
    If DATABASE_URL or POSTGRES_URL is configured (e.g. Neon, Supabase, Vercel Postgres),
    connects to PostgreSQL via psycopg2.
    Otherwise, falls back to embedded SQLite with WAL journal mode.
    """
    db_url = (os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or "").strip()

    if db_url:
        try:
            import psycopg2
            if db_url.startswith("postgres://"):
                db_url = "postgresql://" + db_url[len("postgres://"):]
            if "localhost" not in db_url and "127.0.0.1" not in db_url:
                if "?" not in db_url:
                    db_url += "?sslmode=require"
                elif "sslmode=" not in db_url:
                    db_url += "&sslmode=require"
            raw_conn = psycopg2.connect(db_url)
            conn = PostgresConnectionWrapper(raw_conn)
            ensure_db_initialized(conn)
            return conn
        except Exception as e:
            print(f"[DB ERROR] PostgreSQL connection failed ({e}). Falling back to SQLite.")

    # SQLite Local/Serverless Fallback
    target_path = get_sqlite_path(db_path)
    parent_dir = os.path.dirname(os.path.abspath(target_path))
    if parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except Exception:
            pass

    conn = sqlite3.connect(target_path, timeout=10.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        try:
            conn.execute("PRAGMA journal_mode=DELETE;")
        except Exception:
            pass
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    ensure_db_initialized(conn)
    return conn


# ------------------------------------------------------------------------------
# DOMAIN OBJECT SERIALIZATION & DESERIALIZATION
# ------------------------------------------------------------------------------

def _safe_str(val: Any) -> Optional[str]:
    return str(val) if val is not None else None


def _safe_date(val: Any) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    return parse_date(str(val))


def _safe_datetime(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except Exception:
        return None


def row_to_trainee(row: Any) -> Trainee:
    """Convert database row to Trainee domain model."""
    return Trainee(
        trainee_id=row["trainee_id"],
        trainee_name=row["trainee_name"],
        trainee_email=row["trainee_email"],
        date_of_joining=_safe_date(row["date_of_joining"]),
        manager_name=row["manager_name"],
        manager_email=row["manager_email"],
        department=row["department"],
        location=row["location"],
        status=TraineeStatus(row["status"]),
        last_working_date=_safe_date(row["last_working_date"]),
        lwd_mode=LwdMode(row["lwd_mode"]),
        is_archived=bool(row["is_archived"]),
        created_at=_safe_datetime(row["created_at"]),
        updated_at=_safe_datetime(row["updated_at"]),
    )


def row_to_schedule(row: Any) -> EmailSchedule:
    """Convert database row to EmailSchedule domain model."""
    return EmailSchedule(
        id=row["id"],
        trainee_id=row["trainee_id"],
        stage=EmailStage(row["stage"]),
        recipient_role=row["recipient_role"],
        original_due_date=_safe_date(row["original_due_date"]),
        scheduled_date=_safe_date(row["scheduled_date"]),
        custom_date=_safe_date(row["custom_date"]),
        is_custom_date=bool(row["is_custom_date"]),
        is_opted_out=bool(row["is_opted_out"]),
        status=ScheduleStatus(row["status"]),
        attempt_count=int(row["attempt_count"] or 0),
        claimed_at=_safe_datetime(row["claimed_at"]),
        lease_expires_at=_safe_datetime(row["lease_expires_at"]),
        worker_id=row["worker_id"],
        delivery_phase=DeliveryPhase(row["delivery_phase"]) if row["delivery_phase"] else None,
        last_attempt_at=_safe_datetime(row["last_attempt_at"]),
        last_error=row["last_error"],
        sent_at=_safe_datetime(row["sent_at"]),
        recipient_email_used=row["recipient_email_used"],
        cancellation_reason=row["cancellation_reason"],
        created_at=_safe_datetime(row["created_at"]),
        updated_at=_safe_datetime(row["updated_at"]),
    )


# ------------------------------------------------------------------------------
# REPOSITORY QUERY METHODS
# ------------------------------------------------------------------------------

def get_trainee(conn: Any, trainee_id: str) -> Optional[Trainee]:
    """Retrieve a single trainee by stable identifier."""
    cursor = conn.execute("SELECT * FROM trainees WHERE trainee_id = ?", (trainee_id,))
    row = cursor.fetchone()
    return row_to_trainee(row) if row else None


def list_trainees(conn: Any, include_archived: bool = False) -> List[Trainee]:
    """List trainees from the database."""
    query = "SELECT * FROM trainees"
    if not include_archived:
        query += " WHERE is_archived = 0"
    query += " ORDER BY trainee_id ASC"
    cursor = conn.execute(query)
    return [row_to_trainee(r) for r in cursor.fetchall()]


def get_schedules_for_trainee(conn: Any, trainee_id: str) -> List[EmailSchedule]:
    """Retrieve all email schedules for a trainee, ordered by stage due date."""
    cursor = conn.execute(
        "SELECT * FROM email_schedules WHERE trainee_id = ? ORDER BY id ASC",
        (trainee_id,)
    )
    return [row_to_schedule(r) for r in cursor.fetchall()]


def get_schedule_by_id(conn: Any, schedule_id: int) -> Optional[EmailSchedule]:
    """Retrieve schedule by primary key."""
    cursor = conn.execute("SELECT * FROM email_schedules WHERE id = ?", (schedule_id,))
    row = cursor.fetchone()
    return row_to_schedule(row) if row else None


def archive_trainee(
    conn: Any,
    trainee_id: str,
    actor: str = "system",
    reason: Optional[str] = None
) -> None:
    """Soft-delete/archive a trainee, preserving all schedules and delivery history."""
    trainee = get_trainee(conn, trainee_id)
    if not trainee:
        raise ValueError(f"Trainee {trainee_id} not found.")

    now_iso = datetime.now(APP_TIMEZONE).isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "UPDATE trainees SET is_archived = 1, updated_at = ? WHERE trainee_id = ?",
            (now_iso, trainee_id)
        )
        log_audit_event(
            conn,
            entity_type="trainee",
            entity_id=trainee_id,
            action="ARCHIVE",
            actor=actor,
            old_values={"is_archived": False},
            new_values={"is_archived": True},
            reason=reason or "Archived by user"
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def delete_trainee(conn: Any, trainee_id: str, actor: str = "system") -> None:
    """Attempt hard delete of trainee. Strictly prohibited if any Sent delivery history exists."""
    schedules = get_schedules_for_trainee(conn, trainee_id)
    sent_schedules = [s for s in schedules if s.status == ScheduleStatus.SENT]
    if sent_schedules:
        raise ValueError(
            f"Cannot delete trainee {trainee_id}: {len(sent_schedules)} Sent schedule(s) exist. "
            f"Delivery history is immutable. Use archive_trainee() instead."
        )

    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("DELETE FROM delivery_attempts WHERE trainee_id = ?", (trainee_id,))
        conn.execute("DELETE FROM email_schedules WHERE trainee_id = ?", (trainee_id,))
        conn.execute("DELETE FROM trainees WHERE trainee_id = ?", (trainee_id,))
        log_audit_event(
            conn,
            entity_type="trainee",
            entity_id=trainee_id,
            action="DELETE",
            actor=actor,
            reason="Hard deleted without sent history"
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
