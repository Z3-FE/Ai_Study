import { proxyToFastApi } from "../../../_proxy";

interface RunEventsRouteContext {
  params: Promise<{
    id: string;
  }>;
}

export async function GET(request: Request, context: RunEventsRouteContext) {
  /** 代理某个 run 的 SSE 事件流。 */

  const { id } = await context.params;
  return proxyToFastApi(request, ["runs", id, "events"]);
}
