# 企业级数据智能分析与决策平台 TODO

## 目标

第一阶段目标：

```text
固定 Olist 数据源
-> 新建会话
-> 上传指标口径 / 业务语义文档
-> AI 提取候选语义资产
-> 用户审核采用
-> 自然语言问数
-> LangGraph 生成并审核 SQL
-> 查询 PostgreSQL
-> 展示指标卡、图表、表格、来源和审计
```

本 TODO 用来控制开发顺序，避免一边做页面、一边改接口、一边改 Agent，导致范围失控。

## Phase 0：项目基线确认

- [ ] 确认 Olist 数据已经导入 PostgreSQL。
- [ ] 确认数据库名为 `enterprise_data_ai`。
- [ ] 确认业务 schema 为 `olist`。
- [ ] 确认 9 张 UI 参考图已保存到 `design/ui`。
- [ ] 确认技术文档、联调协议、指标口径文档已整理完成。

验收标准：

- [ ] 可以通过 SQL 查询 Olist 表。
- [ ] 可以打开项目文档并明确第一阶段范围。

## Phase 1：前端静态骨架

- [x] 创建前端项目结构。
- [x] 搭建全局 AppShell。
- [x] 实现左侧导航。
- [x] 实现顶部用户区。
- [x] 实现 `/analysis/new` 新建会话静态页。
- [x] 实现 `/analysis/[conversationId]` 会话详情静态页。
- [x] 实现右侧执行详情抽屉。
- [x] 实现语义资产四个静态页面。

验收标准：

- [x] 页面视觉结构和当前设计图方向一致。
- [x] 左侧导航可以切换主要页面。
- [x] 新建会话、会话详情、语义资产四页都能访问。

## Phase 2：新建会话与语义上传审核

- [x] 实现 `POST /api/conversations` mock。
- [x] 实现 `GET /api/conversations` mock。
- [x] 实现 `GET /api/conversations/{id}` mock。
- [x] 实现 `PUT /api/conversations/{id}` mock。
- [x] 实现 `DELETE /api/conversations/{id}` mock。
- [x] 实现 `GET /api/conversations/{id}/messages` mock。
- [x] 实现 `POST /api/conversations/{id}/messages` mock。
- [x] 新建会话时生成 `conversationId` 和 `threadId`。
- [x] 新建会话页展示固定 Olist 数据源。
- [x] 增加“上传指标口径文档”入口。
- [x] 增加“上传业务语义文档”入口。
- [x] 实现 `SemanticUploadTask` 前端状态。
- [x] 实现候选语义资产 mock 数据。
- [x] 实现 `SemanticDraft` 审核列表。
- [x] 支持查看候选资产来源片段。
- [x] 支持编辑候选资产。
- [x] 支持“采用到本次会话”。
- [x] 支持“修改后采用”。
- [x] 支持“发布到全局”按钮占位。
- [x] 支持“驳回”。
- [x] 显示当前会话已采用的语义资产摘要。

验收标准：

- [x] 用户可以在新建会话页上传指标口径或业务语义文档。
- [x] 页面能展示 AI 提取出的候选指标、业务术语、维度说明或业务规则。
- [x] 用户可以审核、修改、采用或驳回候选资产。
- [x] 已采用资产会影响当前会话语义上下文。

## Phase 3：业务层基础 API

- [x] 创建 FastAPI 项目。
- [x] 建立 PostgreSQL 健康检查连接。
- [x] 设计 `app.conversations` 表。
- [x] 设计 `app.messages` 表。
- [x] 设计 `app.analysis_runs` 表。
- [x] 设计 `app.conversation_semantic_assets` 表。
- [x] 设计 `semantic.semantic_drafts` 表。
- [x] 设计 `corpus.documents` 表。
- [x] 实现 `GET /api/app/bootstrap`。
- [x] 实现 `POST /api/conversations`。
- [x] 实现 `GET /api/conversations`。
- [x] 实现 `GET /api/conversations/{conversation_id}`。
- [x] 实现 `PUT /api/conversations/{conversation_id}`。
- [x] 实现 `DELETE /api/conversations/{conversation_id}`。
- [x] 实现 `GET /api/conversations/{conversation_id}/messages`。
- [x] 实现 `POST /api/conversations/{conversation_id}/messages`。
- [x] 实现 `POST /api/corpus/documents`。
- [x] 实现 `POST /api/corpus/documents/{document_id}/extract-semantic-assets`。
- [x] 实现 `PATCH /api/semantic/drafts/{draft_id}`。
- [x] 实现 `POST /api/semantic/drafts/{draft_id}/adopt`。
- [x] 实现 `POST /api/semantic/drafts/{draft_id}/reject`。
- [x] 实现 `POST /api/semantic/drafts/{draft_id}/publish`。
- [x] 设计 `vector.semantic_asset_embeddings` 表。
- [x] 设计 `vector.embedding_jobs` 表。
- [x] 实现语义资产审核通过后的同步向量更新 mock。
- [x] 实现语义资产审核通过后的异步向量任务占位。
- [x] 实现 `POST /api/vector/assets/{asset_type}/{asset_id}/sync`。
- [x] 实现 `POST /api/vector/rebuild`。
- [x] 实现 `GET /api/vector/jobs`。
- [x] 支持手动全量重建向量索引占位。
- [x] 将内存仓储替换为 PostgreSQL repository。
- [x] 将 `backend/sql/001_business_api_schema.sql` 应用到本地数据库。
- [ ] 接入真正的异步任务队列或后台 worker。
- [ ] 支持定时全量重建向量索引。

