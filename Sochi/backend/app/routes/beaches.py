from os import abort

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import Beach, Location, Sunbed, Booking, User
from app.authz import require_perm
from .utils import legal_required, validate_json

beaches_bp = Blueprint("beaches", __name__)

# -------------------------------------------------
# PUBLIC
# -------------------------------------------------

def _current_user() -> User:
    current = get_jwt_identity()
    return User.query.get(current["id"])


@beaches_bp.route("/", methods=["GET"], strict_slashes=False)
def list_beaches():
    q = Beach.query.filter_by(owner_hidden=False)

    location_id = request.args.get("location_id", type=int)
    if location_id:
        q = q.filter(Beach.location_id == location_id)

    beaches = q.order_by(Beach.id.desc()).all()
    return jsonify([b.to_dict() for b in beaches]), 200


@beaches_bp.route("/<int:beach_id>", methods=["GET"], strict_slashes=False)
def get_beach(beach_id: int):
    beach = Beach.query.get_or_404(beach_id)

    # неактивные не показываем публично
    if not beach.is_active:
        return jsonify({"error": "Beach not found"}), 404

    return jsonify(beach.to_dict()), 200




# -------------------------------------------------
# OWNER / ADMIN
# -------------------------------------------------

@beaches_bp.route("/mine", methods=["GET"], strict_slashes=False)
@require_perm("beach:read")
def my_beaches():
    current = get_jwt_identity()

    beaches = (
        Beach.query
        .filter_by(owner_id=current["id"])
        .order_by(Beach.id.desc())
        .all()
    )
    return jsonify([b.to_dict() for b in beaches]), 200


@beaches_bp.route("/", methods=["POST"], strict_slashes=False)
@require_perm("beach:write")
@legal_required
@validate_json("name", "location_id")
def create_beach():
    current = get_jwt_identity()
    data = request.get_json()

    location = Location.query.get(data["location_id"])
    if not location:
        return jsonify({"error": "Location not found"}), 404

    beach = Beach(
        owner_id=current["id"],
        name=data["name"],
        location_id=data["location_id"],
        description=data.get("description"),
        amenities=data.get("amenities", []),
        is_active=True,
    )

    db.session.add(beach)
    db.session.commit()

    return jsonify({
        "message": "Beach created",
        "beach": beach.to_dict()
    }), 201


# -------------------------------------------------
# UPDATE BEACH (OWNER / ADMIN)
# -------------------------------------------------
@beaches_bp.route("/<int:beach_id>", methods=["PUT"], strict_slashes=False)
@require_perm("beach:write")
@legal_required
def update_beach(beach_id: int):
    current = get_jwt_identity()
    beach = Beach.query.get_or_404(beach_id)

    # owner может редактировать только свои пляжи
    if not beach.owner_id == current["id"]:
        # admin может всё
        from app.models import User
        user = User.query.get(current["id"])
        if not user or not user.has_perm("users:read"):
            return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}

    if "name" in data:
        if not data["name"]:
            return jsonify({"error": "name cannot be empty"}), 400
        beach.name = data["name"]

    if "description" in data:
        beach.description = data["description"]

    if "amenities" in data:
        if not isinstance(data["amenities"], list):
            return jsonify({"error": "amenities must be a list"}), 400
        beach.amenities = data["amenities"]

    if "is_active" in data:
        beach.is_active = bool(data["is_active"])

    db.session.commit()

    return jsonify({
        "message": "Beach updated",
        "beach": beach.to_dict()
    }), 200


# -------------------------------------------------
# DELETE BEACH (SOFT DELETE)
# -------------------------------------------------
@beaches_bp.route("/<int:beach_id>", methods=["DELETE"], strict_slashes=False)
@require_perm("beach:write")
@legal_required
def delete_beach(beach_id: int):
    current = get_jwt_identity()
    beach = Beach.query.get_or_404(beach_id)

    # owner может удалять только свои пляжи
    if not beach.owner_id == current["id"]:
        from app.models import User
        user = User.query.get(current["id"])
        if not user or not user.has_perm("users:read"):
            return jsonify({"error": "Access denied"}), 403

    # ❗ Инвариант: нельзя удалить, если есть бронирования
    has_bookings = (
        db.session.query(Booking.id)
        .join(Sunbed, Sunbed.id == Booking.sunbed_id)
        .filter(Sunbed.beach_id == beach.id)
        .first()
        is not None
    )

    if has_bookings:
        return jsonify({
            "error": "Beach has bookings",
            "details": "Beach cannot be deleted because it has bookings"
        }), 409

    # SOFT DELETE
    beach.is_active = False
    db.session.commit()

    return jsonify({
        "status": "deactivated",
        "beach_id": beach.id
    }), 200


@beaches_bp.route("/<int:beach_id>/sunbeds", methods=["GET"])
@require_perm("sunbed:read")
def get_beach_sunbeds(beach_id: int):
    user = _current_user()

    beach = Beach.query.get_or_404(beach_id)

    # owner → только свои пляжи
    if not user.has_perm("booking:read_all"):
        if beach.owner_id != user.id:
            return jsonify({"error": "Access denied"}), 403

    sunbeds = (
        Sunbed.query
        .filter(Sunbed.beach_id == beach.id)
        .order_by(Sunbed.id.desc())
        .all()
    )

    return jsonify({
        "beach_id": beach.id,
        "beach_name": beach.name,   # 👈 ДОБАВЛЕНО
        "sunbeds": [s.to_dict() for s in sunbeds],
    }), 200


@beaches_bp.route("/<int:beach_id>/owner-toggle", methods=["POST"])
@require_perm("beach:write")
def owner_toggle_beach(beach_id):
    current = get_jwt_identity()

    beach = Beach.query.get_or_404(beach_id)

    # owner может менять только свой пляж
    if beach.owner_id != current["id"]:
        abort(403)

    beach.owner_hidden = not beach.owner_hidden
    db.session.commit()

    return jsonify({
        "id": beach.id,
        "owner_hidden": beach.owner_hidden
    }), 200
