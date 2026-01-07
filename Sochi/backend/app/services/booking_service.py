from __future__ import annotations

from datetime import timedelta

from app import db
from app.config import PENDING_TTL_MINUTES
from app.models import Booking, Sunbed
from app.services.ttlock_service import TTLockService, TTLockError
from app.services.lock_status_service import get_lock_status, LockStatusError
from app.utils.time import now_utc


class BookingServiceError(Exception):
    pass


# ─────────────────────────────────────────────
# PENDING TTL
# ─────────────────────────────────────────────

def is_pending_active(booking: Booking, *, now=None) -> bool:
    """
    Pending считается активным ТОЛЬКО в пределах TTL.
    Все сравнения — tz-aware UTC.
    """
    if booking.status != "pending":
        return False

    if not booking.created_at:
        return False

    now = now or now_utc()
    cutoff = now - timedelta(minutes=PENDING_TTL_MINUTES)
    return booking.created_at >= cutoff


# ─────────────────────────────────────────────
# ACCESS CLEANUP
# ─────────────────────────────────────────────

def clear_access(booking: Booking, *, sunbed: Sunbed | None = None) -> None:
    sunbed = sunbed or Sunbed.query.get(booking.sunbed_id)

    if booking.ttlock_password_id and sunbed and sunbed.lock_identifier:
        try:
            TTLockService().delete_pin(
                int(sunbed.lock_identifier),
                booking.ttlock_password_id,
            )
        except Exception:
            # 🔥 НИКОГДА не роняем бизнес-логику из-за замка
            pass

    booking.access_code = None
    booking.ttlock_password_id = None
    booking.access_code_valid_from = None
    booking.access_code_valid_to = None

    db.session.add(booking)



# ─────────────────────────────────────────────
# PAYMENT → CONFIRMED
# ─────────────────────────────────────────────

def confirm_booking_payment(
    booking: Booking,
    *,
    payment_id: str,
    method: str = "yookassa",
) -> None:
    """
    ЕДИНСТВЕННАЯ точка перехода:
      pending -> confirmed
      payment_status -> paid

    commit делает вызывающий код.
    """
    if booking.payment_status == "paid":
        return

    if booking.status != "pending":
        raise BookingServiceError(
            f"Cannot confirm payment for booking in status={booking.status}"
        )

    booking.payment_status = "paid"
    booking.status = "confirmed"
    booking.payment_id = payment_id
    booking.payment_provider = method
    booking.updated_at = now_utc()

    db.session.add(booking)


# ─────────────────────────────────────────────
# CONFIRMED → COMPLETED
# ─────────────────────────────────────────────

def try_complete_booking(
    booking: Booking,
    *,
    require_user_request: bool = True,
    force: bool = False,
) -> bool:
    """
    Пытается завершить бронь.

    ИНВАРИАНТЫ:
    - source of truth: Booking.status
    - замок ОПЦИОНАЛЕН
    - force=True игнорирует замок и user intent
    - без force:
        - если есть замок → AND-close
        - если нет замка → только user intent
    - НЕ коммитит транзакцию
    """

    # ─────────────────────────────
    # ИДЕМПОТЕНТНОСТЬ
    # ─────────────────────────────
    if booking.status == "completed":
        return True

    # ─────────────────────────────
    # БАЗОВЫЙ ИНВАРИАНТ
    # ─────────────────────────────
    if not force:
        if booking.status != "confirmed" or booking.payment_status != "paid":
            return False

    # ─────────────────────────────
    # USER INTENT (если требуется)
    # ─────────────────────────────
    if not force and require_user_request and not booking.user_requested_close:
        return False

    sunbed = Sunbed.query.get(booking.sunbed_id)

    has_lock = (
        sunbed is not None
        and sunbed.has_lock
        and bool(sunbed.lock_identifier)
    )

    # ─────────────────────────────
    # LOCK CHECK (ТОЛЬКО если есть замок И не force)
    # ─────────────────────────────
    if has_lock and not force:
        try:
            status = get_lock_status(int(sunbed.lock_identifier))
        except LockStatusError as e:
            raise BookingServiceError(str(e))

        if status.get("locked") is not True:
            return False

        booking.lock_closed_confirmed = True
        booking.lock_closed_confirmed_at = now_utc()

    # ─────────────────────────────
    # NO LOCK / FORCE PATH
    # ─────────────────────────────
    if not has_lock or force:
        booking.lock_closed_confirmed = True
        booking.lock_closed_confirmed_at = now_utc()

    # ─────────────────────────────
    # FINALIZE
    # ─────────────────────────────
    booking.status = "completed"
    booking.updated_at = now_utc()

    clear_access(booking, sunbed=sunbed)

    booking.user_requested_close = False
    booking.user_requested_close_at = now_utc()

    db.session.add(booking)
    return True
