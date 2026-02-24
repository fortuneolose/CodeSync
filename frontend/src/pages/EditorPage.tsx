import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import EditorPanel from "../components/EditorPanel";
import { sessionApi, type SessionWithMembers } from "../services/sessionApi";
import styles from "./EditorPage.module.css";

interface EditorPageProps {
  theme: "vs-dark" | "vs";
}

export default function EditorPage({ theme }: EditorPageProps) {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<SessionWithMembers | null>(null);
  const [content, setContent] = useState("");
  const [language, setLanguage] = useState("python");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const saveTimer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (!slug) return;
    sessionApi.get(slug)
      .then(({ data }) => {
        setSession(data);
        setContent(data.content);
        setLanguage(data.language);
      })
      .catch(() => setError("Session not found or access denied."));
  }, [slug]);

  const autoSave = (newContent: string, newLang?: string) => {
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      if (!slug) return;
      setSaving(true);
      await sessionApi.update(slug, { content: newContent, language: newLang ?? language }).catch(() => {});
      setSaving(false);
    }, 800);
  };

  const handleContentChange = (val: string) => {
    setContent(val);
    autoSave(val);
  };

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    autoSave(content, lang);
  };

  if (error) return (
    <div className={styles.center}>
      <p style={{ color: "#f85149" }}>{error}</p>
      <button onClick={() => navigate("/")} className={styles.backBtn}>← Back to dashboard</button>
    </div>
  );

  if (!session) return <div className={styles.center}><p style={{ color: "var(--text-muted)" }}>Loading…</p></div>;

  return (
    <div className={styles.layout}>
      <div className={styles.toolbar}>
        <button className={styles.backBtn} onClick={() => navigate("/")}>← Dashboard</button>
        <span className={styles.sessionTitle}>{session.title}</span>
        <div className={styles.right}>
          {saving && <span className={styles.saving}>Saving…</span>}
          <div className={styles.members}>
            {session.members.map((m) => (
              <span key={m.user_id} className={styles.avatar} title={`${m.username} (${m.role})`}>
                {m.username[0].toUpperCase()}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className={styles.editorWrap}>
        <EditorPanel
          value={content}
          language={language}
          theme={theme}
          onChange={handleContentChange}
          onLanguageChange={handleLanguageChange}
        />
      </div>
    </div>
  );
}
