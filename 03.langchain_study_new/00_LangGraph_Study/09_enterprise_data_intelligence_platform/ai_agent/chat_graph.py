from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import AsyncIterator
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, TypedDict

import psycopg
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph, add_messages
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

load_dotenv()

POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql:///enterprise_data_ai")


class SQLGenerationResult(BaseModel):
    """模型生成 SQL 时返回的结构化结果。"""

    sql: str = Field(description="只读 PostgreSQL SQL，必须只查询 olist schema，并包含 LIMIT")
    reasoning: str = Field(description="简短说明为什么这样生成 SQL")
    tables: list[str] = Field(default_factory=list, description="SQL 使用到的数据表")
    metrics: list[str] = Field(default_factory=list, description="SQL 使用到的指标")
    dimensions: list[str] = Field(default_factory=list, description="SQL 使用到的维度")


class AnalysisState(TypedDict, total=False):
    """Phase 6 最小分析链路状态，承载消息、语义解析、SQL 草稿和审核结果。"""

    messages: Annotated[list[BaseMessage], add_messages]
    semantic_context: dict[str, Any]
    question: str
    semantic_parse: dict[str, Any]
    metric_parse: dict[str, Any]
    generated_sql: str
    sql_review: dict[str, Any]
    sql_result: dict[str, Any]
    final_text: str


def _last_user_text(messages: list[BaseMessage]) -> str:
    """从消息列表中提取最近一条用户问题文本。"""

    return str(next((message.content for message in reversed(messages) if message.type == "human"), "")).strip()


def _contains_any(text: str, keywords: list[str]) -> bool:
    """判断文本中是否包含任意关键词。"""

    lowered = text.lower()
    return any(keyword and keyword.lower() in lowered for keyword in keywords)


def _is_analysis_question(text: str) -> bool:
    """判断用户问题是否属于数据分析/问数意图。"""

    return _contains_any(
        text,
        [
            "销售",
            "订单",
            "品类",
            "客户",
            "退款",
            "支付",
            "gmv",
            "成交额",
            "趋势",
            "最高",
            "最低",
            "top",
            "分析",
            "统计",
            "查询",
            "多少",
            "复购",
            "复购率",
            "流失",
            "高危",
            "留存",
        ],
    )


def _is_customer_retention_question(text: str) -> bool:
    """判断是否是客户复购、流失、留存相关分析问题。"""

    return _contains_any(text, ["复购", "复购率", "流失", "高危", "留存"])


