from .auth import auth_bp
from .beaches import beaches_bp
from .sunbeds import sunbeds_bp
from .bookings import bookings_bp
from .prices import prices_bp
from .payments import payments_bp
from .admin import admin_bp
from .owner_legal import owner_legal_bp
from .dashboard import dashboard_bp
from .locations import locations_bp
from .owner_payment_accounts import owner_payment_bp


__all__ = [
    "auth_bp",
    "beaches_bp",
    "sunbeds_bp",
    "bookings_bp",
    "prices_bp",
    "payments_bp",
    "admin_bp",
    "owner_legal_bp",
    "dashboard_bp",
    "locations_bp",
    "owner_payment_bp",
]
