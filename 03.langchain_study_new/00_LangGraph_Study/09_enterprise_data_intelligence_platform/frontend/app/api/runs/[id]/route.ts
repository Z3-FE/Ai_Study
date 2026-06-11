import { proxyToFastApi } from "../../_proxy";

interface RunRouteContext {
  params: Promise<{
    id: string;
  }>;
}

export async function GET(request: Request, context: RunRouteContext) {
  const { id } = await context.params;
  return proxyToFastApi(request, ["runs", id]);
}
