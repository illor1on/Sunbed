from flask import Blueprint, request, jsonify

from app import db
from app.models import (
    Booking,
    OverdueCharge,
    OwnerPaymentAccount,
    UserPaymentMethod,
)
from app.services.booking_service import confirm_booking_payment, clear_access
from app.services.yookassa_service import YooKassaService
from app.utils.time import now_utc
from flask_jwt_extended import jwt_required, get_jwt_identity


payments_bp = Blueprint("payments", __name__)

# ───────────────────────────────
# Helpers
# ───────────────────────────────

def _get_payment_account(metadata: dict):
    """
    Проверка webhook_token + payment_account_id.
    """
    token = request.args.get("token")
    account_id = metadata.get("payment_account_id")

    if not token or not account_id:
        return None

    account = OwnerPaymentAccount.query.get(int(account_id))
    if not account or not account.is_active:
        return None

    if account.webhook_token != token:
        return None

    return account


def _initiate_booking_refund(
    *,
    booking: Booking,
    payment_id: str,
    account: OwnerPaymentAccount,
    reason: str | None = None,
):
    """
    ЕДИНАЯ точка инициации refund booking.
    """
    booking.payment_status = "refund_pending"
    booking.updated_at = now_utc()
    clear_access(booking)
    db.session.commit()

    svc = YooKassaService(payment_account=account)
    svc.refund_payment(
        payment_id,
        metadata={
            "type": "booking",
            "booking_id": booking.id,
            "payment_account_id": account.id,
            "reason": reason,
        },
    )


# ───────────────────────────────
# YooKassa webhook
# ───────────────────────────────

@payments_bp.route("/yookassa/webhook", methods=["POST"])
def yookassa_webhook():
    event = request.get_json() or {}
    event_type = event.get("event")
    obj = event.get("object") or {}
    metadata = obj.get("metadata") or {}

    account = _get_payment_account(metadata)
    if not account:
        return jsonify({"error": "forbidden"}), 403

    svc = YooKassaService(payment_account=account)

    # ==================================================
    # PAYMENT SUCCEEDED
    # ==================================================
    if event_type == "payment.succeeded":
        payment_type = metadata.get("type")
        payment_id = obj.get("id")

        # ───────────────────────────────
        # BOOKING PAYMENT
        # ───────────────────────────────
        if payment_type == "booking":
            booking_id = metadata.get("booking_id")
            booking = Booking.query.get(int(booking_id)) if booking_id else None

            if not booking:
                return jsonify({"status": "ignored"}), 200

            # ❌ late / invalid booking → refund
            if booking.status != "pending":
                _initiate_booking_refund(
                    booking=booking,
                    payment_id=payment_id,
                    account=account,
                    reason="late_or_invalid_booking",
                )
                return jsonify({"status": "booking_refund_initiated"}), 200

            # ───────────────────────────────
            # 🔒 ACCEPT ONLY BANK CARDS
            # ───────────────────────────────
            pm = obj.get("payment_method") or {}
            pm_type = pm.get("type")
            pm_saved = pm.get("saved")
            pm_external_id = pm.get("id")

            if pm_type != "bank_card":
                _initiate_booking_refund(
                    booking=booking,
                    payment_id=payment_id,
                    account=account,
                    reason=f"unsupported_payment_method:{pm_type}",
                )
                return jsonify({"status": "booking_refund_initiated"}), 200

            # ───────────────────────────────
            # 💳 SAVE PAYMENT METHOD
            # ───────────────────────────────
            if pm_saved and pm_external_id:
                card = pm.get("card") or {}
                method = (
                    UserPaymentMethod.query
                    .filter_by(
                        provider="yookassa",
                        external_id=pm_external_id,
                        user_id=booking.user_id,
                    )
                    .first()
                )

                if not method:
                    method = UserPaymentMethod(
                        user_id=booking.user_id,
                        provider="yookassa",
                        external_id=pm_external_id,
                        card_last4=card.get("last4"),
                        card_brand=card.get("card_type"),
                        is_active=True,
                    )
                    db.session.add(method)
                    db.session.flush()

                booking.payment_method_id = method.id

            # ───────────────────────────────
            # ✅ CONFIRM BOOKING
            # ───────────────────────────────
            confirm_booking_payment(
                booking,
                payment_id=payment_id,
                method="yookassa",
            )
            db.session.commit()

            return jsonify({"status": "booking_confirmed"}), 200

        # ───────────────────────────────
        # OVERDUE PAYMENT
        # ───────────────────────────────
        if payment_type == "overdue":
            overdue_id = metadata.get("overdue_id")
            overdue = OverdueCharge.query.get(int(overdue_id)) if overdue_id else None

            if overdue and overdue.payment_status != "paid":
                overdue.payment_status = "paid"
                overdue.paid_at = now_utc()
                db.session.commit()

            return jsonify({"status": "overdue_paid"}), 200

    # ==================================================
    # REFUND SUCCEEDED
    # ==================================================
    if event_type == "refund.succeeded":
        refund_metadata = obj.get("metadata") or {}
        refund_type = refund_metadata.get("type")
        refund_payment_id = obj.get("payment_id")

        # ───────────────────────────────
        # BOOKING REFUND CONFIRM
        # ───────────────────────────────
        if refund_type == "booking":
            booking_id = refund_metadata.get("booking_id")
            booking = Booking.query.get(int(booking_id)) if booking_id else None

            if booking and booking.payment_status != "refunded":
                booking.payment_status = "refunded"
                booking.updated_at = now_utc()
                clear_access(booking)
                db.session.commit()

            return jsonify({"status": "booking_refund_confirmed"}), 200

        # ───────────────────────────────
        # OVERDUE REFUND CONFIRM
        # ───────────────────────────────
        if refund_type == "overdue_refund":
            overdue_id = refund_metadata.get("overdue_id")
            overdue = OverdueCharge.query.get(int(overdue_id)) if overdue_id else None

            if overdue and overdue.payment_status != "refunded":
                overdue.payment_status = "refunded"
                overdue.refunded_at = now_utc()
                db.session.commit()

            return jsonify({"status": "overdue_refund_confirmed"}), 200

        # ───────────────────────────────
        # FALLBACK (старые refund без metadata)
        # ───────────────────────────────
        if refund_payment_id:
            booking = Booking.query.filter_by(
                payment_id=refund_payment_id,
                payment_status="refund_pending",
            ).first()

            if booking:
                booking.payment_status = "refunded"
                booking.updated_at = now_utc()
                clear_access(booking)
                db.session.commit()
                return jsonify({"status": "booking_refund_confirmed_fallback"}), 200

            overdue = OverdueCharge.query.filter_by(
                payment_id=refund_payment_id,
                payment_status="refund_pending",
            ).first()

            if overdue:
                overdue.payment_status = "refunded"
                overdue.refunded_at = now_utc()
                db.session.commit()
                return jsonify({"status": "overdue_refund_confirmed_fallback"}), 200

    return jsonify({"status": "ignored"}), 200



@payments_bp.route("/me/payment-methods", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_my_payment_methods():
    current = get_jwt_identity()
    user_id = current["id"]

    methods = (
        UserPaymentMethod.query
        .filter_by(user_id=user_id)
        .order_by(UserPaymentMethod.created_at.desc())
        .all()
    )

    return jsonify({
        "items": [
            {
                "id": m.id,
                "provider": m.provider,
                "external_id": m.external_id,
                "is_active": m.is_active,
                "card_last4": m.card_last4,
                "card_brand": m.card_brand,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in methods
        ]
    }), 200