def _parse_chinese_number(value: str) -> int | None:
    """把常见中文数字转换成整数，用于识别“前十”“前五”这类 Top N 问法。"""

    text = value.strip()
    number_map = {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if text in number_map:
        return number_map[text]
    if text.startswith("十") and len(text) == 2:
        return 10 + number_map.get(text[1:], 0)
    if text.endswith("十") and len(text) == 2:
        return number_map.get(text[:1], 0) * 10
    if "十" in text and len(text) == 3:
        return number_map.get(text[:1], 0) * 10 + number_map.get(text[-1:], 0)
    return None


def _expected_limit_from_question(text: str) -> int:
    """根据用户问法识别期望返回行数，区分“最高”与“Top 10 分别是多少”。"""

    top_patterns = [
        r"top\s*(\d+)",
        r"TOP\s*(\d+)",
        r"前\s*(\d+)",
        r"排名\s*前\s*(\d+)",
        r"前\s*([一二两三四五六七八九十]{1,3})",
        r"排名\s*前\s*([一二两三四五六七八九十]{1,3})",
    ]
    for pattern in top_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        raw_value = match.group(1)
        parsed = int(raw_value) if raw_value.isdigit() else _parse_chinese_number(raw_value)
        if parsed:
            return max(1, min(parsed, 100))

    if _contains_any(text, ["最高", "最大", "最多", "最低", "最少"]) and not _contains_any(
        text,
        ["分别", "各", "排行", "排名", "列表", "明细"],
    ):
        return 1

    if _contains_any(text, ["分别", "各", "排行", "排名", "列表", "明细"]):
        return 10

    return 100


def _metric_keywords(metric: dict[str, Any]) -> list[str]:
    """从指标资产中整理可匹配的指标名称、ID 和同义词。"""

    return [
        metric.get("name", ""),
        metric.get("metric_id", ""),
        metric.get("definition", ""),
        *metric.get("synonyms", []),
    ]


def _dimension_keywords(dimension: dict[str, Any]) -> list[str]:
    """从维度资产中整理可匹配的维度名称、字段和同义词。"""

    return [
        dimension.get("name", ""),
        dimension.get("dimension_id", ""),
        dimension.get("field_mapping", ""),
        dimension.get("type", ""),
        *dimension.get("synonyms", []),
    ]


def _conversation_asset_keywords(asset: dict[str, Any]) -> list[str]:
    """从会话级语义资产快照中整理可匹配的标题、描述、映射目标和字段值。"""

    snapshot = asset.get("asset_snapshot") or {}
    field_values = [
        field.get("value", "")
        for field in snapshot.get("fields", [])
        if isinstance(field, dict)
    ]
    return [
        snapshot.get("title", ""),
        snapshot.get("description", ""),
        snapshot.get("mapping_target", ""),
        snapshot.get("source_snippet", ""),
        *field_values,
    ]


def _fallback_metric(context: dict[str, Any]) -> dict[str, Any]:
    """在问题没有明确命中指标时，默认选择销售额指标。"""

    metrics = context.get("metrics") or []
    return next(
        (metric for metric in metrics if metric.get("metric_id") == "sales_amount" or metric.get("name") == "销售额"),
        metrics[0] if metrics else {"name": "销售额", "metric_id": "sales_amount"},
    )


def _customer_metric_from_question(question: str) -> dict[str, Any]:
    """为客户复购/流失类问题提供项目内置指标口径。"""

    if _contains_any(question, ["流失", "高危"]) and _contains_any(question, ["复购", "复购率"]):
        return {
            "name": "流失高危用户及客户复购率",
            "metric_id": "churn_risk_and_repurchase_rate",
            "definition": "同时分析只有一次历史购买且长期未购买的流失高危客户，以及购买次数大于等于 2 的客户占比。",
            "sql_expression": "churn_risk_customer_count, repurchase_rate",
            "synonyms": ["流失高危用户", "客户复购率", "复购率", "高危客户"],
        }
    if _contains_any(question, ["流失", "高危"]):
        return {
            "name": "流失高危用户数",
            "metric_id": "churn_risk_customer_count",
            "definition": "只有一次历史购买且最近购买时间距离数据最大日期较久的客户数。",
            "sql_expression": "COUNT(DISTINCT customer_id)",
            "synonyms": ["流失高危用户", "高危客户", "流失风险用户"],
        }
    return {
        "name": "客户复购率",
        "metric_id": "repurchase_rate",
        "definition": "购买次数大于等于 2 的客户数 / 总客户数。",
        "sql_expression": "repurchase_customer_count / total_customer_count",
        "synonyms": ["复购率", "重复购买率", "客户复购"],
    }


def _fallback_dimension(context: dict[str, Any]) -> dict[str, Any]:
    """在问题没有明确命中维度时，默认选择品类维度。"""

    dimensions = context.get("dimensions") or []
    return next(
        (dimension for dimension in dimensions if "品类" in dimension.get("name", "")),
        dimensions[0] if dimensions else {"name": "品类", "dimension_id": "category"},
    )


def _customer_dimension_from_question() -> dict[str, Any]:
    """为客户分析类问题提供项目内置客户维度。"""

    return {
        "name": "客户",
        "dimension_id": "customer",
        "field_mapping": "orders.customer_id",
        "type": "客户维度",
        "synonyms": ["用户", "客户", "消费者"],
    }


def _build_category_sales_sql() -> str:
    """生成按品类汇总销售额的 PostgreSQL 查询草稿。"""

    return """SELECT
  COALESCE(pct.product_category_name_english, p.product_category_name) AS category,
  ROUND(SUM(oi.price)::numeric, 2) AS sales_amount,
  COUNT(DISTINCT o.order_id) AS order_count
FROM olist.orders o
JOIN olist.order_items oi ON o.order_id = oi.order_id
JOIN olist.products p ON oi.product_id = p.product_id
LEFT JOIN olist.product_category_translation pct
  ON p.product_category_name = pct.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY category
ORDER BY sales_amount DESC
LIMIT 10;"""


def _build_daily_sales_sql() -> str:
    """生成按日期汇总销售额趋势的 PostgreSQL 查询草稿。"""

    return """SELECT
  DATE_TRUNC('day', o.order_purchase_timestamp)::date AS order_date,
  ROUND(SUM(oi.price)::numeric, 2) AS sales_amount,
  COUNT(DISTINCT o.order_id) AS order_count
FROM olist.orders o
JOIN olist.order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY order_date
ORDER BY order_date ASC
LIMIT 100;"""


def _build_sql_model() -> ChatOpenAI | None:
    """按环境变量创建 SQL 生成模型；未配置或 mock 模式时返回 None。"""

    if os.getenv("INSIGHT_SQL_MODEL_MODE") == "mock":
        return None

    api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    if not api_key or not model_name:
        return None

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
        timeout=30,
        max_retries=1,
    )


def _compact_asset_list(items: list[dict[str, Any]], keys: list[str], limit: int = 8) -> list[dict[str, Any]]:
    """压缩语义资产字段，避免把过多无关 UI 字段传给 SQL 生成模型。"""

    compacted = []
    for item in items[:limit]:
        compacted.append({key: item.get(key) for key in keys if item.get(key) not in (None, "", [])})
    return compacted


