from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Tuple, Optional

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

from app import db
from app.config import PENDING_TTL_MINUTES
from app.models import Booking, Sunbed, Price, OwnerPaymentAccount
from app.services.booking_service import try_complete_booking, BookingServiceError
from app.services.yookassa_service import YooKassaService
from app.utils.time import to_utc, now_utc, to_msk
import app.extensions as ext

RATE_LIMIT_SECONDS = 5

bookings_bp = Blueprint("bookings", __name__)


# ============================================================
# Helpers
# ============================================================
def _rate_limit(key: str, seconds: int = RATE_LIMIT_SECONDS) -> bool:
    """
    True = allowed
    False = blocked (too frequent)
    """
    r = getattr(ext, "redis_client", None)
    if not r:
        return True

    try:
        # SET key value NX EX seconds
        ok = r.set(name=key, value="1", nx=True, ex=seconds)
        return bool(ok)
    except Exception:
        # Redis optional — do not fail business flow
        return True


def _pending_cutoff() -> datetime:
    return now_utc() - timedelta(minutes=PENDING_TTL_MINUTES)


def _has_conflict(sunbed_id: int, start: datetime, end: datetime) -> bool:
    """
    Overlap logic:
      start < existing.end AND end > existing.start

    We treat:
      - confirmed always conflicts
      - pending conflicts only if not expired by TTL
    """
    cutoff = _pending_cutoff()

    conflict = (
        Booking.query.filter(
            Booking.sunbed_id == sunbed_id,
            Booking.start_time < end,
            Booking.end_time > start,
            Booking.status.in_(["confirmed", "pending"]),
            or_(
                Booking.status == "confirmed",
                Booking.created_at >= cutoff,
            ),
        )
        .first()
        is not None
    )
    return conflict


