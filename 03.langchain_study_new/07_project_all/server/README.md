# Server（Python LangGraph）

这个后端已经与 `frontend` 的 assistant-ui 前端对齐，关键约定如下：

1. 图 ID：`agent`
2. 导出对象名：`graph`
3. 基于 messages 的最小状态图

## 启动方式

在 `07_project_all` 根目录执行：

```bash
uv run langgraph dev --config server/langgraph.json --host 127.0.0.1 --port 2024 --no-reload
```

启动后本地 API：

- [http://127.0.0.1:2024](http://127.0.0.1:2024)
- [http://127.0.0.1:2024/docs](http://127.0.0.1:2024/docs)

## 前端对应环境变量

前端 `.env.local` 中设置：

```env
LANGGRAPH_API_URL=http://127.0.0.1:2024
NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID=agent
```

## 文件说明

```text
agent_langgraph.py   # 当前主入口，导出 graph
langgraph.json       # 当前服务配置
agent.py             # 本地脚本示例（可独立运行）
fastapi_app.py       # FastAPI 示例（可选）
```