def _build_olist_schema_context() -> str:
    """返回允许模型使用的 Olist PostgreSQL 表结构和常用 Join 关系。"""

    return """
只允许使用以下 PostgreSQL schema 和字段：

olist.orders(
  order_id text PRIMARY KEY,
  customer_id text,
  order_status text,
  order_purchase_timestamp timestamp,
  order_approved_at timestamp,
  order_delivered_carrier_date timestamp,
  order_delivered_customer_date timestamp,
  order_estimated_delivery_date timestamp
)

olist.order_items(
  order_id text,
  order_item_id integer,
  product_id text,
  seller_id text,
  shipping_limit_date timestamp,
  price numeric(12,2),
  freight_value numeric(12,2)
)

olist.products(
  product_id text PRIMARY KEY,
  product_category_name text,
  product_name_length integer,
  product_description_length integer,
  product_photos_qty integer,
  product_weight_g integer,
  product_length_cm integer,
  product_height_cm integer,
  product_width_cm integer
)

olist.product_category_translation(
  product_category_name text PRIMARY KEY,
  product_category_name_english text
)

olist.customers(
  customer_id text PRIMARY KEY,
  customer_unique_id text,
  customer_zip_code_prefix integer,
  customer_city text,
  customer_state text
)

olist.order_payments(
  order_id text,
  payment_sequential integer,
  payment_type text,
  payment_installments integer,
  payment_value numeric(12,2)
)

常用 Join：
- orders.order_id = order_items.order_id
- order_items.product_id = products.product_id
- products.product_category_name = product_category_translation.product_category_name
- orders.customer_id = customers.customer_id
- orders.order_id = order_payments.order_id

核心口径：
- 销售额 / GMV / 成交额：SUM(order_items.price)，不含运费。
- 订单数：COUNT(DISTINCT orders.order_id)。
- 客单价：销售额 / 订单数。
- 复购客户：同一 customer_id 的已完成订单数 >= 2。
- 客户复购率：复购客户数 / 总客户数。
- 流失高危用户：只有一次已完成订单，且最近购买时间距离数据最大购买日期超过 180 天的客户。
- 默认只统计已完成订单：orders.order_status = 'delivered'。
""".strip()


def _build_semantic_sql_prompt(state: AnalysisState) -> list[BaseMessage]:
    """基于当前问题、解析结果和语义资产构造 SQL 生成提示词。"""

    context = state.get("semantic_context", {})
    semantic_parse = state.get("semantic_parse", {})
    metric_parse = state.get("metric_parse", {})
    expected_limit = semantic_parse.get("expected_limit") or _expected_limit_from_question(state.get("question", ""))
    semantic_assets = {
        "matched_semantic_parse": semantic_parse,
        "parsed_metric_and_dimension": metric_parse,
        "metrics": _compact_asset_list(
            context.get("metrics", []),
            ["metric_id", "name", "definition", "sql_expression", "dimensions", "synonyms", "dependencies"],
        ),
        "dimensions": _compact_asset_list(
            context.get("dimensions", []),
            ["dimension_id", "name", "field_mapping", "type", "available_metrics", "synonyms"],
        ),
        "glossary": _compact_asset_list(
            context.get("glossary", []),
            ["term_id", "name", "type", "mapping_target", "explanation", "agent_result"],
        ),
        "conversation_assets": _compact_asset_list(
            context.get("conversation_assets", []),
            ["draft_id", "asset_type", "asset_snapshot"],
            limit=5,
        ),
    }
    system_prompt = f"""
你是企业数据智能分析平台的 Text-to-SQL 节点。
你必须根据用户问题、语义资产和允许的数据表结构生成 PostgreSQL 只读 SQL。

硬性规则：
1. 只能输出 SELECT 查询。
2. 只能查询 olist schema。
3. 禁止 INSERT / UPDATE / DELETE / DROP / ALTER / CREATE / TRUNCATE。
4. 必须包含 LIMIT，除非聚合结果天然只有一行也建议 LIMIT 100。
5. 不要编造不存在的表和字段。
6. 能用语义资产中的指标口径时，优先使用语义资产。
7. SQL 不要包含 Markdown 代码块。
8. 输出列必须使用稳定别名：品类维度 AS category，日期维度 AS order_date，销售额 AS sales_amount，订单数 AS order_count。
9. 查询品类时优先 LEFT JOIN olist.product_category_translation，并使用 COALESCE(product_category_name_english, product_category_name) AS category。
10. 用户本次期望返回 {expected_limit} 行，SQL 最终 LIMIT 必须使用 {expected_limit}。
""".strip()
    human_prompt = f"""
用户问题：
{state.get("question", "")}

期望返回行数：
{expected_limit}

允许的数据结构：
{_build_olist_schema_context()}

当前语义资产和解析结果 JSON：
{json.dumps(semantic_assets, ensure_ascii=False, default=str)}

请返回结构化结果：
- sql: 可直接执行的 PostgreSQL SQL
- reasoning: 生成原因
- tables: 使用的数据表
- metrics: 使用的指标
- dimensions: 使用的维度
""".strip()
    return [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]


