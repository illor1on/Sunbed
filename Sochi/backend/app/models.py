from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app import db
from app.permissions import permissions_for_role
from app.utils.time import now_utc
import secrets


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        index=True
    )

    description = db.Column(db.String(200))

    users = db.relationship("User", backref="role", lazy=True)

    __table_args__ = (
        CheckConstraint(
            "name IN ('user', 'owner', 'admin')",
            name="check_role_name"
        ),
    )



class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False, index=True)

    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc
    )

    __table_args__ = (
        Index("idx_user_phone", "phone_number"),
        Index("idx_user_role", "role_id"),
    )

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


    def has_perm(self, perm: str) -> bool:
        """
        Проверка permission для пользователя.
        Используется во всех сервисах / dashboard / routes.
        """
        role_name = None

        if hasattr(self, "role") and self.role:
            role_name = self.role.name
        else:
            # fallback, если relationship не загружен
            from app.models import Role
            role = Role.query.get(self.role_id)
            role_name = role.name if role else "user"

        return perm in permissions_for_role(role_name)

    @property
    def permissions(self) -> list[str]:
        """
        Список permissions пользователя (для /me, dashboard, frontend)
        """
        role_name = self.role.name if self.role else "user"
        return sorted(list(permissions_for_role(role_name)))


    def to_dict(self):
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "name": self.name,
            "role_id": self.role_id,
            "role": self.role.name if self.role else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OwnerLegalInfo(db.Model):
    __tablename__ = "owner_legal_info"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)

    legal_type = db.Column(db.String(10), nullable=False)  # IP | OOO
    legal_name = db.Column(db.String(255), nullable=False)
    inn = db.Column(db.String(12), nullable=False)
    address = db.Column(db.String(255), nullable=False)

    # OOO
    ogrn = db.Column(db.String(15))
    kpp = db.Column(db.String(9))
    director_name = db.Column(db.String(255))

    # IP
    ogrnip = db.Column(db.String(15))

    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc
    )

    __table_args__ = (
        CheckConstraint("legal_type IN ('IP','OOO')", name="check_legal_type"),
        Index("idx_owner_legal_user", "user_id"),
    )

    def to_dict(self):
        return {
            "legal_type": self.legal_type,
            "legal_name": self.legal_name,
            "inn": self.inn,
            "address": self.address,
            "ogrn": self.ogrn,
            "kpp": self.kpp,
            "director_name": self.director_name,
            "ogrnip": self.ogrnip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OwnerPaymentAccount(db.Model):
    __tablename__ = "owner_payment_accounts"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    provider = db.Column(db.String(50), nullable=False, index=True)
    shop_id = db.Column(db.String(100), nullable=False)

    secret_key = db.Column(db.String(255), nullable=False)
    webhook_token = db.Column(db.String(128), nullable=False, unique=True, index=True)

    is_active = db.Column(db.Boolean, default=True, index=True)

    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    @staticmethod
    def generate_webhook_token():
        return secrets.token_urlsafe(32)

    def rotate_webhook_token(self):
        self.webhook_token = self.generate_webhook_token()

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "provider": self.provider,
            "shop_id": self.shop_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    location_region = db.Column(db.String(100), index=True)
    location_city = db.Column(db.String(100), index=True)
    location_address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Numeric(9, 6))
    longitude = db.Column(db.Numeric(9, 6))

    image_url = db.Column(db.String(255))

    beaches = db.relationship("Beach", backref="location", lazy=True)

    __table_args__ = (Index("idx_location_city_region", "location_city", "location_region"),)

    def to_dict(self):
        return {
            "id": self.id,
            "region": self.location_region,
            "city": self.location_city,
            "address": self.location_address,
            "image_url": self.image_url,
            "coordinates": {
                "latitude": float(self.latitude) if self.latitude is not None else None,
                "longitude": float(self.longitude) if self.longitude is not None else None,
            },
        }


