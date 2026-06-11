# Backend

FastAPI 业务层，用来承接前端和后续 LangGraph Agent。

当前 Phase 3 已经切换为真实 PostgreSQL 持久化：

- 会话和消息 API。
- 文档登记和候选语义资产抽取 API。
- 语义草稿编辑、采用、驳回、发布 API。
- 向量同步、异步任务、全量重建 API。
- PostgreSQL 连接健康检查。

当前代码使用 `psycopg` 直接读写 PostgreSQL。启动后会自动执行 `CREATE SCHEMA/TABLE IF NOT EXISTS`，表结构见：

```text
backend/sql/001_business_api_schema.sql
```

默认连接：

```text
postgresql:///enterprise_data_ai
```

也可以通过环境变量覆盖：

```bash
export POSTGRES_URI="postgresql:///enterprise_data_ai"
```

## 启动

建议先启动 AI Agent 服务：

```bash
cd 00_LangGraph_Study/09_enterprise_data_intelligence_platform
INSIGHT_CHAT_MODEL_MODE=mock uv run uvicorn ai_agent.app:app --reload --host 127.0.0.1 --port 8010
```

再启动业务后端：

```bash
cd 00_LangGraph_Study/09_enterprise_data_intelligence_platform
uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

业务后端通过 `AI_AGENT_BASE_URL` 请求 AI Agent，默认：

```text
http://127.0.0.1:8010
```

API 文档：

```text
http://127.0.0.1:8000/docs
```

## 主要接口

| 模块 | 接口 |
| --- | --- |
| Bootstrap | `GET /api/app/bootstrap` |
| Conversation | `GET /api/conversations`、`POST /api/conversations` |
| Conversation Detail | `GET /api/conversations/{conversation_id}`、`PUT /api/conversations/{conversation_id}`、`DELETE /api/conversations/{conversation_id}` |
| Message | `GET /api/conversations/{conversation_id}/messages`、`POST /api/conversations/{conversation_id}/messages` |
| Corpus | `POST /api/corpus/documents`、`POST /api/corpus/documents/{document_id}/extract-semantic-assets` |
| Semantic Draft | `GET /api/semantic/drafts`、`PATCH /api/semantic/drafts/{draft_id}`、`POST /api/semantic/drafts/{draft_id}/adopt`、`POST /api/semantic/drafts/{draft_id}/reject`、`POST /api/semantic/drafts/{draft_id}/publish` |
| Vector | `POST /api/vector/assets/{asset_type}/{asset_id}/sync`、`POST /api/vector/rebuild`、`GET /api/vector/jobs` |

## 说明

前端可以直接对接这些 API，数据会写入真实 PostgreSQL。

当前仍然保留两个占位实现：

- 文档解析：目前根据文档类型生成固定候选语义资产，后续接入 LLM 提取。
- 向量：目前用本地假向量 `_fake_embedding` 写入 `vector.semantic_asset_embeddings`，后续替换为真实 embedding 模型和 pgvector。

类比前端：

```text
routers = 页面路由
models = TypeScript types
store = PostgreSQL repository
sql/001 = 数据库 schema
```
