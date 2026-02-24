/**
 * SnapshotPanel — right-side panel for creating, listing, and restoring snapshots.
 * Restore triggers a controlled Yjs re-init so collaborators see the change live.
 */
import { useEffect, useState } from "react";
import { snapshotApi, type Snapshot } from "../services/snapshotApi";
import styles from "./SnapshotPanel.module.css";

interface Props {
  slug: string;
  isOwner: boolean;
  getCode: () => string;
  language: string;
  onRestored: (content: string, language: string) => void;
  onClose: () => void;
}

export default function SnapshotPanel({ slug, isOwner, getCode, language, onRestored, onClose }: Props) {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () =>
    snapshotApi.list(slug).then(({ data }) => setSnapshots(data));

  useEffect(() => { load(); }, [slug]);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      await snapshotApi.create(slug, title, getCode(), language);
      setTitle("");
      setMsg("Snapshot saved!");
      await load();
      setTimeout(() => setMsg(""), 2500);
    } finally {
      setSaving(false);
    }
  };

  const restore = async (snap: Snapshot) => {
    if (!confirm(`Restore "${snap.title}"? This will overwrite the current session for all users.`)) return;
    const { data } = await snapshotApi.restore(slug, snap.id);
    onRestored(data.content, data.language);
    setMsg("Restored! Editor reinitialised.");
    setTimeout(() => setMsg(""), 3000);
  };

  const remove = async (snap: Snapshot) => {
    if (!confirm(`Delete snapshot "${snap.title}"?`)) return;
    await snapshotApi.delete(slug, snap.id);
    await load();
  };

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.title}>📸 Snapshots</span>
        <button className={styles.close} onClick={onClose}>✕</button>
      </div>

      {/* Create */}
      <form className={styles.form} onSubmit={save}>
        <input
          className={styles.input}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Snapshot name…"
          required
        />
        <button className={styles.saveBtn} type="submit" disabled={saving}>
          {saving ? "…" : "Save"}
        </button>
      </form>

      {msg && <p className={styles.msg}>{msg}</p>}

      {/* List */}
      <div className={styles.list}>
        {snapshots.length === 0 && <p className={styles.empty}>No snapshots yet.</p>}
        {snapshots.map((s) => (
          <div key={s.id} className={styles.item}>
            <div className={styles.itemMeta}>
              <span className={styles.itemTitle}>{s.title}</span>
              <span className={styles.itemDate}>
                {new Date(s.created_at).toLocaleString()} · {s.author_username ?? "?"}
              </span>
            </div>
            <div className={styles.itemActions}>
              {isOwner && (
                <button className={styles.restoreBtn} onClick={() => restore(s)}>Restore</button>
              )}
              <button className={styles.deleteBtn} onClick={() => remove(s)}>✕</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