def _calc_price(sunbed: Sunbed, start: datetime, end: datetime) -> Tuple[Optional[Decimal], Optional[str]]:
    """
    Price model:
      - price_per_hour
      - optional price_per_day (cap)

    Policy:
      - hours are rounded up to full hours, min 1 hour
      - total = hours * price_per_hour
      - if price_per_day exists => cap by price_per_day
    """
    price = Price.query.get(sunbed.price_id)
    if not price or not price.is_active:
        return None, "Invalid or inactive price"

    seconds = (end - start).total_seconds()
    if seconds <= 0:
        return None, "Invalid time range"

    hours = int((seconds + 3600 - 1) // 3600)  # ceil
    if hours < 1:
        hours = 1

    total = Decimal(price.price_per_hour) * Decimal(hours)

    if price.price_per_day is not None:
        day = Decimal(price.price_per_day)
        if day >= 0:
            total = min(total, day)

    if total < 0:
        total = Decimal("0.00")

    return total, None


def _expire_pending_if_needed(booking: Booking) -> bool:
    """
    Returns True if booking was expired/cancelled.
    """
    if booking.status != "pending":
        return False

    cutoff = _pending_cutoff()
    if booking.created_at and booking.created_at < cutoff:
        booking.status = "cancelled"
        booking.updated_at = now_utc()
        db.session.add(booking)
        db.session.commit()
        return True

    return False


# ============================================================
# Create booking
# ============================================================
@bookings_bp.route("", methods=["POST"])
@jwt_required()
def create_booking():
    current = get_jwt_identity()
    data = request.get_json() or {}

    sunbed_id = data.get("sunbed_id")
    start_raw = data.get("start_time")
    end_raw = data.get("end_time")

    if not sunbed_id or not start_raw or not end_raw:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        start = to_utc(datetime.fromisoformat(start_raw))
        end = to_utc(datetime.fromisoformat(end_raw))
    except Exception:
        return jsonify({"error": "Invalid datetime format"}), 400

    if start >= end:
        return jsonify({"error": "Invalid time range"}), 400

    # Serialize booking creation per sunbed to kill race conditions
    try:
        with db.session.begin():
            sunbed = (
                Sunbed.query.filter_by(id=int(sunbed_id))
                .with_for_update()
                .first()
            )
            if not sunbed:
                return jsonify({"error": "Sunbed not found"}), 404

            if _has_conflict(sunbed.id, start, end):
                return jsonify({"error": "Time slot already booked"}), 409

            total_price, err = _calc_price(sunbed, start, end)
            if err:
                return jsonify({"error": err}), 400

            booking = Booking(
                user_id=current["id"],
                sunbed_id=sunbed.id,
                start_time=start,
                end_time=end,
                total_price=total_price,
                status="pending",
                payment_status="pending",
            )
            db.session.add(booking)

        return jsonify(booking.to_dict()), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Booking failed"}), 500


# ============================================================
# Pay booking (multi-cash)
# ============================================================
@bookings_bp.route("/<int:booking_id>/pay", methods=["POST"])
@jwt_required()
def pay_booking(booking_id: int):
    current = get_jwt_identity()

    if not _rate_limit(f"pay_booking:{current['id']}:{booking_id}", RATE_LIMIT_SECONDS):
        return jsonify({"error": "Too many requests"}), 429

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current["id"]:
        return jsonify({"error": "Access denied"}), 403

    # ───────────────────────────────
    # STATE CHECKS
    # ───────────────────────────────
    if booking.status != "pending":
        return jsonify({"error": "Booking is not payable"}), 409

    if booking.payment_status == "paid":
        return jsonify({"error": "Already paid"}), 400

    # TTL guard
    if _expire_pending_if_needed(booking):
        return jsonify({"error": "Booking expired"}), 409

    # anti-race: payment already created
    if booking.payment_id:
        return jsonify({"error": "Payment already initiated"}), 409

    # ───────────────────────────────
    # RESOLVE PAYMENT ACCOUNT (MULTI-CASH)
    # ───────────────────────────────
    sunbed = booking.sunbed
    if not sunbed or not sunbed.beach:
        return jsonify({"error": "Invalid booking configuration"}), 500

    owner_id = sunbed.beach.owner_id
    payment_account = (
        OwnerPaymentAccount.query
        .filter_by(
            owner_id=owner_id,
            provider="yookassa",
            is_active=True,
        )
        .first()
    )

    if not payment_account:
        return jsonify({"error": "Owner payment account not configured"}), 409

    # ───────────────────────────────
    # CREATE PAYMENT (HTTP YooKassa)
    # ───────────────────────────────
    svc = YooKassaService(payment_account=payment_account)

    try:
        payment = svc.create_payment(
            amount=booking.total_price,
            description=f"Sunbed booking #{booking.id}",
            return_url=current_app.config.get(
                "YOOKASSA_RETURN_URL",
                "https://localhost:5173/profile",
            ),
            save_payment_method=True,
            metadata={
                "type": "booking",
                "booking_id": booking.id,
                "payment_account_id": payment_account.id,
            },
        )
    except Exception as e:
        current_app.logger.exception("YooKassa payment creation failed")
        return jsonify({"error": "Payment initiation failed"}), 502

    # ───────────────────────────────
    # PERSIST PAYMENT INFO
    # ───────────────────────────────
    booking.payment_id = payment["id"]
    booking.payment_provider = "yookassa"
    booking.payment_account_id = payment_account.id
    booking.updated_at = now_utc()

    db.session.commit()

    # ───────────────────────────────
    # RESPONSE
    # ───────────────────────────────
    return jsonify({
        "payment_id": payment["id"],
        "payment_url": payment["confirmation"]["confirmation_url"],
    }), 200



# ============================================================
# Access code
# ============================================================
@bookings_bp.route("/<int:booking_id>/access-code", methods=["GET"])
@jwt_required()
def get_access_code(booking_id: int):
    current = get_jwt_identity()
    now = now_utc()

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current["id"]:
        return jsonify({"error": "Access denied"}), 403

    if booking.payment_status != "paid" or booking.status != "confirmed":
        return jsonify({"error": "Booking not confirmed"}), 409

    if not booking.access_code:
        return jsonify({"error": "Access code not generated"}), 404

    # optional validity checks
    if booking.access_code_valid_from and now < booking.access_code_valid_from:
        return jsonify({"error": "Access code not active yet"}), 409

    if booking.access_code_valid_to and now > booking.access_code_valid_to:
        return jsonify({"error": "Access code expired"}), 409

    return jsonify({
        "access_code": booking.access_code,
        "valid_from": booking.access_code_valid_from.isoformat() if booking.access_code_valid_from else None,
        "valid_to": booking.access_code_valid_to.isoformat() if booking.access_code_valid_to else None,
    }), 200


# ============================================================
# Close-lock request (AND-close flow)
# ============================================================
@bookings_bp.route("/<int:booking_id>/close-lock", methods=["POST"])
@jwt_required()
def close_lock_request(booking_id: int):
    """
    Завершение аренды только если:
      1) пользователь запросил закрытие
      2) замок физически закрыт
    """
    current = get_jwt_identity()
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current["id"]:
        return jsonify({"error": "Access denied"}), 403

    if booking.status == "completed":
        return jsonify({"status": "already_completed"}), 200

    # ✅ фиксируем намерение пользователя
    booking.user_requested_close = True
    booking.user_requested_close_at = now_utc()
    db.session.add(booking)

    try:
        completed = try_complete_booking(
            booking,
            require_user_request=True
        )
        db.session.commit()

        if completed:
            return jsonify({"status": "completed", "booking": booking.to_dict()}), 200

        return jsonify({"status": "not_completed"}), 409

    except BookingServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409


# ============================================================
# Active bookings
# ============================================================
@bookings_bp.route("/active", methods=["GET"])
@jwt_required()
def get_active_bookings():
    current = get_jwt_identity()
    now = now_utc()

    # A booking is "active" if:
    # - confirmed and not completed
    # - or pending and not expired by TTL
    cutoff = _pending_cutoff()

    bookings = (
        Booking.query
        .filter(
            Booking.user_id == current["id"],
            Booking.status.in_(["confirmed", "pending"]),
            or_(
                Booking.status == "confirmed",
                Booking.created_at >= cutoff,
            ),
        )
        .order_by(Booking.start_time.desc())
        .all()
    )

    # Optionally mark stale pending as cancelled (best-effort)
    # (Do not fail request on commit issues)
    expired_ids = []
    for b in bookings:
        if b.status == "pending" and b.created_at and b.created_at < cutoff:
            expired_ids.append(b.id)
    if expired_ids:
        try:
            Booking.query.filter(Booking.id.in_(expired_ids)).update(
                {"status": "cancelled", "updated_at": now},
                synchronize_session=False,
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

        # remove expired from response
        bookings = [b for b in bookings if b.id not in expired_ids]

    return jsonify([b.to_dict() for b in bookings]), 200


# ============================================================
# Booking history
# ============================================================
@bookings_bp.route("/history", methods=["GET"])
@jwt_required()
def get_booking_history():
    current = get_jwt_identity()

    bookings = (
        Booking.query
        .filter(
            Booking.user_id == current["id"],
            Booking.status.in_(["completed", "cancelled"]),
        )
        .order_by(Booking.start_time.desc())
        .all()
    )

    # keep response stable for frontend (city/beach/sunbed names)
    return jsonify([
        {
            "id": b.id,
            "city_name": b.sunbed.beach.location.location_city if b.sunbed and b.sunbed.beach and b.sunbed.beach.location else None,
            "beach_name": b.sunbed.beach.name if b.sunbed and b.sunbed.beach else None,
            "sunbed_name": b.sunbed.name if b.sunbed else None,
            "start_time": to_msk(b.start_time).isoformat() if b.start_time else None,
            "end_time": to_msk(b.end_time).isoformat() if b.end_time else None,
            "total_price": float(b.total_price) if b.total_price is not None else None,
            "status": b.status,
            "payment_status": b.payment_status,
        }
        for b in bookings
    ]), 200
