import { proxyToFastApi } from "../_proxy";

interface ApiProxyContext {
  params: Promise<{
    path: string[];
  }>;
}

async function proxyCatchAll(request: Request, context: ApiProxyContext) {
  /** 兜底代理未单独声明的 API 路径。 */

  const { path } = await context.params;
  return proxyToFastApi(request, path);
}

export async function GET(request: Request, context: ApiProxyContext) {
  /** 兜底代理 GET 请求。 */

  return proxyCatchAll(request, context);
}

export async function POST(request: Request, context: ApiProxyContext) {
  /** 兜底代理 POST 请求。 */

  return proxyCatchAll(request, context);
}

export async function PUT(request: Request, context: ApiProxyContext) {
  /** 兜底代理 PUT 请求。 */

  return proxyCatchAll(request, context);
}

export async function PATCH(request: Request, context: ApiProxyContext) {
  /** 兜底代理 PATCH 请求。 */

  return proxyCatchAll(request, context);
}

export async function DELETE(request: Request, context: ApiProxyContext) {
  /** 兜底代理 DELETE 请求。 */

  return proxyCatchAll(request, context);
}
