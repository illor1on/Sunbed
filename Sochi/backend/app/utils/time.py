from datetime import datetime, timezone, timedelta

# UTC+3 (Москва)
MSK = timezone(timedelta(hours=3))

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def now_msk() -> datetime:
    return datetime.now(MSK)

def to_utc(dt: datetime) -> datetime:
    """
    Преобразует datetime в UTC.
    Если tzinfo отсутствует — считаем, что это MSK (фронт).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    return dt.astimezone(timezone.utc)

def to_msk(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MSK)
