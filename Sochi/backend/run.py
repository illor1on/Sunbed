import os
from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Sunbed Rental API с PostgreSQL")
    print("=" * 60)
    print(f"📊 База данных: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🌐 Режим: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"🐍 Python: {os.sys.version}")
    print("=" * 60)
    print("📚 Доступные маршруты:")
    print("  POST /api/auth/register - Регистрация")
    print("  POST /api/auth/login    - Вход")
    print("  GET  /api/beaches       - Список пляжей")
    print("=" * 60)

    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config['DEBUG']
    )
