const GET_REPLAY_WINDOW_MS = 1000;
const inFlightGetRequests = new Map<string, Promise<any>>();
const recentGetResponses = new Map<string, { data: any; expiresAt: number }>();

export async function apiGet(path: string): Promise<any> {
  const url = path;
  const now = Date.now();
  const recent = recentGetResponses.get(url);

  if (recent && recent.expiresAt > now) {
    return recent.data;
  }

  if (recent) {
    recentGetResponses.delete(url);
  }

  const inFlight = inFlightGetRequests.get(url);

  if (inFlight) {
    return inFlight;
  }

  // React dev Strict Mode can run effects twice; collapse duplicate GETs here.
  const request = fetch(url, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  })
    .then(async (response) => {
      const data: any = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail ?? "接口请求失败");
      }

      recentGetResponses.set(url, {
        data,
        expiresAt: Date.now() + GET_REPLAY_WINDOW_MS,
      });

      return data;
    })
    .finally(() => {
      inFlightGetRequests.delete(url);
    });

  inFlightGetRequests.set(url, request);

  return request;
}

export async function apiPost(path: string, body: unknown): Promise<any> {
  const response = await fetch(path, {
    method: "POST",
    cache: "no-store",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const data: any = await response.json();

  if (!response.ok) {
    throw new Error(data?.detail ?? "接口请求失败");
  }

  return data;
}
