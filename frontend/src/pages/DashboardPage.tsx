import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSessionStore } from "../store/sessionStore";
import CreateSessionModal from "../components/CreateSessionModal";
import styles from "./DashboardPage.module.css";
import type { Session } from "../types";

export default function DashboardPage() {
  const { sessions, loading, fetch, create, remove } = useSessionStore();
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { fetch(); }, []);

  const handleCreate = async (title: string, language: string, isPublic: boolean) => {
    const s = await create(title, language, isPublic);
    setShowModal(false);
    navigate(`/editor/${s.slug}`);
  };

  return (
    <div className={styles.page}>
      <div className={styles.topBar}>
        <h1 className={styles.heading}>My sessions</h1>
        <button className={styles.newBtn} onClick={() => setShowModal(true)}>+ New session</button>
      </div>

      {loading && <p className={styles.muted}>Loading…</p>}

      {!loading && sessions.length === 0 && (
        <div className={styles.empty}>
          <p>No sessions yet.</p>
          <button className={styles.newBtn} onClick={() => setShowModal(true)}>Create your first session</button>
        </div>
      )}

      <div className={styles.grid}>
        {sessions.map((s: Session) => (
          <div key={s.id} className={styles.card} onClick={() => navigate(`/editor/${s.slug}`)}>
            <div className={styles.cardTitle}>{s.title}</div>
            <div className={styles.cardMeta}>
              <span className={styles.badge}>{s.language}</span>
              {s.is_public && <span className={styles.publicBadge}>public</span>}
            </div>
            <button
              className={styles.deleteBtn}
              onClick={(e) => { e.stopPropagation(); remove(s.slug); }}
              title="Delete"
            >✕</button>
          </div>
        ))}
      </div>

      {showModal && <CreateSessionModal onClose={() => setShowModal(false)} onCreate={handleCreate} />}
    </div>
  );
}
