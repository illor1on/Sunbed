from flask import Blueprint, request, jsonify

from app import db
from app.models import Location, Beach
from app.authz import require_perm

locations_bp = Blueprint("locations", __name__)


# -------------------------------------------------
# CREATE LOCATION (ADMIN)
# -------------------------------------------------
@locations_bp.route("/", methods=["POST"], strict_slashes=False)
@require_perm("location:write")
def create_location():
    data = request.get_json() or {}

    region = data.get("region")
    city = data.get("city")
    address = data.get("address")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not address:
        return jsonify({"error": "address is required"}), 400

    location = Location(
        location_region=region,
        location_city=city,
        location_address=address,
        latitude=latitude,
        longitude=longitude,
    )

    db.session.add(location)
    db.session.commit()

    return jsonify(location.to_dict()), 201


# -------------------------------------------------
# LIST LOCATIONS (PUBLIC)
# -------------------------------------------------
@locations_bp.route("/", methods=["GET"], strict_slashes=False)
def list_locations():
    locations = Location.query.order_by(
        Location.location_region,
        Location.location_city
    ).all()

    return jsonify([l.to_dict() for l in locations]), 200


# -------------------------------------------------
# UPDATE LOCATION (ADMIN)
# -------------------------------------------------
@locations_bp.route("/<int:location_id>", methods=["PUT"], strict_slashes=False)
@require_perm("location:write")
def update_location(location_id: int):
    location = Location.query.get_or_404(location_id)
    data = request.get_json() or {}

    if "region" in data:
        location.location_region = data["region"]

    if "city" in data:
        location.location_city = data["city"]

    if "address" in data:
        if not data["address"]:
            return jsonify({"error": "address cannot be empty"}), 400
        location.location_address = data["address"]

    if "latitude" in data:
        location.latitude = data["latitude"]

    if "longitude" in data:
        location.longitude = data["longitude"]

    db.session.commit()
    return jsonify(location.to_dict()), 200


# -------------------------------------------------
# DELETE LOCATION (ADMIN)
# -------------------------------------------------
@locations_bp.route("/<int:location_id>", methods=["DELETE"], strict_slashes=False)
@require_perm("location:write")
def delete_location(location_id: int):
    location = Location.query.get_or_404(location_id)

    # ❗ Инвариант: нельзя удалить город, если есть пляжи
    used = Beach.query.filter_by(location_id=location.id).first()
    if used:
        return jsonify({
            "error": "Location is in use",
            "details": "There are beaches linked to this location"
        }), 409

    db.session.delete(location)
    db.session.commit()

    return jsonify({"status": "deleted"}), 200
