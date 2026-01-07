import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";

type Sunbed = {
  id: number;
  name: string;
  is_active: boolean;
  has_lock: boolean;
  lock_identifier: string | null;
  price_id: number | null;
};

export default function OwnerSunbeds() {
  const { id } = useParams<{ id: string }>(); // beach id
  const navigate = useNavigate();

  const [sunbeds, setSunbeds] = useState<Sunbed[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get(`/beaches/${id}/sunbeds`)
      .then((res) => {
        // res.data.sunbeds, потому что тут НЕ pagination
        setSunbeds(res.data?.sunbeds ?? []);
      })
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <>
      <div className="container">
        {/* HEADER */}
        <div className="beach-header">
          <button className="beach-back" onClick={() => navigate(-1)}>
            ←
          </button>
          <div className="beach-header-title">
            Лежаки
            <span className="beach-pin">🪑</span>
          </div>
        </div>

        <div className="beach-divider" />

        {loading && <div>Загрузка...</div>}

        {!loading && sunbeds.length === 0 && (
          <div className="profile-card">
            <div style={{ fontWeight: 600, marginBottom: 6 }}>
              Лежаков пока нет
            </div>
            <div style={{ fontSize: 14, opacity: 0.75 }}>
              Добавь первый лежак, чтобы начать сдачу в аренду.
            </div>
          </div>
        )}

        {!loading &&
          sunbeds.map((s) => (
            <div
              key={s.id}
              className="profile-card"
              style={{ marginBottom: 12 }}
            >
              <div style={{ fontWeight: 600 }}>
                {s.name || `Лежак #${s.id}`}
              </div>

              <div style={{ fontSize: 13, opacity: 0.7, marginTop: 4 }}>
                {s.has_lock ? "🔒 Замок есть" : "— Без замка"}
              </div>

              <div style={{ fontSize: 13, opacity: 0.7, marginTop: 4 }}>
                {s.price_id
                  ? `💰 Тариф #${s.price_id}`
                  : "⚠️ Тариф не назначен"}
              </div>

              <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                <button
                  className="profile-help-item"
                  onClick={() =>
                    alert("Редактирование лежака — следующий шаг")
                  }
                >
                  Редактировать
                </button>
              </div>
            </div>
          ))}
      </div>

      {/* ADD */}
      <button
        className="qr-button"
        onClick={() =>
          navigate(`/owner/beaches/${id}/sunbeds/new`)
        }
      >
        ＋
      </button>

    </>
  );
}
