export type Interval = "1h" | "3h" | "day";

export function calcEndTime(interval: Interval, start: Date): Date {
  switch (interval) {
    case "1h":
      return new Date(start.getTime() + 1 * 60 * 60 * 1000);

    case "3h":
      return new Date(start.getTime() + 3 * 60 * 60 * 1000);

    case "day": {
      const end = new Date(start);
      end.setHours(23, 59, 59, 999);
      return end;
    }

    default:
      // ⛔ сюда мы никогда не попадём,
      // но TS должен это увидеть
      throw new Error(`Unknown interval: ${interval}`);
  }
}
