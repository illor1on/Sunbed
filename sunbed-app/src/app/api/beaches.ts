import { http } from "./http";
import type { Location } from "./locations";

export type Beach = {
  id: number;
  name: string;
  description: string | null;
  amenities: string[];
  count_of_sunbeds: number;
  is_active: boolean;
  image_url: string | null;
  location: Location;
};

export async function getBeachesByLocation(locationId: number): Promise<Beach[]> {
  const res = await http.get("/beaches", {
    params: { location_id: locationId },
  });
  return res.data;
}

export async function getBeachById(beachId: number) {
  const res = await http.get(`/beaches/${beachId}`);
  return res.data;
}
