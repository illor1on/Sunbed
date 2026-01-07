import { api } from "./client";

/* =====================
   TYPES
===================== */

export type SunbedPrice = {
  id: number;
  currency: string;
  price_per_hour: number;
  price_per_day: number;
  is_active: boolean;
};

export type Sunbed = {
  id: number;
  name: string;
  beach_id: number;
  location_id: number;
  has_lock: boolean;
  lock_identifier: string | null;
  status: "available" | "unavailable";
  price_id: number;
  price: SunbedPrice;
};

/* =====================
   API
===================== */

export async function getAvailableSunbeds(
  beachId: number
): Promise<Sunbed[]> {
  const res = await api.get("/sunbeds/available", {
    params: { beach_id: beachId },
  });

  return res.data.sunbeds;
}
