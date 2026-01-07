# app/services/yookassa_service.py

import uuid
import requests
from typing import Optional
from flask import current_app

from app.models import OwnerPaymentAccount


# ============================================================
# ERRORS
# ============================================================

class YooKassaServiceError(Exception):
    pass


# ============================================================
# SERVICE (HTTP, NO SDK, MULTI-CASH SAFE)
# ============================================================

class YooKassaService:
    """
    YooKassa HTTP client (thread-safe, multi-cash safe).

    ❌ НЕ использует yookassa.Configuration
    ❌ НЕ имеет глобального состояния
    ✅ per-request Basic Auth
    ✅ Idempotence-Key на каждый запрос
    """

    BASE_URL = "https://api.yookassa.ru/v3"

    def __init__(self, *, payment_account: OwnerPaymentAccount):
        if not payment_account:
            raise YooKassaServiceError("payment_account is required")

        if payment_account.provider != "yookassa":
            raise YooKassaServiceError("Invalid payment provider")

        if not payment_account.is_active:
            raise YooKassaServiceError("Payment account is inactive")

        self.account = payment_account
        self.auth = (
            payment_account.shop_id,
            payment_account.secret_key,
        )

    # --------------------------------------------------------
    # INTERNAL
    # --------------------------------------------------------

    def _headers(self, *, idem_key: Optional[str] = None) -> dict:
        headers = {
            "Content-Type": "application/json",
        }
        if idem_key:
            headers["Idempotence-Key"] = idem_key
        return headers

    def _post(self, path: str, payload: dict) -> dict:
        idem_key = str(uuid.uuid4())

        try:
            resp = requests.post(
                f"{self.BASE_URL}{path}",
                json=payload,
                auth=self.auth,
                headers=self._headers(idem_key=idem_key),
                timeout=10,
            )
        except requests.RequestException as e:
            raise YooKassaServiceError(f"Network error: {e}") from e

        if not resp.ok:
            raise YooKassaServiceError(
                f"YooKassa error {resp.status_code}: {resp.text}"
            )

        return resp.json()

    def _get(self, path: str) -> dict:
        try:
            resp = requests.get(
                f"{self.BASE_URL}{path}",
                auth=self.auth,
                timeout=10,
            )
        except requests.RequestException as e:
            raise YooKassaServiceError(f"Network error: {e}") from e

        if not resp.ok:
            raise YooKassaServiceError(
                f"YooKassa error {resp.status_code}: {resp.text}"
            )

        return resp.json()

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    def create_payment(
        self,
        *,
        amount,
        description: str,
        metadata: dict,
        return_url: Optional[str] = None,
        save_payment_method: bool = False,
        payment_method_id: Optional[str] = None,
        capture: bool = True,
    ) -> dict:
        if amount is None:
            raise YooKassaServiceError("amount is required")

        meta = dict(metadata or {})
        meta.setdefault("payment_account_id", self.account.id)

        payload = {
            "amount": {
                "value": f"{float(amount):.2f}",
                "currency": "RUB",
            },
            "capture": bool(capture),
            "description": description,
            "metadata": meta,
        }

        # ───────────── AUTOPAY ─────────────
        if payment_method_id:
            payload["payment_method_id"] = payment_method_id

        # ───────────── FIRST PAYMENT (REDIRECT) ─────────────
        else:
            if not return_url:
                return_url = current_app.config.get(
                    "YOOKASSA_RETURN_URL",
                    "https://localhost:5173/profile",
                )

            payload["confirmation"] = {
                "type": "redirect",
                "return_url": return_url,
            }
            payload["save_payment_method"] = bool(save_payment_method)

        return self._post("/payments", payload)

    # --------------------------------------------------------
    # REFUNDS
    # --------------------------------------------------------

    def refund_payment(
        self,
        payment_id: str,
        *,
        metadata: dict,
    ) -> dict:
        if not payment_id:
            raise YooKassaServiceError("payment_id is required")

        if not metadata:
            raise YooKassaServiceError("metadata is required for refund")

        # 1️⃣ Получаем платёж, чтобы взять точную сумму
        payment = self._get(f"/payments/{payment_id}")

        amount = payment.get("amount")
        if not amount:
            raise YooKassaServiceError("Payment amount not found")

        payload = {
            "payment_id": payment_id,
            "amount": {
                "value": amount["value"],
                "currency": amount["currency"],
            },
            "metadata": metadata,
        }

        return self._post("/refunds", payload)
