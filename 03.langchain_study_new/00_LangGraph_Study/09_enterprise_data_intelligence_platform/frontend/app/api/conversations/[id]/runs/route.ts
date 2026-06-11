import { proxyToFastApi } from "../../../_proxy";

interface ConversationRunsRouteContext {
  params: Promise<{
    id: string;
  }>;
}

export async function POST(request: Request, context: ConversationRunsRouteContext) {
  const { id } = await context.params;
  return proxyToFastApi(request, ["conversations", id, "runs"]);
}
