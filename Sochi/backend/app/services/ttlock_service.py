import time
import random
import requests
from flask import current_app
import app.extensions as ext


# ───────────────────────────────
# CONFIG
# ───────────────────────────────

TTLOCK_TIMEOUT = 5               # seconds
TTLOCK_MAX_RETRIES = 3
TTLOCK_BACKOFF = 1.5

TTLOCK_RATE_LIMIT = 20           # requests
TTLOCK_RATE_WINDOW = 60          # seconds

TTLOCK_CIRCUIT_KEY = "circuit:ttlock"
TTLOCK_CIRCUIT_TTL = 60          # seconds


# ───────────────────────────────
# ERRORS
# ───────────────────────────────

class TTLockError(Exception):
    pass


# ───────────────────────────────
# SERVICE
# ───────────────────────────────

class TTLockService:
    """
    TTLock Cloud API v3 + Gateway
    Safe version with:
      - timeout
      - retry + backoff
      - rate limit
      - circuit breaker
    """

    def __init__(self):
        self.client_id = current_app.config.get("TTLOCK_CLIENT_ID")
        self.access_token = current_app.config.get("TTLOCK_ACCESS_TOKEN")
        self.base_url = current_app.config.get(
            "TTLOCK_BASE_URL",
            "https://api.sciener.com"
        )

        if not self.client_id or not self.access_token:
            raise TTLockError("TTLock credentials are not configured")

    # ────────────────
    # helpers
    # ────────────────

    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def _generate_pin(self) -> str:
        return "".join(random.choice("0123456789") for _ in range(6))

    # ────────────────
    # core request
    # ────────────────

    def _request(self, method: str, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}{endpoint}"

        # ── circuit breaker
        if ext.redis_client and ext.redis_client.get(TTLOCK_CIRCUIT_KEY):
            raise TTLockError("TTLock circuit breaker is open")

        # ── rate limit
        if ext.redis_client:
            key = "ratelimit:ttlock"
            count = ext.redis_client.incr(key)
            if count == 1:
                ext.redis_client.expire(key, TTLOCK_RATE_WINDOW)
            if count > TTLOCK_RATE_LIMIT:
                raise TTLockError("TTLock rate limit exceeded")

        delay = 1

        for attempt in range(1, TTLOCK_MAX_RETRIES + 1):
            try:
                resp = requests.request(
                    method=method,
                    url=url,
                    data=payload,
                    timeout=TTLOCK_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("errcode") != 0:
                    raise TTLockError(
                        f"{data.get('errcode')}: {data.get('errmsg')}"
                    )

                return data

            except (requests.Timeout, requests.ConnectionError) as e:
                current_app.logger.warning(
                    f"TTLock timeout (attempt {attempt}/{TTLOCK_MAX_RETRIES})"
                )

                if attempt == TTLOCK_MAX_RETRIES:
                    if ext.redis_client:
                        ext.redis_client.setex(
                            TTLOCK_CIRCUIT_KEY,
                            TTLOCK_CIRCUIT_TTL,
                            "1"
                        )
                    raise TTLockError("TTLock unavailable") from e

                time.sleep(delay)
                delay *= TTLOCK_BACKOFF

    # ───────────────────────────────
    # PUBLIC API
    # ───────────────────────────────

    def create_pin(self, lock_id: int, start_time, end_time) -> dict:
        for _ in range(3):
            pin = self._generate_pin()

            payload = {
                "clientId": self.client_id,
                "accessToken": self.access_token,
                "lockId": int(lock_id),
                "keyboardPwd": pin,
                "keyboardPwdName": "booking",
                "startDate": int(start_time.timestamp() * 1000),
                "endDate": int(end_time.timestamp() * 1000),
                "addType": 2,
                "date": self._now_ms(),
            }

            data = self._request(
                "POST",
                "/v3/keyboardPwd/add",
                payload
            )

            # 10006 = PIN collision
            if data.get("errcode") == 10006:
                continue

            return {
                "pin": pin,
                "password_id": data.get("keyboardPwdId"),
            }

        raise TTLockError("Failed to generate unique PIN")

    def delete_pin(self, lock_id: int, password_id: str) -> bool:
        payload = {
            "clientId": self.client_id,
            "accessToken": self.access_token,
            "lockId": int(lock_id),
            "keyboardPwdId": password_id,
            "date": self._now_ms(),
        }

        self._request(
            "POST",
            "/v3/keyboardPwd/delete",
            payload
        )
        return True

    def query_status(self, lock_id: int) -> dict:
        payload = {
            "clientId": self.client_id,
            "accessToken": self.access_token,
            "lockId": int(lock_id),
            "date": self._now_ms(),
        }

        data = self._request(
            "POST",
            "/v3/lock/queryStatus",
            payload
        )

        lock_status = data.get("lockStatus")
        return {
            "raw": data,
            "lockStatus": lock_status,
            "locked": lock_status == 1,
        }

    def get_lock_records(self, lock_id: int, page: int = 1, page_size: int = 20) -> list:
        payload = {
            "clientId": self.client_id,
            "accessToken": self.access_token,
            "lockId": int(lock_id),
            "pageNo": int(page),
            "pageSize": int(page_size),
            "date": self._now_ms(),
        }

        data = self._request(
            "POST",
            "/v3/lockRecord/list",
            payload
        )
        return data.get("list", [])

    def remote_unlock(self, lock_id: int) -> bool:
        payload = {
            "clientId": self.client_id,
            "accessToken": self.access_token,
            "lockId": int(lock_id),
            "date": self._now_ms(),
        }

        self._request(
            "POST",
            "/v3/lock/unlock",
            payload
        )
        return True