def _strip_sql_fences(sql: str) -> str:
    """清理模型可能返回的 Markdown 代码块，只保留 SQL 本体。"""

    cleaned = sql.strip()
    cleaned = re.sub(r"^```(?:sql)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned if cleaned.endswith(";") else f"{cleaned};"


def _apply_expected_limit(sql: str, expected_limit: int) -> str:
    """把 SQL 的最终 LIMIT 校正为语义解析得到的期望行数，避免模型误把 Top 10 写成 LIMIT 1。"""

    cleaned = _strip_sql_fences(sql)
    safe_limit = max(1, min(int(expected_limit or 100), 1000))
    matches = list(re.finditer(r"\bLIMIT\s+\d+\b", cleaned, re.IGNORECASE))
    if matches:
        last_match = matches[-1]
        return f"{cleaned[:last_match.start()]}LIMIT {safe_limit}{cleaned[last_match.end():]}"
    return f"{cleaned.rstrip(';')}\nLIMIT {safe_limit};"


def _fallback_sql_for_question(question: str) -> tuple[str, str]:
    """模型不可用或生成失败时，根据问题返回确定性兜底 SQL。"""

    if _contains_any(question, ["趋势", "每天", "每日", "按天", "时间"]):
        return _build_daily_sales_sql(), "template_fallback_daily_sales"
    return _build_category_sales_sql(), "template_fallback_category_sales"


def _generate_sql_with_model(state: AnalysisState) -> dict[str, Any]:
    """调用模型基于语义资产生成 SQL；失败时返回模板兜底结果。"""

    question = state.get("question", "")
    expected_limit = state.get("semantic_parse", {}).get("expected_limit") or _expected_limit_from_question(question)
    model = _build_sql_model()
    if model is None:
        sql, mode = _fallback_sql_for_question(question)
        sql = _apply_expected_limit(sql, expected_limit)
        return {
            "sql": sql,
            "reasoning": "模型未配置或处于 mock 模式，使用确定性 SQL 模板兜底。",
            "tables": ["olist.orders", "olist.order_items", "olist.products", "olist.product_category_translation"],
            "metrics": ["销售额"],
            "dimensions": ["品类" if "category" in mode else "日期"],
            "generation_mode": mode,
            "expected_limit": expected_limit,
        }

    messages = _build_semantic_sql_prompt(state)
    try:
        structured_model = model.with_structured_output(SQLGenerationResult)
        result = structured_model.invoke(messages)
        sql = _apply_expected_limit(result.sql, expected_limit)
        return {
            "sql": sql,
            "reasoning": result.reasoning,
            "tables": result.tables,
            "metrics": result.metrics,
            "dimensions": result.dimensions,
            "generation_mode": "llm_semantic_assets",
            "expected_limit": expected_limit,
        }
    except Exception as exc:
        sql, mode = _fallback_sql_for_question(question)
        sql = _apply_expected_limit(sql, expected_limit)
        return {
            "sql": sql,
            "reasoning": f"模型生成 SQL 失败，已使用模板兜底：{exc}",
            "tables": ["olist.orders", "olist.order_items", "olist.products", "olist.product_category_translation"],
            "metrics": ["销售额"],
            "dimensions": ["品类" if "category" in mode else "日期"],
            "generation_mode": mode,
            "expected_limit": expected_limit,
        }


async def _generate_sql_with_model_async(state: AnalysisState) -> dict[str, Any]:
    """在线程池中调用同步模型接口，避免阻塞 async LangGraph 节点。"""

    return await asyncio.to_thread(_generate_sql_with_model, state)


def _review_sql(sql: str) -> dict[str, Any]:
    """执行最小 SQL 安全审核，确保只读、限定 olist schema，并存在 LIMIT。"""

    normalized = re.sub(r"\s+", " ", sql.strip()).upper()
    forbidden = ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "TRUNCATE ", "ALTER ", "CREATE "]
    starts_with_readonly_query = normalized.startswith("SELECT ") or normalized.startswith("WITH ")
    checks = [
        {"name": "SELECT / WITH only", "passed": starts_with_readonly_query},
        {"name": "禁止 DDL / DML", "passed": not any(word in normalized for word in forbidden)},
        {"name": "限定 olist schema", "passed": " OLIST." in normalized or "\nFROM OLIST." in normalized},
        {"name": "默认 LIMIT", "passed": " LIMIT " in normalized},
    ]
    passed = all(check["passed"] for check in checks)
    return {
        "passed": passed,
        "risk_level": "low" if passed else "high",
        "checks": checks,
        "summary": "SQL 安全审核通过，可进入只读执行阶段。" if passed else "SQL 审核未通过，需要人工确认。",
    }


