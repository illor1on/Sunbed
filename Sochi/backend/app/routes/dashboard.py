from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
from app.utils.time import now_utc, to_msk, to_utc

from app import db
from app.models import User, Beach, Sunbed, Booking
from app.authz import require_perm
from app.services.ttlock_service import TTLockService, TTLockError

from app.services.booking_service import try_complete_booking, BookingServiceError


dashboard_bp = Blueprint("dashboard", __name__)


# ───────────────────────────────
# helpers
# ───────────────────────────────

def _current_user() -> User:
    current = get_jwt_identity()
    return User.query.get(current["id"])


def _owner_beach_ids(user: User):
    return [b.id for b in Beach.query.filter_by(owner_id=user.id).all()]


def _scoped_bookings_query(user: User):
    q = Booking.query

    # admin → всё
    if not user.has_perm("booking:read_all"):
        q = q.join(Sunbed).filter(
            Sunbed.beach_id.in_(_owner_beach_ids(user))
        )

    return q


def _scoped_sunbeds_query(user: User):
    q = Sunbed.query

    if not user.has_perm("booking:read_all"):
        q = q.filter(
            Sunbed.beach_id.in_(_owner_beach_ids(user))
        )

    return q

def _scoped_beaches_query(user: User):
    q = Beach.query

    # admin → все пляжи
    if not user.has_perm("booking:read_all"):
        q = q.filter(
            Beach.owner_id == user.id
        )

    return q



# ───────────────────────────────
# SUMMARY
# ───────────────────────────────

@dashboard_bp.route("/summary", methods=["GET"])
@require_perm("dashboard:read")
def dashboard_summary():
    user = _current_user()
    now = now_utc()

    bookings_q = _scoped_bookings_query(user)
    sunbeds_q = _scoped_sunbeds_query(user)
    beaches_q = _scoped_beaches_query(user)

    # ───────────────────────────────
    # TODAY RANGE (MSK → UTC)
    # ───────────────────────────────
    now_msk = to_msk(now)
    today_start_msk = now_msk.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_start_utc = to_utc(today_start_msk)

    # ───────────────────────────────
    # REVENUE (ONLY COMPLETED + PAID)
    # ───────────────────────────────
    completed_paid = bookings_q.filter(
        Booking.status == "completed",
        Booking.payment_status == "paid",
    )

    revenue_today = sum(
        b.total_price
        for b in completed_paid.filter(
            Booking.updated_at >= today_start_utc
        )
    )

    return jsonify({
        "active_bookings": bookings_q.filter(
            Booking.status == "confirmed"
        ).count(),

        "problematic_bookings": bookings_q.filter(
            Booking.status == "confirmed",
            Booking.end_time < now,
            Booking.lock_closed_confirmed.is_(False)
        ).count(),

        "beaches_total": beaches_q.count(),
        "sunbeds_total": sunbeds_q.count(),

        # 💰 NEW
        "revenue_today": float(revenue_today),
    }), 200



# ───────────────────────────────
# BOOKINGS
# ───────────────────────────────

@dashboard_bp.route("/bookings/active", methods=["GET"])
@require_perm("booking:read")
def active_bookings():
    user = _current_user()

    bookings = (
        _scoped_bookings_query(user)
        .filter(Booking.status == "confirmed")
        .order_by(Booking.end_time)
        .all()
    )

    return jsonify({
        "bookings": [
            {
                "id": b.id,
                "sunbed_id": b.sunbed_id,
                "end_time": to_msk(b.end_time).isoformat(),
                "user_requested_close": b.user_requested_close,
                "lock_closed_confirmed": b.lock_closed_confirmed,
            }
            for b in bookings
        ]
    }), 200


@dashboard_bp.route("/bookings/problematic", methods=["GET"])
@require_perm("booking:read")
def problematic_bookings():
    user = _current_user()
    now = now_utc()

    bookings = (
        _scoped_bookings_query(user)
        .filter(
            Booking.status == "confirmed",
            Booking.end_time < now,
            Booking.lock_closed_confirmed.is_(False),
        )
        .order_by(Booking.end_time)
        .all()
    )

    return jsonify({
        "problematic": [
            {
                "id": b.id,
                "sunbed_id": b.sunbed_id,
                "end_time": to_msk(b.end_time).isoformat(),
                "user_requested_close": b.user_requested_close,
            }
            for b in bookings
        ]
    }), 200


@dashboard_bp.route("/bookings/<int:booking_id>/force-close", methods=["POST"])
@require_perm("booking:force_close")
def force_close(booking_id: int):
    user = _current_user()

    booking = Booking.query.get_or_404(booking_id)
    sunbed = Sunbed.query.get_or_404(booking.sunbed_id)

    if not user.has_perm("booking:read_all"):
        beach = Beach.query.get(sunbed.beach_id)
        if not beach or beach.owner_id != user.id:
            return jsonify({"error": "Access denied"}), 403

    if booking.status == "completed":
        return jsonify({
            "status": "already_completed",
            "booking_id": booking.id,
        }), 200

    try:
        completed = try_complete_booking(
            booking,
            require_user_request=False,
            force=True,
        )

        if not completed:
            db.session.rollback()
            return jsonify({"error": "Booking cannot be completed"}), 409

        db.session.commit()

        return jsonify({
            "status": "completed",
            "booking_id": booking.id,
        }), 200


    except BookingServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409

    except Exception as e:
        db.session.rollback()
        # 🔥 ВАЖНО: логируем причину
        current_app.logger.exception("Force close failed")
        return jsonify({"error": "Force close failed"}), 500




