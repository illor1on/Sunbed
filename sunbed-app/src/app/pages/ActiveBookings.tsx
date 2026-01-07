import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import { getMyActiveBooking, closeBookingLock } from "../api/bookings";
import type { ActiveBooking } from "../api/bookings";
import { formatRemaining } from "../utils/time";

export default function ActiveBookings() {
  const navigate = useNavigate();

  const [bookings, setBookings] = useState<ActiveBooking[]>([]);
  const [loading, setLoading] = useState(true);

  // ⏱ текущее время — для таймера
  const [now, setNow] = useState(Date.now());

  // 🔐 завершение аренды
  const [closingBookingId, setClosingBookingId] = useState<number | null>(null);
  const [closing, setClosing] = useState(false);
  const [closeError, setCloseError] = useState<string | null>(null);

  /* 1️⃣ Загрузка активных аренд */
  const loadBookings = async () => {
    try {
      const res = await getMyActiveBooking();
      setBookings(res);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBookings();
  }, []);

  /* 2️⃣ Таймер: обновляем время раз в секунду */
  useEffect(() => {
    const interval = setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  /* 3️⃣ Завершение аренды → проверка замка */
  const handleCloseBooking = async (bookingId: number) => {
    setClosingBookingId(bookingId);
    setClosing(true);
    setCloseError(null);

    try {
      const res = await closeBookingLock(bookingId);

      // успех только если completed / already_completed
      if (!res || (res.status !== "completed" && res.status !== "already_completed")) {
        throw new Error("not_completed");
      }

      setBookings((prev) => prev.filter((b) => b.id !== bookingId));

      setClosing(false);
      setClosingBookingId(null);
      setCloseError(null);
    } catch (e) {
      setCloseError("Не удалось проверить замок. Попробуйте ещё раз.");
    }
  };

  if (loading) {
    return <div className="container">Загрузка...</div>;
  }

  return (
    <>
      <div className="container active-bookings-page">
        {/* HEADER */}
        <div className="sunbeds-header">
          <button className="sunbeds-back" onClick={() => navigate(-1)}>
            ←
          </button>
          <div className="sunbeds-title">Активные аренды</div>
          <div />
        </div>

        {/* EMPTY */}
        {bookings.length === 0 && (
          <div className="empty">У вас нет активных аренд</div>
        )}

        {/* LIST */}
        <div className="active-bookings-list">
          {bookings.map((b) => {
            const endMs = new Date(b.end_time).getTime();
            const remainingMs = endMs - now;

            return (
              <div key={b.id} className="active-booking-card">
                <div className="booking-city">{b.city_name}</div>
                <div className="booking-beach">{b.beach_name}</div>

                <div className="booking-sunbed">
                  Лежак {b.sunbed_name}
                </div>

                <div className="booking-remaining">
                  Осталось:{" "}
                  <span className="remaining-time">
                    {formatRemaining(remainingMs)}
                  </span>
                </div>

                <button
                  className="booking-finish"
                  onClick={() => handleCloseBooking(b.id)}
                >
                  Завершить аренду
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* 🔐 POPUP ЗАКРЫТИЯ ЗАМКА */}
      {closing && (
        <div className="overlay">
          <div className="popup">
            {!closeError ? (
              <>
                <div className="spinner" />
                <p>Проверьте, что замок закрыт…</p>
              </>
            ) : (
              <>
                <p>{closeError}</p>
                <div className="popup-actions">
                  <button
                    className="popup-action"
                    onClick={() => {
                      setCloseError(null);
                      if (closingBookingId) {
                        handleCloseBooking(closingBookingId);
                      }
                    }}
                  >
                    Проверить ещё раз
                  </button>
                  <button
                    className="popup-action secondary"
                    onClick={() => {
                      setClosing(false);
                      setClosingBookingId(null);
                      setCloseError(null);
                    }}
                  >
                    Закрыть
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <BottomNav />
    </>
  );
}
