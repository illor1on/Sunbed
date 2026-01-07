from datetime import datetime
from app.permissions import permissions_for_role
from app.utils.time import now_utc

class DashboardService:
    @staticmethod
    def build(role: str, user_id: int, range_: str = "today") -> dict:
        perms = permissions_for_role(role)

        widgets = []

        # USER-база (есть у всех, включая owner/admin)
        if "booking:read_self" in perms:
            widgets.append({
                "key": "my_active_bookings",
                "type": "my_active_bookings",
                "title": "Мои бронирования",
                "data": {},  # заполним позже в шаге “данные”
            })

        if "booking:create" in perms:
            widgets.append({
                "key": "cta_book",
                "type": "cta",
                "title": "Забронировать лежак",
                "data": {"action": "navigate:/beaches"}
            })

        if "booking:read_self" in perms:
            widgets.append({
                "key": "my_history",
                "type": "my_booking_history",
                "title": "История бронирований",
                "data": {},
            })

        # OWNER-виджеты
        if "payout:read" in perms:
            widgets.append({
                "key": "owner_kpi",
                "type": "owner_kpi",
                "title": "Статистика",
                "data": {"range": range_},
            })

        # ADMIN-виджеты
        if "booking:read_all" in perms:
            widgets.append({
                "key": "admin_kpi",
                "type": "admin_kpi",
                "title": "Платформа",
                "data": {"range": range_},
            })

        return {
            "schema_version": 1,
            "role": role,
            "range": range_,
            "generated_at": now_utc().isoformat(),
            "widgets": widgets,
        }
