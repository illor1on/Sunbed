import { api } from "./client";

export async function pingAuth() {
  const res = await api.post("/auth/login", {
    phone_number: "+79991234567",
    password: "pass123",
  });
  return res.data;
}
