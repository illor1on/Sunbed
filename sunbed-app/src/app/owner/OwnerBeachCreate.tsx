import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

type Location = {
  id: number;
  city: string;
  region: string;
  address: string;
};

export default function OwnerBeachCreate() {
  const navigate = useNavigate();

  const [locations, setLocations] = useState<Location[]>([]);
  const [locationId, setLocationId] = useState<number | null>(null);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [imageUrl, setImageUrl] = useState("");

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get("/locations").then((res) => {
      setLocations(res.data ?? []);
    });
  }, []);

  async function submit() {
    if (!locationId || !name.trim()) {
      alert("Заполни название и выбери локацию");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/beaches", {
        name,
        location_id: locationId,
        description,
        image_url: imageUrl || null,
      });

      navigate(`/owner/beaches/${res.data.id}`);
    } catch (e: any) {
      alert(e?.response?.data?.error || "Не удалось создать пляж");
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
            Новый пляж
            <span className="beach-pin">🏖</span>
          </div>
        </div>

        <div className="beach-divider" />

        {/* FORM */}
        <div className="profile-card">
          <Field label="Локация">
            <select
              className="auth-input"
              value={locationId ?? ""}
              onChange={(e) => setLocationId(Number(e.target.value))}
            >
              <option value="">Выберите город</option>
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.city}, {l.region} — {l.address}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Название пляжа">
            <input
              className="auth-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Например: Центральный пляж"
            />
          </Field>

          <Field label="Описание">
            <textarea
              className="auth-input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Краткое описание пляжа"
              rows={3}
            />
          </Field>

          <Field label="Изображение (URL)">
            <input
              className="auth-input"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://..."
            />
          </Field>

          <button
            className="profile-action"
            disabled={loading}
            onClick={submit}
            style={{ marginTop: 12 }}
          >
            {loading ? "Создаём..." : "Создать пляж"}
          </button>
        </div>
      </div>

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
