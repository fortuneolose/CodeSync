const BASE = `${import.meta.env.VITE_API_URL ?? "/api"}/ai`;
const AUTH_BASE = import.meta.env.VITE_API_URL ?? "/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return null;
  try {
    const res = await fetch(`${AUTH_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    if (data.refresh_token) localStorage.setItem("refresh_token", data.refresh_token);
    return data.access_token;
  } catch {
    return null;
  }
}

async function streamRequest(
  path: string,
  body: object,
  onChunk: (text: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const doFetch = (token: string | null) =>
    fetch(`${BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
      signal,
    });

  let res = await doFetch(getToken());

  // On 401, attempt a token refresh and retry once
  if (res.status === 401) {
    const newToken = await refreshAccessToken();
    if (!newToken) throw new Error(`AI request failed: ${res.status}`);
    res = await doFetch(newToken);
  }

  if (!res.ok) throw new Error(`AI request failed: ${res.status}`);
  if (!res.body) return;

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6).trim();
      if (payload === "[DONE]") return;
      try {
        const parsed = JSON.parse(payload);
        if (parsed.content) onChunk(parsed.content);
      } catch { /* ignore malformed */ }
    }
  }
}

export const aiApi = {
  explain: (slug: string, code: string, language: string, onChunk: (t: string) => void, signal?: AbortSignal) =>
    streamRequest("/explain", { slug, code, language }, onChunk, signal),

  refactor: (slug: string, code: string, language: string, onChunk: (t: string) => void, signal?: AbortSignal) =>
    streamRequest("/refactor", { slug, code, language }, onChunk, signal),

  chat: (slug: string, code: string, language: string, message: string, history: ChatMessage[], onChunk: (t: string) => void, signal?: AbortSignal) =>
    streamRequest("/chat", { slug, code, language, message, history }, onChunk, signal),
};
