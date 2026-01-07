import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# ===============================
# GLOBAL SINGLETON CONSTANTS
# ===============================

PENDING_TTL_MINUTES = 15
OVERDUE_REFUND_GRACE_MINUTES = 5
AUTO_REFUND_CHECK_INTERVAL_SECONDS = 60

YOOKASSA_WEBHOOK_SECRET = "test_zych0DYaqUcZykzSFoQ1U-2S6yxwbBjPZmh_YD_I3Ro"


class Config:
    """
    ЕДИНСТВЕННАЯ конфигурация приложения.
    Используется как singleton.
    """

    # ---------- SECURITY ----------
    SECRET_KEY = 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = 'dev-jwt-secret-change-in-production'

    # ---------- DATABASE ----------
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'sunbed')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '1922')

    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # ---------- JWT ----------
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # ---------- APP ----------
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')

    # ---------- CORS ----------
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

    # ---------- API (оставляем как есть) ----------
    API_PREFIX = '/api'
    API_VERSION = 'v1'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # ---------- YOOKASSA ----------
    YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
    YOOKASSA_WEBHOOK_SECRET = os.getenv("YOOKASSA_WEBHOOK_SECRET") or YOOKASSA_WEBHOOK_SECRET
    YOOKASSA_RETURN_URL = os.getenv(
        "YOOKASSA_RETURN_URL",
        "http://localhost:5173/profile"
    )

    # ---------- TTLOCK ----------
    TTLOCK_CLIENT_ID = os.getenv("TTLOCK_CLIENT_ID")
    TTLOCK_ACCESS_TOKEN = os.getenv("TTLOCK_ACCESS_TOKEN")
    TTLOCK_BASE_URL = os.getenv(
        "TTLOCK_BASE_URL",
        "https://api.sciener.com"
    )

    # ---------- REDIS ----------
    REDIS_URL = os.getenv("REDIS_URL")
