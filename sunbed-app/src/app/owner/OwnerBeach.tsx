import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";

type Location = {
  city: string;
  region: string;
  address: string;
};

type Beach = {
  id: number;
  name: string;
  image_url: string | null;
  owner_hidden: boolean;
  count_of_sunbeds: number;
  location: Location;
};

export default function OwnerBeach() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [beach, setBeach] = useState<Beach | null>(null);
  const [sunbedsCount, setSunbedsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        // 1️⃣ Пляж
        const beachRes = await api.get(`/beaches/${id}`);
        if (!mounted) return;
        setBeach(beachRes.data);

        // 2️⃣ Лежаки
        try {
          const sunbedsRes = await api.get(`/beaches/${id}/sunbeds`);
          if (mounted) {
            setSunbedsCount(
              (sunbedsRes.data?.sunbeds ?? []).length
            );
          }
        } catch {
          if (mounted) setSunbedsCount(0);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, [id]);

  const toggleBeach = async () => {
    if (!beach || updating) return;

    setUpdating(true);
    try {
      await api.post(`/beaches/${beach.id}/owner-toggle`);

      setBeach({
        ...beach,
        owner_hidden: !beach.owner_hidden,
      });
    } finally {
      setUpdating(false);
    }
  };

  const deleteBeach = async () => {
    if (!beach) return;
    if (!confirm("Удалить пляж без возможности восстановления?")) return;

    await api.delete(`/beaches/${beach.id}`);
    navigate("/owner/beaches");
  };

  if (loading || !beach) {
    return <div className="container">Загрузка...</div>;
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
                Пляж
                <span className="beach-pin">🏖</span>
            </div>
        </div>

        <div className="beach-divider" />
        <div className="owner-beach-header">
          {/* IMAGE */}
          <div className="owner-beach-image profile-card">
            <img
              src={beach.image_url || "/placeholder-beach.jpg"}
              alt={beach.name}
            />
          </div>

          {/* RIGHT SIDE */}
          <div className="owner-beach-info">
            {/* INFO */}
            <div className="profile-card">
              <div style={{ fontWeight: 600 }}>
                {beach.location.city}, {beach.location.region}
              </div>
              <div style={{ fontSize: 14, opacity: 0.7 }}>
                {beach.location.address}
              </div>
              <div
                style={{
                  marginTop: 6,
                  fontSize: 14,
                  color: beach.owner_hidden ? "#d84315" : "#2e7d32",
                }}
              >
                {beach.owner_hidden
                  ? "Пляж скрыт владельцем"
                  : "Пляж активен"}
              </div>
            </div>

            {/* STATS */}
            <div className="profile-stats">
              
              <div
              className="profile-card"
              style={{
                cursor: "pointer",
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-start",
                gap: 6,
              }}
              onClick={() =>
                navigate(`/owner/beaches/${beach.id}/sunbeds`)
              }
            >
              <div style={{ fontSize: 14, fontWeight: 500 }}>
                Лежаки
              </div>

              <div style={{ fontSize: 22, fontWeight: 600 }}>
                {beach.count_of_sunbeds}
              </div>
            </div>
            <div className="profile-card">
              <button
                className="profile-help-item"
                disabled={updating}
                onClick={toggleBeach}
              >
                {beach.owner_hidden
                  ? "Показать пляж"
                  : "Скрыть пляж"}
              </button>

              <button
                className="profile-help-item"
                style={{ color: "#d84315" }}
                onClick={deleteBeach}
              >
                Удалить пляж
              </button>
            </div>
            </div>

            {/* ACTIONS */}
            
          </div>
        </div>
      </div>

      
    </>
  );
}
