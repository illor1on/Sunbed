import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

type Location = {
  id: number;
  city: string;
  region: string;
  address: string;
};

type Beach = {
  id: number;
  name: string;
  image_url: string | null;
  is_active: boolean;
  owner_hidden: boolean;
  count_of_sunbeds: number;
  location: Location;
};

export default function OwnerBeaches() {
  const navigate = useNavigate();

  const [beaches, setBeaches] = useState<Beach[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/beaches/mine")
      .then((res) => setBeaches(res.data ?? []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
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
            Мои пляжи
            <span className="beach-pin">🏖</span>
          </div>
        </div>

        {/* EMPTY */}
        {beaches.length === 0 && (
          <div className="profile-card" style={{ marginTop: 16 }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>
              У вас пока нет пляжей
            </div>
            <div style={{ fontSize: 14 }}>
              Добавьте первый пляж, чтобы начать приём аренды.
            </div>
          </div>
        )}

        {/* LIST */}
        <div className="beach-grid">
          {beaches.map((beach) => (
            <div
              key={beach.id}
              className="beach-card"
              style={{ cursor: "pointer" }}
              onClick={() => navigate(`/owner/beaches/${beach.id}`)}
            >
              <img
                src={beach.image_url || "/placeholder-beach.jpg"}
                alt={beach.name}
              />

              <div className="beach-name">
                {beach.name}

                <div style={{ fontSize: 12, opacity: 0.7 }}>
                  {beach.location.city},{" "}
                  {beach.location.region}
                </div>

                <div
                  style={{
                    fontSize: 12,
                    marginTop: 4,
                    color: beach.owner_hidden ? "#d84315" : "#2e7d32",
                  }}
                >
                  {beach.owner_hidden ? "Скрыт" : "Активен"} · Лежаков:{" "}
                  {beach.count_of_sunbeds}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ADD BUTTON */}
      <button
        className="qr-button"
        title="Добавить пляж"
        onClick={() => navigate("/owner/beaches/new")}
      >
        ＋
      </button>

    </>
  );
}
