import app.extensions as ext
from app.services.ttlock_service import TTLockService, TTLockError

LOCK_STATUS_TTL = 30  # секунд


class LockStatusError(Exception):
    pass


def get_lock_status(lock_id: int) -> dict:
    """
    Возвращает статус замка.
    Использует Redis как кэш, если он включён.
    """

    cache_key = f"lock:{lock_id}:status"

    # 1️⃣ пробуем Redis (если есть)
    if ext.redis_client:
        cached = ext.redis_client.get(cache_key)
        if cached:
            return {
                "locked": cached == "locked",
                "cached": True
            }

    # 2️⃣ дергаем TTLock
    try:
        status = TTLockService().query_status(lock_id=lock_id)
    except TTLockError as e:
        raise LockStatusError(str(e))

    # 3️⃣ сохраняем в Redis (если есть)
    if ext.redis_client:
        try:
            ext.redis_client.setex(
                cache_key,
                LOCK_STATUS_TTL,
                "locked" if status.get("locked") else "unlocked"
            )
        except Exception:
            pass  # Redis не должен ломать бизнес-логику

    status["cached"] = False
    return status
