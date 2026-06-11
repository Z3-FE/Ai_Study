# Frontend（assistant-ui + Next.js）

这个前端来自 [assistant-ui](https://github.com/assistant-ui/assistant-ui) 的 LangGraph 模板，  
但已经改为连接你自己的 **Python LangGraph 后端**（`../server`）。

## 快速启动

1. 先在 `07_project_all` 根目录启动后端：

```bash
uv run langgraph dev --config server/langgraph.json --host 127.0.0.1 --port 2024 --no-reload
```

2. 再启动前端：

```bash
npm install
npm run dev
```

3. 访问地址：

- [http://127.0.0.1:3000](http://127.0.0.1:3000)（Next.js 前端）
- [http://127.0.0.1:2024/docs](http://127.0.0.1:2024/docs)（LangGraph 后端文档）

## 环境变量

`.env.local` 建议至少包含：

```env
LANGGRAPH_API_URL=http://127.0.0.1:2024
NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID=agent
```

## 目录速读

```text
app/assistant.tsx            # 构建 assistant-ui runtime（LangGraph stream）
app/api/[..._path]/route.ts  # 代理 /api 请求到 LANGGRAPH_API_URL
lib/chatApi.ts               # LangGraph SDK client 创建
components/assistant-ui/     # 聊天 UI 组件
backend/agent.ts             # 模板 JS 后端（当前不用）
```

`app/assistant.tsx` 使用 `@assistant-ui/react-langgraph` 的 `unstable_createLangGraphStream(...)` 连接后端流式结果。
