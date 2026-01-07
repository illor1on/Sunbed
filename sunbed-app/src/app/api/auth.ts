import { http } from "./http";

export async function login(phone: string, password: string) {
  const res = await http.post("/auth/login", {
    phone_number: phone,
    password,
  });
  return res.data;
}

export async function register(data: {
  name: string;
  email: string;
  phone: string;
  password: string;
}) {
  const res = await http.post("/auth/register", {
    name: data.name,
    email: data.email,
    phone_number: data.phone,
    password: data.password,
  });
  return res.data;
}

export async function getMe() {
  const res = await http.get("/auth/me");
  return res.data;
}
