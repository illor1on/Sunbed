export function validatePhone(phone: string): string | null {
  const clean = phone.replace(/\D/g, "");

  if (!/^(\+7|8)\d{10}$/.test(phone) && !/^\d{11}$/.test(clean)) {
    return "Неверный формат телефона";
  }

  return null;
}

export function validatePassword(password: string): string | null {
  if (password.length < 6) {
    return "Минимум 6 символов";
  }

  if (!/\d/.test(password)) {
    return "Пароль должен содержать цифру";
  }

  return null;
}
