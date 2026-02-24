import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import styles from "./AuthPage.module.css";

export default function LoginPage() {
  const [id, setId] = useState("");
  const [pw, setPw] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await login(id, pw);
      navigate("/");
    } catch {
      setError("Invalid username/email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <form className={styles.card} onSubmit={submit}>
        <h1 className={styles.brand}>Code<span className={styles.accent}>Sync</span></h1>
        <h2 className={styles.heading}>Sign in</h2>
        {error && <p className={styles.error}>{error}</p>}
        <label className={styles.label}>Username or email
          <input className={styles.input} value={id} onChange={(e) => setId(e.target.value)} required autoFocus />
        </label>
        <label className={styles.label}>Password
          <input className={styles.input} type="password" value={pw} onChange={(e) => setPw(e.target.value)} required />
        </label>
        <button className={styles.btn} type="submit" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <p className={styles.footer}>No account? <Link className={styles.link} to="/register">Register</Link></p>
      </form>
    </div>
  );
}
