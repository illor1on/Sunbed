from datetime import timedelta
from decimal import Decimal

from app import db
from app.models import Booking, OverdueCharge, Price
from app.services.lock_status_service import get_lock_status, LockStatusError
from app.services.yookassa_service import YooKassaService, YooKassaServiceError
from app.config import OVERDUE_REFUND_GRACE_MINUTES
from app.utils.time import now_utc

# списываем не чаще, чем раз в час
OVERDUE_INTERVAL = timedelta(hours=1)


def process_overdue_booking(booking: Booking) -> bool:
    """
    Обрабатывает одну бронь на предмет overdue.
    Возвращает True, если выполнено хоть одно действие.
    """

    now = now_utc()

    # ───────────────────────────────
    # 1. Базовые инварианты
    # ───────────────────────────────
    if booking.status != "confirmed":
        return False

    if now <= booking.end_time + timedelta(minutes=OVERDUE_REFUND_GRACE_MINUTES):
        return False

    # ───────────────────────────────
    # 2. Rate limit (1 час)
    # ───────────────────────────────
    last = (
        OverdueCharge.query
        .filter_by(booking_id=booking.id)
        .order_by(OverdueCharge.created_at.desc())
        .first()
    )

    if last and now - last.created_at < OVERDUE_INTERVAL:
        return False

    # ───────────────────────────────
    # 3. Защита от дублей pending
    # ───────────────────────────────
    pending = (
        OverdueCharge.query
        .filter_by(
            booking_id=booking.id,
            payment_status="pending",
        )
        .first()
    )
    if pending:
        return False

    # ───────────────────────────────
    # 4. Проверка замка
    # ───────────────────────────────
    sunbed = booking.sunbed
    if not sunbed or not sunbed.has_lock or not sunbed.lock_identifier:
        return False

    try:
        status = get_lock_status(int(sunbed.lock_identifier))
    except LockStatusError:
        return False

    if status.get("locked") is True:
        return False

    # ───────────────────────────────
    # 5. Цена
    # ───────────────────────────────
    price = Price.query.get(sunbed.price_id)
    if not price or not price.price_per_hour:
        return False

    # ───────────────────────────────
    # 6. Создаём overdue (INTENT)
    # ───────────────────────────────
    overdue = OverdueCharge(
        booking_id=booking.id,
        hours=1,
        amount=Decimal(price.price_per_hour),
        payment_status="pending",
    )

    db.session.add(overdue)
    db.session.flush()  # нужен overdue.id

    # ───────────────────────────────
    # 7. AUTOPAY невозможен
    # ───────────────────────────────
    if not booking.payment_account or not booking.autopay_available:
        overdue.payment_status = "requires_payment"
        db.session.commit()
        return True

    # ───────────────────────────────
    # 8. AUTOPAY (SAFE)
    # ───────────────────────────────
    svc = YooKassaService(payment_account=booking.payment_account)

    try:
        payment = svc.create_payment(
            amount=overdue.amount,
            description=f"Overdue rent (1h) booking #{booking.id}",
            payment_method_id=booking.payment_method.external_id,
            capture=True,
            metadata={
                "type": "overdue",
                "overdue_id": overdue.id,
                "booking_id": booking.id,
                "payment_account_id": booking.payment_account.id,
            },
        )

        overdue.payment_id = payment["id"]
        db.session.commit()
        return True

    except YooKassaServiceError:
        db.session.rollback()
        return False

    except Exception:
        db.session.rollback()
        return False
