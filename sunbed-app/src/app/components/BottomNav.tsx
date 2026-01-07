import { NavLink } from "react-router-dom";

export default function BottomNav() {
  return (
    <div className="bottom-nav">
      <NavLink
        to="/profile"
        className={({ isActive }) =>
          isActive ? "nav-item nav-item--active" : "nav-item"
        }
      >
        Профиль
      </NavLink>

      <NavLink
        to="/city"
        className={({ isActive }) =>
          isActive ? "nav-item nav-item--active" : "nav-item"
        }
      >
        Города
      </NavLink>

      {/* SUPPORT — внешняя ссылка */}
      <a
        href="https://t.me/illor1on"
        target="_blank"
        rel="noopener noreferrer"
        className="nav-item"
      >
        Поддержка
      </a>
    </div>
  );
}
