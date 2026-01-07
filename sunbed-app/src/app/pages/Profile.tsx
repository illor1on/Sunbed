import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import BottomNav from "../components/BottomNav";
import { getMyActiveBooking, getMyBookingHistory } from "../api/bookings";
import type { ActiveBooking } from "../api/bookings";
import { api } from "../api/client";

type UserPaymentMethod = {
  id: number;
  provider: string;
  external_id: string;
  card_last4?: string | null;
  card_brand?: string | null; // payment_method_id from YooKassa (как в models.py)
  is_active: boolean;
  created_at?: string;
};

function maskExternalId(externalId: string) {
  if (!externalId) return "—";
  const tail = externalId.slice(-4);
  return `•••• ${tail}`;
}

export default function Profile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeBookings, setActiveBookings] = useState<ActiveBooking[]>([]);
  const [awaiting, setAwaiting] = useState(false);

  // количество прошлых бронирований
  const [historyCount, setHistoryCount] = useState<number>(0);

  // способы оплаты
  const [methods, setMethods] = useState<UserPaymentMethod[]>([]);
  const [methodsLoading, setMethodsLoading] = useState(false);
  const [methodsError, setMethodsError] = useState<string | null>(null);

  /* 1️⃣ Проверяем, вернулся ли пользователь с оплаты */
  useEffect(() => {
    if (sessionStorage.getItem("awaiting_booking") === "1") {
      setAwaiting(true);
      sessionStorage.removeItem("awaiting_booking");
    }
  }, []);

  /* 2️⃣ Загружаем активные аренды */
  useEffect(() => {
    getMyActiveBooking()
      .then((res) => setActiveBookings(res ?? []))
      .catch(() => setActiveBookings([]));
  }, []);

  /* 3️⃣ Загружаем историю бронирований (только счётчик) */
  useEffect(() => {
    getMyBookingHistory()
      .then((res) => {
        const items = res ?? [];
        setHistoryCount(items.length);
      })
      .catch(() => {
        setHistoryCount(0);
      });
  }, []);

  /* 4️⃣ Polling: пока ждём подтверждение оплаты */
  useEffect(() => {
    if (!awaiting) return;

    const load = async () => {
      try {
        const bookings = await getMyActiveBooking();
        setActiveBookings(bookings ?? []);

        // как только появилась активная аренда — закрываем popup
        if (bookings && bookings.length > 0) {
          setAwaiting(false);
        }
      } catch {
        // просто продолжаем ждать
      }
    };

    load();
    const interval = setInterval(load, 2000);
    return () => clearInterval(interval);
  }, [awaiting]);

  /* 5️⃣ Загружаем сохранённые способы оплаты */
  useEffect(() => {
    if (!user) return;

    const loadMethods = async () => {
      setMethodsLoading(true);
      setMethodsError(null);

      try {
        // ВАЖНО: этот эндпоинт нужно добавить на бэке (я ниже напишу где).
        const res = await api.get("/payments/me/payment-methods");
        const items = res.data?.items ?? [];
        setMethods(items);
      } catch (e: any) {
        setMethods([]);
        setMethodsError(
          e?.response?.data?.error ||
            "Не удалось загрузить способы оплаты"
        );
      } finally {
        setMethodsLoading(false);
      }
    };

    loadMethods();
  }, [user]);

  if (!user) return null;

  return (
    <>
      <div className="container profile-page">
        {/* USER */}
        <div className="profile-header">
          <div className="profile-name">{user.name}</div>
          <div className="profile-phone">{user.phone_number}</div>
        </div>

        {/* STATS */}
        <div className="profile-stats">
          <div
            className="profile-stat profile-stat--clickable"
            onClick={() => navigate("/active-bookings")}
          >
            <div className="stat-title">Активные аренды</div>
            <div className="stat-value">{activeBookings.length}</div>
          </div>

          <div
            className="profile-stat profile-stat--clickable"
            onClick={() => navigate("/booking-history")}
          >
            <div className="stat-title">История бронирований</div>
            <div className="stat-value">{historyCount}</div>
          </div>
        </div>

        {/* PAYMENT (ПЕРЕДЕЛАНО ПО ТВОИМ ТРЕБОВАНИЯМ) */}
        <div className="profile-card">
          <div
            style={{
              fontWeight: 700,
              fontSize: 16,
              marginBottom: 12,
            }}
          >
            Мои способы оплаты
          </div>

          {methodsLoading && (
            <div style={{ fontSize: 13, opacity: 0.7 }}>
              Загрузка…
            </div>
          )}

          {!methodsLoading && methodsError && (
            <div style={{ fontSize: 13, color: "#d84315", marginBottom: 8 }}>
              {methodsError}
            </div>
          )}

          {!methodsLoading && !methodsError && methods.length === 0 && (
            <div style={{ fontSize: 13, opacity: 0.7, marginBottom: 8 }}>
              Сохранённых карт нет
            </div>
          )}

          {!methodsLoading && methods.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {methods.map((m) => (
                <div
                  key={m.id}
                  style={{
                    padding: "10px 12px",
                    borderRadius: 12,
                    background: "rgba(0,0,0,0.04)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    fontSize: 14,
                    opacity: m.is_active ? 1 : 0.5,
                  }}
                >
                  <div>
                    💳 •••• {m.card_last4 ?? "••••"}
                    {m.card_brand && (
                      <span style={{ marginLeft: 8, opacity: 0.6 }}>
                        {m.card_brand}
                      </span>
                    )}
                  </div>

                  {!m.is_active && (
                    <span style={{ fontSize: 12, opacity: 0.6 }}>
                      неактивен
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

        </div>

        {/* HELP */}
        <div className="profile-help">
          {/* Заменить потом на VK видео */}
          <button
            className="profile-help-item"
            onClick={() => window.open("https://t.me/illor1on", "_blank")}
          >
            Как арендовать?
          </button>
          <button
            className="profile-help-item"
            onClick={() => window.open("https://t.me/illor1on", "_blank")}
          >
            Чат поддержки
          </button>
        </div>

        {/* LOGOUT */}
        <button className="profile-logout" onClick={logout}>
          Выйти
        </button>
      </div>

      {/* ⏳ POPUP ОЖИДАНИЯ */}
      {awaiting && (
        <div className="overlay">
          <div className="popup">
            <div className="spinner" />
            <p>Подтверждаем аренду…</p>
          </div>
        </div>
      )}

      <BottomNav />
    </>
  );
}
