import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
from app.extensions import init_redis
from app.config import Config


# Создаем экземпляры расширений
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()


def create_app(config_class=None):
    """
    Фабрика приложений Flask для PostgreSQL
    """
    # 1. Создаем приложение Flask
    app = Flask(__name__)

    # CORS
    CORS(
        app,
        origins=["http://localhost:5173"],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        supports_credentials=True,
    )

    """# 2. Загружаем конфигурацию
    if config_class is None:
        from .config import Config
        config_class = Config"""

    app.config.from_object(Config)

    # 3. Настраиваем логирование
    setup_logging(app)

    # 4. Инициализируем расширения
    initialize_extensions(app)

    # 5. Регистрируем обработчики ошибок
    register_error_handlers(app)

    # 6. Регистрируем маршруты
    register_blueprints(app)

    initialize_database(app)

    # 7. Создаем команды CLI
    register_commands(app)

    # 8. Проверяем подключение к базе данных
    check_database_connection(app)

    from app.tasks.booking_cleanup import cancel_expired_pending_bookings
    import os

    import os
    from apscheduler.schedulers.background import BackgroundScheduler

    def start_scheduler(app):
        # ❗ не запускать scheduler дважды при flask debug reload
        if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            return

        scheduler = BackgroundScheduler()

        # ---------- pending → cancelled ----------
        from app.tasks.booking_cleanup import cancel_expired_pending_bookings

        def cleanup_job():
            with app.app_context():
                cancel_expired_pending_bookings()

        scheduler.add_job(
            cleanup_job,
            trigger="interval",
            minutes=1,
            id="booking_cleanup"
        )

        # ---------- auto complete booking ----------
        from app.tasks.booking_autocomplete import auto_complete_bookings

        def autocomplete_job():
            with app.app_context():
                auto_complete_bookings()

        scheduler.add_job(
            autocomplete_job,
            trigger="interval",
            minutes=1,
            id="booking_autocomplete"
        )

        # ---------- overdue booking ----------
        from app.tasks.booking_overdue import process_overdue_bookings

        def overdue_job():
            with app.app_context():
                process_overdue_bookings()

        scheduler.add_job(
            overdue_job,
            "interval",
            minutes=1,
            id="booking_overdue"
        )

        # ---------- autorefund ----------#
        from app.services.overdue_autorefund_service import auto_refund_overdue_charges
        from app.config import AUTO_REFUND_CHECK_INTERVAL_SECONDS
        def autorefund_job():
            with app.app_context():
                auto_refund_overdue_charges()

        scheduler.add_job(
            autorefund_job,
            "interval",
            seconds=AUTO_REFUND_CHECK_INTERVAL_SECONDS,
            id="auto_refund_overdue",
            replace_existing=True
        )

        scheduler.start()

        # ❗ сохраняем ссылку, чтобы GC не убил scheduler
        app.scheduler = scheduler

    init_redis(app)
    start_scheduler(app)

    return app



def setup_logging(app):
    """Настройка логирования"""
    if app.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


def initialize_database(app):
    """Инициализация базы данных при старте"""
    with app.app_context():
        try:
            # Создаем таблицы, если их нет
            db.create_all()
            app.logger.info("✅ Таблицы базы данных проверены/созданы")

            # Создаем начальные роли, если их нет
            from app.models import Role
            initial_roles = ['admin', 'owner', 'user']

            created_count = 0
            for role_name in initial_roles:
                if not Role.query.filter_by(name=role_name).first():
                    role = Role(name=role_name, description=f'{role_name.capitalize()} role')
                    db.session.add(role)
                    created_count += 1

            if created_count > 0:
                db.session.commit()
                app.logger.info(f"✅ Создано {created_count} начальных ролей")
            else:
                app.logger.info("✅ Начальные роли уже существуют")

        except Exception as e:
            app.logger.error(f"❌ Ошибка инициализации БД: {e}")
            app.logger.error("Создайте таблицы вручную или проверьте подключение к БД")
            db.session.rollback()


def initialize_extensions(app):
    """Инициализация расширений Flask"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])

    # Дополнительная настройка JWT
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please login again'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': str(error)
        }), 401


def register_error_handlers(app):
    """Регистрация обработчиков ошибок"""

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        # В продакшене логируем ошибку, но не показываем клиенту
        app.logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        app.logger.error(f'Database Error: {error}')
        return jsonify({'error': 'Database error occurred'}), 500

    # app/__init__.py (часть регистрации Blueprint)

def register_blueprints(app):
    from app.routes import (
        auth_bp, beaches_bp, sunbeds_bp, bookings_bp,
        prices_bp, payments_bp, admin_bp, owner_legal_bp, dashboard_bp, locations_bp, owner_payment_bp
    )

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(beaches_bp, url_prefix="/api/beaches")
    app.register_blueprint(sunbeds_bp, url_prefix="/api/sunbeds")
    app.register_blueprint(bookings_bp, url_prefix="/api/bookings")
    app.register_blueprint(prices_bp, url_prefix="/api/prices")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")
    app.register_blueprint(owner_legal_bp, url_prefix="/api/owner/legal")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(locations_bp, url_prefix="/api/locations")
    app.register_blueprint(owner_payment_bp, url_prefix="/api/owner")


def register_commands(app):
    """Регистрация CLI команд"""

    @app.cli.command('init-db')
    def init_db():
        """Инициализация базы данных"""
        from app.models import Role
        db.create_all()

        # Создаем стандартные роли
        roles = ['admin', 'owner', 'user']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                role = Role(name=role_name)
                db.session.add(role)

        db.session.commit()
        print("✅ База данных инициализирована")

    @app.cli.command('create-admin')
    def create_admin():
        """Создание администратора"""
        from app.models import User, Role
        admin_role = Role.query.filter_by(name='admin').first()

        if not admin_role:
            print("❌ Роль admin не найдена. Сначала выполните init-db")
            return

        admin = User(
            phone_number='+79160000000',
            name='Администратор',
            role_id=admin_role.id
        )
        admin.set_password('admin123')

        db.session.add(admin)
        db.session.commit()
        print("✅ Администратор создан: +79160000000 / admin123")


def check_database_connection(app):
    """Проверка подключения к базе данных"""
    with app.app_context():
        try:
            # Для SQLAlchemy 2.0 нужно использовать text()
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            app.logger.info("✅ Подключение к базе данных успешно")
        except Exception as e:
            app.logger.error(f"❌ Ошибка подключения к базе данных: {e}")
            raise
