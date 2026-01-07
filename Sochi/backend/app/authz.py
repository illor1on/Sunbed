from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User
from app.permissions import has_perm


def require_perm(perm: str):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current = get_jwt_identity()
            if not current or "id" not in current:
                return jsonify({"error": "unauthorized"}), 401

            user = User.query.get(current["id"])
            if not user:
                return jsonify({"error": "user_not_found"}), 401

            if not has_perm(user, perm):
                return jsonify({
                    "error": "forbidden",
                    "missing": perm
                }), 403

            return fn(*args, **kwargs)

        return wrapper
    return decorator
