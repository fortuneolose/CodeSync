/**
 * PresencePanel — shows connected collaborators with colour-coded avatars
 * and a live connection indicator.
 */
import type { PeerInfo } from "../hooks/useCollabEditor";
import styles from "./PresencePanel.module.css";

interface Props {
  peers: PeerInfo[];
  connected: boolean;
  selfUsername?: string;
  selfColor?: string;
}

export default function PresencePanel({ peers, connected, selfUsername, selfColor }: Props) {
  return (
    <div className={styles.panel}>
      <span className={`${styles.dot} ${connected ? styles.green : styles.red}`} title={connected ? "Connected" : "Reconnecting…"} />

      {/* Self */}
      {selfUsername && (
        <Avatar name={selfUsername} color={selfColor ?? "#58a6ff"} self />
      )}

      {/* Peers */}
      {peers.map((p) => (
        <Avatar key={p.clientId} name={p.user.name} color={p.user.color} />
      ))}

      {peers.length > 0 && (
        <span className={styles.count} title={`${peers.length} collaborator${peers.length > 1 ? "s" : ""} online`}>
          +{peers.length}
        </span>
      )}
    </div>
  );
}

function Avatar({ name, color, self }: { name: string; color: string; self?: boolean }) {
  return (
    <div
      className={styles.avatar}
      style={{ background: color, border: self ? "2px solid #fff" : `2px solid ${color}` }}
      title={self ? `${name} (you)` : name}
    >
      {name[0]?.toUpperCase()}
    </div>
  );
}
