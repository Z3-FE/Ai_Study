import { proxyToFastApi } from "../../../_proxy";

interface ConversationRunsRouteContext {
  params: Promise<{
    id: string;
  }>;
}

export async function POST(request: Request, context: ConversationRunsRouteContext) {
  /** 代理创建会话 run，并返回后续订阅 SSE 的地址。 */

  const { id } = await context.params;
  return proxyToFastApi(request, ["conversations", id, "runs"]);
}
