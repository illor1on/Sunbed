from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import re
from app import db
from app.models import User, Role
from app.permissions import permissions_for_role


auth_bp = Blueprint('auth', __name__)


def validate_phone(phone):
    """Валидация российского номера телефона"""
    pattern = r'^\+7\d{10}$|^8\d{10}$'
    return bool(re.match(pattern, phone))


def validate_password(password):
    """Валидация пароля"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, ""


@auth_bp.route("/register", methods=["POST"], strict_slashes=False)
def register():
    data = request.get_json() or {}

    email = data.get("email")
    phone_number = data.get("phone_number")
    name = data.get("name")
    password = data.get("password")
    role_name = "user"

    # ---- обязательные поля ----
    if not email or not phone_number or not name or not password:
        return jsonify({
            "error": "email, phone_number, name and password are required"
        }), 400

    # ---- валидация телефона ----
    if not validate_phone(phone_number):
        return jsonify({
            "error": "Invalid phone number format"
        }), 400

    # ---- уникальность ----
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    if User.query.filter_by(phone_number=phone_number).first():
        return jsonify({"error": "Phone number already registered"}), 409

    # ---- роль ----
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"error": "Invalid role"}), 400

    # ---- создание пользователя ----
    user = User(
        email=email,
        phone_number=phone_number,
        name=name,
        role=role
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User registered",
        "user": user.to_dict()
    }), 201



@auth_bp.route('/login', methods=['POST'])
def login():
    """Вход пользователя"""
    try:
        data = request.get_json()

        if not data or 'phone_number' not in data or 'password' not in data:
            return jsonify({'error': 'Phone number and password required'}), 400

        user = User.query.filter_by(phone_number=data['phone_number']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        role = Role.query.get(user.role_id)

        # Генерация токена
        access_token = create_access_token(
            identity={
                'id': user.id,
                'phone': user.phone_number,
                'role': role.name if role else 'customer',
                'name': user.name
            }
        )

        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'name': user.name,
                'role': role.name if role else 'customer'
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """Получение данных текущего пользователя"""
    try:
        """
            Возвращает данные текущего пользователя + role + permissions
            Используется фронтом для навигации и dashboard
            """
        current = get_jwt_identity()

        user = User.query.get(current["id"])
        if not user:
            return jsonify({"error": "User not found"}), 404

        role_obj = Role.query.get(user.role_id)
        role_name = role_obj.name if role_obj else "user"

        permissions = sorted(list(permissions_for_role(role_name)))

        return jsonify({
            "id": user.id,
            "phone_number": user.phone_number,
            "name": user.name,
            "role": role_name,
            "permissions": permissions,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to get user data'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Обновление access токена"""
    try:
        current_user = get_jwt_identity()

        user = User.query.get(current_user['id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        role = Role.query.get(user.role_id)

        new_access_token = create_access_token(
            identity={
                'id': user.id,
                'phone': user.phone_number,
                'role': role.name if role else 'customer',
                'name': user.name
            }
        )

        return jsonify({'access_token': new_access_token}), 200

    except Exception as e:
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/phone-check/<phone>', methods=['GET'])
def check_phone(phone):
    """Проверка доступности номера телефона"""
    try:
        if not validate_phone(phone):
            return jsonify({'available': False, 'message': 'Invalid phone format'}), 400

        existing = User.query.filter_by(phone_number=phone).first()

        return jsonify({
            'available': not bool(existing),
            'message': 'Phone already registered' if existing else 'Phone available'
        }), 200

    except Exception as e:
        return jsonify({'error': 'Phone check failed'}), 500


