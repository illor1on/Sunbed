import type { AxiosError } from "axios";

type BackendError = {
  error?: string;
  message?: string;
};

export function getApiErrorMessage(err: unknown): string {
  const e = err as AxiosError<BackendError>;

  if (!e || typeof e !== "object" || !("isAxiosError" in e)) {
    return "Неизвестная ошибка";
  }

  const status = e.response?.status;
  const raw =
    e.response?.data?.error ||
    e.response?.data?.message ||
    "";

  // --- МАППИНГ backend → UX ---
  if (status === 401) {
    if (raw.toLowerCase().includes("invalid")) {
      return "Неверный телефон или пароль";
    }
    return "Ошибка авторизации";
  }

  if (status === 409) {
    if (raw.toLowerCase().includes("email")) {
      return "Email уже зарегистрирован";
    }
    if (raw.toLowerCase().includes("phone")) {
      return "Телефон уже зарегистрирован";
    }
    return "Пользователь уже существует";
  }

  if (status === 400) {
    if (raw.toLowerCase().includes("phone")) {
      return "Неверный формат телефона";
    }
    return "Проверьте введённые данные";
  }

  if (status === 500) {
    return "Ошибка сервера. Попробуйте позже";
  }

  if (e.code === "ERR_NETWORK") {
    return "Сервер недоступен";
  }

  return raw || e.message || "Ошибка запроса";
}
