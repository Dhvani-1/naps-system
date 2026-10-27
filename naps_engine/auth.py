"""Role-based access control (RBAC) and permission checking for NAPS Engine."""

from enum import Enum
import hmac
import os
from typing import List, Optional

class UserRole(str, Enum):
    USER = "User"
    ADMIN = "Admin"

class Permission(str, Enum):
    # User permissions
    ADD_TRAINEE = "add_trainee"
    UPDATE_TRAINEE = "update_trainee"
    EDIT_SCHEDULED_DATE = "edit_scheduled_date"
    CHANGE_PREFERENCES = "change_preferences"
    IMPORT_DATA = "import_data"
    RUN_WORKER = "run_worker"
    
    # Admin-only permissions
    LIFECYCLE_OVERRIDE = "lifecycle_override"
    REACTIVATE_CANCELLED = "reactivate_cancelled"
    RESOLVE_UNCERTAIN = "resolve_uncertain"
    CONFIGURE_SAFETY_MODE = "configure_safety_mode"
    DELETE_TRAINEE = "delete_trainee"

ROLE_PERMISSIONS = {
    UserRole.USER: {
        Permission.ADD_TRAINEE,
        Permission.UPDATE_TRAINEE,
        Permission.EDIT_SCHEDULED_DATE,
        Permission.CHANGE_PREFERENCES,
        Permission.IMPORT_DATA,
        Permission.RUN_WORKER,
    },
    UserRole.ADMIN: {
        Permission.ADD_TRAINEE,
        Permission.UPDATE_TRAINEE,
        Permission.EDIT_SCHEDULED_DATE,
        Permission.CHANGE_PREFERENCES,
        Permission.IMPORT_DATA,
        Permission.RUN_WORKER,
        Permission.LIFECYCLE_OVERRIDE,
        Permission.REACTIVATE_CANCELLED,
        Permission.RESOLVE_UNCERTAIN,
        Permission.CONFIGURE_SAFETY_MODE,
        Permission.DELETE_TRAINEE,
    }
}

def has_permission(role: UserRole, permission: Permission) -> bool:
    """Verify whether a role is authorized for a specific system operation."""
    allowed = ROLE_PERMISSIONS.get(role, set())
    return permission in allowed

def enforce_permission(role: UserRole, permission: Permission) -> None:
    """Raise PermissionError if the specified role lacks the permission."""
    if not has_permission(role, permission):
        raise PermissionError(
            f"Action denied: Role '{role.value}' does not possess permission '{permission.value}'. "
            "Administrator authorization is required."
        )

# -------------------------------------------------------------
# Centralized Administrator Credentials & Authentication
# -------------------------------------------------------------
DEFAULT_ADMIN_USERNAME = os.environ.get("NAPS_ADMIN_USERNAME", "admin").strip().lower()
DEFAULT_ADMIN_EMAIL = os.environ.get("NAPS_ADMIN_EMAIL", "admin@company.com").strip().lower()
DEFAULT_ADMIN_PASSWORD = os.environ.get("NAPS_ADMIN_PASSWORD", "Admin@123")

def verify_admin_credentials(username: Optional[str], password: Optional[str]) -> bool:
    """Verify administrator login credentials using timing-attack safe string comparison.
    
    Accepts configured username (default: 'admin') or email (default: 'admin@company.com').
    """
    if not username or not password:
        return False
    
    clean_user = username.strip().lower()
    valid_users = {DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL}
    
    user_match = clean_user in valid_users
    pass_match = hmac.compare_digest(password.strip(), DEFAULT_ADMIN_PASSWORD)
    
    return user_match and pass_match

