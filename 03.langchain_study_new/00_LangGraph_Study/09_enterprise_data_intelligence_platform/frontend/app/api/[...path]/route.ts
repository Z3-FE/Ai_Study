import { proxyToFastApi } from "../_proxy";

interface ApiProxyContext {
  params: Promise<{
    path: string[];
  }>;
}

async function proxyCatchAll(request: Request, context: ApiProxyContext) {
  const { path } = await context.params;
  return proxyToFastApi(request, path);
}

export async function GET(request: Request, context: ApiProxyContext) {
  return proxyCatchAll(request, context);
}

export async function POST(request: Request, context: ApiProxyContext) {
  return proxyCatchAll(request, context);
}

export async function PUT(request: Request, context: ApiProxyContext) {
  return proxyCatchAll(request, context);
}

export async function PATCH(request: Request, context: ApiProxyContext) {
  return proxyCatchAll(request, context);
}

export async function DELETE(request: Request, context: ApiProxyContext) {
  return proxyCatchAll(request, context);
}
