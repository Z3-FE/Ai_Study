import { proxyToFastApi } from "../../_proxy";

interface ConversationRouteContext {
  params: Promise<{
    id: string;
  }>;
}

async function proxyConversation(request: Request, context: ConversationRouteContext) {
  /** 读取动态路由 id，并代理到 FastAPI 的单会话接口。 */

  const { id } = await context.params;
  return proxyToFastApi(request, ["conversations", id]);
}

export async function GET(request: Request, context: ConversationRouteContext) {
  /** 代理查询单个会话详情。 */

  return proxyConversation(request, context);
}

export async function PUT(request: Request, context: ConversationRouteContext) {
  /** 代理更新单个会话。 */

  return proxyConversation(request, context);
}

export async function DELETE(request: Request, context: ConversationRouteContext) {
  /** 代理删除单个会话。 */

  return proxyConversation(request, context);
}
