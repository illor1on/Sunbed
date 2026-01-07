"""
RBAC permissions configuration.

ЕДИНСТВЕННЫЙ источник истины для permissions.
Используется:
- authz.require_perm
- User.has_perm
- frontend (navigation / feature flags)
"""

# =================================================
# BASE USER PERMISSIONS
# =================================================

BASE_USER_PERMS = {
    # dashboard
    "dashboard:read",

    # bookings (self)
    "booking:create",
    "booking:read_self",
    "booking:cancel_self",
}

# =================================================
# OWNER PERMISSIONS (business owner)
# =================================================

OWNER_EXTRA_PERMS = {
    # beaches
    "beach:read",
    "beach:write",

    # sunbeds
    "sunbed:read",
    "sunbed:write",

    # prices
    "price:read",
    "price:write",

    # bookings (own scope)
    "booking:read",
    "booking:write",

    # finance (OWN DATA ONLY)
    "payout:read",
    "payout:write",
}

# =================================================
# ADMIN PERMISSIONS (platform)
# =================================================

ADMIN_EXTRA_PERMS = {
    # users
    "users:read",
    "users:write",

    # locations
    "location:write",

    # bookings (GLOBAL)
    "booking:read_all",
    "booking:force_close",
    "booking:cancel_any",
    "booking:refund_overdue",

    # platform
    "platform:stats",

    "sunbed:remote_unlock",
}

# =================================================
# ROLE → PERMISSIONS MAP
# =================================================

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "user": BASE_USER_PERMS,
    "owner": BASE_USER_PERMS | OWNER_EXTRA_PERMS,
    "admin": BASE_USER_PERMS | OWNER_EXTRA_PERMS | ADMIN_EXTRA_PERMS,
}

# =================================================
# PUBLIC API
# =================================================

def permissions_for_role(role_name: str) -> set[str]:
    """
    Возвращает set permissions для роли.
    """
    if role_name not in ROLE_PERMISSIONS:
        raise ValueError(f"Unknown role: {role_name}")
    return ROLE_PERMISSIONS[role_name]


def has_perm(user, permission: str) -> bool:
    """
    Универсальная проверка permission.

    Используется в:
        require_perm(...)
        User.has_perm(...)
    """
    if not user:
        return False

    # Получаем имя роли
    role_name = None

    if hasattr(user, "role") and user.role:
        role_name = user.role.name
    else:
        # fallback (без падений)
        try:
            from app.models import Role
            role = Role.query.get(user.role_id)
            role_name = role.name if role else None
        except Exception:
            role_name = None

    if not role_name:
        return False

    try:
        return permission in permissions_for_role(role_name)
    except ValueError:
        return False
