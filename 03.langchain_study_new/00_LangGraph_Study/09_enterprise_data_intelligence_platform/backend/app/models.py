from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DataSource(BaseModel):
    id: str = "olist"
    name: str = "Olist Ecommerce"
    type: str = "postgresql"
    database: str = "enterprise_data_ai"
    schema_name: str = Field(default="olist", serialization_alias="schema")
    table_count: int = 9
    status: str = "active"


class User(BaseModel):
    id: str
    name: str
    email: str
    role: str


class ConversationStatus(StrEnum):
    idle = "idle"
    running = "running"
    waiting_user = "waiting_user"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ConversationCreate(BaseModel):
    question: str | None = None
    data_source_id: str = "olist"
    adopted_semantic_draft_ids: list[str] = Field(default_factory=list)
    adopted_semantic_draft_titles: list[str] = Field(default_factory=list)


class ConversationUpdate(BaseModel):
    title: str | None = None
    status: ConversationStatus | None = None


class Conversation(BaseModel):
    id: str
    thread_id: str
    title: str
    data_source_id: str = "olist"
    status: ConversationStatus = ConversationStatus.idle
    last_message_preview: str | None = None
    adopted_semantic_draft_ids: list[str] = Field(default_factory=list)
    adopted_semantic_draft_titles: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class MessageRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"


class MessageCreate(BaseModel):
    role: MessageRole = MessageRole.user
    content: str
    run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    id: str
    conversation_id: str
    run_id: str | None = None
    role: MessageRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class AnalysisRunStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ChatRunCreate(BaseModel):
    question: str


class AnalysisRun(BaseModel):
    id: str
    conversation_id: str
    thread_id: str
    question: str
    data_source_id: str = "olist"
    status: AnalysisRunStatus = AnalysisRunStatus.queued
    current_step: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class DocumentType(StrEnum):
    metric_spec = "metric_spec"
    business_semantics = "business_semantics"
    generic = "generic"


class DocumentCreate(BaseModel):
    file_name: str
    file_size: str | None = None
    document_type: DocumentType = DocumentType.generic


class Document(BaseModel):
    id: str
    file_name: str
    file_size: str | None = None
    document_type: DocumentType
    status: str = "uploaded"
    created_at: datetime = Field(default_factory=utcnow)


class SemanticDraftKind(StrEnum):
    metric = "metric"
    dimension = "dimension"
    glossary = "glossary"
    business_rule = "business_rule"


class SemanticDraftStatus(StrEnum):
    pending = "pending"
    adopted = "adopted"
    rejected = "rejected"
    published = "published"


class SemanticDraftField(BaseModel):
    label: str
    value: str


class SemanticDraftUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    mapping_target: str | None = None
    fields: list[SemanticDraftField] | None = None


class SemanticDraftReview(BaseModel):
    conversation_id: str | None = None
    adopted_scope: str = "session"


class SemanticDraft(BaseModel):
    id: str
    document_id: str | None = None
    kind: SemanticDraftKind
    status: SemanticDraftStatus = SemanticDraftStatus.pending
    title: str
    description: str
    mapping_target: str
    confidence: float = 0.8
    source_document: str
    source_snippet: str
    fields: list[SemanticDraftField] = Field(default_factory=list)
    adopted_scope: str | None = None
    vector_status: str = "pending"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class VectorSyncMode(StrEnum):
    sync = "sync"
    async_ = "async"


class VectorJobStatus(StrEnum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class VectorSyncRequest(BaseModel):
    mode: VectorSyncMode = VectorSyncMode.sync


class VectorRebuildRequest(BaseModel):
    mode: VectorSyncMode = VectorSyncMode.async_
    asset_types: list[str] = Field(default_factory=list)


class VectorJob(BaseModel):
    id: str
    job_type: str
    asset_type: str | None = None
    asset_id: str | None = None
    status: VectorJobStatus = VectorJobStatus.pending
    retry_count: int = 0
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class VectorEmbeddingRecord(BaseModel):
    id: str
    asset_type: str
    asset_id: str
    asset_version: int = 1
    embedding_text: str
    embedding_vector: list[float]
    status: str = "active"
    updated_at: datetime = Field(default_factory=utcnow)
