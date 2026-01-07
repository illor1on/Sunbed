import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="auth-screen">
      <div className="auth-container">{children}</div>
    </div>
  );
}
