import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCity } from "../city/CityContext";
import BottomNav from "../components/BottomNav";
import { getLocations } from "../api/locations";
import type { Location } from "../api/locations";

export default function CitySelect() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);

  const { setLocation } = useCity();
  const navigate = useNavigate();

  useEffect(() => {
    getLocations()
      .then(setLocations)
      .finally(() => setLoading(false));
  }, []);

  function handleSelect(location: Location) {
    setLocation(location);
    navigate("/beaches");
  }

  if (loading) {
    return <div className="container">Загрузка...</div>;
  }

  return (
    <>
      <div className="container">
        <h2 className="city-title">Выберите город</h2>

        <div className="city-grid">
          {locations.map((loc) => (
            <div
              key={loc.id}
              className="city-card"
              onClick={() => handleSelect(loc)}
            >
              <img
                src={loc.image_url || "/placeholder-city.jpg"}
                alt={loc.city}
              />
              <div className="city-name">
                {loc.city}
                <div style={{ fontSize: 12, opacity: 0.7 }}>
                  {loc.region}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <BottomNav />
    </>
  );
}
