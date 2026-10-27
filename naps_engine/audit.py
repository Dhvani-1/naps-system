"""Append-only audit logging module."""

from datetime import datetime
import json
from typing import Any, Dict, Optional
import sqlite3

from naps_engine.config import APP_TIMEZONE

def log_audit_event(
    conn: sqlite3.Connection,
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str = "system",
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None
) -> None:
    """Record an append-only audit event in the database.
    Passwords and sensitive secrets must never be passed to this function.
    """
    now_iso = datetime.now(APP_TIMEZONE).isoformat()
    old_json = json.dumps(old_values, default=str) if old_values else None
    new_json = json.dumps(new_values, default=str) if new_values else None
    
    conn.execute(
        """
        INSERT INTO audit_logs (
            timestamp, actor, entity_type, entity_id, action, old_values, new_values, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now_iso, actor, entity_type, entity_id, action, old_json, new_json, reason)
    )
