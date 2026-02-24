import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import EditorPanel from "../components/EditorPanel";
import PresencePanel from "../components/PresencePanel";
import { sessionApi, type SessionWithMembers } from "../services/sessionApi";
import { useCollabEditor } from "../hooks/useCollabEditor";
import { useAuthStore } from "../store/authStore";
import styles from "./EditorPage.module.css";

interface EditorPageProps {
  theme: "vs-dark" | "vs";
}

export default function EditorPage({ theme }: EditorPageProps) {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [session, setSession] = useState<SessionWithMembers | null>(null);
  const [language, setLanguage] = useState("python");
  const [error, setError] = useState("");

  const { bindEditor, connected, peers } = useCollabEditor(slug ?? "");

  // Load session metadata
  useEffect(() => {
    if (!slug) return;
    sessionApi.get(slug)
      .then(({ data }) => {
        setSession(data);
        setLanguage(data.language);
      })
      .catch(() => setError("Session not found or access denied."));
  }, [slug]);

  // Persist language changes to backend (debounced lightly)
  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    if (slug) sessionApi.update(slug, { language: lang }).catch(() => {});
  };

  if (error) return (
    <div className={styles.center}>
      <p style={{ color: "#f85149" }}>{error}</p>
      <button onClick={() => navigate("/")} className={styles.backBtn}>← Dashboard</button>
    </div>
  );

  if (!session) return (
    <div className={styles.center}>
      <p style={{ color: "var(--text-muted)" }}>Loading…</p>
    </div>
  );

  return (
    <div className={styles.layout}>
      {/* ── Toolbar ── */}
      <div className={styles.toolbar}>
        <button className={styles.backBtn} onClick={() => navigate("/")}>← Dashboard</button>
        <span className={styles.sessionTitle}>{session.title}</span>
        <div className={styles.right}>
          <PresencePanel
            peers={peers}
            connected={connected}
            selfUsername={user?.username}
          />
        </div>
      </div>

      {/* ── Editor ── */}
      <div className={styles.editorWrap}>
        <EditorPanel
          language={language}
          theme={theme}
          onMount={bindEditor}
          onLanguageChange={handleLanguageChange}
        />
      </div>
    </div>
  );
}