验收标准：

- [x] 前端可以通过基础 API 创建会话。
- [x] 前端可以通过基础 API 查看会话详情和消息列表。
- [x] 前端可以通过基础 API 上传文档。
- [x] 前端可以通过基础 API 获取候选语义资产。
- [x] 前端可以采用候选资产到当前会话。
- [x] 语义资产发布后可以同步或异步创建向量索引任务。
- [x] 管理端可以手动触发全量向量重建任务。
- [x] 数据写入真实 PostgreSQL 后重启仍然保留。

## Phase 4：SSE 事件与会话详情

> 已先围绕普通聊天实现最小事件链路。复杂分析事件会在 LangGraph SQL 分析节点接入后继续补齐。

- [ ] 实现文档提取 SSE mock。
- [ ] 实现 `semantic.extract.started`。
- [ ] 实现 `semantic.extract.progress`。
- [ ] 实现 `semantic.drafts.created`。
- [ ] 实现 `semantic.draft.reviewed`。
- [x] 实现普通聊天分析任务 SSE。
- [x] 实现 `run.started`。
- [x] 实现 `step.started`。
- [x] 实现 `step.completed`。
- [x] 实现 `message.delta`。
- [x] 实现 `message.completed`。
- [ ] 实现 `sql.generated`。
- [ ] 实现 `sql.reviewed`。
- [ ] 实现 `artifact.created`。
- [ ] 实现 `sources.created`。
- [ ] 实现 `audit.created`。
- [x] 实现 `run.completed`。
- [x] 实现 `run.failed`。

验收标准：

- [ ] 新建会话页上传文档时可以看到进度变化。
- [x] 会话详情页可以被普通聊天 SSE 事件驱动更新。
- [x] 右侧 Steps 能随着普通聊天事件更新。
- [ ] 右侧 SQL / Sources / Audit 能随着分析事件更新。

## Phase 5：语义资产四页

- [x] 实现指标管理页。
- [x] 实现维度管理页。
- [x] 实现数据集说明页。
- [x] 实现业务术语页。
- [x] 实现指标详情抽屉。
- [x] 实现维度详情抽屉。
- [x] 实现数据集详情和 Join 路径展示。
- [x] 实现业务术语详情和映射展示。
- [x] 接入真实语义资产 API。
- [x] 新增 `/api/semantic/assets/metrics`。
- [x] 新增 `/api/semantic/assets/dimensions`。
- [x] 新增 `/api/semantic/assets/datasets`。
- [x] 新增 `/api/semantic/assets/glossary`。
- [x] 统一 `apiGet` 层处理开发环境 Strict Mode 导致的重复 GET 请求。

验收标准：

- [x] 可以查看指标、维度、数据集、业务术语。
- [x] 进入四个语义资产页面时，同一接口不会因为客户端 effect 双执行而产生重复真实 GET。
- [ ] Agent 后续生成 SQL 时能读取这些语义资产。

## Phase 6：LangGraph 最小分析链路

- [x] 定义普通聊天最小 `MessagesState`。
- [x] 实现普通聊天 LangGraph：`START -> chat -> END`。
- [x] 实现普通聊天节点流式输出。
- [x] 实现无 API Key / 本地测试时的 mock 模型兜底。
- [x] 将 AI Agent 独立为 HTTP 服务，由业务后端通过 API 请求 LangGraph。
- [x] 实现用户消息和助手消息写入 PostgreSQL。
- [x] 实现 `analysis_runs` 与 `run_id` 关联。
- [x] 实现问题理解节点的最小事件占位。
- [ ] 实现结构化语义解析节点，优先查询 `semantic.metrics`、`semantic.dimensions`、`semantic.datasets`、`semantic.business_terms`。
- [ ] 实现低置信度语义召回节点，仅在结构化语义层命中不足时查询向量索引。
- [ ] 实现指标解析节点。
- [ ] 实现 SQL 生成节点。
- [ ] 实现 SQL 审核节点。
- [ ] 实现 SQL 执行节点。
- [ ] 实现数据分析节点。
- [ ] 实现报告生成节点。
- [ ] 接入会话级语义资产。
- [ ] 接入全局语义资产。
- [ ] 向量命中后通过 `asset_type + asset_id` 回源查询正式 semantic 表。
- [ ] 接入用户长期记忆读取，结构化记忆优先，语义型记忆再走向量召回。

