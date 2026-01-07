import { useState } from "react";
import AuthLayout from "../components/AuthLayout";
import { useAuth } from "../auth/AuthContext";
import { getApiErrorMessage } from "../api/errors";

export default function Login() {
  const { login } = useAuth();

  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{
    phone?: string;
    password?: string;
    form?: string;
  }>({});
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const cleanPhone = phone.replace(/\s|-/g, "");

    if (!/^(\+7\d{10}|8\d{10})$/.test(cleanPhone)) {
      setErrors({ phone: "Неверный формат телефона" });
      return;
    }

    if (!password) {
      setErrors({ password: "Введите пароль" });
      return;
    }

    try {
      setLoading(true);
      await login(cleanPhone, password);
    } catch (err) {
      const msg = getApiErrorMessage(err).toLowerCase();

      if (msg.includes("телефон")) {
        setErrors({ phone: "Неверный телефон" });
      } else {
        setErrors({ password: "Неверный пароль" });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <form onSubmit={handleSubmit}>
        {/* ТЕЛЕФОН */}
        <h2 className="auth-title">Введите номер телефона</h2>

        <input
          className={`auth-input ${errors.phone ? "input-error" : ""}`}
          placeholder="+7 (000) 000-00-00"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        {errors.phone && <div className="error-text">{errors.phone}</div>}

        {/* БОЛЬШОЙ ОТСТУП */}
        <div className="auth-spacer--large" />

        {/* ПАРОЛЬ */}
        <h2 className="auth-title auth-title--compact">
          Введите пароль
        </h2>

        <input
          type="password"
          className={`auth-input ${errors.password ? "input-error" : ""}`}
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {errors.password && (
          <div className="error-text">{errors.password}</div>
        )}

        {/* БОЛЬШОЙ ОТСТУП ПЕРЕД КНОПКОЙ */}
        <div className="auth-spacer--large" />

        <button className="auth-button" disabled={loading}>
          {loading ? "Вход..." : "Войти"}
        </button>
      </form>
    </AuthLayout>
  );
}
