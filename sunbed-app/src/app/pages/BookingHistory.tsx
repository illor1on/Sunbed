import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import { getMyBookingHistory } from "../api/bookings";
import type { BookingHistoryItem } from "../api/bookings";

export default function BookingHistory() {
  const navigate = useNavigate();
  const [bookings, setBookings] = useState<BookingHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyBookingHistory()
      .then((res) => setBookings(res ?? []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="container">Загрузка...</div>;
  }

  return (
    <>
      <div className="container booking-history-page">
        {/* HEADER */}
        <div className="sunbeds-header">
          <button className="sunbeds-back" onClick={() => navigate(-1)}>
            ←
          </button>
          <div className="sunbeds-title">Прошлые аренды</div>
          <div />
        </div>

        {/* EMPTY */}
        {bookings.length === 0 && (
          <div className="empty">У вас нет прошлых аренд</div>
        )}

        {/* LIST */}
        <div className="booking-history-list">
          {bookings.map((b) => (
            <div key={b.id} className="booking-history-card">
              <div className="booking-history-top">
                <div className="booking-city">{b.city_name}</div>
                <div className="booking-date">{formatDate(b.start_time)}</div>
              </div>

              <div className="booking-beach">{b.beach_name}</div>
              <div className="booking-sunbed">Лежак {b.sunbed_name}</div>

              <div className="booking-time">
                <span className="booking-label">Начало:</span>{" "}
                {formatTime(b.start_time)}
              </div>

              <div className="booking-time">
                <span className="booking-label">Окончание:</span>{" "}
                {formatTime(b.end_time)}
              </div>

              {b.total_price != null && (
                <div className="booking-price">
                  Стоимость: {b.total_price} ₽
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <BottomNav />
    </>
  );
}

/* ======================
   HELPERS
====================== */

function formatDate(value: string) {
  const d = new Date(value);
  return d.toLocaleDateString("ru-RU");
}

function formatTime(value: string) {
  const d = new Date(value);
  return d.toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });
}
