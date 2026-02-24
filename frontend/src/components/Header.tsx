import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import styles from "./Header.module.css";

interface HeaderProps {
  theme: "vs-dark" | "vs";
  onToggleTheme: () => void;
}

export default function Header({ theme, onToggleTheme }: HeaderProps) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className={styles.header}>
      <div className={styles.brand} onClick={() => navigate("/")} role="button" tabIndex={0}>
        Code<span className={styles.accent}>Sync</span>
      </div>
      <div className={styles.right}>
        <button className={styles.themeBtn} onClick={onToggleTheme} title="Toggle theme">
          {theme === "vs-dark" ? "☀" : "🌙"}
        </button>
        {user && (
          <>
            <span className={styles.username}>{user.username}</span>
            <button className={styles.logoutBtn} onClick={handleLogout}>Sign out</button>
          </>
        )}
      </div>
    </header>
  );
}
