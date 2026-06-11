const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://127.0.0.1:8000";

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

function buildTargetUrl(request: Request, path: string[]) {
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(`/api/${path.join("/")}`, FASTAPI_BASE_URL);
  targetUrl.search = incomingUrl.search;
  return targetUrl;
}

function buildForwardHeaders(request: Request) {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");

  if (contentType) headers.set("content-type", contentType);
  if (accept) headers.set("accept", accept);

  return headers;
}

function buildResponseHeaders(upstreamHeaders: Headers) {
  const headers = new Headers();

  upstreamHeaders.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  return headers;
}

export async function proxyToFastApi(request: Request, path: string[]) {
  const method = request.method.toUpperCase();
  const hasBody = method !== "GET" && method !== "HEAD";
  const targetUrl = buildTargetUrl(request, path);

  const upstream = await fetch(targetUrl, {
    method,
    headers: buildForwardHeaders(request),
    body: hasBody ? await request.arrayBuffer() : undefined,
    cache: "no-store",
  });

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: buildResponseHeaders(upstream.headers),
  });
}
