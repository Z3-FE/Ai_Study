import { proxyToFastApi } from "../_proxy";

export async function GET(request: Request) {
  return proxyToFastApi(request, ["conversations"]);
}

export async function POST(request: Request) {
  return proxyToFastApi(request, ["conversations"]);
}
