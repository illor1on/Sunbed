import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import BottomNav from "../components/BottomNav";
import BookingSheet from "../components/BookingSheet";
import { getAvailableSunbeds } from "../api/sunbeds";
import { getBeachById } from "../api/beaches";
import type { Sunbed } from "../api/sunbeds";
import { createBooking, payBooking } from "../api/bookings";
import { calcEndTime } from "../utils/bookingTime";
import { calcPrice } from "../utils/price";
import type { Interval } from "../utils/bookingTime";

export default function Sunbeds() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [sunbeds, setSunbeds] = useState<Sunbed[]>([]);
  const [beachName, setBeachName] = useState("");
  const [loading, setLoading] = useState(true);

  // booking sheet state
  const [selectedSunbed, setSelectedSunbed] = useState<Sunbed | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [bookingLoading, setBookingLoading] = useState(false);

  useEffect(() => {
    if (!id) return;

    setLoading(true);

    Promise.all([
      getAvailableSunbeds(Number(id)),
      getBeachById(Number(id)),
    ])
      .then(([sunbedsData, beach]) => {
        setSunbeds(sunbedsData);
        setBeachName(beach.name);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="container">Загрузка...</div>;
  }

  return (
    <>
      <div className="container sunbeds-page">
        {/* HEADER */}
        <div className="sunbeds-header">
          <button className="sunbeds-back" onClick={() => navigate(-1)}>
            ←
          </button>

          <div className="sunbeds-title">{beachName}</div>

          <div />
        </div>

        {/* GRID */}
        <div className="sunbeds-grid">
          {sunbeds.map((bed) => (
            <div
              key={bed.id}
              className="sunbed sunbed--available"
              onClick={() => {
                setSelectedSunbed(bed);
                setSheetOpen(true);
              }}
            >
              <div className="sunbed-icon">🪑</div>
              <div className="sunbed-number">{bed.name}</div>
            </div>
          ))}
        </div>
      </div>

      {/* BOOKING SHEET */}
      <BookingSheet
        open={sheetOpen}
        sunbedName={selectedSunbed?.name ?? ""}
        prices={
          selectedSunbed
            ? {
                "1h": calcPrice(selectedSunbed.price, "1h"),
                "3h": calcPrice(selectedSunbed.price, "3h"),
                "day": calcPrice(selectedSunbed.price, "day"),
              }
            : { "1h": 0, "3h": 0, "day": 0 }
        }
        loading={bookingLoading}
        onClose={() => {
          if (bookingLoading) return;
          setSheetOpen(false);
        }}
        onConfirm={async (interval: Interval) => {
          if (!selectedSunbed || bookingLoading) return;

          try {
            setBookingLoading(true);

            const start = new Date(); // ⏱ момент клика
            const end = calcEndTime(interval, start);

            const booking = await createBooking({
              sunbed_id: selectedSunbed.id,
              start_time: start.toISOString(),
              end_time: end.toISOString(),
            });

            const payment = await payBooking(booking.id);

            const url = payment.payment_url;
            if (!url) {
              throw new Error("Payment URL not found");
            }

            sessionStorage.setItem("awaiting_booking", "1");
            window.location.href = url;

          } catch (err) {
            console.error("BOOKING ERROR", err);
            alert("Не удалось начать аренду. Попробуйте другой лежак.");
            setBookingLoading(false);
          }
        }}
      />

      
      
      <BottomNav />
    </>
  );
}
