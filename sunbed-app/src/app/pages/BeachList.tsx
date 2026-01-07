import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCity } from "../city/CityContext";
import BottomNav from "../components/BottomNav";
import { getBeachesByLocation } from "../api/beaches";
import type { Beach } from "../api/beaches";

export default function BeachList() {
  const { location } = useCity();
  const navigate = useNavigate();

  const [beaches, setBeaches] = useState<Beach[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!location) return;

    setLoading(true);
    getBeachesByLocation(location.id)
      .then(setBeaches)
      .finally(() => setLoading(false));
  }, [location]);

  if (!location) return null;

  if (loading) {
    return <div className="container">Загрузка...</div>;
  }

  return (
    <>
      <div className="container">
        {/* HEADER */}
        <div className="beach-header">
          <button
            className="beach-back"
            onClick={() => navigate("/city")}
          >
            ←
          </button>

          <div className="beach-header-title">
            {location.city}
            <span className="beach-pin">📍</span>
          </div>
        </div>

        {/* BEACH LIST */}
        <div className="beach-grid">
          {beaches.map((beach) => (
            <div
              key={beach.id}
              className="beach-card"
              onClick={() => navigate(`/beach/${beach.id}/sunbeds`)}
              style={{ cursor: "pointer" }}
            >
              <img
                src={beach.image_url || "/placeholder-beach.jpg"}
                alt={beach.name}
              />
              <div className="beach-name">{beach.name}</div>
            </div>
          ))}
        </div>
      </div>

      <BottomNav />
    </>
  );
}
