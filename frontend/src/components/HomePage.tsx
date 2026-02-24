export default function HomePage() {
  return (
    <div style={{ display: "grid", placeItems: "center", height: "100vh" }}>
      <div style={{ textAlign: "center", gap: "1rem", display: "flex", flexDirection: "column" }}>
        <h1 style={{ fontSize: "2.5rem", fontWeight: 700 }}>
          Code<span style={{ color: "var(--accent)" }}>Sync</span>
        </h1>
        <p style={{ color: "var(--text-muted)" }}>
          Real-time collaborative code editor — coming soon.
        </p>
        <span style={{ color: "var(--green)", fontSize: "0.85rem" }}>
          ● scaffold ready
        </span>
      </div>
    </div>
  );
}
