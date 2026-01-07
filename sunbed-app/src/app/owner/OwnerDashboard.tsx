import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

type DashboardSummary = {
  active_bookings: number;
  beaches_total: number;
  sunbeds_total: number;
  problematic_bookings: number;
  revenue_today: number;
};

export default function OwnerDashboard() {
  const navigate = useNavigate();

  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/dashboard/summary")
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="container">Загрузка...</div>;
  }

  if (!data) {
    return (
      <div className="container">
        <div className="profile-card">
          Не удалось загрузить данные
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="container profile-page">
        {/* HEADER */}
        <div className="profile-header">
          <div className="profile-name">Панель владельца</div>
          <div className="profile-phone">
            Управление пляжами и арендами
          </div>
        </div>

        {/* STATS */}
        <div className="profile-stats">
          <div
            className="profile-stat profile-stat--clickable"
            onClick={() => navigate("/owner/beaches")}
          >
            <div className="stat-title">Пляжи</div>
            <div className="stat-value">{data.beaches_total}</div>
          </div>

          <div
            className="profile-stat profile-stat--clickable"
            onClick={() => navigate("/owner/bookings")}
          >
            <div className="stat-title">Активные аренды</div>
            <div className="stat-value">{data.active_bookings}</div>
          </div>
        </div>

        {/* SECOND ROW */}
        <div className="profile-stats">
          <div className="profile-stat">
            <div className="stat-title">Лежаки</div>
            <div className="stat-value">{data.sunbeds_total}</div>
          </div>

          <div className="profile-stat">
            <div className="stat-title">Доход сегодня</div>
            <div className="stat-value">
              {data.revenue_today.toLocaleString("ru-RU")} ₽
            </div>
          </div>
        </div>

        {/* PROBLEMS */}
        {data.problematic_bookings > 0 && (
          <div
            className="profile-card"
            style={{
              border: "2px solid #d84315",
              cursor: "pointer",
            }}
            onClick={() => navigate("/owner/bookings")}
          >
            <div style={{ fontWeight: 600, marginBottom: 6 }}>
              ⚠ Проблемные аренды
            </div>
            <div style={{ fontSize: 14 }}>
              Требуют внимания: {data.problematic_bookings}
            </div>
          </div>
        )}

        {/* ACTIONS */}
        <div className="profile-help">
          <button
            className="profile-help-item"
            onClick={() => navigate("/owner/beaches")}
          >
            Управлять пляжами
          </button>

          <button
            className="profile-help-item"
            onClick={() => navigate("/owner/bookings")}
          >
            Аренды и проблемы
          </button>
          <button
            className="profile-help-item"
            onClick={() => navigate("/owner/prices")}
          >
            💰 Тарифы
          </button>

          <button
            className="profile-help-item"
            onClick={() => navigate("/owner/payment")}
          >
            Касса и выплаты
          </button>
        </div>
      </div>

    </>
  );
}
