from datetime import timedelta

from app import db
from app.models import OverdueCharge, Booking, Sunbed
from app.services.lock_status_service import get_lock_status, LockStatusError
from app.services.overdue_refund_service import refund_overdue_charge
from app.utils.time import now_utc
from app.config import OVERDUE_REFUND_GRACE_MINUTES


def auto_refund_overdue_charges():
    """
    Авто-возврат overdue, если замок закрыт в grace-период.
    """

    now = now_utc()
    grace = timedelta(minutes=OVERDUE_REFUND_GRACE_MINUTES)

    charges = (
        OverdueCharge.query
        .filter(
            OverdueCharge.payment_status == "paid",
            OverdueCharge.created_at >= now - grace,
        )
        .all()
    )

    for overdue in charges:
        booking = Booking.query.get(overdue.booking_id)
        if not booking:
            continue

        sunbed = Sunbed.query.get(booking.sunbed_id)
        if not sunbed or not sunbed.has_lock or not sunbed.lock_identifier:
            continue

        try:
            status = get_lock_status(int(sunbed.lock_identifier))
        except LockStatusError:
            continue

        if status.get("locked") is True:
            try:
                refund_overdue_charge(overdue)
            except Exception:
                continue

    return {"status": "ok"}
