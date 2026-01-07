import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import { api } from "../api/client";

type Price = {
  id: number;
  name: string;
  price_per_day: number;
  price_per_hour: number;
};

export default function OwnerSunbedCreate() {
  const { beachId } = useParams<{ beachId: string }>();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [prices, setPrices] = useState<Price[]>([]);
  const [priceId, setPriceId] = useState<number | "">("");
  const [hasLock, setHasLock] = useState(false);
  const [lockId, setLockId] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/prices").then((res) => {
      setPrices(res.data.prices);
    });
  }, []);

  async function submit() {
    if (!name.trim()) {
      alert("Укажи название лежака");
      return;
    }

    if (!priceId) {
      alert("Выбери тариф");
      return;
    }

    if (hasLock && !lockId.trim()) {
      alert("Укажи идентификатор замка");
      return;
    }

    setLoading(true);
    try {
        console.log("CREATE SUNBED PAYLOAD", {
  name,
  beach_id: beachId,
  price_id: priceId,
  has_lock: hasLock,
  lock_identifier: lockId,
});
      await api.post("/sunbeds", {
  name: name.trim(),
  beach_id: Number(beachId), // 👈 ВАЖНО
  price_id: priceId,
  has_lock: hasLock,
  lock_identifier: hasLock ? lockId.trim() : null,
});

      navigate(`/owner/beaches/${beachId}/sunbeds`);
    } catch (e: any) {
      alert(
        e?.response?.data?.error ||
          "Не удалось создать лежак"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="container">
        {/* HEADER */}
        <div className="beach-header">
          <button
            className="beach-back"
            onClick={() => navigate(-1)}
          >
            ←
          </button>

          <div className="beach-header-title">
            Новый лежак
            <span className="beach-pin">🪑</span>
          </div>
        </div>

        <div className="beach-divider" />

        <div className="profile-card">
          {/* NAME */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>
              Название
            </div>
            <input
              className="auth-input"
              placeholder="Например: Лежак 4"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {/* PRICE */}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>
              Тариф
            </div>
            <select
              className="auth-input"
              value={priceId}
              onChange={(e) =>
                setPriceId(Number(e.target.value))
              }
            >
              <option value="">Выбери тариф</option>
              {prices.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.price_per_day} ₽ / день
                </option>
              ))}
            </select>
          </div>

          {/* LOCK */}
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: 14,
              marginBottom: hasLock ? 8 : 0,
            }}
          >
            <input
              type="checkbox"
              checked={hasLock}
              onChange={(e) => setHasLock(e.target.checked)}
            />
            Есть замок
          </label>

          {hasLock && (
            <input
              className="auth-input"
              placeholder="Идентификатор замка"
              value={lockId}
              onChange={(e) => setLockId(e.target.value)}
            />
          )}

          <button
            className="profile-action"
            onClick={submit}
            disabled={loading}
            style={{ marginTop: 16 }}
          >
            {loading ? "Создаём..." : "Создать лежак"}
          </button>
        </div>
      </div>

      <BottomNav />
    </>
  );
}