# ───────────────────────────────
# SUNBEDS / TTLOCK
# ───────────────────────────────

@dashboard_bp.route("/sunbeds/<int:sunbed_id>/lock-status", methods=["GET"])
@require_perm("sunbed:read")
def get_lock_status(sunbed_id: int):
    user = _current_user()
    sunbed = Sunbed.query.get_or_404(sunbed_id)

    if not user.has_perm("booking:read_all"):
        beach = Beach.query.get(sunbed.beach_id)
        if not beach or beach.owner_id != user.id:
            return jsonify({"error": "Access denied"}), 403

    if not sunbed.has_lock or not sunbed.lock_identifier:
        return jsonify({"error": "No lock configured for this sunbed"}), 400

    try:
        status = TTLockService().query_status(
            lock_id=int(sunbed.lock_identifier)
        )
    except TTLockError as e:
        return jsonify({
            "error": "Failed to query lock status",
            "details": str(e),
        }), 502

    return jsonify({
        "sunbed_id": sunbed.id,
        "lock_identifier": sunbed.lock_identifier,
        "locked": status.get("locked"),
        "lock_status_raw": status.get("raw"),
    }), 200


@dashboard_bp.route("/sunbeds/<int:sunbed_id>/lock-records", methods=["GET"])
@require_perm("sunbed:read")
def get_lock_records(sunbed_id: int):
    user = _current_user()
    sunbed = Sunbed.query.get_or_404(sunbed_id)

    if not user.has_perm("booking:read_all"):
        beach = Beach.query.get(sunbed.beach_id)
        if not beach or beach.owner_id != user.id:
            return jsonify({"error": "Access denied"}), 403

    if not sunbed.has_lock or not sunbed.lock_identifier:
        return jsonify({"error": "No lock configured for this sunbed"}), 400

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)

    try:
        records = TTLockService().get_lock_records(
            lock_id=int(sunbed.lock_identifier),
            page=page,
            page_size=page_size,
        )
    except TTLockError as e:
        return jsonify({
            "error": "Failed to fetch lock records",
            "details": str(e),
        }), 502

    return jsonify({
        "sunbed_id": sunbed.id,
        "lock_identifier": sunbed.lock_identifier,
        "page": page,
        "page_size": page_size,
        "records": records,
    }), 200


@dashboard_bp.route("/sunbeds/<int:sunbed_id>/remote-unlock", methods=["POST"])
@require_perm("sunbed:remote_unlock")
def remote_unlock(sunbed_id: int):
    user = _current_user()
    sunbed = Sunbed.query.get_or_404(sunbed_id)

    if not user.has_perm("booking:read_all"):
        beach = Beach.query.get(sunbed.beach_id)
        if not beach or beach.owner_id != user.id:
            return jsonify({"error": "Access denied"}), 403

    if not sunbed.has_lock or not sunbed.lock_identifier:
        return jsonify({"error": "No lock configured for this sunbed"}), 400

    try:
        TTLockService().remote_unlock(
            lock_id=int(sunbed.lock_identifier)
        )
    except TTLockError as e:
        return jsonify({
            "error": "Failed to unlock",
            "details": str(e),
        }), 502

    return jsonify({
        "message": "Unlock command sent",
        "sunbed_id": sunbed.id,
    }), 200


# ───────────────────────────────
# FINANCE
# ───────────────────────────────

@dashboard_bp.route("/finance/summary", methods=["GET"])
@require_perm("payout:read")
def finance_summary():
    user = _current_user()
    now = now_utc()
    # 1️⃣ берём "сейчас" в MSK
    now_msk = to_msk(now)

    # 2️⃣ начало дня в MSK
    today_start_msk = now_msk.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # 3️⃣ переводим обратно в UTC для БД
    today_start_utc = to_utc(today_start_msk)

    q = _scoped_bookings_query(user)

    completed_paid = q.filter(
        Booking.status == "completed",
        Booking.payment_status == "paid",
    )

    active_paid = q.filter(
        Booking.status == "confirmed",
        Booking.payment_status == "paid",
    )

    total_earned = sum(b.total_price for b in completed_paid)
    earned_today = sum(
        b.total_price
        for b in completed_paid.filter(
            Booking.updated_at >= today_start_utc
        )
    )
    active_holding = sum(b.total_price for b in active_paid)

    return jsonify({
        "total_earned": float(total_earned),
        "earned_today": float(earned_today),
        "active_holding": float(active_holding),
        "completed_count": completed_paid.count(),
    }), 200


@dashboard_bp.route("/finance/bookings", methods=["GET"])
@require_perm("payout:read")
def finance_bookings():
    user = _current_user()

    bookings = (
        _scoped_bookings_query(user)
        .filter(Booking.payment_status == "paid")
        .order_by(Booking.updated_at.desc())
        .limit(200)
        .all()
    )

    return jsonify({
        "count": len(bookings),
        "bookings": [
            {
                "booking_id": b.id,
                "sunbed_id": b.sunbed_id,
                "status": b.status,
                "payment_status": b.payment_status,
                "total_price": float(b.total_price),
                "start_time": to_msk(b.start_time).isoformat(),
                "end_time": to_msk(b.end_time).isoformat(),
            }
            for b in bookings
        ],
    }), 200
