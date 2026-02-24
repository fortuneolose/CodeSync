import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import styles from "./AuthPage.module.css";

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuthStore();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await register(username, email, pw);
      navigate("/");
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <form className={styles.card} onSubmit={submit}>
        <h1 className={styles.brand}>Code<span className={styles.accent}>Sync</span></h1>
        <h2 className={styles.heading}>Create account</h2>
        {error && <p className={styles.error}>{error}</p>}
        <label className={styles.label}>Username
          <input className={styles.input} value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
        </label>
        <label className={styles.label}>Email
          <input className={styles.input} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label className={styles.label}>Password (min 8 chars)
          <input className={styles.input} type="password" value={pw} onChange={(e) => setPw(e.target.value)} required minLength={8} />
        </label>
        <button className={styles.btn} type="submit" disabled={loading}>
          {loading ? "Creating…" : "Create account"}
        </button>
        <p className={styles.footer}>Have an account? <Link className={styles.link} to="/login">Sign in</Link></p>
      </form>
    </div>
  );
}