### AI 生成内容路线

- [ ] 第一阶段先让 AI 按自己的分析思路生成内容，不强绑定固定卡片和图表样式。
- [ ] 定义 `AnalysisContentDraft`，用于承载 AI 生成的标题、摘要、关键发现、指标解释、表格数据、图表建议、来源和限制说明。
- [ ] 报告生成节点先输出半结构化 JSON，而不是直接输出 JSX、HTML 或 Tailwind 样式。
- [ ] 前端先用通用报告区渲染 `AnalysisContentDraft`，验证 AI 分析内容是否真的有价值。
- [ ] 后续再把稳定字段逐步收敛为 `DashboardSpec`，映射到定制化 `KpiCard`、`ChartPanel`、`DataTable`、`SourcePanel` 等组件。
- [ ] 明确边界：AI 负责生成分析内容和展示建议，前端负责稳定的组件样式、布局、安全渲染和交互状态。

验收标准：

- [x] 用户问题可以触发普通聊天 LangGraph 流程。
- [ ] LangGraph 能读取当前会话采用的指标和业务术语。
- [ ] LangGraph 能优先使用结构化语义表，而不是默认先查向量库。
- [ ] LangGraph 在低置信度时可以使用向量索引召回候选资产，并回源确认正式定义。
- [ ] LangGraph 能生成 SQL 草稿。
- [ ] AI 可以生成一份可读的分析内容草稿，即使暂时还没有映射成复杂卡片和图表。

## Phase 7：真实 PostgreSQL 查询

- [ ] 实现只读 SQL 执行工具。
- [ ] 限制只允许查询 `olist` schema。
- [ ] 禁止 DDL / DML。
- [ ] 默认追加或校验 `LIMIT`。
- [ ] 执行 `哪个品类销售额最高？`。
- [ ] 执行 `本月商品销售趋势分析`。
- [ ] 将结果转换为 table artifact。
- [ ] 将结果转换为 chart artifact。
- [ ] 将结果转换为 report artifact。

验收标准：

- [ ] 前端展示真实数据库查询结果。
- [ ] SQL、表格、图表、结论可以形成闭环。

## Phase 8：SQL / Sources / Audit 闭环

- [ ] SQL tab 展示生成 SQL。
- [ ] SQL tab 展示安全检查结果。
- [ ] Sources tab 展示使用的数据表。
- [ ] Sources tab 展示使用的字段。
- [ ] Sources tab 展示使用的指标和维度。
- [ ] Sources tab 标记来源是全局语义还是本次会话语义。
- [ ] Audit tab 展示风险等级。
- [ ] Audit tab 展示审核记录。
- [ ] Audit tab 展示执行耗时和返回行数。
- [ ] Sources tab 展示语义资产是否来自结构化语义表、会话临时资产或向量召回后回源确认。
- [ ] Audit tab 展示向量命中是否回源确认、是否存在版本不一致或 stale 记录。

验收标准：

- [ ] 每一次分析都可以追溯 SQL、来源和审核记录。
- [ ] 面试时可以清楚讲出“不是裸跑 SQL，而是经过安全审核和审计”。

## Phase 9：Human-in-the-loop

- [ ] 设计 interrupt UI。
- [ ] SQL 风险较高时触发确认。
- [ ] 指标口径冲突时触发确认。
- [ ] 用户可以确认执行。
- [ ] 用户可以要求重写 SQL。
- [ ] 用户可以取消分析。
- [ ] Audit 记录人工确认行为。

验收标准：

- [ ] Agent 可以在风险点暂停。
- [ ] 用户确认后流程可以继续。

## Phase 10：简历展示与收尾

- [ ] 整理 README。
- [ ] 整理项目架构图。
- [ ] 整理核心流程图。
- [ ] 整理演示问题。
- [ ] 准备 3 个面试讲解点。
- [ ] 准备演示视频或截图。

推荐演示问题：

```text
哪个品类销售额最高？
本月商品销售趋势如何？
退款率最高的品类是什么？
GMV 最高的地区有哪些？
```

面试讲解重点：

- [ ] 语义层如何提升 Text-to-SQL 可靠性。
- [ ] LangGraph 如何拆分多步骤 Agent 流程。
- [ ] SQL Safety Guard 和 Audit 如何保证可控性。
- [ ] 新建会话上传指标口径 / 业务语义文档如何实现 Document-to-Semantic-Layer。
- [ ] 为什么结构化语义层是主流程，向量检索只是低置信度兜底和文档增强。
- [ ] 向量索引如何通过同步、异步、手动全量和定时全量重建保持一致。
