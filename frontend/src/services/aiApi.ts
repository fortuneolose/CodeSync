const BASE = `${import.meta.env.VITE_API_URL ?? "/api"}/ai`;

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function streamRequest(
  path: string,
  body: object,
  onChunk: (text: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
    signal,
  });

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