def _json_safe(value: Any) -> Any:
    """把 PostgreSQL 查询结果转换为前端可 JSON 序列化的数据。"""

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _extract_limit(sql: str) -> int:
    """从 SQL 中提取 LIMIT 数值，用于前端审计展示。"""

    match = re.search(r"\bLIMIT\s+(\d+)\b", sql, re.IGNORECASE)
    if not match:
        return 0
    return int(match.group(1))


def _extract_sql_tables(sql: str, generated_tables: list[str] | None = None) -> list[str]:
    """从 SQL 和模型生成结果中整理实际使用的数据表。"""

    tables = set(generated_tables or [])
    tables.update(re.findall(r"\bolist\.[a-zA-Z_][a-zA-Z0-9_]*\b", sql))
    return sorted(tables)


def _extract_sql_fields(sql: str) -> list[str]:
    """从 SQL 文本中轻量提取 table alias 字段引用，供 Sources tab 追溯。"""

    fields = set()
    for alias, field in re.findall(r"\b([a-zA-Z][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\b", sql):
        if alias.lower() != "olist":
            fields.add(f"{alias}.{field}")
    return sorted(fields)


def _build_sources_payload(state: AnalysisState, generation: dict[str, Any]) -> dict[str, Any]:
    """组装 Sources 事件，描述本次 SQL 使用的数据表、字段、指标和维度。"""

    sql = generation.get("sql", "")
    semantic_parse = state.get("semantic_parse", {})
    context = state.get("semantic_context", {})
    return {
        "type": "sources.created",
        "tables": _extract_sql_tables(sql, generation.get("tables")),
        "fields": _extract_sql_fields(sql),
        "metrics": generation.get("metrics", []),
        "dimensions": generation.get("dimensions", []),
        "semantic_source": semantic_parse.get("source", "structured_semantic_assets"),
        "conversation_asset_count": semantic_parse.get("conversation_asset_count", 0),
        "matched_terms": semantic_parse.get("matched_terms", []),
        "matched_conversation_assets": semantic_parse.get("matched_conversation_assets", []),
        "used_global_assets": bool(context.get("metrics") or context.get("dimensions") or context.get("glossary")),
        "used_conversation_assets": bool(semantic_parse.get("matched_conversation_assets")),
        "vector_fallback_used": False,
        "stale_vector_record": False,
    }


def _build_audit_payload(state: AnalysisState, result: dict[str, Any]) -> dict[str, Any]:
    """组装 Audit 事件，描述 SQL 审核、执行耗时、返回行数和可追溯状态。"""

    review = state.get("sql_review", {})
    return {
        "type": "audit.created",
        "risk_level": review.get("risk_level", "unknown"),
        "review_passed": review.get("passed", False),
        "checks": review.get("checks", []),
        "row_count": result.get("row_count", 0),
        "elapsed_ms": result.get("elapsed_ms", 0),
        "limit": result.get("limit", 0),
        "execution_status": "failed" if result.get("error") else "success",
        "error": result.get("error"),
        "human_confirmation_required": False,
        "vector_fallback_used": False,
        "stale_vector_record": False,
    }


def _execute_readonly_sql(sql: str) -> dict[str, Any]:
    """以只读方式执行已审核 SQL，并返回列名、行数据和执行统计。"""

    started_at = datetime.now()
    with psycopg.connect(POSTGRES_URI, row_factory=dict_row) as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '5000ms'")
            cursor = conn.execute(sql)
            rows = cursor.fetchall()

    safe_rows = _json_safe(rows)
    columns = list(safe_rows[0].keys()) if safe_rows else []
    elapsed_ms = round((datetime.now() - started_at).total_seconds() * 1000, 2)
    return {
        "columns": columns,
        "rows": safe_rows,
        "row_count": len(safe_rows),
        "limit": _extract_limit(sql),
        "elapsed_ms": elapsed_ms,
    }


async def _execute_readonly_sql_async(sql: str) -> dict[str, Any]:
    """在线程池中执行同步 psycopg 查询，避免阻塞 LangGraph async 节点。"""

    return await asyncio.to_thread(_execute_readonly_sql, sql)


def _first_present_value(row: dict[str, Any], keys: list[str]) -> Any:
    """从查询结果行中按候选字段名取第一个非空值，兼容模型生成的不同列别名。"""

    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return "--"


