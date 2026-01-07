import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import { api } from "../api/client";

type Price = {
  id: number;
  price_per_hour: number;
  price_per_day: number | null;
  is_active: boolean;
};

export default function OwnerPriceEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [price, setPrice] = useState<Price | null>(null);
  const [priceHour, setPriceHour] = useState("");
  const [priceDay, setPriceDay] = useState("");
  const [isActive, setIsActive] = useState(true);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    api
      .get(`/prices/${id}`)
      .then((res) => {
        const p = res.data;
        setPrice(p);
        setPriceHour(String(p.price_per_hour));
        setPriceDay(p.price_per_day != null ? String(p.price_per_day) : "");
        setIsActive(p.is_active);
      })
      .catch(() => {
        alert("Тариф не найден");
        navigate("/owner/prices");
      })
      .finally(() => setLoading(false));
  }, [id, navigate]);

  async function save() {
    if (!priceHour) {
      alert("Цена за час обязательна");
      return;
    }

    setSaving(true);
    try {
      await api.put(`/prices/${id}`, {
        price_per_hour: Number(priceHour),
        price_per_day: priceDay ? Number(priceDay) : null,
        is_active: isActive,
      });

      navigate("/owner/prices");
    } catch (e: any) {
      alert(e?.response?.data?.error || "Не удалось сохранить тариф");
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!price) return;
    if (!confirm("Удалить тариф без возможности восстановления?")) return;

    setDeleting(true);
    try {
      await api.delete(`/prices/${price.id}`);
      navigate("/owner/prices");
    } catch (e: any) {
      alert(
        e?.response?.data?.error ||
          "Нельзя удалить тариф (возможно, он используется)"
      );
    } finally {
      setDeleting(false);
    }
  }

  if (loading || !price) {
    return <div className="container">Загрузка...</div>;
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
            Тариф
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
            />
          </Field>

          <Field label="Цена за день (₽)">
            <input
              className="auth-input"
              type="number"
              min="0"
              step="1"
              value={priceDay}
              onChange={(e) => setPriceDay(e.target.value)}
              placeholder="Необязательно"
            />
          </Field>

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
            onClick={save}
            disabled={saving}
            style={{ marginTop: 16 }}
          >
            {saving ? "Сохраняем..." : "Сохранить"}
          </button>

          <button
            className="profile-help-item"
            onClick={remove}
            disabled={deleting}
            style={{
              marginTop: 12,
              color: "#d84315",
            }}
          >
            {deleting ? "Удаляем..." : "Удалить тариф"}
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
