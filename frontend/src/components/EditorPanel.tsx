import MonacoEditor, { type OnMount } from "@monaco-editor/react";

export const LANGUAGES = [
  "python", "javascript", "typescript", "java", "cpp", "c",
  "go", "rust", "html", "css", "json", "markdown", "plaintext",
];

interface EditorPanelProps {
  language: string;
  theme: "vs-dark" | "vs";
  readOnly?: boolean;
  /** Called once Monaco editor + model are ready — used to bind Yjs */
  onMount?: OnMount;
  onLanguageChange?: (lang: string) => void;
}

export default function EditorPanel({
  language, theme, readOnly = false, onMount, onLanguageChange,
}: EditorPanelProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      <div style={{
        display: "flex", alignItems: "center", gap: "0.5rem",
        padding: "0.4rem 0.75rem", background: "var(--surface)",
        borderBottom: "1px solid var(--border)", flexShrink: 0,
      }}>
        <label style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Language</label>
        <select
          value={language}
          onChange={(e) => onLanguageChange?.(e.target.value)}
          disabled={readOnly}
          style={{
            background: "var(--bg)", color: "var(--text)",
            border: "1px solid var(--border)", borderRadius: 4,
            padding: "2px 6px", fontSize: "0.8rem", cursor: readOnly ? "not-allowed" : "pointer",
          }}
        >
          {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        <MonacoEditor
          height="100%"
          language={language}
          theme={theme}
          defaultValue=""
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            wordWrap: "on",
            readOnly,
            scrollBeyondLastLine: false,
            lineNumbers: "on",
            renderLineHighlight: "all",
            padding: { top: 12 },
          }}
          onMount={onMount}
        />
      </div>
    </div>
  );
}
