from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func

from app import db
from app.models import (
    User,
    Beach,
    Sunbed,
    Booking,
    OverdueCharge,
)
from app.authz import require_perm
from app.services.booking_service import try_complete_booking, BookingServiceError
from app.services.overdue_refund_service import refund_overdue_charge, OverdueRefundError
from app.utils.time import now_utc

admin_bp = Blueprint("admin", __name__)

# -------------------------------------------------
# USERS
# -------------------------------------------------
@admin_bp.route("/users", methods=["GET"])
@require_perm("users:read")
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


# -------------------------------------------------
# BEACHES
# -------------------------------------------------
@admin_bp.route("/beaches", methods=["GET"])
@require_perm("beach:write")
def admin_beaches():
    beaches = Beach.query.order_by(Beach.id.desc()).all()
    return jsonify({"beaches": [b.to_dict() for b in beaches]}), 200


@admin_bp.route("/beaches/<int:beach_id>/deactivate", methods=["POST"])
@require_perm("users:write")
def admin_deactivate_beach(beach_id: int):
    beach = Beach.query.get_or_404(beach_id)

    beach.is_active = False
    db.session.commit()

    return jsonify({
        "status": "deactivated",
        "beach_id": beach.id,
    }), 200


# -------------------------------------------------
# SUNBEDS
# -------------------------------------------------
@admin_bp.route("/sunbeds/<int:sunbed_id>/deactivate", methods=["POST"])
@require_perm("users:write")
def admin_deactivate_sunbed(sunbed_id: int):
    sunbed = Sunbed.query.get_or_404(sunbed_id)

    sunbed.status = "inactive"
    db.session.commit()

    return jsonify({
        "status": "deactivated",
        "sunbed_id": sunbed.id,
    }), 200


# -------------------------------------------------
# BOOKINGS
# -------------------------------------------------
@admin_bp.route("/bookings", methods=["GET"])
@require_perm("booking:read_all")
def admin_bookings():
    bookings = (
        Booking.query
        .order_by(Booking.created_at.desc())
        .limit(200)
        .all()
    )
    return jsonify({"bookings": [b.to_dict() for b in bookings]}), 200


@admin_bp.route("/bookings/<int:booking_id>/force-close", methods=["POST"])
@require_perm("booking:force_close")
def admin_force_close_booking(booking_id: int):
    booking = Booking.query.get_or_404(booking_id)

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
            return jsonify({
                "error": "Booking cannot be completed"
            }), 409

        db.session.commit()
        return jsonify({
            "status": "completed",
            "booking_id": booking.id,
        }), 200

    except BookingServiceError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Force close failed"}), 500


@admin_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@require_perm("booking:cancel_any")
def admin_cancel_booking(booking_id: int):
    booking = Booking.query.get_or_404(booking_id)

    if booking.status in ("completed", "cancelled"):
        return jsonify({
            "status": "already_final",
            "booking_id": booking.id,
        }), 200

    booking.status = "cancelled"
    booking.updated_at = now_utc()
    db.session.commit()

    return jsonify({
        "status": "cancelled",
        "booking_id": booking.id,
    }), 200


# -------------------------------------------------
# OVERDUE / REFUNDS
# -------------------------------------------------
@admin_bp.route("/overdue/<int:overdue_id>/refund", methods=["POST"])
@require_perm("booking:refund_overdue")
def admin_refund_overdue(overdue_id: int):
    overdue = OverdueCharge.query.get_or_404(overdue_id)

    try:
        refund_overdue_charge(overdue)
        return jsonify({
            "status": "refund_initiated",
            "overdue_id": overdue.id,
        }), 200
    except OverdueRefundError as e:
        return jsonify({
            "error": "Refund failed",
            "details": str(e),
        }), 400


# -------------------------------------------------
# PLATFORM STATS
# -------------------------------------------------
@admin_bp.route("/stats", methods=["GET"])
@require_perm("platform:stats")
def platform_stats():
    revenue = (
        db.session.query(func.sum(Booking.total_price))
        .filter(Booking.payment_status == "paid")
        .scalar()
        or 0
    )

    return jsonify({
        "users_total": User.query.count(),
        "beaches_total": Beach.query.count(),
        "sunbeds_total": Sunbed.query.count(),
        "bookings_total": Booking.query.count(),
        "revenue_total": float(revenue),
    }), 200
