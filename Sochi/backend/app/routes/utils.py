from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from app.models import User, OwnerLegalInfo


def get_current_user() -> User | None:
    """
    Лёгкий helper: достаёт текущего пользователя по JWT identity.
    НЕ делает никаких role/permission проверок.
    """
    current = get_jwt_identity()
    if not current:
        return None
    return User.query.get(current.get("id"))


def legal_required(f):
    """
    Требует заполненной юридической информации (OwnerLegalInfo).
    Админ (по permissions) может обходить это требование.

    Важно: jwt_required должен быть выше по стеку (или в require_perm),
    иначе get_jwt_identity() будет пустой.
    """
    @wraps(f)
    def w(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        # Admin bypass: используем permissions (не role.name)
        if user.has_perm("booking:read_all"):
            return f(*args, **kwargs)

        info = OwnerLegalInfo.query.filter_by(user_id=user.id).first()
        if not info:
            return jsonify({
                "error": "Legal information required",
                "message": "Fill legal info (IP/OOO) before using this feature"
            }), 403

        return f(*args, **kwargs)

    return w


def validate_json(*required_fields):
    def decorator(f):
        @wraps(f)
        def w(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "JSON data required"}), 400

            for field in required_fields:
                if field not in data or data[field] is None:
                    return jsonify({"error": f"{field} is required"}), 400

            return f(*args, **kwargs)

        return w

    return decorator


def paginate(query, page=1, per_page=20):
    return query.paginate(page=page, per_page=per_page, error_out=False)


def format_pagination(pagination, data_key="items"):
    return {
        data_key: [item.to_dict() for item in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }
