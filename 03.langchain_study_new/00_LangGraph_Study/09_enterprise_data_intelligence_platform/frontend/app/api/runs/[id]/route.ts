import { proxyToFastApi } from "../../_proxy";

interface RunRouteContext {
  params: Promise<{
    id: string;
  }>;
}

export async function GET(request: Request, context: RunRouteContext) {
  /** 代理查询某个 run 的状态。 */

  const { id } = await context.params;
  return proxyToFastApi(request, ["runs", id]);
}