def _build_result_sentence(
    metric_name: str,
    top_label: Any,
    top_value: Any,
    top_row: dict[str, Any],
    row_count: int = 0,
) -> str:
    """根据指标类型生成更自然的结果摘要，避免所有问题都说排名第一。"""

    if ("复购" in metric_name and ("流失" in metric_name or "高危" in metric_name)) or (
        "churn_risk_customer_count" in top_row and "repurchase_rate" in top_row
    ):
        churn_count = _first_present_value(top_row, ["churn_risk_customer_count", "risk_customer_count"])
        repurchase_rate = _first_present_value(top_row, ["repurchase_rate"])
        return f"本次聚合结果显示：流失高危用户数为 {churn_count}，客户复购率为 {repurchase_rate}。"
    if "复购" in metric_name:
        repurchase_rate = _first_present_value(top_row, ["repurchase_rate"])
        repurchase_customers = _first_present_value(top_row, ["repurchase_customer_count"])
        total_customers = _first_present_value(top_row, ["total_customer_count", "customer_count"])
        return (
            f"首行结果维度为 {top_label}，复购率为 {repurchase_rate}，"
            f"复购客户数 {repurchase_customers}，客户总数 {total_customers}。"
        )
    if "流失" in metric_name or "高危" in metric_name:
        churn_count = _first_present_value(top_row, ["churn_risk_customer_count", "risk_customer_count", "customer_count"])
        return f"首行结果维度为 {top_label}，流失高危用户数为 {churn_count}。"
    if row_count > 1:
        return f"已返回前 {row_count} 个结果，当前排名第一的是：{top_label}，销售额为 {top_value}。"
    return f"当前结果中排名第一的是：{top_label}，销售额为 {top_value}。"


def _emit_step_started(step: str, name: str) -> None:
    """向前端发送节点开始事件。"""

    get_stream_writer()({"type": "step.started", "step": step, "name": name})


def _emit_step_completed(step: str, name: str, summary: str, **extra: Any) -> None:
    """向前端发送节点完成事件。"""

    get_stream_writer()(
        {
            "type": "step.completed",
            "step": step,
            "name": name,
            "summary": summary,
            **extra,
        }
    )


async def _semantic_parse_node(state: AnalysisState) -> dict[str, Any]:
    """结构化语义解析节点：优先用后端传入的指标、维度、术语表做确定性匹配。"""

    _emit_step_started("semantic_parse", "结构化语义解析")
    question = _last_user_text(state["messages"])
    context = state.get("semantic_context", {})
    expected_limit = _expected_limit_from_question(question)

    matched_metrics = [
        metric
        for metric in context.get("metrics", [])
        if _contains_any(question, _metric_keywords(metric))
    ]
    matched_dimensions = [
        dimension
        for dimension in context.get("dimensions", [])
        if _contains_any(question, _dimension_keywords(dimension))
    ]
    matched_terms = [
        term
        for term in context.get("glossary", [])
        if _contains_any(question, [term.get("name", ""), term.get("mapping_target", ""), term.get("explanation", "")])
    ]
    matched_conversation_assets = [
        asset
        for asset in context.get("conversation_assets", [])
        if _contains_any(question, _conversation_asset_keywords(asset))
    ]

    if not matched_metrics and _contains_any(question, ["销售", "销售额", "gmv", "成交额", "金额"]):
        matched_metrics = [_fallback_metric(context)]
    if not matched_dimensions and _contains_any(question, ["品类", "商品类型", "类别"]):
        matched_dimensions = [_fallback_dimension(context)]
    if _is_customer_retention_question(question):
        if not matched_metrics:
            matched_metrics = [_customer_metric_from_question(question)]
        if not matched_dimensions:
            matched_dimensions = [_customer_dimension_from_question()]

    confidence = 0.92 if matched_metrics and matched_dimensions else 0.62 if matched_metrics else 0.35
    semantic_parse = {
        "question": question,
        "is_analysis_intent": _is_analysis_question(question),
        "matched_metrics": matched_metrics[:3],
        "matched_dimensions": matched_dimensions[:3],
        "matched_terms": matched_terms[:5],
        "matched_conversation_assets": matched_conversation_assets[:5],
        "conversation_asset_count": len(context.get("conversation_assets", [])),
        "confidence": confidence,
        "needs_vector_fallback": confidence < 0.7,
        "source": "structured_semantic_assets",
        "expected_limit": expected_limit,
    }

    _emit_step_completed(
        "semantic_parse",
        "结构化语义解析",
        (
            f"命中指标 {len(matched_metrics)} 个、维度 {len(matched_dimensions)} 个、"
            f"术语 {len(matched_terms)} 个、会话资产 {len(matched_conversation_assets)} 个，"
            f"置信度 {confidence:.2f}，期望返回 {expected_limit} 行。"
        ),
        semantic_parse=semantic_parse,
    )
    await asyncio.sleep(0)
    return {"question": question, "semantic_parse": semantic_parse}


def _route_after_semantic_parse(state: AnalysisState) -> str:
    """根据语义解析结果决定走数据分析链路还是普通聊天链路。"""

    if state.get("semantic_parse", {}).get("is_analysis_intent"):
        return "metric_parse"
    return "chat"


