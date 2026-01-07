from datetime import timedelta

from app import db
from app.config import PENDING_TTL_MINUTES
from app.models import Booking
from app.utils.time import now_utc
from app.services.booking_service import clear_access


def cancel_expired_pending_bookings() -> int:
    now = now_utc()
    cutoff = now - timedelta(minutes=PENDING_TTL_MINUTES)

    expired = (
        Booking.query
        .filter(
            Booking.status == "pending",
            Booking.payment_status == "pending",
            Booking.created_at < cutoff,
        )
        .all()
    )

    for booking in expired:
        booking.status = "cancelled"
        if booking.payment_status == "pending":
            booking.payment_status = "failed"

        booking.updated_at = now
        clear_access(booking)  # 🔒 на всякий случай

    if expired:
        db.session.commit()

    return len(expired)
