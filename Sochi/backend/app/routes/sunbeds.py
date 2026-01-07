from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from datetime import timedelta

from app import db
from app.models import Sunbed, Price, Beach, Booking
from app.authz import require_perm
from app.utils.time import now_utc
from app.config import PENDING_TTL_MINUTES

sunbeds_bp = Blueprint("sunbeds", __name__)


# -------------------------------------------------
# helpers
# -------------------------------------------------

def _pending_is_active(created_at, now):
    cutoff = now - timedelta(minutes=PENDING_TTL_MINUTES)
    return created_at and created_at >= cutoff


# -------------------------------------------------
# PUBLIC: AVAILABLE SUNBEDS
# -------------------------------------------------
@sunbeds_bp.route("/available", methods=["GET"])
def get_available():
    beach_id = request.args.get("beach_id", type=int)
    if not beach_id:
        return jsonify({"error": "beach_id is required"}), 400

    now = now_utc()

    busy_confirmed = (
        db.session.query(Booking.sunbed_id)
        .filter(
            Booking.end_time > now,
            Booking.status == "confirmed",
        )
        .subquery()
    )

    pending = (
        Booking.query
        .with_entities(Booking.sunbed_id, Booking.created_at)
        .filter(
            Booking.status == "pending",
            Booking.payment_status == "pending",
            Booking.end_time > now,
        )
        .all()
    )

    active_pending_ids = [
        sid for (sid, created_at) in pending
        if _pending_is_active(created_at, now)
    ]

    q = Sunbed.query.filter(
        Sunbed.beach_id == beach_id,
        ~Sunbed.id.in_(busy_confirmed),
    )

    if active_pending_ids:
        q = q.filter(~Sunbed.id.in_(active_pending_ids))

    sunbeds = q.all()

    result = []
    for s in sunbeds:
        price = Price.query.get(s.price_id)
        if not price or not price.is_active:
            continue

        d = s.to_dict()
        d["price"] = price.to_dict()
        result.append(d)

    return jsonify({"sunbeds": result}), 200


# -------------------------------------------------
# CREATE SUNBED (OWNER / ADMIN)
# -------------------------------------------------
@sunbeds_bp.route("/", methods=["POST"], strict_slashes=False)
@require_perm("sunbed:write")
def create_sunbed():
    current = get_jwt_identity()
    data = request.get_json() or {}

    name = data.get("name")
    beach_id = data.get("beach_id")
    price_id = data.get("price_id")

    if not all([name, beach_id, price_id]):
        return jsonify({
            "error": "name, beach_id and price_id are required"
        }), 400

    beach = Beach.query.get_or_404(beach_id)

    # owner может работать только со своими пляжами
    if beach.owner_id != current["id"]:
        from app.models import User
        user = User.query.get(current["id"])
        if not user or not user.has_perm("beach:read_all"):
            return jsonify({"error": "Access denied"}), 403

    price = Price.query.get(price_id)
    if not price or not price.is_active:
        return jsonify({"error": "Invalid price"}), 400

    if price.owner_id != beach.owner_id:
        return jsonify({
            "error": "Price does not belong to this owner"
        }), 400

    sunbed = Sunbed(
        name=name,
        beach_id=beach.id,
        location_id=beach.location_id,
        price_id=price.id,
        status="available",
        has_lock=bool(data.get("has_lock", False)),
        lock_identifier=data.get("lock_identifier"),
    )

    db.session.add(sunbed)
    beach.count_of_sunbeds = (beach.count_of_sunbeds or 0) + 1
    db.session.commit()

    return jsonify({
        "message": "Sunbed created",
        "sunbed": sunbed.to_dict()
    }), 201


# -------------------------------------------------
# UPDATE SUNBED (OWNER / ADMIN)
# -------------------------------------------------
@sunbeds_bp.route("/<int:sunbed_id>", methods=["PUT"])
@require_perm("sunbed:write")
def update_sunbed(sunbed_id: int):
    current = get_jwt_identity()
    sunbed = Sunbed.query.get_or_404(sunbed_id)

    beach = Beach.query.get(sunbed.beach_id)
    if not beach or beach.owner_id != current["id"]:
        from app.models import User
        user = User.query.get(current["id"])
        if not user or not user.has_perm("beach:read_all"):
            return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}

    if "price_id" in data:
        price = Price.query.get(data["price_id"])
        if not price or not price.is_active:
            return jsonify({"error": "Invalid price_id"}), 400
        if price.owner_id != beach.owner_id:
            return jsonify({"error": "Price ownership mismatch"}), 400
        sunbed.price_id = price.id

    # 🔒 статус booked — только системой
    if "status" in data and data["status"] == "booked":
        return jsonify({"error": "status 'booked' is system-managed"}), 400

    # 🔒 нельзя менять lock_identifier, если есть активная бронь
    if "lock_identifier" in data:
        active_booking = (
            Booking.query
            .filter(
                Booking.sunbed_id == sunbed.id,
                Booking.status.in_(["confirmed", "pending"]),
            )
            .first()
        )
        if active_booking:
            return jsonify({
                "error": "Cannot change lock while booking is active"
            }), 409

    for field in ("name", "status", "has_lock", "lock_identifier"):
        if field in data:
            setattr(sunbed, field, data[field])

    db.session.commit()

    return jsonify({
        "message": "Sunbed updated",
        "sunbed": sunbed.to_dict()
    }), 200


# -------------------------------------------------
# DELETE SUNBED (SAFE DELETE)
# -------------------------------------------------
@sunbeds_bp.route("/<int:sunbed_id>", methods=["DELETE"])
@require_perm("sunbed:write")
def delete_sunbed(sunbed_id: int):
    current = get_jwt_identity()
    sunbed = Sunbed.query.get_or_404(sunbed_id)

    beach = Beach.query.get(sunbed.beach_id)
    if not beach or beach.owner_id != current["id"]:
        from app.models import User
        user = User.query.get(current["id"])
        if not user or not user.has_perm("beach:read_all"):
            return jsonify({"error": "Access denied"}), 403

    # ❗ Инвариант: нельзя удалить, если есть бронирования
    used = (
        Booking.query
        .filter(
            Booking.sunbed_id == sunbed.id,
            Booking.status != "cancelled",
        )
        .first()
    )

    if used:
        return jsonify({
            "error": "Sunbed has bookings",
            "details": "Sunbed cannot be deleted because it has bookings"
        }), 409

    db.session.delete(sunbed)

    if beach.count_of_sunbeds:
        beach.count_of_sunbeds -= 1

    db.session.commit()

    return jsonify({
        "status": "deleted",
        "sunbed_id": sunbed.id
    }), 200


