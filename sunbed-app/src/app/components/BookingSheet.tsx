import { useState } from "react";
import type { Interval } from "../utils/bookingTime";

type Prices = Record<Interval, number>;

type Props = {
  open: boolean;
  sunbedName: string;
  prices: Prices;
  loading?: boolean;
  onClose: () => void;
  onConfirm: (interval: Interval) => Promise<void> | void;
};

export default function BookingSheet({
  open,
  sunbedName,
  prices,
  loading = false,
  onClose,
  onConfirm,
}: Props) {
  const [interval, setInterval] = useState<Interval>("1h");

  if (!open) return null;

  // ⏱ локальное время пользователя (UTC+3 для твоего кейса)
  const now = Number(
    new Intl.DateTimeFormat("ru-RU", {
      hour: "2-digit",
      hour12: false,
      timeZone: "Europe/Moscow",
    }).format(new Date())
  );
  const dayAllowed = now < 21;

  // если пользователь уже выбрал day, но он стал недоступен
  // (например, открыл sheet в 20:59 и сидит до 22:00)
  const effectiveInterval =
    interval === "day" && !dayAllowed ? "1h" : interval;

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div
        className="booking-sheet"
        onClick={(e) => e.stopPropagation()}
      >
        {/* HANDLE */}
        <div
          className="sheet-handle"
          onClick={onClose}
        />

        <div className="sheet-content">
          {/* TITLE */}
          <div className="sheet-title">Лежак</div>
          <div className="sheet-sunbed">{sunbedName}</div>

          {/* INTERVALS */}
          <div className="sheet-intervals">
            <IntervalButton
              label="1 час"
              price={prices["1h"]}
              active={effectiveInterval === "1h"}
              disabled={loading}
              onClick={() => setInterval("1h")}
            />

            <IntervalButton
              label="3 часа"
              price={prices["3h"]}
              active={effectiveInterval === "3h"}
              disabled={loading}
              onClick={() => setInterval("3h")}
            />

            <IntervalButton
              label="До конца дня"
              price={prices["day"]}
              active={effectiveInterval === "day"}
              disabled={loading || !dayAllowed}
              onClick={() => setInterval("day")}
            />
          </div>

          {/* HINT */}
          {!dayAllowed && (
            <div className="sheet-hint">
              Тариф «до конца дня» доступен до 21:00
            </div>
          )}

          {/* TOTAL */}
          <div className="sheet-total">
            К оплате: <b>{prices[effectiveInterval]} ₽</b>
          </div>

          {/* CONFIRM */}
          <button
            className="sheet-confirm"
            disabled={loading}
            onClick={() => onConfirm(effectiveInterval)}
          >
            {loading ? "Бронируем..." : "Забронировать"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* =====================
   SUBCOMPONENT
===================== */

function IntervalButton({
  label,
  price,
  active,
  disabled,
  onClick,
}: {
  label: string;
  price: number;
  active: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className={`sheet-interval ${active ? "active" : ""}`}
      onClick={onClick}
      disabled={disabled || active}
    >
      <div className="interval-label">{label}</div>
      <div className="interval-price">{price} ₽</div>
    </button>
  );
}
