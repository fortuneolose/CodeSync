/**
 * Unit tests for the SSE stream client in aiApi.ts.
 * We mock the global fetch to simulate different server payloads.
 */
import { aiApi } from "../aiApi";

function makeReadableStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) {
        controller.enqueue(encoder.encode(chunks[i++]));
      } else {
        controller.close();
      }
    },
  });
}

function mockFetch(chunks: string[], status = 200) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: status === 200,
    status,
    body: makeReadableStream(chunks),
  }));
}

describe("aiApi SSE client", () => {
  afterEach(() => { vi.unstubAllGlobals(); });

  it("collects streamed content tokens", async () => {
    mockFetch([
      'data: {"content":"Hello"}\n\n',
      'data: {"content":" world"}\n\n',
      "data: [DONE]\n\n",
    ]);
    const tokens: string[] = [];
    await aiApi.explain("slug1", "print(1)", "python", (t) => tokens.push(t));
    expect(tokens).toEqual(["Hello", " world"]);
  });

  it("stops collecting after [DONE]", async () => {
    mockFetch([
      'data: {"content":"tok"}\n\ndata: [DONE]\n\ndata: {"content":"ignored"}\n\n',
    ]);
    const tokens: string[] = [];
    await aiApi.chat("s", "", "python", "q", [], (t) => tokens.push(t));
    expect(tokens).toEqual(["tok"]);
  });

  it("ignores malformed JSON lines", async () => {
    mockFetch([
      'data: not-json\n\ndata: {"content":"ok"}\n\ndata: [DONE]\n\n',
    ]);
    const tokens: string[] = [];
    await aiApi.refactor("s", "code", "python", (t) => tokens.push(t));
    expect(tokens).toEqual(["ok"]);
  });

  it("throws on non-200 response", async () => {
    mockFetch([], 403);
    await expect(
      aiApi.explain("s", "x", "python", () => {})
    ).rejects.toThrow("403");
  });
});
