from app.models import Booking
from app.services.overdue_service import process_overdue_booking
from app.utils.time import now_utc
from flask import current_app


def process_overdue_bookings():
    """
    Periodic job (scheduler):

    Creates / updates overdue charges for bookings that:
      - are confirmed (active rent)
      - have end_time in the past
      - are not completed
    """

    now = now_utc()

    bookings = Booking.query.filter(
        Booking.status == "confirmed",
        Booking.end_time < now,
        Booking.lock_closed_confirmed.is_(False),  # 🔒 КЛЮЧЕВОЕ
    ).all()

    print(bookings)

    if not bookings:
        return

    for booking in bookings:
        try:
            process_overdue_booking(booking)
        except Exception:
            current_app.logger.exception(
                f"Overdue processing failed for booking {booking.id}"
            )
