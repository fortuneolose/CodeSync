import { useState } from "react";
import { LANGUAGES } from "./EditorPanel";
import styles from "./CreateSessionModal.module.css";

interface Props {
  onClose: () => void;
  onCreate: (title: string, language: string, isPublic: boolean) => Promise<void>;
}

export default function CreateSessionModal({ onClose, onCreate }: Props) {
  const [title, setTitle] = useState("Untitled");
  const [language, setLanguage] = useState("python");
  const [isPublic, setIsPublic] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try { await onCreate(title, language, isPublic); }
    finally { setLoading(false); }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <form className={styles.modal} onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2 className={styles.title}>New session</h2>
        <label className={styles.label}>Title
          <input className={styles.input} value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label className={styles.label}>Language
          <select className={styles.input} value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </label>
        <label className={styles.checkRow}>
          <input type="checkbox" checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />
          Public (anyone with the link can join)
        </label>
        <div className={styles.actions}>
          <button type="button" className={styles.cancel} onClick={onClose}>Cancel</button>
          <button type="submit" className={styles.create} disabled={loading}>
            {loading ? "Creating…" : "Create"}
          </button>
        </div>
      </form>
    </div>
  );
}
