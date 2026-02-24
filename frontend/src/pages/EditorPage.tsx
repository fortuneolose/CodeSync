import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type * as Monaco from "monaco-editor";
import EditorPanel from "../components/EditorPanel";
import PresencePanel from "../components/PresencePanel";
import AiPanel from "../components/AiPanel";
import SnapshotPanel from "../components/SnapshotPanel";
import { sessionApi, type SessionWithMembers } from "../services/sessionApi";
import { useCollabEditor } from "../hooks/useCollabEditor";
import { useAuthStore } from "../store/authStore";
import styles from "./EditorPage.module.css";

type SidePanel = "ai" | "snapshots" | null;

interface Props { theme: "vs-dark" | "vs" }

export default function EditorPage({ theme }: Props) {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [session, setSession] = useState<SessionWithMembers | null>(null);
  const [language, setLanguage] = useState("python");
  const [error, setError] = useState("");
  const [sidePanel, setSidePanel] = useState<SidePanel>(null);

  // Hold a ref to the live Monaco editor instance for AI/snapshot access
  const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);

  const { bindEditor, connected, peers } = useCollabEditor(slug ?? "");

  // Load session metadata
  useEffect(() => {
    if (!slug) return;
    sessionApi.get(slug)
      .then(({ data }) => { setSession(data); setLanguage(data.language); })
      .catch(() => setError("Session not found or access denied."));
  }, [slug]);

  // onMount: capture editor ref AND bind Yjs
  const handleEditorMount = (
    editor: Monaco.editor.IStandaloneCodeEditor,
    monaco: typeof Monaco,
  ) => {
    editorRef.current = editor;
    bindEditor(editor, monaco);
  };

  const getCode = () => editorRef.current?.getValue() ?? "";

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    if (slug) sessionApi.update(slug, { language: lang }).catch(() => {});
  };

  // Snapshot restore: reinit Yjs with restored content
  const handleRestored = (content: string, lang: string) => {
    setLanguage(lang);
    const editor = editorRef.current;
    if (editor) {
      // Let Yjs handle the value update; just set it directly on the model
      // The Yjs provider will sync it to peers on next update
      editor.setValue(content);
    }
    if (slug) sessionApi.update(slug, { language: lang, content }).catch(() => {});
    setSidePanel(null);
  };

  const togglePanel = (panel: SidePanel) =>
    setSidePanel((prev) => (prev === panel ? null : panel));

  const isOwner = session?.owner_id === user?.id;

  if (error) return (
    <div className={styles.center}>
      <p style={{ color: "#f85149" }}>{error}</p>
      <button className={styles.backBtn} onClick={() => navigate("/")}>← Dashboard</button>
    </div>
  );
  if (!session) return <div className={styles.center}><p style={{ color: "var(--text-muted)" }}>Loading…</p></div>;

  return (
    <div className={styles.layout}>
      {/* ── Toolbar ── */}
      <div className={styles.toolbar}>
        <button className={styles.backBtn} onClick={() => navigate("/")}>← Dashboard</button>
        <span className={styles.sessionTitle}>{session.title}</span>

        <div className={styles.right}>
          <PresencePanel peers={peers} connected={connected} selfUsername={user?.username} />

          <button
            className={`${styles.panelBtn} ${sidePanel === "snapshots" ? styles.active : ""}`}
            onClick={() => togglePanel("snapshots")}
            title="Snapshots"
          >📸</button>

          <button
            className={`${styles.panelBtn} ${sidePanel === "ai" ? styles.active : ""}`}
            onClick={() => togglePanel("ai")}
            title="AI Assistant"
          >✦ AI</button>
        </div>
      </div>

      {/* ── Body: editor + optional side panel ── */}
      <div className={styles.body}>
        <div className={styles.editorWrap}>
          <EditorPanel
            language={language}
            theme={theme}
            onMount={handleEditorMount}
            onLanguageChange={handleLanguageChange}
          />
        </div>

        {sidePanel === "ai" && (
          <AiPanel
            slug={slug!}
            getCode={getCode}
            language={language}
            onClose={() => setSidePanel(null)}
          />
        )}

        {sidePanel === "snapshots" && (
          <SnapshotPanel
            slug={slug!}
            isOwner={isOwner}
            getCode={getCode}
            language={language}
            onRestored={handleRestored}
            onClose={() => setSidePanel(null)}
          />
        )}
      </div>
    </div>
  );
}
