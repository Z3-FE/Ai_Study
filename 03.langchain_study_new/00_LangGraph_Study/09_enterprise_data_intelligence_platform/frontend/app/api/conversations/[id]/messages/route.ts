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
  const { id } = await context.params;
  return proxyToFastApi(request, ["conversations", id, "messages"]);
}

export async function GET(request: Request, context: ConversationMessagesRouteContext) {
  return proxyConversationMessages(request, context);
}

export async function POST(request: Request, context: ConversationMessagesRouteContext) {
  return proxyConversationMessages(request, context);
}
