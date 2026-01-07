import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function OwnerGuard() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [checking, setChecking] = useState(true);
  const [hasLegalInfo, setHasLegalInfo] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;

    async function checkLegal() {
      if (!user || user.role !== "owner") {
        if (mounted) {
          setHasLegalInfo(true);
          setChecking(false);
        }
        return;
      }

      try {
        const res = await api.get("/owner/legal/");
        const info = res.data?.legal_info ?? null;
        if (mounted) {
          setHasLegalInfo(!!info);
        }
      } catch {
        // если ошибка — не блокируем owner
        if (mounted) {
          setHasLegalInfo(true);
        }
      } finally {
        if (mounted) setChecking(false);
      }
    }

    checkLegal();
    return () => {
      mounted = false;
    };
  }, [user]);

  if (loading || checking) {
    return null;
  }

  if (!user || user.role !== "owner") {
    return null;
  }

  const isPaymentPage = location.pathname === "/owner/payment";

  // ❗ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ:
  // блокируем owner-раздел ТОЛЬКО если
  // нет юр-данных И это НЕ страница заполнения
  if (hasLegalInfo === false && !isPaymentPage) {
    return (
      <div className="container">
        <div className="profile-card" style={{ marginTop: 16 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>
            Нужны юридические данные
          </div>

          <div style={{ fontSize: 14, opacity: 0.75, marginBottom: 12 }}>
            Чтобы принимать оплату и настраивать кассу, заполни данные ИП/ООО.
          </div>

          <button
            className="profile-action"
            onClick={() => navigate("/owner/payment")}
          >
            Заполнить →
          </button>
        </div>
      </div>
    );
  }

  // ✅ во всех остальных случаях — пускаем дальше
  return <Outlet />;
}
