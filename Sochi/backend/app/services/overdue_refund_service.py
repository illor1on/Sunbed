from app import db
from app.models import OverdueCharge, Booking, OwnerPaymentAccount
from app.services.yookassa_service import YooKassaService, YooKassaServiceError


class OverdueRefundError(Exception):
    pass


def refund_overdue_charge(overdue: OverdueCharge) -> None:
    """
    Инициирует refund overdue.
    Финальный статус ('refunded') ставится ТОЛЬКО webhook'ом.
    """

    if not overdue:
        raise OverdueRefundError("OverdueCharge is required")

    if overdue.payment_status == "refunded":
        return

    if overdue.payment_status != "paid":
        raise OverdueRefundError("OverdueCharge is not paid")

    booking = Booking.query.get(overdue.booking_id)
    if not booking:
        raise OverdueRefundError("Booking not found")

    account = OwnerPaymentAccount.query.get(booking.payment_account_id)
    if not account or not account.is_active:
        raise OverdueRefundError("Payment account invalid")

    # ───────────────────────────────
    # INTENT
    # ───────────────────────────────
    overdue.payment_status = "refund_pending"
    overdue.refunded_at = None
    db.session.commit()

    svc = YooKassaService(payment_account=account)

    try:
        svc.refund_payment(
            overdue.payment_id,
            metadata={
                "type": "overdue_refund",
                "overdue_id": overdue.id,
                "payment_account_id": account.id,
            },
        )
    except YooKassaServiceError as e:
        overdue.payment_status = "paid"
        db.session.commit()
        raise OverdueRefundError(str(e)) from e
