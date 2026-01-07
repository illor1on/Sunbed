import redis

redis_client = None


def init_redis(app):
    """
    Инициализация Redis.
    Redis опционален: если REDIS_URL не задан — просто отключаем redis_client.
    """
    global redis_client

    redis_url = app.config.get("REDIS_URL")
    if not redis_url:
        redis_client = None
        app.logger.warning("REDIS_URL not set, Redis disabled")
        return

    try:
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True
        )
        # тестовое обращение
        redis_client.ping()
        app.logger.info("Redis connected")
    except Exception as e:
        redis_client = None
        app.logger.error(f"Redis connection failed: {e}")
