import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import { api } from "../api/client";

type Price = {
  id: number;
  price_per_hour: number;
  price_per_day: number | null;
  currency: string;
  is_active: boolean;
};

type PricesResponse = {
  prices: Price[];
  total: number;
  pages: number;
  current_page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
};


export default function OwnerPrices() {
  const navigate = useNavigate();
  const [prices, setPrices] = useState<Price[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/prices")
        .then((res) => {
        setPrices(res.data.prices); // ✅ ВОТ ТУТ
        })
    .finally(() => setLoading(false));
  }, []);


  


  return (
    <>
      <div className="container">
        {/* HEADER */}
        <div className="beach-header">
          <button className="beach-back" onClick={() => navigate(-1)}>
            ←
          </button>
          <div className="beach-header-title">
            Тарифы
            <span className="beach-pin">💰</span>
          </div>
        </div>

        <div className="beach-divider" />

        {loading && <div>Загрузка...</div>}

        {!loading && prices.length === 0 && (
          <div className="profile-card">
            <div style={{ fontWeight: 600, marginBottom: 6 }}>
              Тарифов пока нет
            </div>
            <div style={{ fontSize: 14, opacity: 0.75 }}>
              Создай тариф, чтобы назначать его лежакам.
            </div>
          </div>
        )}

        {!loading &&
          prices.map((p) => (
            <div
              key={p.id}
              className="profile-card"
              style={{ marginBottom: 12, cursor: "pointer" }}
              onClick={() => navigate(`/owner/prices/${p.id}`)}
            >
              <div style={{ fontWeight: 600 }}>
                {p.price_per_hour} ₽ / час
                {p.price_per_day && ` · ${p.price_per_day} ₽ / день`}
              </div>

              <div style={{ fontSize: 13, opacity: 0.7, marginTop: 4 }}>
                {p.is_active ? "🟢 Активен" : "🔴 Неактивен"}
              </div>
            </div>
          ))}
      </div>

      {/* ADD */}
      <button
        className="qr-button"
        title="Добавить тариф"
        onClick={() => navigate("/owner/prices/new")}
      >
        ＋
      </button>

      <BottomNav />
    </>
  );
}
