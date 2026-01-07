from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import OwnerPaymentAccount
from app.authz import require_perm
from app.utils.time import now_utc

owner_payment_bp = Blueprint(
    "owner_payment_accounts",
    __name__
)

# ───────────────────────────────
# GET ACTIVE PAYMENT ACCOUNT
# ───────────────────────────────
@owner_payment_bp.route("/payment-account", methods=["GET"])
@require_perm("payout:read")
def get_active_payment_account():
    current = get_jwt_identity()
    owner_id = current["id"]

    account = (
        OwnerPaymentAccount.query
        .filter_by(
            owner_id=owner_id,
            is_active=True
        )
        .first()
    )

    if not account:
        return jsonify({"payment_account": None}), 200

    return jsonify(account.to_dict()), 200


# ───────────────────────────────
# CREATE / REPLACE PAYMENT ACCOUNT
# ───────────────────────────────
@owner_payment_bp.route("/payment-account", methods=["POST"])
@require_perm("payout:write")
def create_payment_account():
    current = get_jwt_identity()
    owner_id = current["id"]

    data = request.get_json() or {}

    provider = data.get("provider")
    shop_id = data.get("shop_id")
    secret_key = data.get("secret_key")

    if not all([provider, shop_id, secret_key]):
        return jsonify({"error": "Missing required fields"}), 400

    # ───────────────────────────────
    # DEACTIVATE OLD ACTIVE ACCOUNTS
    # ───────────────────────────────
    OwnerPaymentAccount.query.filter_by(
        owner_id=owner_id,
        provider=provider,
        is_active=True
    ).update({
        "is_active": False,
        "updated_at": now_utc()
    })

    # ───────────────────────────────
    # CREATE NEW ACCOUNT
    # webhook_token генерируем САМИ
    # ───────────────────────────────
    account = OwnerPaymentAccount(
        owner_id=owner_id,
        provider=provider,
        shop_id=shop_id,
        secret_key=secret_key,
        webhook_token=OwnerPaymentAccount.generate_webhook_token(),
        is_active=True,
    )

    db.session.add(account)
    db.session.commit()

    return jsonify(account.to_dict()), 201


# ───────────────────────────────
# UPDATE PAYMENT ACCOUNT
# ───────────────────────────────
@owner_payment_bp.route("/payment-account/<int:account_id>", methods=["PUT"])
@require_perm("payout:write")
def update_payment_account(account_id):
    current = get_jwt_identity()
    owner_id = current["id"]

    account = OwnerPaymentAccount.query.get_or_404(account_id)
    if account.owner_id != owner_id:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}

    if "shop_id" in data:
        account.shop_id = data["shop_id"]

    if "secret_key" in data:
        account.secret_key = data["secret_key"]

    account.updated_at = now_utc()
    db.session.commit()

    return jsonify(account.to_dict()), 200


# ───────────────────────────────
# ROTATE WEBHOOK TOKEN (IMPORTANT)
# ───────────────────────────────
@owner_payment_bp.route("/payment-account/<int:account_id>/rotate-webhook-token", methods=["POST"])
@require_perm("payout:write")
def rotate_webhook_token(account_id):
    current = get_jwt_identity()
    owner_id = current["id"]

    account = OwnerPaymentAccount.query.get_or_404(account_id)
    if account.owner_id != owner_id:
        return jsonify({"error": "Access denied"}), 403

    account.webhook_token = OwnerPaymentAccount.generate_webhook_token()
    account.updated_at = now_utc()
    db.session.commit()

    return jsonify({"status": "rotated"}), 200


# ───────────────────────────────
# GET WEBHOOK URL (OWNER ONLY)
# ───────────────────────────────
@owner_payment_bp.route("/payment-account/<int:account_id>/webhook", methods=["GET"])
@require_perm("payout:read")
def get_payment_account_webhook(account_id):
    current = get_jwt_identity()
    owner_id = current["id"]

    account = OwnerPaymentAccount.query.get_or_404(account_id)
    if account.owner_id != owner_id:
        return jsonify({"error": "Access denied"}), 403

    base = current_app.config.get("PUBLIC_API_BASE_URL")
    if not base:
        return jsonify({"error": "PUBLIC_API_BASE_URL not configured"}), 500

    return jsonify({
        "webhook_url": f"{base}/api/payments/yookassa/webhook?token={account.webhook_token}"
    }), 200


# ───────────────────────────────
# DEACTIVATE PAYMENT ACCOUNT
# ───────────────────────────────
@owner_payment_bp.route("/payment-account/<int:account_id>", methods=["DELETE"])
@require_perm("payout:write")
def deactivate_payment_account(account_id):
    current = get_jwt_identity()
    owner_id = current["id"]

    account = OwnerPaymentAccount.query.get_or_404(account_id)
    if account.owner_id != owner_id:
        return jsonify({"error": "Access denied"}), 403

    account.is_active = False
    account.updated_at = now_utc()
    db.session.commit()

    return jsonify({"status": "deactivated"}), 200


@owner_payment_bp.route("/payment-account/<int:account_id>/webhook-token", methods=["GET"])
@require_perm("payout:read")
def get_payment_account_webhook_token(account_id):
    current = get_jwt_identity()
    owner_id = current["id"]

    account = OwnerPaymentAccount.query.get_or_404(account_id)
    if account.owner_id != owner_id:
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"webhook_token": account.webhook_token}), 200

