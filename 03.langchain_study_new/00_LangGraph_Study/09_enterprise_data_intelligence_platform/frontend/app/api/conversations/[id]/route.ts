import { proxyToFastApi } from "../../_proxy";

interface ConversationRouteContext {
  params: Promise<{
    id: string;
  }>;
}

async function proxyConversation(request: Request, context: ConversationRouteContext) {
  const { id } = await context.params;
  return proxyToFastApi(request, ["conversations", id]);
}

export async function GET(request: Request, context: ConversationRouteContext) {
  return proxyConversation(request, context);
}

export async function PUT(request: Request, context: ConversationRouteContext) {
  return proxyConversation(request, context);
}

export async function DELETE(request: Request, context: ConversationRouteContext) {
  return proxyConversation(request, context);
}