class Beach(db.Model):
    __tablename__ = "beaches"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    description = db.Column(db.Text)
    amenities = db.Column(JSONB, default=list)
    count_of_sunbeds = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    owner_hidden = db.Column(db.Boolean, server_default="false", nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc
    )

    owner = db.relationship("User", foreign_keys=[owner_id])
    sunbeds = db.relationship("Sunbed", backref="beach", lazy=True)

    image_url = db.Column(db.String(255))

    __table_args__ = (
        Index("idx_beach_owner", "owner_id"),
        Index("idx_beach_location", "location_id"),
        CheckConstraint("count_of_sunbeds >= 0", name="check_sunbeds_count"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "location_id": self.location_id,
            "description": self.description,
            "amenities": self.amenities or [],
            "count_of_sunbeds": self.count_of_sunbeds,
            "is_active": self.is_active,
            "owner_hidden": self.owner_hidden,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "location": self.location.to_dict() if self.location else None,
            "image_url": self.image_url,
        }


class Price(db.Model):
    __tablename__ = "prices"

    id = db.Column(db.Integer, primary_key=True)

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    price_per_hour = db.Column(db.Numeric(10, 2), nullable=False)
    price_per_day = db.Column(db.Numeric(10, 2))

    currency = db.Column(db.String(3), default="RUB")

    is_active = db.Column(db.Boolean, default=True)

    valid_from = db.Column(
        db.DateTime(timezone=True),
        default=now_utc,
        index=True
    )
    valid_to = db.Column(db.DateTime(timezone=True))

    owner = db.relationship("User", foreign_keys=[owner_id])

    __table_args__ = (
        CheckConstraint("price_per_hour >= 0", name="check_price_hour"),
        CheckConstraint("price_per_day >= 0", name="check_price_day"),
        Index("idx_price_owner", "owner_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "price_per_hour": float(self.price_per_hour) if self.price_per_hour is not None else None,
            "price_per_day": float(self.price_per_day) if self.price_per_day is not None else None,
            "currency": self.currency,
            "is_active": self.is_active,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
        }


class Sunbed(db.Model):
    __tablename__ = "sunbeds"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    beach_id = db.Column(
        db.Integer,
        db.ForeignKey("beaches.id"),
        nullable=False,
        index=True
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.id")
    )

    price_id = db.Column(
        db.Integer,
        db.ForeignKey("prices.id"),
        nullable=False
    )

    # ⚠️ ОПЕРАЦИОННЫЙ СТАТУС (НЕ ИСТОЧНИК ИСТИНЫ)
    # available   — можно сдавать
    # booked      — есть активная confirmed бронь (кэш)
    # maintenance — отключён владельцем
    status = db.Column(
        db.String(20),
        default="available",
        index=True
    )

    # TTLock
    has_lock = db.Column(db.Boolean, default=False)
    lock_identifier = db.Column(
        db.String(100),
        unique=True,
        index=True
    )  # TTLock lockId

    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc
    )

    price = db.relationship("Price", foreign_keys=[price_id])
    location = db.relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_sunbed_beach_status", "beach_id", "status"),
        Index("idx_sunbed_lock", "lock_identifier"),
        CheckConstraint(
            "status IN ('available','booked','maintenance')",
            name="check_sunbed_status"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "beach_id": self.beach_id,
            "location_id": self.location_id,
            "price_id": self.price_id,
            "status": self.status,
            "has_lock": self.has_lock,
            "lock_identifier": self.lock_identifier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Booking(db.Model):
    __tablename__ = "bookings"

    # ───────────────────────────────
    # PRIMARY KEY
    # ───────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ───────────────────────────────
    # RELATIONS (CORE)
    # ───────────────────────────────
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    sunbed_id = db.Column(
        db.Integer,
        db.ForeignKey("sunbeds.id"),
        nullable=False,
        index=True
    )

    # Владелец кассы, через которую прошла оплата
    # nullable — для старых броней
    payment_account_id = db.Column(
        db.Integer,
        db.ForeignKey("owner_payment_accounts.id"),
        index=True
    )

    # ───────────────────────────────
    # TIME WINDOW
    # ───────────────────────────────
    start_time = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True
    )

    end_time = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True
    )

    # ───────────────────────────────
    # PRICING
    # ───────────────────────────────
    total_price = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    # ───────────────────────────────
    # PAYMENT METHOD (AUTOPAY)
    # ───────────────────────────────
    payment_method_id = db.Column(
        db.Integer,
        db.ForeignKey("user_payment_methods.id"),
        index=True
    )

    # ───────────────────────────────
    # BOOKING LIFECYCLE (SOURCE OF TRUTH)
    #
    # pending     — создана, ждём оплату
    # confirmed   — оплачена, активна
    # completed   — корректно завершена (AND-close)
    # cancelled   — отменена (TTL / вручную)
    # ───────────────────────────────
    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
        index=True
    )

    # ───────────────────────────────
    # PAYMENT STATUS (TECHNICAL)
    #
    # pending            — платёж создан
    # paid               — подтверждён
    # failed             — не оплачен
    # refund_pending     — возврат запрошен
    # refunded           — возвращён
    # requires_payment   — автосписание невозможно
    # ───────────────────────────────
    payment_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
        index=True
    )

    # ───────────────────────────────
    # PAYMENT PROVIDER META
    # ───────────────────────────────
    payment_id = db.Column(db.String(100), index=True)
    payment_provider = db.Column(db.String(50))  # "yookassa", "stripe", ...

    # ───────────────────────────────
    # TTLOCK ACCESS
    # ───────────────────────────────
    access_code = db.Column(db.String(10))
    access_code_valid_from = db.Column(db.DateTime(timezone=True))
    access_code_valid_to = db.Column(db.DateTime(timezone=True))
    ttlock_password_id = db.Column(db.String(50), index=True)

    # ───────────────────────────────
    # AND-CLOSE FLOW
    # ───────────────────────────────
    user_requested_close = db.Column(db.Boolean, default=False)
    user_requested_close_at = db.Column(db.DateTime(timezone=True))

    lock_closed_confirmed = db.Column(db.Boolean, default=False)
    lock_closed_confirmed_at = db.Column(db.DateTime(timezone=True))

    # служебное (НЕ источник истины)
    last_overdue_charge_at = db.Column(db.DateTime(timezone=True))

    # ───────────────────────────────
    # SERVICE FLAGS
    # ───────────────────────────────
    reminder_sent = db.Column(db.Boolean, default=False)

    # ───────────────────────────────
    # META
    # ───────────────────────────────
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=now_utc
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc
    )

    # ───────────────────────────────
    # ORM RELATIONSHIPS
    # ───────────────────────────────
    user = db.relationship("User", foreign_keys=[user_id])
    sunbed = db.relationship("Sunbed", foreign_keys=[sunbed_id])

    payment_account = db.relationship(
        "OwnerPaymentAccount",
        foreign_keys=[payment_account_id]
    )

    payment_method = db.relationship(
        "UserPaymentMethod",
        foreign_keys=[payment_method_id]
    )

    # ───────────────────────────────
    # OVERDUE HELPERS (НЕ SOURCE OF TRUTH)
    # ───────────────────────────────
    overdue_hours = db.Column(db.Integer, default=0)

    # ───────────────────────────────
    # AUTOPAY COMPUTED FLAGS
    # ───────────────────────────────
    @property
    def autopay_available(self) -> bool:
        if self.status != "confirmed":
            return False

        if not self.payment_account or not self.payment_account.is_active:
            return False

        pm = self.payment_method
        if not pm or not pm.is_active:
            return False

        if pm.provider != "yookassa":
            return False

        if not pm.external_id:
            return False

        return True

    @property
    def autopay_unavailable_reason(self) -> str | None:
        if self.status != "confirmed":
            return "booking_not_confirmed"

        if not self.payment_account:
            return "missing_payment_account"

        if not self.payment_account.is_active:
            return "payment_account_inactive"

        pm = self.payment_method
        if not pm:
            return "missing_payment_method"

        if not pm.is_active:
            return "payment_method_inactive"

        if pm.provider != "yookassa":
            return "unsupported_provider"

        if not pm.external_id:
            return "missing_external_id"

        return None

    # ───────────────────────────────
    # CONSTRAINTS / INDEXES
    # ───────────────────────────────
    __table_args__ = (
        Index("idx_booking_dates", "start_time", "end_time"),
        Index("idx_booking_user_status", "user_id", "status"),
        Index("idx_booking_sunbed_status", "sunbed_id", "status"),
        Index("idx_booking_payment_account", "payment_account_id"),

        CheckConstraint(
            "end_time > start_time",
            name="check_booking_dates"
        ),
        CheckConstraint(
            "total_price >= 0",
            name="check_booking_price"
        ),
        CheckConstraint(
            "status IN ('pending','confirmed','completed','cancelled')",
            name="check_booking_status"
        ),
        CheckConstraint(
            "payment_status IN ("
            "'pending',"
            "'paid',"
            "'failed',"
            "'refund_pending',"
            "'refunded',"
            "'requires_payment'"
            ")",
            name="check_booking_payment_status"
        ),
    )

    # ───────────────────────────────
    # SERIALIZATION
    # ───────────────────────────────
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "sunbed_id": self.sunbed_id,
            "payment_account_id": self.payment_account_id,

            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,

            "total_price": float(self.total_price) if self.total_price is not None else None,

            "status": self.status,
            "payment_status": self.payment_status,
            "payment_id": self.payment_id,
            "payment_provider": self.payment_provider,

            "has_access_code": bool(self.access_code),
            "user_requested_close": self.user_requested_close,
            "lock_closed_confirmed": self.lock_closed_confirmed,
            "reminder_sent": self.reminder_sent,

            "autopay_available": self.autopay_available,
            "autopay_unavailable_reason": self.autopay_unavailable_reason,

            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


