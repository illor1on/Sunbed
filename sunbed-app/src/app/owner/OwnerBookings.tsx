import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

type ActiveBooking = {
  id: number;
  sunbed_id: number;
  end_time: string; // MSK iso string
  user_requested_close: boolean;
  lock_closed_confirmed: boolean;
};

type ProblemBooking = {
  id: number;
  sunbed_id: number;
  end_time: string; // MSK iso string
  user_requested_close: boolean;
};

type LockStatus = {
  sunbed_id: number;
  lock_identifier: string;
  locked: boolean | null;
  lock_status_raw?: any;
};

function formatDT(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("ru-RU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function OwnerBookings() {
  const navigate = useNavigate();

  const [active, setActive] = useState<ActiveBooking[]>([]);
  const [problematic, setProblematic] = useState<ProblemBooking[]>([]);
  const [loading, setLoading] = useState(true);

  const [busyId, setBusyId] = useState<number | null>(null);
  const [lockStatusBySunbed, setLockStatusBySunbed] = useState<
    Record<number, LockStatus | { error: string }>
  >({});

  async function load() {
    setLoading(true);
    try {
      const [a, p] = await Promise.all([
        api.get("/dashboard/bookings/active"),
        api.get("/dashboard/bookings/problematic"),
      ]);

      setActive(a.data?.bookings ?? []);
      setProblematic(p.data?.problematic ?? []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function forceClose(bookingId: number) {
    if (busyId) return;
    if (!confirm("Принудительно завершить аренду?")) return;

    setBusyId(bookingId);
    try {
      await api.post(`/dashboard/bookings/${bookingId}/force-close`);
      await load();
    } finally {
      setBusyId(null);
    }
  }

  async function fetchLockStatus(sunbedId: number) {
    if (busyId) return;
    setBusyId(sunbedId);
    try {
      const res = await api.get(`/dashboard/sunbeds/${sunbedId}/lock-status`);
      setLockStatusBySunbed((prev) => ({
        ...prev,
        [sunbedId]: res.data,
      }));
    } catch (e: any) {
      const msg =
        e?.response?.data?.error ||
        e?.response?.data?.details ||
        "Не удалось получить статус замка";
      setLockStatusBySunbed((prev) => ({
        ...prev,
        [sunbedId]: { error: msg },
      }));
    } finally {
      setBusyId(null);
    }
  }

  async function remoteUnlock(sunbedId: number) {
    if (busyId) return;
    if (!confirm("Отправить команду удалённого открытия?")) return;

    setBusyId(sunbedId);
    try {
      await api.post(`/dashboard/sunbeds/${sunbedId}/remote-unlock`);
      // сразу обновим статус
      await fetchLockStatus(sunbedId);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="container">
        {/* HEADER */}
        <div className="beach-header">
          <button className="beach-back" onClick={() => navigate(-1)}>
            ←
          </button>

          <div className="beach-header-title">
            Аренды
            <span className="beach-pin">🧾</span>
          </div>
        </div>

        {loading && <div style={{ marginTop: 16 }}>Загрузка...</div>}

        {!loading && problematic.length > 0 && (
          <div className="profile-card" style={{ marginTop: 16 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>
              Проблемные аренды
            </div>

            {problematic.map((b) => (
              <div
                key={b.id}
                style={{
                  padding: 12,
                  borderRadius: 12,
                  background: "rgba(216, 67, 21, 0.08)",
                  marginBottom: 10,
                }}
              >
                <div style={{ fontWeight: 600 }}>
                  Бронь #{b.id} · Лежак #{b.sunbed_id}
                </div>

                <div style={{ fontSize: 14, opacity: 0.8, marginTop: 4 }}>
                  Окончание: {formatDT(b.end_time)}
                </div>

                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  <button
                    className="profile-help-item"
                    disabled={busyId === b.id}
                    onClick={() => forceClose(b.id)}
                    style={{ color: "#d84315" }}
                  >
                    {busyId === b.id ? "..." : "Force close"}
                  </button>

                  <button
                    className="profile-help-item"
                    disabled={busyId === b.sunbed_id}
                    onClick={() => fetchLockStatus(b.sunbed_id)}
                  >
                    Статус замка
                  </button>

                  <button
                    className="profile-help-item"
                    disabled={busyId === b.sunbed_id}
                    onClick={() => remoteUnlock(b.sunbed_id)}
                  >
                    Открыть
                  </button>
                </div>

                <LockStatusRow
                  sunbedId={b.sunbed_id}
                  value={lockStatusBySunbed[b.sunbed_id]}
                />
              </div>
            ))}
          </div>
        )}

        {!loading && (
          <div className="profile-card" style={{ marginTop: 16 }}>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>
              Активные аренды
            </div>

            {active.length === 0 ? (
              <div style={{ fontSize: 14, opacity: 0.75 }}>
                Активных аренд нет.
              </div>
            ) : (
              active.map((b) => (
                <div
                  key={b.id}
                  style={{
                    padding: 12,
                    borderRadius: 12,
                    background: "rgba(0,0,0,0.03)",
                    marginBottom: 10,
                  }}
                >
                  <div style={{ fontWeight: 600 }}>
                    Бронь #{b.id} · Лежак #{b.sunbed_id}
                  </div>

                  <div style={{ fontSize: 14, opacity: 0.8, marginTop: 4 }}>
                    Окончание: {formatDT(b.end_time)}
                  </div>

                  <div style={{ fontSize: 12, opacity: 0.75, marginTop: 6 }}>
                    intent: {b.user_requested_close ? "close requested" : "—"} ·
                    lock: {b.lock_closed_confirmed ? "confirmed" : "—"}
                  </div>

                  <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                    <button
                      className="profile-help-item"
                      disabled={busyId === b.sunbed_id}
                      onClick={() => fetchLockStatus(b.sunbed_id)}
                    >
                      Статус замка
                    </button>

                    <button
                      className="profile-help-item"
                      disabled={busyId === b.sunbed_id}
                      onClick={() => remoteUnlock(b.sunbed_id)}
                    >
                      Открыть
                    </button>
                  </div>

                  <LockStatusRow
                    sunbedId={b.sunbed_id}
                    value={lockStatusBySunbed[b.sunbed_id]}
                  />
                </div>
              ))
            )}
          </div>
        )}
      </div>

    </>
  );
}

function LockStatusRow({
  sunbedId,
  value,
}: {
  sunbedId: number;
  value: LockStatus | { error: string } | undefined;
}) {
  if (!value) return null;

  if ("error" in value) {
    return (
      <div style={{ marginTop: 8, fontSize: 13, color: "#d84315" }}>
        Лежак #{sunbedId}: {value.error}
      </div>
    );
  }

  const locked =
    value.locked === true ? "Закрыт" : value.locked === false ? "Открыт" : "—";

  return (
    <div style={{ marginTop: 8, fontSize: 13, opacity: 0.85 }}>
      Замок: <b>{locked}</b> · id: {value.lock_identifier}
    </div>
  );
}
