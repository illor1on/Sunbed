import { api } from "./client";

export type BookingStatus =
  | "pending"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "expired";


export async function createBooking(data: {
  sunbed_id: number;
  start_time: string;
  end_time: string;
}) {
  const res = await api.post("/bookings", data);
  return res.data;
}

export async function payBooking(bookingId: number) {
  const res = await api.post(`/bookings/${bookingId}/pay`);
  return res.data;
}

export type ActiveBooking = {
  id: number;
  status: BookingStatus;
  city_name: string;
  beach_name: string;
  sunbed_name: string;
  start_time: string;
  end_time: string;
};

export async function getMyActiveBooking(): Promise<ActiveBooking[]> {
  try {
    const res = await api.get("/bookings/active");

    return (res.data ?? []).filter(
      (b: ActiveBooking) => b.status === "confirmed"
    );
  } catch (err: any) {
    if (err.response?.status === 404 || err.response?.status === 204) {
      return [];
    }
    throw err;
  }
}



export async function closeBookingLock(bookingId: number) {
  const res = await api.post(`/bookings/${bookingId}/close-lock`);
  return res.data;
}


export type BookingHistoryItem = {
  id: number;
  city_name: string;
  beach_name: string;
  sunbed_name: string;
  start_time: string;
  end_time: string;
  total_price?: number;
};

export async function getMyBookingHistory(): Promise<BookingHistoryItem[]> {
  const res = await api.get("/bookings/history");
  return res.data;
}