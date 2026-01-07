import { http } from "./http";

export type Location = {
  id: number;
  city: string;
  region: string;
  address: string;
  image_url: string | null;
  coordinates: {
    latitude: number | null;
    longitude: number | null;
  };
};

export async function getLocations(): Promise<Location[]> {
  const res = await http.get("/locations");
  return res.data;
}
