import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

type LegalInfo = {
  legal_type: "IP" | "OOO";
  legal_name: string;
  inn: string;
  address: string;
  ogrnip?: string | null;
  ogrn?: string | null;
  kpp?: string | null;
  director_name?: string | null;
};

type PaymentAccount = {
  id: number;
  owner_id: number;
  provider: string;
  shop_id: string;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export default function OwnerPayment() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  // ===== LEGAL (ОСТАВЛЕНО 1:1) =====
  const [legal, setLegal] = useState<LegalInfo | null>(null);
  const legalLocked = !!legal;
  const lockedType = legal?.legal_type;
  const [legalForm, setLegalForm] = useState<LegalInfo>({
    legal_type: "IP",
    legal_name: "",
    inn: "",
    address: "",
    ogrnip: "",
    ogrn: "",
    kpp: "",
    director_name: "",
  });
  const [savingLegal, setSavingLegal] = useState(false);
  const legalIsOOO = useMemo(() => legalForm.legal_type === "OOO", [legalForm]);

  // ===== PAYMENT =====
  const [account, setAccount] = useState<PaymentAccount | null>(null);
  const [provider] = useState("yookassa");
  const [shopId, setShopId] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [savingAccount, setSavingAccount] = useState(false);

  const [webhookUrl, setWebhookUrl] = useState<string | null>(null);
  const [webhookError, setWebhookError] = useState<string | null>(null);
  const [webhookToken, setWebhookToken] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [l, a] = await Promise.all([
        api.get("/owner/legal/"),
        api.get("/owner/payment-account"),
      ]);

      const legalInfo = l.data?.legal_info ?? null;
      setLegal(legalInfo);

      if (legalInfo) {
        setLegalForm({
          legal_type: legalInfo.legal_type,
          legal_name: legalInfo.legal_name ?? "",
          inn: legalInfo.inn ?? "",
          address: legalInfo.address ?? "",
          ogrnip: legalInfo.ogrnip ?? "",
          ogrn: legalInfo.ogrn ?? "",
          kpp: legalInfo.kpp ?? "",
          director_name: legalInfo.director_name ?? "",
        });
      }

      const acc = a.data?.payment_account === null ? null : a.data;
      setAccount(acc ?? null);
      if (acc?.shop_id) setShopId(acc.shop_id);

      setWebhookUrl(null);
      setWebhookError(null);
      setWebhookToken(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function saveLegal() {
    if (savingLegal) return;
    setSavingLegal(true);
    try {
      await api.post("/owner/legal/", legalForm);
      await load();
    } catch (e: any) {
      alert(e?.response?.data?.error || "Не удалось сохранить юридические данные");
    } finally {
      setSavingLegal(false);
    }
  }

  async function saveAccount() {
    if (savingAccount) return;
    if (!shopId || !secretKey) {
      alert("Укажи shop_id и secret_key");
      return;
    }
    setSavingAccount(true);
    try {
      await api.post("/owner/payment-account", {
        provider,
        shop_id: shopId,
        secret_key: secretKey,
      });
      setSecretKey("");
      await load();
    } catch (e: any) {
      alert(e?.response?.data?.error || "Не удалось сохранить кассу");
    } finally {
      setSavingAccount(false);
    }
  }

  async function fetchWebhookUrl() {
    if (!account) return;
    setWebhookUrl(null);
    setWebhookError(null);
    try {
      const res = await api.get(`/owner/payment-account/${account.id}/webhook`);
      setWebhookUrl(res.data?.webhook_url ?? null);
    } catch (e: any) {
      setWebhookError(
        e?.response?.data?.error ||
          "Не удалось получить webhook URL (проверь PUBLIC_API_BASE_URL)"
      );
    }
  }

  async function fetchWebhookToken() {
    if (!account) return;
    try {
      const res = await api.get(
        `/owner/payment-account/${account.id}/webhook-token`
      );
      setWebhookToken(res.data?.webhook_token ?? null);
    } catch (e: any) {
      alert(e?.response?.data?.error || "Не удалось получить webhook token");
    }
  }

  async function rotateWebhook() {
    if (!account) return;
    if (!confirm("Обновить webhook token? Старый URL перестанет работать."))
      return;
    try {
      await api.post(
        `/owner/payment-account/${account.id}/rotate-webhook-token`
      );
      setWebhookUrl(null);
      setWebhookToken(null);
      alert("Webhook token обновлён");
    } catch (e: any) {
      alert(e?.response?.data?.error || "Не удалось обновить webhook token");
    }
  }

  async function deactivateAccount() {
    if (!account) return;
    if (!confirm("Отключить кассу?")) return;
    try {
      await api.delete(`/owner/payment-account/${account.id}`);
      await load();
    } catch (e: any) {
      alert(e?.response?.data?.error || "Не удалось отключить кассу");
    }
  }

  if (loading) {
    return <div className="container">Загрузка...</div>;
  }

  return (
    <div className="container">
      {/* HEADER */}
      <div className="beach-header">
        <button className="beach-back" onClick={() => navigate(-1)}>
          ←
        </button>
        <div className="beach-header-title">
          Касса и выплаты <span className="beach-pin">💳</span>
        </div>
      </div>

      {/* ===== LEGAL (JSX 1:1 ИЗ ТВОЕГО ФАЙЛА) ===== */}
      <div className="profile-card" style={{ marginTop: 16 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>
          Юридические данные
        </div>

        <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
          <button
            className="profile-help-item"
            disabled={legalLocked && lockedType !== "IP"}
            onClick={() => {
              if (legalLocked) return;
              setLegalForm((p) => ({ ...p, legal_type: "IP" }));
            }}
            style={{
              opacity:
                legalForm.legal_type === "IP"
                  ? 1
                  : legalLocked
                  ? 0.4
                  : 0.6,
              cursor:
                legalLocked && lockedType !== "IP"
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            ИП
          </button>

          <button
            className="profile-help-item"
            disabled={legalLocked && lockedType !== "OOO"}
            onClick={() => {
              if (legalLocked) return;
              setLegalForm((p) => ({ ...p, legal_type: "OOO" }));
            }}
            style={{
              opacity:
                legalForm.legal_type === "OOO"
                  ? 1
                  : legalLocked
                  ? 0.4
                  : 0.6,
              cursor:
                legalLocked && lockedType !== "OOO"
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            ООО
          </button>
        </div>

        <Input
          label="Наименование"
          value={legalForm.legal_name}
          onChange={(v) => setLegalForm((p) => ({ ...p, legal_name: v }))}
        />
        <Input
          label="ИНН"
          value={legalForm.inn}
          onChange={(v) => setLegalForm((p) => ({ ...p, inn: v }))}
        />
        <Input
          label="Адрес"
          value={legalForm.address}
          onChange={(v) => setLegalForm((p) => ({ ...p, address: v }))}
        />

        {!legalIsOOO && (
          <Input
            label="ОГРНИП"
            value={legalForm.ogrnip ?? ""}
            onChange={(v) => setLegalForm((p) => ({ ...p, ogrnip: v }))}
          />
        )}

        {legalIsOOO && (
          <>
            <Input
              label="ОГРН"
              value={legalForm.ogrn ?? ""}
              onChange={(v) => setLegalForm((p) => ({ ...p, ogrn: v }))}
            />
            <Input
              label="КПП"
              value={legalForm.kpp ?? ""}
              onChange={(v) => setLegalForm((p) => ({ ...p, kpp: v }))}
            />
            <Input
              label="Директор"
              value={legalForm.director_name ?? ""}
              onChange={(v) =>
                setLegalForm((p) => ({ ...p, director_name: v }))
              }
            />
          </>
        )}

        <button
          className="profile-action"
          disabled={savingLegal}
          onClick={saveLegal}
          style={{ marginTop: 10 }}
        >
          {savingLegal ? "Сохраняем..." : legal ? "Обновить" : "Сохранить"}
        </button>
      </div>

      {/* ===== PAYMENT ACCOUNT (ПЕРЕДЕЛАНО) ===== */}
      <div className="profile-card" style={{ marginTop: 16 }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Касса YooKassa</div>

        {account && (
          <div style={{ fontSize: 13, opacity: 0.8, marginBottom: 10 }}>
            Активна: <b>{account.is_active ? "да" : "нет"}</b> · shop_id:{" "}
            <b>{account.shop_id}</b>
          </div>
        )}

        <Input
          label="shop_id"
          value={shopId}
          onChange={setShopId}
          placeholder="Например: 123456"
        />
        <Input
          label="secret_key"
          value={secretKey}
          onChange={setSecretKey}
          placeholder="••••••••"
        />

        <button
          className="profile-action"
          disabled={savingAccount}
          onClick={saveAccount}
          style={{ marginTop: 10 }}
        >
          {savingAccount
            ? "Сохраняем..."
            : account
            ? "Заменить кассу"
            : "Подключить кассу"}
        </button>

        {account && (
          <div
            style={{
              display: "flex",
              gap: 8,
              marginTop: 10,
              flexWrap: "wrap",
            }}
          >
            <button className="profile-help-item" onClick={fetchWebhookUrl}>
              Webhook URL
            </button>
            <button className="profile-help-item" onClick={fetchWebhookToken}>
              Webhook токен
            </button>
            <button className="profile-help-item" onClick={rotateWebhook}>
              Перевыпустить токен
            </button>
            <button
              className="profile-help-item"
              style={{ color: "#d84315" }}
              onClick={deactivateAccount}
            >
              Отключить
            </button>
          </div>
        )}

        {webhookUrl && (
          <div style={{ marginTop: 10, fontSize: 13 }}>
            <div style={{ opacity: 0.7, marginBottom: 6 }}>Webhook URL:</div>
            <div
              style={{
                padding: 10,
                borderRadius: 12,
                background: "rgba(0,0,0,0.04)",
                wordBreak: "break-all",
              }}
            >
              {webhookUrl}
            </div>
          </div>
        )}

        {webhookToken && (
          <div style={{ marginTop: 10, fontSize: 13 }}>
            <div style={{ opacity: 0.7, marginBottom: 6 }}>
              Webhook токен:
            </div>
            <div
              style={{
                padding: 10,
                borderRadius: 12,
                background: "rgba(0,0,0,0.04)",
              }}
            >
              {webhookToken}
            </div>
          </div>
        )}

        {webhookError && (
          <div style={{ marginTop: 10, fontSize: 13, color: "#d84315" }}>
            {webhookError}
          </div>
        )}
      </div>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>{label}</div>
      <input
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="auth-input"
      />
    </div>
  );
}
