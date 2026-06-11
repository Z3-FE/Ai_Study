import { proxyToFastApi } from "../../../_proxy";

interface RunEventsRouteContext {
  params: Promise<{
    id: string;
  }>;
}

export async function GET(request: Request, context: RunEventsRouteContext) {
  const { id } = await context.params;
  return proxyToFastApi(request, ["runs", id, "events"]);
}
