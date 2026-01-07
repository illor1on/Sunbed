// src/app/auth/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, getMe } from "../api/auth";

export type Permission = string;

export type User = {
  id: number;
  name: string;
  phone_number: string;
  role: "user" | "owner" | "admin";

  permissions: Permission[];
};

type AuthContextType = {
  user: User | null;
  login: (phone: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType>(null!);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function login(phone: string, password: string) {
    const data = await apiLogin(phone, password);
    localStorage.setItem("access_token", data.access_token);
    setUser(data.user);
  }

  function logout() {
    localStorage.removeItem("access_token");
    setUser(null);
  }

  // 🔁 восстановление сессии
  useEffect(() => {
    async function init() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const me = await getMe();
        setUser(me);
      } catch (err: any) {
        // ❗ УДАЛЯЕМ ТОКЕН ТОЛЬКО ПРИ 401
        if (err?.response?.status === 401) {
          localStorage.removeItem("access_token");
          setUser(null);
        }
        // во всех остальных случаях — НЕ трогаем токен
      } finally {
        setLoading(false);
      }
    }

    init();
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