from datetime import datetime

class OverdueCharge(db.Model):
    __tablename__ = "overdue_charges"

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id"),
        nullable=False,
        index=True
    )

    hours = db.Column(db.Integer, nullable=False, default=1)

    amount = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    # YooKassa payment id
    payment_id = db.Column(
        db.String(100),
        unique=True,
        index=True
    )

    # pending | paid | refund_pending | refunded | requires_payment
    payment_status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
        index=True
    )

    refund_id = db.Column(
        db.String(100),
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=now_utc,
        nullable=False
    )

    paid_at = db.Column(db.DateTime(timezone=True))
    refunded_at = db.Column(db.DateTime(timezone=True))

    booking = db.relationship(
        "Booking",
        backref=db.backref("overdue_charges", lazy=True)
    )

    __table_args__ = (
        CheckConstraint(
            "payment_status IN ("
            "'pending',"
            "'paid',"
            "'refund_pending',"
            "'refunded',"
            "'requires_payment'"
            ")",
            name="check_overdue_payment_status"
        ),
    )


# app/models.py

class UserPaymentMethod(db.Model):
    __tablename__ = "user_payment_methods"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    provider = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )  # "yookassa"

    external_id = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )  # payment_method_id from YooKassa

    card_last4 = db.Column(db.String(4))
    card_brand = db.Column(db.String(16))

    is_active = db.Column(db.Boolean, default=True, index=True)

    created_at = db.Column(db.DateTime(timezone=True), default=now_utc)

    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint(
            "provider",
            "external_id",
            name="uq_user_payment_method_external"
        ),
    )
