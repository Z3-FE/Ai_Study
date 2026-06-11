from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .models import (
    AnalysisRun,
    AnalysisRunStatus,
    Conversation,
    ConversationCreate,
    ConversationStatus,
    ConversationUpdate,
    DataSource,
    Document,
    DocumentCreate,
    DocumentType,
    Message,
    MessageCreate,
    SemanticDraft,
    SemanticDraftField,
    SemanticDraftKind,
    SemanticDraftReview,
    SemanticDraftStatus,
    SemanticDraftUpdate,
    User,
    VectorEmbeddingRecord,
    VectorJob,
    VectorJobStatus,
    VectorRebuildRequest,
    VectorSyncMode,
)
from .settings import settings


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _title_from_question(question: str | None) -> str:
    normalized = (question or "").strip()
    if not normalized:
        return "新建数据分析"
    return normalized[:18] + ("..." if len(normalized) > 18 else "")


def _fake_embedding(text: str) -> list[float]:
    """A deterministic local vector stub; replace with a real embedding model later."""

    values = [0.0] * 8
    for index, char in enumerate(text[:256]):
        values[index % len(values)] += (ord(char) % 97) / 100.0
    total = sum(values) or 1.0
    return [round(value / total, 6) for value in values]


def _schema_sql_path() -> Path:
    return Path(__file__).resolve().parents[1] / "sql" / "001_business_api_schema.sql"


def _draft_fields_to_json(fields: list[SemanticDraftField]) -> list[dict[str, str]]:
    return [field.model_dump() for field in fields]


def _field_value(row: dict, label: str, default: str = "") -> str:
    for item in row.get("fields") or []:
        if item.get("label") == label:
            return item.get("value") or default
    return default


def _split_field_value(value: str) -> list[str]:
    if not value:
        return []
    separators = ["、", ",", "，", "/", "；", ";"]
    values = [value]
    for separator in separators:
        values = [part for item in values for part in item.split(separator)]
    return [item.strip() for item in values if item.strip()]


def _semantic_page_status(status: str) -> str:
    return "published" if status == SemanticDraftStatus.published.value else "pending"


