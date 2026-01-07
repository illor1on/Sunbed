import type { Interval } from "./bookingTime";
import type { SunbedPrice } from "../api/sunbeds";

export function calcPrice(
  price: SunbedPrice,
  interval: Interval
): number {
  switch (interval) {
    case "1h":
      return price.price_per_hour;

    case "3h":
      return price.price_per_hour * 3;

    case "day":
      return price.price_per_day;

    default:
      throw new Error(`Unknown interval: ${interval}`);
  }
}
