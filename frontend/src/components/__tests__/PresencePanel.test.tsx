import { render, screen } from "@testing-library/react";
import PresencePanel from "../PresencePanel";
import type { PeerInfo } from "../../hooks/useCollabEditor";

const PEERS: PeerInfo[] = [
  { clientId: 1, user: { name: "alice", color: "#f78166" } },
  { clientId: 2, user: { name: "bob",   color: "#79c0ff" } },
];

describe("PresencePanel", () => {
  it("renders connection status title for connected", () => {
    render(<PresencePanel peers={[]} connected={true} />);
    const dot = document.querySelector("[title='Connected']");
    expect(dot).toBeTruthy();
  });

  it("renders connection status title for disconnected", () => {
    render(<PresencePanel peers={[]} connected={false} />);
    const dot = document.querySelector("[title='Reconnecting…']");
    expect(dot).toBeTruthy();
  });

  it("renders self avatar with '(you)' suffix in title", () => {
    render(<PresencePanel peers={[]} connected={true} selfUsername="carol" />);
    expect(screen.getByTitle("carol (you)")).toBeTruthy();
  });

  it("renders peer count when peers present", () => {
    render(<PresencePanel peers={PEERS} connected={true} />);
    expect(screen.getByText("+2")).toBeTruthy();
  });

  it("renders peer avatars by name", () => {
    render(<PresencePanel peers={PEERS} connected={true} />);
    expect(screen.getByTitle("alice")).toBeTruthy();
    expect(screen.getByTitle("bob")).toBeTruthy();
  });
});
