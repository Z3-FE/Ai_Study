# 07_project_all：LangGraph + assistant-ui 最小实战

这个目录是你当前最推荐的一套本地开发结构：  
**Python LangGraph 后端 + Next.js assistant-ui 前端**。

---

## 1. 项目结构（已按现状整理）

```text
07_project_all/
├─ README.md                         # 你现在看的总说明
├─ langgraph.json                    # 顶层配置（可选）
├─ 前端如何接这个agent.md             # 前端接入说明（中文）
├─ useStream最小实例说明.md           # useStream 概念说明（中文）
├─ server/
│  ├─ README.md                      # 后端启动说明（中文）
│  ├─ langgraph.json                 # 后端主配置（当前使用）
│  ├─ agent_langgraph.py             # 导出 graph 的 LangGraph 应用（当前主入口）
│  ├─ agent.py                       # 本地 Agent 示例脚本
│  ├─ fastapi_app.py                 # FastAPI 示例接口（可选）
│  ├─ env_utils.py                   # 环境变量工具
│  └─ __init__.py
└─ frontend/
   ├─ README.md                      # 前端启动说明（中文）
   ├─ package.json                   # Next.js + assistant-ui 依赖与脚本
   ├─ .env.example                   # 环境变量示例
   ├─ app/
   │  ├─ page.tsx                    # 页面入口
   │  ├─ assistant.tsx               # assistant-ui 运行时组装
   │  └─ api/[..._path]/route.ts     # 代理 LangGraph API
   ├─ lib/chatApi.ts                 # LangGraph SDK client
   ├─ components/assistant-ui/       # 聊天 UI 组件
   └─ backend/agent.ts               # 模板 JS 后端（当前可不使用）
```

---

## 2. 你现在主要跑哪一套

推荐只跑这一套，最稳定：

1. 后端：`server/langgraph.json` + `server/agent_langgraph.py`
2. 前端：`frontend`（assistant-ui LangGraph 模板）

`server/fastapi_app.py` 和 `server/agent.py` 是练习/对比示例，不是当前主链路必需。

---

## 3. 一次跑通（最短路径）

在项目根目录 `07_project_all`：

```bash
uv run langgraph dev --config server/langgraph.json --host 127.0.0.1 --port 2024 --no-reload
```

新开一个终端：

```bash
cd frontend
npm install
npm run dev
```

然后访问：

- 前端页面：[http://127.0.0.1:3000](http://127.0.0.1:3000)
- 后端 API Docs：[http://127.0.0.1:2024/docs](http://127.0.0.1:2024/docs)

---

## 4. 快速理解这个项目怎么工作

1. 前端 `app/assistant.tsx` 创建 assistant-ui runtime。  
2. runtime 通过 `lib/chatApi.ts` 调用 LangGraph API。  
3. `app/api/[..._path]/route.ts` 负责把前端请求代理到 `LANGGRAPH_API_URL`。  
4. 后端 `agent_langgraph.py` 的 `graph` 处理消息并流式返回。  
5. 你在 UI 里看到的 messages/tool calls/streaming 都来自这条链路。

---

## 5. 常见问题（你这次踩过的坑）

1. 端口漂移：开发时建议加 `--no-reload`，并固定 `--port 2024`。  
2. 前端依赖缺失（`lightningcss` / `rollup`）：  
   确保 `frontend/.npmrc` 允许 optional deps，再重装依赖。  
3. LangSmith 页面黄色提示（缺 API Key）：  
   不影响本地联调，只影响云端 tracing 上传。
