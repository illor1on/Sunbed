import { useState } from "react";
import { register as apiRegister } from "../api/auth";
import { useAuth } from "../auth/AuthContext";
import { getApiErrorMessage } from "../api/errors";

export default function Register() {
  const { login } = useAuth();

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
  });

  const [errors, setErrors] = useState<{
    name?: string;
    email?: string;
    phone?: string;
    password?: string;
    form?: string;
  }>({});

  const [loading, setLoading] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const cleanPhone = form.phone.replace(/\s|-/g, "");

    // ---- frontend validation ----
    if (!form.name.trim()) {
      setErrors({ name: "Введите имя" });
      return;
    }

    if (!form.email.trim()) {
      setErrors({ email: "Введите email" });
      return;
    }

    if (!/^(\+7\d{10}|8\d{10})$/.test(cleanPhone)) {
      setErrors({ phone: "Неверный формат телефона" });
      return;
    }

    if (form.password.length < 6) {
      setErrors({ password: "Минимум 6 символов" });
      return;
    }

    // ---- backend ----
    try {
      setLoading(true);

      await apiRegister({
        name: form.name,
        email: form.email,
        phone: cleanPhone,
        password: form.password,
      });

      await login(cleanPhone, form.password);
    } catch (err) {
      const message = getApiErrorMessage(err).toLowerCase();

      if (message.includes("email")) {
        setErrors({ email: "Email уже зарегистрирован" });
      } else if (message.includes("телефон")) {
        setErrors({ phone: "Телефон уже зарегистрирован" });
      } else if (message.includes("пароль")) {
        setErrors({ password: message });
      } else {
        setErrors({ form: message });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <form onSubmit={handleSubmit}>
          <h2 className="auth-title">Регистрация</h2>

          <div className="auth-field">
            <label className="auth-label">Имя</label>
            <input
              name="name"
              placeholder="Иван"
              className={`auth-input ${errors.name ? "input-error" : ""}`}
              value={form.name}
              onChange={handleChange}
            />
            {errors.name && <div className="error-text">{errors.name}</div>}
          </div>

          <div className="auth-field">
            <label className="auth-label">Email</label>
            <input
              name="email"
              placeholder="ivan@mail.ru"
              className={`auth-input ${errors.email ? "input-error" : ""}`}
              value={form.email}
              onChange={handleChange}
            />
            {errors.email && <div className="error-text">{errors.email}</div>}
          </div>

          <div className="auth-field">
            <label className="auth-label">Телефон</label>
            <input
              name="phone"
              placeholder="+7 000 000-00-00"
              className={`auth-input ${errors.phone ? "input-error" : ""}`}
              value={form.phone}
              onChange={handleChange}
            />
            {errors.phone && <div className="error-text">{errors.phone}</div>}
          </div>

          <div className="auth-field">
            <label className="auth-label">Пароль</label>
            <input
              type="password"
              name="password"
              className={`auth-input ${errors.password ? "input-error" : ""}`}
              value={form.password}
              onChange={handleChange}
            />
            {errors.password && (
              <div className="error-text">{errors.password}</div>
            )}
          </div>

          {errors.form && (
            <div className="error-text" style={{ marginBottom: 10 }}>
              {errors.form}
            </div>
          )}

          <button className="auth-button" disabled={loading}>
            {loading ? "Регистрация..." : "Зарегистрироваться"}
          </button>
        </form>
      </div>
    </div>
  );
}
