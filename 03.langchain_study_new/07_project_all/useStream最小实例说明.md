**useStream 最小实例说明**

这份实例对应官方 Frontend 章节的标准架构：

- 后端：LangGraph Agent Server
- 前端：`useStream`

和你前面那个 `FastAPI + fetch` 版本不一样：

- `fetch` 版
  - 前端请求你自己写的 `/chat`
  - 返回一整段结果

- `useStream` 版
  - 前端直接连接 LangGraph Agent Server
  - 实时拿到 `messages`、`history`、`loading state`
  - 更接近官方推荐架构

官方参考：
- [Frontend Overview](https://docs.langchain.com/oss/python/langchain/frontend/overview)
- [UI-Library integrations](https://docs.langchain.com/oss/python/langchain/frontend/integrations)
- [Run a local server](https://docs.langchain.com/oss/python/langgraph/local-server)

**目录结构**

新增的文件有：

- [langgraph.json](/Users/z523/Desktop/zizhi/ai_Python/Ai_Study/03.langchain_study_new/07_project_all/langgraph.json:1)
- [frontend_use_stream/package.json](/Users/z523/Desktop/zizhi/ai_Python/Ai_Study/03.langchain_study_new/07_project_all/frontend_use_stream/package.json:1)
- [frontend_use_stream/src/App.tsx](/Users/z523/Desktop/zizhi/ai_Python/Ai_Study/03.langchain_study_new/07_project_all/frontend_use_stream/src/App.tsx:1)

**这个版本怎么跑**

1. 启动 LangGraph Agent Server

先安装 CLI：

```bash
uv add "langgraph-cli[inmem]"
```

然后进入：

```bash
cd /Users/z523/Desktop/zizhi/ai_Python/Ai_Study/03.langchain_study_new/07_project_all
```

启动：

```bash
uv run langgraph dev
```

正常情况下你会得到一个本地地址：

```text
http://127.0.0.1:2024
```

这里的 `assistantId` 就来自 [langgraph.json](/Users/z523/Desktop/zizhi/ai_Python/Ai_Study/03.langchain_study_new/07_project_all/langgraph.json:1) 里的图名称：

```json
"graphs": {
  "agent": "./server/agent.py:agent"
}
```

所以前端会使用：

- `apiUrl = "http://127.0.0.1:2024"`
- `assistantId = "agent"`

2. 启动 `useStream` 前端

```bash
cd /Users/z523/Desktop/zizhi/ai_Python/Ai_Study/03.langchain_study_new/07_project_all/frontend_use_stream
npm install
npm run dev
```

默认地址：

```text
http://127.0.0.1:5174
```

**这个前端做了什么**

核心代码在 [App.tsx](/Users/z523/Desktop/zizhi/ai_Python/Ai_Study/03.langchain_study_new/07_project_all/frontend_use_stream/src/App.tsx:1)：

```tsx
const stream = useStream<AgentState>({
  apiUrl: "http://127.0.0.1:2024",
  assistantId: "agent",
  reconnectOnMount: true,
  fetchStateHistory: true,
});
```

提交消息：

```tsx
stream.submit({
  messages: [{ type: "human", content: trimmed }],
});
```

渲染消息：

```tsx
stream.messages.map(...)
```

新对话：

```tsx
stream.switchThread(null)
```

**为什么这才叫 useStream 版本**

因为它不再手写：

```ts
fetch("/chat")
```

而是直接通过：

```ts
useStream(...)
```

连到 LangGraph 的流式后端。

这也是官方文档强调的标准结构：
- `create_agent` 后端
- `useStream` 前端

**一句话总结**

- 如果你想先理解“前后端最基本怎么通信”，看 `FastAPI + fetch`
- 如果你想对齐官方 Frontend 文档，重点看这个 `useStream` 版本
