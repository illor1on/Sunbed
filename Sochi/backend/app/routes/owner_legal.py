from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import OwnerLegalInfo, User
from app.authz import require_perm

owner_legal_bp = Blueprint("owner_legal", __name__)


# ───────────────────────────────
# GET MY LEGAL INFO
# ───────────────────────────────

@owner_legal_bp.route("/", methods=["GET"])
@require_perm("payout:write")
def get_my_legal():
    current = get_jwt_identity()
    user = User.query.get(current["id"])

    info = OwnerLegalInfo.query.filter_by(user_id=user.id).first()
    return jsonify({
        "legal_info": info.to_dict() if info else None
    }), 200


# ───────────────────────────────
# UPSERT MY LEGAL INFO
# ───────────────────────────────

@owner_legal_bp.route("/", methods=["POST"])
@require_perm("payout:write")
def upsert_my_legal():
    current = get_jwt_identity()
    user = User.query.get(current["id"])

    data = request.get_json() or {}
    legal_type = data.get("legal_type")

    if legal_type not in ("IP", "OOO"):
        return jsonify({"error": "legal_type must be IP or OOO"}), 400

    for f in ("legal_name", "inn", "address"):
        if not data.get(f):
            return jsonify({"error": f"{f} is required"}), 400

    if legal_type == "IP" and not data.get("ogrnip"):
        return jsonify({"error": "ogrnip is required for IP"}), 400

    if legal_type == "OOO":
        for f in ("ogrn", "kpp", "director_name"):
            if not data.get(f):
                return jsonify({"error": f"{f} is required for OOO"}), 400

    info = OwnerLegalInfo.query.filter_by(user_id=user.id).first()
    if not info:
        info = OwnerLegalInfo(user_id=user.id)

    info.legal_type = legal_type
    info.legal_name = data["legal_name"]
    info.inn = data["inn"]
    info.address = data["address"]
    info.ogrnip = data.get("ogrnip")
    info.ogrn = data.get("ogrn")
    info.kpp = data.get("kpp")
    info.director_name = data.get("director_name")

    db.session.add(info)
    db.session.commit()

    return jsonify({
        "message": "Legal info saved",
        "legal_info": info.to_dict()
    }), 200
