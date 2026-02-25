/**
 * useCollabEditor
 *
 * Wires a Yjs document to a Monaco editor instance via:
 *  - y-websocket  →  connects to backend WS and syncs Yjs updates
 *  - y-monaco     →  binds the Yjs text to the Monaco model
 *
 * Awareness messages (cursor positions, user colours) are handled by the
 * WebsocketProvider automatically; the EditorPage reads provider.awareness
 * to render the presence list.
 */
import { useEffect, useRef, useState } from "react";
import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";
import { MonacoBinding } from "y-monaco";
import type * as Monaco from "monaco-editor";
import { useAuthStore } from "../store/authStore";

export interface PeerInfo {
  clientId: number;
  user: { name: string; color: string };
  cursor?: { line: number; col: number };
}

const COLORS = [
  "#f78166", "#79c0ff", "#56d364", "#ffa657",
  "#d2a8ff", "#ff7b72", "#a5d6ff", "#7ee787",
];

function hashColor(str: string): string {
  let h = 5381;
  for (let i = 0; i < str.length; i++) h = ((h << 5) + h) ^ str.charCodeAt(i);
  return COLORS[Math.abs(h) % COLORS.length];
}

export function useCollabEditor(slug: string) {
  const { user } = useAuthStore();
  const ydocRef = useRef<Y.Doc | null>(null);
  const providerRef = useRef<WebsocketProvider | null>(null);
  const bindingRef = useRef<MonacoBinding | null>(null);
  const [connected, setConnected] = useState(false);
  const [peers, setPeers] = useState<PeerInfo[]>([]);

  const destroy = () => {
    bindingRef.current?.destroy();
    providerRef.current?.destroy();
    ydocRef.current?.destroy();
    bindingRef.current = null;
    providerRef.current = null;
    ydocRef.current = null;
    setConnected(false);
    setPeers([]);
  };

  const bindEditor = (
    editor: Monaco.editor.IStandaloneCodeEditor,
    _monaco: typeof Monaco,
  ) => {
    destroy(); // clean up any previous binding

    const token = localStorage.getItem("access_token") ?? "";
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const wsBase = import.meta.env.VITE_WS_URL ??
      `${proto}://${window.location.host}/ws`;

    const ydoc = new Y.Doc();
    ydocRef.current = ydoc;

    const provider = new WebsocketProvider(wsBase, slug, ydoc, {
      params: { token },
    });
    providerRef.current = provider;

    // Set local user awareness state
    provider.awareness.setLocalStateField("user", {
      name: user?.username ?? "anonymous",
      color: hashColor(user?.id ?? slug),
    });

    provider.on("status", ({ status }: { status: string }) => {
      setConnected(status === "connected");
    });

    // Track peer awareness for presence panel
    const updatePeers = () => {
      const states = provider.awareness.getStates();
      const list: PeerInfo[] = [];
      states.forEach((state, clientId) => {
        if (clientId !== provider.awareness.clientID && state.user) {
          list.push({ clientId, user: state.user, cursor: state.cursor });
        }
      });
      setPeers(list);
    };
    provider.awareness.on("change", updatePeers);

    const binding = new MonacoBinding(
      ydoc.getText("content"),
      editor.getModel()!,
      new Set([editor]),
      provider.awareness,
    );
    bindingRef.current = binding;
  };

  // Cleanup when slug changes or component unmounts
  useEffect(() => {
    return () => { destroy(); };
  }, [slug]);

  return { bindEditor, destroy, connected, peers };
}
