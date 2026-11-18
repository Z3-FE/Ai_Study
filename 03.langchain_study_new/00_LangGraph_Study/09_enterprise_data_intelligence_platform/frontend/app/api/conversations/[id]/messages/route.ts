import { proxyToFastApi } from "../../../_proxy";

interface ConversationMessagesRouteContext {
  params: Promise<{
    id: string;
  }>;
}

async function proxyConversationMessages(
  request: Request,
  context: ConversationMessagesRouteContext,
) {
  /** 读取会话 id，并代理到 FastAPI 的会话消息接口。 */

  const { id } = await context.params;
  return proxyToFastApi(request, ["conversations", id, "messages"]);
}

export async function GET(request: Request, context: ConversationMessagesRouteContext) {
  /** 代理查询会话消息列表。 */

  return proxyConversationMessages(request, context);
}

export async function POST(request: Request, context: ConversationMessagesRouteContext) {
  /** 代理新增会话消息。 */

  return proxyConversationMessages(request, context);
}
