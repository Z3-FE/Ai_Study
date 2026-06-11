# AI Agent

AI 分析层目录，用独立 FastAPI 服务承载 LangGraph Agent。

职责边界：

- 问题理解。
- 语义检索。
- 指标解析。
- SQL 生成。
- SQL 审核。
- 数据分析。
- 报告生成。
- interrupt 人机确认。

## 启动

```bash
cd 00_LangGraph_Study/09_enterprise_data_intelligence_platform
INSIGHT_CHAT_MODEL_MODE=mock uv run uvicorn ai_agent.app:app --reload --host 127.0.0.1 --port 8010
```

业务后端通过环境变量 `AI_AGENT_BASE_URL` 调用本服务，默认值：

```text
http://127.0.0.1:8010
```

## 接口

| 接口 | 作用 |
| --- | --- |
| `GET /api/health` | AI 服务健康检查 |
| `POST /api/chat/stream` | 执行普通聊天 LangGraph，并以 SSE 返回事件 |