async def _chat_node(state: AnalysisState) -> dict[str, Any]:
    """普通聊天节点：非问数问题不生成 SQL，只返回自然语言回复。"""

    _emit_step_started("chat", "普通聊天")
    question = state.get("question") or _last_user_text(state["messages"])
    final_text = (
        "你好，我在。当前我已经支持两类能力：普通聊天，以及数据分析问题的 "
        "结构化语义解析、SQL 生成和 SQL 审核最小闭环。\n\n"
        f"你刚才说的是：{question}\n\n"
        "如果你想测试分析链路，可以问：哪个品类销售额最高？"
    )

    for token in final_text:
        get_stream_writer()({"type": "message.delta", "content": token})
        await asyncio.sleep(0)

    get_stream_writer()({"type": "message.completed", "content": final_text})
    _emit_step_completed("chat", "普通聊天", "已完成普通聊天回复。")
    return {"final_text": final_text, "messages": [AIMessage(content=final_text)]}


async def _metric_parse_node(state: AnalysisState) -> dict[str, Any]:
    """指标解析节点：确定最终使用的指标、维度和默认过滤条件。"""

    _emit_step_started("metric_parse", "指标解析")
    context = state.get("semantic_context", {})
    semantic_parse = state.get("semantic_parse", {})
    metric = (semantic_parse.get("matched_metrics") or [_fallback_metric(context)])[0]
    dimension = (semantic_parse.get("matched_dimensions") or [_fallback_dimension(context)])[0]

    metric_parse = {
        "metric": {
            "name": metric.get("name", "销售额"),
            "metric_id": metric.get("metric_id", metric.get("mapping_target", "sales_amount")),
            "sql_expression": metric.get("sql_expression", "SUM(order_items.price)"),
        },
        "dimensions": [
            {
                "name": dimension.get("name", "品类"),
                "dimension_id": dimension.get("dimension_id", dimension.get("mapping_target", "category")),
                "field_mapping": dimension.get("field_mapping", "products.product_category_name"),
            }
        ],
        "filters": ["orders.order_status = 'delivered'"],
    }

    _emit_step_completed(
        "metric_parse",
        "指标解析",
        f"确认指标：{metric_parse['metric']['name']}；分析维度：{metric_parse['dimensions'][0]['name']}。",
        metric_parse=metric_parse,
    )
    await asyncio.sleep(0)
    return {"metric_parse": metric_parse}


async def _sql_generate_node(state: AnalysisState) -> dict[str, Any]:
    """SQL 生成节点：优先基于语义资产动态生成 SQL，失败时使用模板兜底。"""

    _emit_step_started("sql_generate", "SQL 生成")
    generation = await _generate_sql_with_model_async(state)
    sql = generation["sql"]

    event = {
        "type": "sql.generated",
        "sql": sql,
        "dialect": "postgresql",
        "tables": generation.get("tables", []),
        "metrics": generation.get("metrics", []),
        "dimensions": generation.get("dimensions", []),
        "reasoning": generation.get("reasoning", ""),
        "generation_mode": generation.get("generation_mode", "unknown"),
        "expected_limit": generation.get("expected_limit"),
        "summary": "已基于语义资产生成 PostgreSQL SELECT 查询草稿。",
    }
    get_stream_writer()(event)
    get_stream_writer()(_build_sources_payload(state, event))
    _emit_step_completed(
        "sql_generate",
        "SQL 生成",
        f"已生成只读 SQL 草稿，生成模式：{event['generation_mode']}，等待安全审核。",
        sql=sql,
        sql_generation=event,
    )
    await asyncio.sleep(0)
    return {"generated_sql": sql}


async def _sql_review_node(state: AnalysisState) -> dict[str, Any]:
    """SQL 审核节点：检查只读、schema、危险语句和 LIMIT。"""

    _emit_step_started("sql_review", "SQL 审核")
    review = _review_sql(state.get("generated_sql", ""))
    get_stream_writer()({"type": "sql.reviewed", **review})
    _emit_step_completed(
        "sql_review",
        "SQL 审核",
        review["summary"],
        sql_review=review,
    )
    await asyncio.sleep(0)
    return {"sql_review": review}


