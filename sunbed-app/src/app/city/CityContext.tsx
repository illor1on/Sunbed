import { createContext, useContext, useState } from "react";
import type { Location } from "../api/locations";

type CityContextType = {
  location: Location | null;
  setLocation: (location: Location) => void;
  clearLocation: () => void;
};

const CityContext = createContext<CityContextType | null>(null);

export function CityProvider({ children }: { children: React.ReactNode }) {
  const [location, setLocationState] = useState<Location | null>(() => {
    const saved = localStorage.getItem("location");
    return saved ? JSON.parse(saved) : null;
  });

  function setLocation(location: Location) {
    setLocationState(location);
    localStorage.setItem("location", JSON.stringify(location));
  }

  function clearLocation() {
    setLocationState(null);
    localStorage.removeItem("location");
  }

  return (
    <CityContext.Provider
      value={{
        location,
        setLocation,
        clearLocation,
      }}
    >
      {children}
    </CityContext.Provider>
  );
}

export function useCity() {
  const context = useContext(CityContext);
  if (!context) {
    throw new Error("useCity must be used within a CityProvider");
  }
  return context;
}
