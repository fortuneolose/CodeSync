/**
 * AiPanel — sliding right-side panel with three AI modes:
 *   Explain · Refactor · Chat
 * Responses stream in token-by-token via SSE.
 */
import { useRef, useState } from "react";
import { aiApi, type ChatMessage } from "../services/aiApi";
import styles from "./AiPanel.module.css";

interface Props {
  slug: string;
  getCode: () => string;
  language: string;
  onClose: () => void;
}

type Mode = "explain" | "refactor" | "chat";

export default function AiPanel({ slug, getCode, language, onClose }: Props) {
  const [mode, setMode] = useState<Mode>("explain");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  const append = (chunk: string) =>
    setOutput((prev) => {
      const next = prev + chunk;
      requestAnimationFrame(() => {
        if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
      });
      return next;
    });

  const run = async (userMessage?: string) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setOutput("");
    setLoading(true);

    const code = getCode();
    try {
      if (mode === "explain") {
        await aiApi.explain(slug, code, language, append, ctrl.signal);
      } else if (mode === "refactor") {
        await aiApi.refactor(slug, code, language, append, ctrl.signal);
      } else {
        const msg = userMessage ?? chatInput;
        if (!msg.trim()) return;
        const newHistory: ChatMessage[] = [...history, { role: "user", content: msg }];
        let response = "";
        await aiApi.chat(slug, code, language, msg, history, (chunk) => {
          append(chunk);
          response += chunk;
        }, ctrl.signal);
        setHistory([...newHistory, { role: "assistant", content: response }]);
        setChatInput("");
      }
    } catch (e: any) {
      if (e?.name !== "AbortError") setOutput((p) => p + "\n\n[Error: request failed]");
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (m: Mode) => {
    setMode(m);
    setOutput("");
    setHistory([]);
  };

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.header}>
        <span className={styles.title}>✦ AI Assistant</span>
        <button className={styles.close} onClick={onClose}>✕</button>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        {(["explain", "refactor", "chat"] as Mode[]).map((m) => (
          <button
            key={m}
            className={`${styles.tab} ${mode === m ? styles.activeTab : ""}`}
            onClick={() => switchMode(m)}
          >
            {m.charAt(0).toUpperCase() + m.slice(1)}
          </button>
        ))}
      </div>

      {/* Output */}
      <div className={styles.output} ref={outputRef}>
        {output ? (
          <pre className={styles.pre}>{output}</pre>
        ) : (
          <p className={styles.placeholder}>
            {mode === "explain" && "Click Explain to understand the current code."}
            {mode === "refactor" && "Click Refactor to get improvement suggestions."}
            {mode === "chat" && "Ask anything about the code in the chat below."}
          </p>
        )}
        {loading && <span className={styles.cursor}>▌</span>}
      </div>

      {/* Actions */}
      {mode !== "chat" ? (
        <div className={styles.footer}>
          <button
            className={styles.runBtn}
            onClick={() => run()}
            disabled={loading}
          >
            {loading ? "Thinking…" : mode === "explain" ? "Explain code" : "Refactor code"}
          </button>
          {loading && (
            <button className={styles.stopBtn} onClick={() => abortRef.current?.abort()}>Stop</button>
          )}
        </div>
      ) : (
        <form className={styles.chatForm} onSubmit={(e) => { e.preventDefault(); run(); }}>
          <input
            className={styles.chatInput}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask about the code…"
            disabled={loading}
            autoFocus
          />
          <button className={styles.runBtn} type="submit" disabled={loading || !chatInput.trim()}>
            {loading ? "…" : "Send"}
          </button>
        </form>
      )}
    </div>
  );
}