def _row_to_conversation(row: dict) -> Conversation:
    return Conversation(
        id=row["id"],
        thread_id=row["thread_id"],
        title=row["title"],
        data_source_id=row["data_source_id"],
        status=ConversationStatus(row["status"]),
        last_message_preview=row["last_message_preview"],
        adopted_semantic_draft_ids=row["adopted_semantic_draft_ids"] or [],
        adopted_semantic_draft_titles=row["adopted_semantic_draft_titles"] or [],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_message(row: dict) -> Message:
    return Message(
        id=row["id"],
        conversation_id=row["conversation_id"],
        run_id=row["run_id"],
        role=row["role"],
        content=row["content"],
        metadata=row["metadata"] or {},
        created_at=row["created_at"],
    )


def _row_to_analysis_run(row: dict) -> AnalysisRun:
    return AnalysisRun(
        id=row["id"],
        conversation_id=row["conversation_id"],
        thread_id=row["thread_id"],
        question=row["question"],
        data_source_id=row["data_source_id"],
        status=AnalysisRunStatus(row["status"]),
        current_step=row["current_step"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        created_at=row["created_at"],
    )


def _row_to_document(row: dict) -> Document:
    return Document(
        id=row["id"],
        file_name=row["file_name"],
        file_size=row["file_size"],
        document_type=DocumentType(row["document_type"]),
        status=row["status"],
        created_at=row["created_at"],
    )


def _row_to_draft(row: dict) -> SemanticDraft:
    return SemanticDraft(
        id=row["id"],
        document_id=row["document_id"],
        kind=SemanticDraftKind(row["kind"]),
        status=SemanticDraftStatus(row["status"]),
        title=row["title"],
        description=row["description"],
        mapping_target=row["mapping_target"],
        confidence=float(row["confidence"]),
        source_document=row["source_document"],
        source_snippet=row["source_snippet"],
        fields=[SemanticDraftField(**item) for item in (row["fields"] or [])],
        adopted_scope=row["adopted_scope"],
        vector_status=row["vector_status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_vector_job(row: dict) -> VectorJob:
    return VectorJob(
        id=row["id"],
        job_type=row["job_type"],
        asset_type=row["asset_type"],
        asset_id=row["asset_id"],
        status=VectorJobStatus(row["status"]),
        retry_count=row["retry_count"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PostgresStore:
    """PostgreSQL repository for the business API.

    路由层仍然调用 store.xxx()，但数据已经写入真实 PostgreSQL。
    这相当于前端把 mock adapter 替换成真实 request adapter。
    """

    def __init__(self) -> None:
        self.data_source = DataSource()
        self.current_user = User(
            id="user_admin",
            name="管理员",
            email="admin@insight.com",
            role="semantic_admin",
        )
        self._ensure_schema()
        self._seed_if_empty()

    def _connect(self):
        return psycopg.connect(settings.postgres_uri, row_factory=dict_row)

    def _ensure_schema(self) -> None:
        sql = _schema_sql_path().read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.execute(sql)

    def _seed_if_empty(self) -> None:
        self._seed_conversations_if_empty()
        self._seed_semantic_assets()

    def _seed_conversations_if_empty(self) -> None:
        with self._connect() as conn:
            count = conn.execute("SELECT count(*) AS count FROM app.conversations").fetchone()["count"]
            if count:
                return
            for title in ["本月商品销售趋势分析", "Top10 品类分析", "用户复购分析"]:
                conversation = Conversation(
                    id=_id("conv"),
                    thread_id=_id("thread"),
                    title=title,
                    status=ConversationStatus.completed,
                    last_message_preview=title,
                )
                self._insert_conversation(conn, conversation)
                for role, content in [
                    ("user", title),
                    ("assistant", "已生成模拟分析结果，后续接入 LangGraph 后会返回真实执行过程。"),
                ]:
                    message = Message(
                        id=_id("msg"),
                        conversation_id=conversation.id,
                        role=role,
                        content=content,
                    )
                    self._insert_message(conn, message)

    def _seed_semantic_assets(self) -> None:
        seeds = [
            SemanticDraft(
                id="seed_metric_sales_amount",
                kind=SemanticDraftKind.metric,
                status=SemanticDraftStatus.published,
                title="销售额",
                description="订单商品成交金额，不包含运费，默认仅统计已送达订单。",
                mapping_target="sales_amount",
                confidence=0.98,
                source_document="指标口径文件资料.md",
                source_snippet="销售额 = SUM(order_items.price)，默认过滤 delivered 订单。",
                fields=[
                    SemanticDraftField(label="指标 ID", value="sales_amount"),
                    SemanticDraftField(label="SQL 表达式", value="SUM(order_items.price)"),
                    SemanticDraftField(label="默认过滤", value="orders.order_status = 'delivered'"),
                    SemanticDraftField(label="依赖表", value="orders、order_items"),
                    SemanticDraftField(label="可用维度", value="品类、客户地区、下单时间、支付方式"),
                    SemanticDraftField(label="同义词", value="GMV、成交额、销售金额"),
                    SemanticDraftField(label="示例问题", value="本月商品销售总额是多少？"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_metric_order_count",
                kind=SemanticDraftKind.metric,
                status=SemanticDraftStatus.published,
                title="订单数",
                description="去重订单数量，使用订单主表的 order_id 进行去重统计。",
                mapping_target="order_count",
                confidence=0.97,
                source_document="指标口径文件资料.md",
                source_snippet="订单数 = COUNT(DISTINCT orders.order_id)。",
                fields=[
                    SemanticDraftField(label="指标 ID", value="order_count"),
                    SemanticDraftField(label="SQL 表达式", value="COUNT(DISTINCT orders.order_id)"),
                    SemanticDraftField(label="依赖表", value="orders"),
                    SemanticDraftField(label="可用维度", value="品类、客户地区、下单时间"),
                    SemanticDraftField(label="同义词", value="订单量、交易笔数、总订单数"),
                    SemanticDraftField(label="示例问题", value="2024 年 5 月份有多少笔交易？"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_metric_average_order_value",
                kind=SemanticDraftKind.metric,
                status=SemanticDraftStatus.published,
                title="客单价",
                description="平均每笔订单的商品成交金额，使用销售额除以去重订单数。",
                mapping_target="average_order_value",
                confidence=0.94,
                source_document="指标口径文件资料.md",
                source_snippet="客单价 = 商品销售额 / 去重订单数。",
                fields=[
                    SemanticDraftField(label="指标 ID", value="average_order_value"),
                    SemanticDraftField(label="SQL 表达式", value="sales_amount / order_count"),
                    SemanticDraftField(label="依赖表", value="orders、order_items"),
                    SemanticDraftField(label="可用维度", value="品类、客户地区、下单时间"),
                    SemanticDraftField(label="同义词", value="笔单价、订单均价、AOV"),
                    SemanticDraftField(label="示例问题", value="各个品类的平均客单价是多少？"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_metric_refund_rate",
                kind=SemanticDraftKind.metric,
                status=SemanticDraftStatus.pending,
                title="退款率",
                description="退款订单数除以总订单数，第一阶段等待确认退款判定口径。",
                mapping_target="refund_rate",
                confidence=0.78,
                source_document="AI 候选",
                source_snippet="退款率需要结合订单取消、退货或支付退款字段确认。",
                fields=[
                    SemanticDraftField(label="指标 ID", value="refund_rate"),
                    SemanticDraftField(label="SQL 表达式", value="refund_order_count / order_count"),
                    SemanticDraftField(label="依赖表", value="orders、order_payments"),
                    SemanticDraftField(label="可用维度", value="下单时间、品类、支付方式"),
                    SemanticDraftField(label="同义词", value="退款占比、退单率"),
                    SemanticDraftField(label="示例问题", value="上周退款率最高的商品是什么？"),
                ],
            ),
            SemanticDraft(
                id="seed_dimension_product_category",
                kind=SemanticDraftKind.dimension,
                status=SemanticDraftStatus.published,
                title="品类",
                description="使用商品表中的 product_category_name 作为商品品类维度。",
                mapping_target="product_category",
                confidence=0.96,
                source_document="数据库扫描",
                source_snippet="products.product_category_name 表示商品所属品类。",
                fields=[
                    SemanticDraftField(label="字段映射", value="products.product_category_name"),
                    SemanticDraftField(label="所属数据集", value="products"),
                    SemanticDraftField(label="维度类型", value="分类维度"),
                    SemanticDraftField(label="可用指标", value="销售额、订单数、客单价"),
                    SemanticDraftField(label="同义词", value="产品类别、商品类型、品类名称"),
                    SemanticDraftField(label="示例问题", value="哪个商品品类的表现最好？"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_dimension_customer_region",
                kind=SemanticDraftKind.dimension,
                status=SemanticDraftStatus.published,
                title="客户地区",
                description="使用 customers.customer_state 作为客户地区维度。",
                mapping_target="customer_region",
                confidence=0.95,
                source_document="数据库扫描",
                source_snippet="地区分析统一使用客户收货州编码 customer_state。",
                fields=[
                    SemanticDraftField(label="字段映射", value="customers.customer_state"),
                    SemanticDraftField(label="所属数据集", value="customers"),
                    SemanticDraftField(label="维度类型", value="地理维度"),
                    SemanticDraftField(label="可用指标", value="销售额、订单数、客户数"),
                    SemanticDraftField(label="常用过滤", value="非空地区"),
                    SemanticDraftField(label="同义词", value="客户所在省份、省份、买家区域"),
                    SemanticDraftField(label="示例问题", value="哪个地区销售额最高？"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_dimension_order_time",
                kind=SemanticDraftKind.dimension,
                status=SemanticDraftStatus.published,
                title="下单时间",
                description="使用 orders.order_purchase_timestamp 作为订单时间维度。",
                mapping_target="order_purchase_time",
                confidence=0.95,
                source_document="数据库扫描",
                source_snippet="订单趋势分析统一使用下单时间字段。",
                fields=[
                    SemanticDraftField(label="字段映射", value="orders.order_purchase_timestamp"),
                    SemanticDraftField(label="所属数据集", value="orders"),
                    SemanticDraftField(label="维度类型", value="时间维度"),
                    SemanticDraftField(label="可用指标", value="销售额、订单数、退款率"),
                    SemanticDraftField(label="同义词", value="购买时间、支付历史时间、购买年月日"),
                    SemanticDraftField(label="示例问题", value="对比过去三个月的订单量趋势。"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_dimension_payment_type",
                kind=SemanticDraftKind.dimension,
                status=SemanticDraftStatus.published,
                title="支付方式",
                description="使用 order_payments.payment_type 作为支付方式维度。",
                mapping_target="payment_type",
                confidence=0.93,
                source_document="数据库扫描",
                source_snippet="支付方式来自订单支付表 payment_type。",
                fields=[
                    SemanticDraftField(label="字段映射", value="order_payments.payment_type"),
                    SemanticDraftField(label="所属数据集", value="order_payments"),
                    SemanticDraftField(label="维度类型", value="分类维度"),
                    SemanticDraftField(label="可用指标", value="销售额、订单数、退款率"),
                    SemanticDraftField(label="同义词", value="付款通道、结算工具、支付卡类型"),
                    SemanticDraftField(label="示例问题", value="信用卡支付和 boleto 支付的订单占比分别是多少？"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_term_gmv",
                kind=SemanticDraftKind.glossary,
                status=SemanticDraftStatus.published,
                title="GMV",
                description="用户提到 GMV 时映射到销售额指标。",
                mapping_target="sales_amount",
                confidence=0.94,
                source_document="指标口径文件资料.md",
                source_snippet="GMV / 成交额 / 销售金额：第一阶段统一映射到不含运费的商品销售额。",
                fields=[
                    SemanticDraftField(label="术语类型", value="指标别名"),
                    SemanticDraftField(label="映射目标", value="销售额"),
                    SemanticDraftField(label="冲突校验", value="无冲突"),
                    SemanticDraftField(label="Agent 解析结果", value="GMV -> 销售额"),
                    SemanticDraftField(label="示例问题", value="本月 GMV 最高的品类是什么？"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_term_product_category",
                kind=SemanticDraftKind.glossary,
                status=SemanticDraftStatus.published,
                title="商品类型",
                description="用户说商品类型、商品分类、品类名称时，统一映射到品类维度。",
                mapping_target="product_category",
                confidence=0.92,
                source_document="业务语义词典.xlsx",
                source_snippet="商品类型、商品分类、品类名称统一指向品类维度。",
                fields=[
                    SemanticDraftField(label="术语类型", value="维度别名"),
                    SemanticDraftField(label="映射目标", value="品类"),
                    SemanticDraftField(label="冲突校验", value="无冲突"),
                    SemanticDraftField(label="Agent 解析结果", value="商品类型 -> 品类"),
                    SemanticDraftField(label="示例问题", value="哪个商品类型的销量最高？"),
                ],
                adopted_scope="global",
                vector_status="synced",
            ),
            SemanticDraft(
                id="seed_rule_delivered_orders",
                kind=SemanticDraftKind.business_rule,
                status=SemanticDraftStatus.pending,
                title="有效成交订单",
                description="经营分析默认仅统计 delivered 状态订单。",
                mapping_target="delivered_orders_only",
                confidence=0.88,
                source_document="业务规则文档.md",
                source_snippet="默认经营分析只统计已完成交付订单 delivered。",
                fields=[
                    SemanticDraftField(label="术语类型", value="业务规则"),
                    SemanticDraftField(label="映射目标", value="orders.order_status = 'delivered'"),
                    SemanticDraftField(label="冲突校验", value="低风险"),
                    SemanticDraftField(label="Agent 解析结果", value="有效成交订单 -> delivered 过滤规则"),
                    SemanticDraftField(label="示例问题", value="有效成交订单的销售额是多少？"),
                ],
            ),
        ]
        with self._connect() as conn:
            for draft in seeds:
                conn.execute(
                    """
                    INSERT INTO semantic.semantic_drafts (
                        id, document_id, kind, status, title, description, mapping_target,
                        confidence, source_document, source_snippet, fields,
                        adopted_scope, vector_status, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        draft.id,
                        draft.document_id,
                        draft.kind.value,
                        draft.status.value,
                        draft.title,
                        draft.description,
                        draft.mapping_target,
                        draft.confidence,
                        draft.source_document,
                        draft.source_snippet,
                        Jsonb(_draft_fields_to_json(draft.fields)),
                        draft.adopted_scope,
                        draft.vector_status,
                        draft.created_at,
                        draft.updated_at,
                    ),
                )

    def _insert_conversation(self, conn, conversation: Conversation) -> None:
        conn.execute(
            """
            INSERT INTO app.conversations (
                id, thread_id, title, data_source_id, status, last_message_preview,
                adopted_semantic_draft_ids, adopted_semantic_draft_titles,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                conversation.id,
                conversation.thread_id,
                conversation.title,
                conversation.data_source_id,
                conversation.status.value,
                conversation.last_message_preview,
                conversation.adopted_semantic_draft_ids,
                conversation.adopted_semantic_draft_titles,
                conversation.created_at,
                conversation.updated_at,
            ),
        )

    def _insert_message(self, conn, message: Message) -> None:
        conn.execute(
            """
            INSERT INTO app.messages (
                id, conversation_id, run_id, role, content, metadata, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                message.id,
                message.conversation_id,
                message.run_id,
                message.role.value if hasattr(message.role, "value") else message.role,
                message.content,
                Jsonb(message.metadata),
                message.created_at,
            ),
        )

    def list_conversations(self, keyword: str | None = None) -> list[Conversation]:
        with self._connect() as conn:
            if keyword:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM app.conversations
                    WHERE title ILIKE %s
                    ORDER BY updated_at DESC
                    """,
                    (f"%{keyword}%",),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM app.conversations
                    ORDER BY updated_at DESC
                    """
                ).fetchall()
        return [_row_to_conversation(row) for row in rows]

    def create_conversation(self, payload: ConversationCreate) -> Conversation:
        conversation = Conversation(
            id=_id("conv"),
            thread_id=_id("thread"),
            title=_title_from_question(payload.question),
            data_source_id=payload.data_source_id,
            status=ConversationStatus.idle,
            last_message_preview=payload.question,
            adopted_semantic_draft_ids=payload.adopted_semantic_draft_ids,
            adopted_semantic_draft_titles=payload.adopted_semantic_draft_titles,
        )
        with self._connect() as conn:
            self._insert_conversation(conn, conversation)
            if payload.question:
                message = Message(
                    id=_id("msg"),
                    conversation_id=conversation.id,
                    role="user",
                    content=payload.question,
                )
                self._insert_message(conn, message)
                row = conn.execute(
                    """
                    UPDATE app.conversations
                    SET status = %s, last_message_preview = %s, updated_at = now()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (ConversationStatus.running.value, payload.question, conversation.id),
                ).fetchone()
                conversation = _row_to_conversation(row)
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM app.conversations WHERE id = %s",
                (conversation_id,),
            ).fetchone()
        return _row_to_conversation(row) if row else None

    def update_conversation(self, conversation_id: str, payload: ConversationUpdate) -> Conversation | None:
        current = self.get_conversation(conversation_id)
        if not current:
            return None
        title = payload.title if payload.title is not None else current.title
        status = payload.status.value if payload.status is not None else current.status.value
        with self._connect() as conn:
            row = conn.execute(
                """
                UPDATE app.conversations
                SET title = %s, status = %s, updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (title, status, conversation_id),
            ).fetchone()
        return _row_to_conversation(row) if row else None

    def delete_conversation(self, conversation_id: str) -> bool:
        with self._connect() as conn:
            result = conn.execute(
                "DELETE FROM app.conversations WHERE id = %s",
                (conversation_id,),
            )
            return result.rowcount > 0

    def list_messages(self, conversation_id: str) -> list[Message] | None:
        if not self.get_conversation(conversation_id):
            return None
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM app.messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            ).fetchall()
        return [_row_to_message(row) for row in rows]

    def add_message(self, conversation_id: str, payload: MessageCreate) -> Message | None:
        if not self.get_conversation(conversation_id):
            return None
        message = Message(
            id=_id("msg"),
            conversation_id=conversation_id,
            run_id=payload.run_id,
            role=payload.role,
            content=payload.content,
            metadata=payload.metadata,
        )
        with self._connect() as conn:
            self._insert_message(conn, message)
            status = ConversationStatus.running.value if payload.role.value == "user" else None
            if status:
                title = _title_from_question(payload.content)
                conn.execute(
                    """
                    UPDATE app.conversations
                    SET status = %s,
                        title = CASE WHEN title = '新建数据分析' THEN %s ELSE title END,
                        last_message_preview = %s,
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (status, title, payload.content, conversation_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE app.conversations
                    SET last_message_preview = %s, updated_at = now()
                    WHERE id = %s
                    """,
                    (payload.content, conversation_id),
                )
        return message

    def create_analysis_run(self, conversation_id: str, question: str) -> AnalysisRun | None:
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        run = AnalysisRun(
            id=_id("run"),
            conversation_id=conversation_id,
            thread_id=conversation.thread_id,
            question=question,
            data_source_id=conversation.data_source_id,
        )
        with self._connect() as conn:
            row = conn.execute(
                """
                INSERT INTO app.analysis_runs (
                    id, conversation_id, thread_id, question, data_source_id,
                    status, current_step, started_at, completed_at, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    run.id,
                    run.conversation_id,
                    run.thread_id,
                    run.question,
                    run.data_source_id,
                    run.status.value,
                    run.current_step,
                    run.started_at,
                    run.completed_at,
                    run.created_at,
                ),
            ).fetchone()
        return _row_to_analysis_run(row)

    def get_analysis_run(self, run_id: str) -> AnalysisRun | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM app.analysis_runs WHERE id = %s",
                (run_id,),
            ).fetchone()
        return _row_to_analysis_run(row) if row else None

    def update_analysis_run(
        self,
        run_id: str,
        status: AnalysisRunStatus,
        current_step: str | None = None,
    ) -> AnalysisRun | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                UPDATE app.analysis_runs
                SET status = %s,
                    current_step = %s,
                    started_at = CASE
                        WHEN %s = 'running' THEN COALESCE(started_at, now())
                        ELSE started_at
                    END,
                    completed_at = CASE
                        WHEN %s IN ('completed', 'failed', 'cancelled') THEN now()
                        ELSE completed_at
                    END
                WHERE id = %s
                RETURNING *
                """,
                (status.value, current_step, status.value, status.value, run_id),
            ).fetchone()
        return _row_to_analysis_run(row) if row else None

    def update_conversation_status(
        self,
        conversation_id: str,
        status: ConversationStatus,
    ) -> Conversation | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                UPDATE app.conversations
                SET status = %s, updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (status.value, conversation_id),
            ).fetchone()
        return _row_to_conversation(row) if row else None

    def create_document(self, payload: DocumentCreate) -> Document:
        document = Document(
            id=_id("doc"),
            file_name=payload.file_name,
            file_size=payload.file_size,
            document_type=payload.document_type,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO corpus.documents (
                    id, file_name, file_size, document_type, status, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    document.id,
                    document.file_name,
                    document.file_size,
                    document.document_type.value,
                    document.status,
                    document.created_at,
                ),
            )
        return document

    def get_document(self, document_id: str) -> Document | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM corpus.documents WHERE id = %s",
                (document_id,),
            ).fetchone()
        return _row_to_document(row) if row else None

    def extract_semantic_drafts(self, document_id: str) -> list[SemanticDraft] | None:
        document = self.get_document(document_id)
        if not document:
            return None
        drafts = self._build_drafts_for_document(document)
        with self._connect() as conn:
            conn.execute(
                "UPDATE corpus.documents SET status = 'extracted' WHERE id = %s",
                (document_id,),
            )
            for draft in drafts:
                self._insert_draft(conn, draft)
        return drafts

    def _build_drafts_for_document(self, document: Document) -> list[SemanticDraft]:
        if document.document_type == DocumentType.business_semantics:
            return [
                SemanticDraft(
                    id=_id("draft"),
                    document_id=document.id,
                    kind=SemanticDraftKind.glossary,
                    title="GMV",
                    description="用户提到 GMV、成交额、销售金额时，默认映射到销售额指标。",
                    mapping_target="sales_amount",
                    confidence=0.91,
                    source_document=document.file_name,
                    source_snippet="GMV / 成交额 / 销售金额：均表示商品成交金额，第一阶段不含运费。",
                    fields=[
                        SemanticDraftField(label="术语类型", value="指标别名"),
                        SemanticDraftField(label="映射目标", value="销售额"),
                    ],
                )
            ]

        return [
            SemanticDraft(
                id=_id("draft"),
                document_id=document.id,
                kind=SemanticDraftKind.metric,
                title="销售额",
                description="订单商品成交金额，不包含运费，默认仅统计已送达订单。",
                mapping_target="sales_amount",
                confidence=0.93,
                source_document=document.file_name,
                source_snippet="销售额 = 商品成交金额之和，不含运费；默认过滤 delivered 订单。",
                fields=[
                    SemanticDraftField(label="指标 ID", value="sales_amount"),
                    SemanticDraftField(label="SQL 表达式", value="SUM(order_items.price)"),
                    SemanticDraftField(label="默认过滤", value="orders.order_status = 'delivered'"),
                ],
            ),
            SemanticDraft(
                id=_id("draft"),
                document_id=document.id,
                kind=SemanticDraftKind.dimension,
                title="客户地区",
                description="使用 customers.customer_state 作为地区维度。",
                mapping_target="customer_region",
                confidence=0.84,
                source_document=document.file_name,
                source_snippet="地区分析统一使用客户收货州编码 customer_state。",
                fields=[SemanticDraftField(label="字段映射", value="customers.customer_state")],
            ),
        ]

    def _insert_draft(self, conn, draft: SemanticDraft) -> None:
        conn.execute(
            """
            INSERT INTO semantic.semantic_drafts (
                id, document_id, kind, status, title, description, mapping_target,
                confidence, source_document, source_snippet, fields,
                adopted_scope, vector_status, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                draft.id,
                draft.document_id,
                draft.kind.value,
                draft.status.value,
                draft.title,
                draft.description,
                draft.mapping_target,
                draft.confidence,
                draft.source_document,
                draft.source_snippet,
                Jsonb(_draft_fields_to_json(draft.fields)),
                draft.adopted_scope,
                draft.vector_status,
                draft.created_at,
                draft.updated_at,
            ),
        )

    def list_drafts(self, status: SemanticDraftStatus | None = None) -> list[SemanticDraft]:
        with self._connect() as conn:
            if status is None:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM semantic.semantic_drafts
                    ORDER BY created_at DESC
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM semantic.semantic_drafts
                    WHERE status = %s
                    ORDER BY created_at DESC
                    """,
                    (status.value,),
                ).fetchall()
        return [_row_to_draft(row) for row in rows]

    def update_draft(self, draft_id: str, payload: SemanticDraftUpdate) -> SemanticDraft | None:
        current = self._get_draft(draft_id)
        if not current:
            return None
        title = payload.title if payload.title is not None else current.title
        description = payload.description if payload.description is not None else current.description
        mapping_target = payload.mapping_target if payload.mapping_target is not None else current.mapping_target
        fields = payload.fields if payload.fields is not None else current.fields
        with self._connect() as conn:
            row = conn.execute(
                """
                UPDATE semantic.semantic_drafts
                SET title = %s,
                    description = %s,
                    mapping_target = %s,
                    fields = %s,
                    vector_status = 'stale',
                    updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (
                    title,
                    description,
                    mapping_target,
                    Jsonb(_draft_fields_to_json(fields)),
                    draft_id,
                ),
            ).fetchone()
        return _row_to_draft(row) if row else None

    def adopt_draft(self, draft_id: str, payload: SemanticDraftReview) -> SemanticDraft | None:
        draft = self._get_draft(draft_id)
        if not draft:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                UPDATE semantic.semantic_drafts
                SET status = %s, adopted_scope = %s, updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (SemanticDraftStatus.adopted.value, payload.adopted_scope, draft_id),
            ).fetchone()
            if payload.conversation_id:
                conn.execute(
                    """
                    UPDATE app.conversations
                    SET adopted_semantic_draft_ids = array_append(adopted_semantic_draft_ids, %s),
                        adopted_semantic_draft_titles = array_append(adopted_semantic_draft_titles, %s),
                        updated_at = now()
                    WHERE id = %s
                      AND NOT (%s = ANY(adopted_semantic_draft_ids))
                    """,
                    (draft.id, draft.title, payload.conversation_id, draft.id),
                )
                conn.execute(
                    """
                    INSERT INTO app.conversation_semantic_assets (
                        id, conversation_id, draft_id, asset_type, asset_snapshot
                    )
                    SELECT %s, %s, %s, %s, %s
                    WHERE EXISTS (
                        SELECT 1 FROM app.conversations WHERE id = %s
                    )
                    ON CONFLICT (conversation_id, draft_id) DO NOTHING
                    """,
                    (
                        _id("csa"),
                        payload.conversation_id,
                        draft.id,
                        draft.kind.value,
                        Jsonb(draft.model_dump(mode="json")),
                        payload.conversation_id,
                    ),
                )
        return _row_to_draft(row) if row else None

    def reject_draft(self, draft_id: str) -> SemanticDraft | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                UPDATE semantic.semantic_drafts
                SET status = %s, updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (SemanticDraftStatus.rejected.value, draft_id),
            ).fetchone()
        return _row_to_draft(row) if row else None

    def publish_draft(self, draft_id: str, mode: VectorSyncMode = VectorSyncMode.sync) -> tuple[
                                                                                              SemanticDraft, VectorJob] | None:
        draft = self._get_draft(draft_id)
        if not draft:
            return None
        with self._connect() as conn:
            row = conn.execute(
                """
                UPDATE semantic.semantic_drafts
                SET status = %s, adopted_scope = 'global', updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (SemanticDraftStatus.published.value, draft_id),
            ).fetchone()
        job = self.create_vector_job("asset_sync", draft.kind.value, draft.id, mode)
        vector_status = "synced" if job.status == VectorJobStatus.success else "pending"
        with self._connect() as conn:
            row = conn.execute(
                """
                UPDATE semantic.semantic_drafts
                SET vector_status = %s, updated_at = now()
                WHERE id = %s
                RETURNING *
                """,
                (vector_status, draft_id),
            ).fetchone()
        return (_row_to_draft(row), job) if row else None

    def _get_draft(self, draft_id: str) -> SemanticDraft | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM semantic.semantic_drafts WHERE id = %s",
                (draft_id,),
            ).fetchone()
        return _row_to_draft(row) if row else None

    def create_vector_job(
            self,
            job_type: str,
            asset_type: str | None,
            asset_id: str | None,
            mode: VectorSyncMode,
    ) -> VectorJob:
        job = VectorJob(
            id=_id("vjob"),
            job_type=job_type,
            asset_type=asset_type,
            asset_id=asset_id,
            status=VectorJobStatus.pending,
        )
        with self._connect() as conn:
            self._insert_vector_job(conn, job)
        if mode == VectorSyncMode.sync:
            self._complete_vector_job(job.id)
            refreshed = self._get_vector_job(job.id)
            return refreshed or job
        return job

    def _insert_vector_job(self, conn, job: VectorJob) -> None:
        conn.execute(
            """
            INSERT INTO vector.embedding_jobs (
                id, job_type, asset_type, asset_id, status,
                retry_count, error_message, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                job.id,
                job.job_type,
                job.asset_type,
                job.asset_id,
                job.status.value,
                job.retry_count,
                job.error_message,
                job.created_at,
                job.updated_at,
            ),
        )

    def _complete_vector_job(self, job_id: str) -> None:
        job = self._get_vector_job(job_id)
        if not job:
            return
        with self._connect() as conn:
            if job.asset_type and job.asset_id:
                draft = self._get_draft(job.asset_id)
                embedding_text = draft.description if draft else f"{job.asset_type}:{job.asset_id}"
                record = VectorEmbeddingRecord(
                    id=f"{job.asset_type}:{job.asset_id}",
                    asset_type=job.asset_type,
                    asset_id=job.asset_id,
                    embedding_text=embedding_text,
                    embedding_vector=_fake_embedding(embedding_text),
                )
                conn.execute(
                    """
                    INSERT INTO vector.semantic_asset_embeddings (
                        id, asset_type, asset_id, asset_version,
                        embedding_text, embedding_vector, status, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        embedding_text = EXCLUDED.embedding_text,
                        embedding_vector = EXCLUDED.embedding_vector,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        record.id,
                        record.asset_type,
                        record.asset_id,
                        record.asset_version,
                        record.embedding_text,
                        record.embedding_vector,
                        record.status,
                        record.updated_at,
                    ),
                )
            conn.execute(
                """
                UPDATE vector.embedding_jobs
                SET status = %s, updated_at = now()
                WHERE id = %s
                """,
                (VectorJobStatus.success.value, job_id),
            )

    def _get_vector_job(self, job_id: str) -> VectorJob | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM vector.embedding_jobs WHERE id = %s",
                (job_id,),
            ).fetchone()
        return _row_to_vector_job(row) if row else None

    def sync_vector_asset(self, asset_type: str, asset_id: str, mode: VectorSyncMode) -> VectorJob:
        return self.create_vector_job("asset_sync", asset_type, asset_id, mode)

    def rebuild_vectors(self, payload: VectorRebuildRequest) -> list[VectorJob]:
        with self._connect() as conn:
            if payload.asset_types:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM semantic.semantic_drafts
                    WHERE status = %s
                      AND kind = ANY(%s)
                    ORDER BY updated_at DESC
                    """,
                    (SemanticDraftStatus.published.value, payload.asset_types),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM semantic.semantic_drafts
                    WHERE status = %s
                    ORDER BY updated_at DESC
                    """,
                    (SemanticDraftStatus.published.value,),
                ).fetchall()
        published = [_row_to_draft(row) for row in rows]
        if not published:
            return [self.create_vector_job("full_rebuild", None, None, payload.mode)]
        return [
            self.create_vector_job("full_rebuild", draft.kind.value, draft.id, payload.mode)
            for draft in published
        ]

    def list_vector_jobs(self) -> list[VectorJob]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM vector.embedding_jobs
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [_row_to_vector_job(row) for row in rows]

    def _list_asset_rows(self, kind: str) -> list[dict]:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT *
                FROM semantic.semantic_drafts
                WHERE kind = %s
                  AND status <> %s
                ORDER BY
                    CASE status
                        WHEN 'published' THEN 0
                        WHEN 'adopted' THEN 1
                        WHEN 'pending' THEN 2
                        ELSE 3
                    END,
                    updated_at DESC
                """,
                (kind, SemanticDraftStatus.rejected.value),
            ).fetchall()

    def list_metric_assets(self) -> list[dict]:
        rows = self._list_asset_rows(SemanticDraftKind.metric.value)
        return [
            {
                "id": row["id"],
                "metric_id": _field_value(row, "指标 ID", row["mapping_target"]),
                "name": row["title"],
                "definition": row["description"],
                "sql_expression": _field_value(row, "SQL 表达式"),
                "dimensions": _split_field_value(_field_value(row, "可用维度")),
                "source": row["source_document"],
                "status": _semantic_page_status(row["status"]),
                "updated_at": row["updated_at"],
                "dependencies": _split_field_value(_field_value(row, "依赖表")),
                "synonyms": _split_field_value(_field_value(row, "同义词")),
                "sample_question": _field_value(row, "示例问题"),
                "vector_status": row["vector_status"],
            }
            for row in rows
        ]

    def list_dimension_assets(self) -> list[dict]:
        rows = self._list_asset_rows(SemanticDraftKind.dimension.value)
        return [
            {
                "id": row["id"],
                "dimension_id": row["mapping_target"],
                "name": row["title"],
                "field_mapping": _field_value(row, "字段映射"),
                "dataset": _field_value(row, "所属数据集"),
                "type": _field_value(row, "维度类型", "分类维度"),
                "available_metrics": _split_field_value(_field_value(row, "可用指标")),
                "source": row["source_document"],
                "status": _semantic_page_status(row["status"]),
                "updated_at": row["updated_at"],
                "common_filter": _field_value(row, "常用过滤"),
                "synonyms": _split_field_value(_field_value(row, "同义词")),
                "sample_question": _field_value(row, "示例问题"),
                "vector_status": row["vector_status"],
            }
            for row in rows
        ]

    def list_glossary_assets(self) -> list[dict]:
        rows = self._list_asset_rows(SemanticDraftKind.glossary.value)
        rule_rows = self._list_asset_rows(SemanticDraftKind.business_rule.value)
        assets = rows + rule_rows
        return [
            {
                "id": row["id"],
                "term_id": row["mapping_target"],
                "name": row["title"],
                "type": _field_value(row, "术语类型", "业务规则" if row["kind"] == "business_rule" else "指标别名"),
                "mapping_target": _field_value(row, "映射目标", row["mapping_target"]),
                "explanation": row["description"],
                "source": row["source_document"],
                "status": _semantic_page_status(row["status"]),
                "last_used": row["updated_at"],
                "conflict_check": _field_value(row, "冲突校验", "无冲突"),
                "agent_result": _field_value(row, "Agent 解析结果"),
                "sample_question": _field_value(row, "示例问题"),
                "vector_status": row["vector_status"],
            }
            for row in assets
        ]

    def list_dataset_assets(self) -> list[dict]:
        metadata = {
            "orders": {
                "description": "订单主表，记录订单状态、购买时间、审批时间、发货时间和交付时间。",
                "primary_key": "order_id",
                "common_time_field": "order_purchase_timestamp",
                "dependent_relations": [
                    "orders.order_id -> order_items.order_id",
                    "orders.order_id -> order_payments.order_id",
                    "orders.customer_id -> customers.customer_id",
                ],
            },
            "order_items": {
                "description": "订单明细表，记录订单内商品、卖家、价格和运费。",
                "primary_key": "order_id + order_item_id",
                "common_time_field": "shipping_limit_date",
                "dependent_relations": [
                    "order_items.order_id -> orders.order_id",
                    "order_items.product_id -> products.product_id",
                    "order_items.seller_id -> sellers.seller_id",
                ],
            },
            "products": {
                "description": "商品表，记录商品品类、尺寸、重量等属性。",
                "primary_key": "product_id",
                "common_time_field": "",
                "dependent_relations": [
                    "products.product_id -> order_items.product_id",
                    "products.product_category_name -> product_category_translation.product_category_name",
                ],
            },
            "customers": {
                "description": "客户表，记录客户所在城市和州。",
                "primary_key": "customer_id",
                "common_time_field": "",
                "dependent_relations": ["customers.customer_id -> orders.customer_id"],
            },
            "order_payments": {
                "description": "支付表，记录支付方式、分期数和支付金额。",
                "primary_key": "order_id + payment_sequential",
                "common_time_field": "",
                "dependent_relations": ["order_payments.order_id -> orders.order_id"],
            },
            "order_reviews": {
                "description": "评价表，记录订单评分、评论和评价时间。",
                "primary_key": "review_id",
                "common_time_field": "review_creation_date",
                "dependent_relations": ["order_reviews.order_id -> orders.order_id"],
            },
            "sellers": {
                "description": "卖家表，记录卖家所在城市和州。",
                "primary_key": "seller_id",
                "common_time_field": "",
                "dependent_relations": ["sellers.seller_id -> order_items.seller_id"],
            },
            "geolocation": {
                "description": "地理位置表，记录邮编、经纬度、城市和州。",
                "primary_key": "geolocation_zip_code_prefix",
                "common_time_field": "",
                "dependent_relations": [],
            },
            "product_category_translation": {
                "description": "品类翻译表，记录葡语品类名与英文品类名映射。",
                "primary_key": "product_category_name",
                "common_time_field": "",
                "dependent_relations": [
                    "product_category_translation.product_category_name -> products.product_category_name"],
            },
        }
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT table_name, column_name, data_type, ordinal_position
                FROM information_schema.columns
                WHERE table_schema = 'olist'
                ORDER BY table_name, ordinal_position
                """
            ).fetchall()
        columns_by_table: dict[str, list[dict]] = {}
        for row in rows:
            columns_by_table.setdefault(row["table_name"], []).append(row)

        table_names = sorted(set(metadata) | set(columns_by_table))
        return [
            {
                "name": table_name,
                "description": metadata.get(table_name, {}).get("description", "Olist 数据表。"),
                "primary_key": metadata.get(table_name, {}).get("primary_key", ""),
                "core_fields": [column["column_name"] for column in columns_by_table.get(table_name, [])[:6]],
                "fields": [
                    {
                        "name": column["column_name"],
                        "description": column["column_name"],
                        "type": column["data_type"],
                        "status": "已命中语义层" if column["ordinal_position"] <= 6 else "待补充语义",
                    }
                    for column in columns_by_table.get(table_name, [])
                ],
                "query_allowed": True,
                "dependent_relations": metadata.get(table_name, {}).get("dependent_relations", []),
                "common_time_field": metadata.get(table_name, {}).get("common_time_field", ""),
            }
            for table_name in table_names
        ]

    def semantic_counts(self) -> dict[str, int]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    (SELECT count(*) FROM semantic.semantic_drafts) AS drafts,
                    (SELECT count(*) FROM semantic.semantic_drafts WHERE status = 'published') AS published,
                    (SELECT count(*) FROM vector.embedding_jobs) AS vector_jobs,
                    (SELECT count(*) FROM vector.semantic_asset_embeddings) AS vector_embeddings
                """
            ).fetchone()
        return {
            "drafts": row["drafts"],
            "published": row["published"],
            "vector_jobs": row["vector_jobs"],
            "vector_embeddings": row["vector_embeddings"],
        }


store = PostgresStore()
