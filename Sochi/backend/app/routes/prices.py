from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import Price, User, Sunbed
from app.authz import require_perm
from .utils import paginate, format_pagination, legal_required

prices_bp = Blueprint("prices", __name__)


def _current_user() -> User:
    current = get_jwt_identity()
    return User.query.get(current["id"])


# -------------------------------------------------
# CREATE
# -------------------------------------------------
@prices_bp.route("/", methods=["POST"])
@require_perm("price:write")
@legal_required
def create_price():
    user = _current_user()
    data = request.get_json() or {}

    if data.get("price_per_hour") is None:
        return jsonify({"error": "price_per_hour is required"}), 400

    price = Price(
        owner_id=user.id,
        price_per_hour=data["price_per_hour"],
        price_per_day=data.get("price_per_day"),
        currency=data.get("currency", "RUB"),
        is_active=bool(data.get("is_active", True)),
    )

    db.session.add(price)
    db.session.commit()

    return jsonify({
        "message": "Price created",
        "price": price.to_dict()
    }), 201


# -------------------------------------------------
# LIST
# -------------------------------------------------
@prices_bp.route("", methods=["GET"])
@prices_bp.route("/", methods=["GET"])
@require_perm("price:read")
def list_prices():
    user = _current_user()

    q = Price.query
    if not user.has_perm("price:read_all"):
        q = q.filter(Price.owner_id == user.id)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = paginate(q.order_by(Price.id.desc()), page, per_page)
    return jsonify(format_pagination(pagination, "prices")), 200


# -------------------------------------------------
# GET SINGLE PRICE (EDIT FORM)
# -------------------------------------------------
@prices_bp.route("/<int:price_id>", methods=["GET"])
@require_perm("price:read")
def get_price(price_id: int):
    user = _current_user()
    price = Price.query.get_or_404(price_id)

    # owner видит только свои, admin — все
    if not user.has_perm("price:read_all") and price.owner_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify(price.to_dict()), 200


# -------------------------------------------------
# UPDATE
# -------------------------------------------------
@prices_bp.route("/<int:price_id>", methods=["PUT"])
@require_perm("price:write")
@legal_required
def update_price(price_id: int):
    user = _current_user()
    price = Price.query.get_or_404(price_id)

    if not user.has_perm("price:read_all") and price.owner_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}

    for field in (
        "price_per_hour",
        "price_per_day",
        "currency",
        "is_active",
        "valid_to",
    ):
        if field in data:
            setattr(price, field, data[field])

    db.session.commit()

    return jsonify({
        "message": "Price updated",
        "price": price.to_dict()
    }), 200


# -------------------------------------------------
# DELETE
# -------------------------------------------------
@prices_bp.route("/<int:price_id>", methods=["DELETE"])
@require_perm("price:write")
@legal_required
def delete_price(price_id: int):
    user = _current_user()
    price = Price.query.get_or_404(price_id)

    if not user.has_perm("price:read_all") and price.owner_id != user.id:
        return jsonify({"error": "Access denied"}), 403

    used = Sunbed.query.filter_by(price_id=price.id).first()
    if used:
        return jsonify({"error": "Price is in use"}), 400

    db.session.delete(price)
    db.session.commit()

    return jsonify({"message": "Price deleted"}), 200
