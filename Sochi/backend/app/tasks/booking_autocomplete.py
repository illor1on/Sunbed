from app.models import Booking
from app.services.booking_service import try_complete_booking, BookingServiceError
from app import db


def auto_complete_bookings():
    bookings = Booking.query.filter(
        Booking.status == "confirmed",
        Booking.user_requested_close.is_(True),
        Booking.lock_closed_confirmed.is_(False)
    ).all()

    for booking in bookings:
        try:
            completed = try_complete_booking(
                booking,
                require_user_request=True
            )
            if completed:
                db.session.commit()
        except BookingServiceError:
            db.session.rollback()
            continue
        except Exception:
            db.session.rollback()
            continue
