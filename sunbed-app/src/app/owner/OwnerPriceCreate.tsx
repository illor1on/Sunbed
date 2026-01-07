import { useState } from "react";
import { useNavigate } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import { api } from "../api/client";

export default function OwnerPriceCreate() {
  const navigate = useNavigate();

  const [priceHour, setPriceHour] = useState("");
  const [priceDay, setPriceDay] = useState("");
  const [isActive, setIsActive] = useState(true);

  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!priceHour || !priceDay) {
        alert("Укажи цену за час и за день");
        return;
}

    setLoading(true);
    try {
      await api.post("/prices", {
        price_per_hour: Number(priceHour),
        price_per_day: Number(priceDay),
        is_active: isActive,
      });

      navigate("/owner/prices");
    } catch (e: any) {
      alert(e?.response?.data?.error || "Не удалось создать тариф");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="container">
        {/* HEADER */}
        <div className="beach-header">
          <button className="beach-back" onClick={() => navigate(-1)}>
            ←
          </button>
          <div className="beach-header-title">
            Новый тариф
            <span className="beach-pin">💰</span>
          </div>
        </div>

        <div className="beach-divider" />

        {/* FORM */}
        <div className="profile-card">
          <Field label="Цена за час (₽)">
            <input
              className="auth-input"
              type="number"
              min="0"
              step="1"
              value={priceHour}
              onChange={(e) => setPriceHour(e.target.value)}
              placeholder="Например: 500"
            />
          </Field>

          <Field label="Цена за день (₽)*">
            <input
              className="auth-input"
              type="number"
              min="0"
              step="1"
              value={priceDay}
              onChange={(e) => setPriceDay(e.target.value)}
              placeholder="Обязательно"
            />
          </Field>

          {/* ACTIVE */}
          <div style={{ marginTop: 12 }}>
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                cursor: "pointer",
                fontSize: 14,
              }}
            >
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              Тариф активен
            </label>
          </div>

          <button
            className="profile-action"
            onClick={submit}
            disabled={loading}
            style={{ marginTop: 16 }}
          >
            {loading ? "Создаём..." : "Создать тариф"}
          </button>
        </div>
      </div>

      <BottomNav />
    </>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>
        {label}
      </div>
      {children}
    </div>
  );
}
