import { ayahCountOf } from "@/lib/surahs";

const MCP_URL = "https://mcp.tafsir.net/mcp";
const TAFSIR_SOURCE = "mukhtasar_ar";
const MCP_TIMEOUT_MS = 25_000;

interface TafsirResult {
  surah: number;
  ayah: number;
  attribution: string;
  text: string;
}

class RateLimitError extends Error {}

// Tafsir of a verse is immutable — cache for the lifetime of the server process.
const cache = new Map<string, TafsirResult>();

const MCP_HEADERS: Record<string, string> = {
  "Content-Type": "application/json",
  Accept: "application/json, text/event-stream",
};

/** MCP replies as SSE (`data: {...}`) or plain JSON — handle both. */
function parseMcpBody(text: string): unknown {
  const trimmed = text.trim();
  if (trimmed.startsWith("{")) {
    try {
      return JSON.parse(trimmed);
    } catch {
      /* fall through to SSE parsing */
    }
  }
  for (const line of trimmed.split(/\r?\n/)) {
    const l = line.trim();
    if (l.startsWith("data:")) {
      const json = l.slice(5).trim();
      if (json.startsWith("{")) {
        try {
          return JSON.parse(json);
        } catch {
          /* ignore malformed event */
        }
      }
    }
  }
  return null;
}

function mcpPost(body: object, sessionId?: string): Promise<Response> {
  const headers = { ...MCP_HEADERS };
  if (sessionId) headers["mcp-session-id"] = sessionId;
  return fetch(MCP_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(MCP_TIMEOUT_MS),
  });
}

async function fetchTafsir(surah: number, ayah: number): Promise<TafsirResult> {
  // 1. initialize — the session id comes back in a response header
  const initRes = await mcpPost({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2025-06-18",
      capabilities: {},
      clientInfo: { name: "student-dashboard", version: "1.0" },
    },
  });
  if (initRes.status === 429) throw new RateLimitError();
  if (!initRes.ok) throw new Error(`MCP initialize failed: ${initRes.status}`);
  const sessionId = initRes.headers.get("mcp-session-id");
  await initRes.text(); // drain
  if (!sessionId) throw new Error("MCP: missing session id");

  // 2. acknowledge initialization (notification — no response payload)
  await mcpPost({ jsonrpc: "2.0", method: "notifications/initialized" }, sessionId).then(
    (r) => r.text(),
  );

  // 3. call the fetch_tafsir tool
  const callRes = await mcpPost(
    {
      jsonrpc: "2.0",
      id: 2,
      method: "tools/call",
      params: {
        name: "fetch_tafsir",
        arguments: { surah, ayah, sources: [TAFSIR_SOURCE] },
      },
    },
    sessionId,
  );
  if (callRes.status === 429) throw new RateLimitError();
  if (!callRes.ok) throw new Error(`MCP tools/call failed: ${callRes.status}`);

  const rpc = parseMcpBody(await callRes.text()) as
    | { result?: { content?: Array<{ text?: string }>; isError?: boolean } }
    | null;
  const contentText = rpc?.result?.content?.[0]?.text;
  if (!contentText) throw new Error("MCP: unexpected response shape");

  if (rpc?.result?.isError && /\b429\b|rate.?limit|reset_in/i.test(contentText)) {
    throw new RateLimitError();
  }

  const payload = JSON.parse(contentText) as {
    tafsirs?: Array<{ attribution?: string; text?: string }>;
  };
  const entry = payload.tafsirs?.[0];
  if (!entry?.text) throw new Error("MCP: no tafsir text in response");

  return {
    surah,
    ayah,
    attribution: entry.attribution ?? "",
    text: entry.text,
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const surah = Number(searchParams.get("surah"));
  const ayah = Number(searchParams.get("ayah"));

  if (
    !Number.isInteger(surah) ||
    surah < 1 ||
    surah > 114 ||
    !Number.isInteger(ayah) ||
    ayah < 1 ||
    ayah > ayahCountOf(surah)
  ) {
    return Response.json({ error: "bad_request" }, { status: 400 });
  }

  const key = `${surah}:${ayah}`;
  const cached = cache.get(key);
  if (cached) {
    return Response.json(cached, {
      headers: { "Cache-Control": "public, max-age=31536000, immutable" },
    });
  }

  try {
    const result = await fetchTafsir(surah, ayah);
    cache.set(key, result);
    return Response.json(result, {
      headers: { "Cache-Control": "public, max-age=31536000, immutable" },
    });
  } catch (err) {
    if (err instanceof RateLimitError) {
      return Response.json({ error: "rate_limited" }, { status: 429 });
    }
    console.error("tafsir route error:", err);
    return Response.json({ error: "unavailable" }, { status: 502 });
  }
}