async def _sql_execute_node(state: AnalysisState) -> dict[str, Any]:
    """SQL 执行节点：审核通过后查询真实 PostgreSQL，并发出表格 artifact。"""

    _emit_step_started("sql_execute", "SQL 执行")
    review = state.get("sql_review", {})
    sql = state.get("generated_sql", "")
    if not review.get("passed"):
        result = {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "limit": 0,
            "elapsed_ms": 0,
            "skipped": True,
            "error": "SQL 审核未通过，已跳过执行。",
        }
        _emit_step_completed("sql_execute", "SQL 执行", result["error"], sql_result=result)
        return {"sql_result": result}

    try:
        result = await _execute_readonly_sql_async(sql)
        get_stream_writer()(
            {
                "type": "artifact.created",
                "artifact_type": "table",
                "title": "SQL 查询结果",
                "columns": result["columns"],
                "rows": result["rows"],
                "row_count": result["row_count"],
                "elapsed_ms": result["elapsed_ms"],
            }
        )
        get_stream_writer()(_build_audit_payload(state, result))
        _emit_step_completed(
            "sql_execute",
            "SQL 执行",
            f"真实 PostgreSQL 查询完成，返回 {result['row_count']} 行，耗时 {result['elapsed_ms']} ms。",
            sql_result=result,
        )
    except Exception as exc:
        result = {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "limit": _extract_limit(sql),
            "elapsed_ms": 0,
            "error": str(exc),
        }
        get_stream_writer()(_build_audit_payload(state, result))
        _emit_step_completed("sql_execute", "SQL 执行", f"SQL 执行失败：{exc}", sql_result=result)

    return {"sql_result": result}


async def _report_node(state: AnalysisState) -> dict[str, Any]:
    """报告生成节点：基于真实 SQL 查询结果输出可读分析草稿。"""

    _emit_step_started("report", "报告生成")
    metric_parse = state.get("metric_parse", {})
    metric_name = metric_parse.get("metric", {}).get("name", "销售额")
    dimension_name = (metric_parse.get("dimensions") or [{"name": "品类"}])[0].get("name", "品类")
    review = state.get("sql_review", {})
    sql = state.get("generated_sql", "")
    sql_result = state.get("sql_result", {})
    rows = sql_result.get("rows", [])
    top_row = rows[0] if rows else {}
    top_label = _first_present_value(
        top_row,
        [
            "category",
            "product_category_name",
            "product_category_name_english",
            "order_date",
            "customer_state",
            "payment_type",
        ],
    )
    top_value = _first_present_value(
        top_row,
        ["sales_amount", "gmv", "total_sales", "revenue", "order_count", "count"],
    )
    result_sentence = _build_result_sentence(metric_name, top_label, top_value, top_row, sql_result.get("row_count", 0))

    final_text = (
        f"已完成真实 PostgreSQL 查询闭环：结构化语义解析 -> 指标解析 -> SQL 生成 -> SQL 审核 -> SQL 执行。\n\n"
        f"- 识别指标：{metric_name}\n"
        f"- 识别维度：{dimension_name}\n"
        f"- SQL 审核：{'通过' if review.get('passed') else '未通过'}，风险等级 {review.get('risk_level', '--')}\n\n"
        f"查询返回 {sql_result.get('row_count', 0)} 行，耗时 {sql_result.get('elapsed_ms', 0)} ms。\n"
        f"{result_sentence}\n\n"
        f"生成的 SQL 草稿：\n```sql\n{sql}\n```"
    )

    for token in final_text:
        get_stream_writer()({"type": "message.delta", "content": token})
        await asyncio.sleep(0)

    get_stream_writer()({"type": "message.completed", "content": final_text})
    _emit_step_completed("report", "报告生成", "已生成 Phase 6 分析草稿。")
    return {"final_text": final_text, "messages": [AIMessage(content=final_text)]}


def build_chat_graph():
    """构建最小分析 Graph：语义解析、SQL 生成、审核、执行和报告生成。"""

    builder = StateGraph(AnalysisState)
    builder.add_node("semantic_parse", _semantic_parse_node)
    builder.add_node("chat", _chat_node)
    builder.add_node("metric_parse", _metric_parse_node)
    builder.add_node("sql_generate", _sql_generate_node)
    builder.add_node("sql_review", _sql_review_node)
    builder.add_node("sql_execute", _sql_execute_node)
    builder.add_node("report", _report_node)

    builder.add_edge(START, "semantic_parse")
    builder.add_conditional_edges(
        "semantic_parse",
        _route_after_semantic_parse,
        {
            "chat": "chat",
            "metric_parse": "metric_parse",
        },
    )
    builder.add_edge("chat", END)
    builder.add_edge("metric_parse", "sql_generate")
    builder.add_edge("sql_generate", "sql_review")
    builder.add_edge("sql_review", "sql_execute")
    builder.add_edge("sql_execute", "report")
    builder.add_edge("report", END)
    return builder.compile()


chat_graph = build_chat_graph()


async def stream_chat_graph(
    messages: list[BaseMessage],
    thread_id: str,
    semantic_context: dict | None = None,
) -> AsyncIterator[dict]:
    """执行 Phase 6 Graph，并把 custom stream 事件逐条产出给 AI 服务接口。"""

    config = {"configurable": {"thread_id": thread_id}}
    async for event in chat_graph.astream(
        {
            "messages": messages,
            "semantic_context": semantic_context or {},
        },
        config=config,
        stream_mode="custom",
    ):
        yield event
