-- Phase 3 business API schema.
-- The FastAPI repository runs this file with CREATE IF NOT EXISTS at startup.

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS semantic;
CREATE SCHEMA IF NOT EXISTS corpus;
CREATE SCHEMA IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS app.conversations (
    id text PRIMARY KEY,
    thread_id text NOT NULL UNIQUE,
    title text NOT NULL,
    data_source_id text NOT NULL DEFAULT 'olist',
    status text NOT NULL DEFAULT 'idle',
    last_message_preview text,
    adopted_semantic_draft_ids text[] NOT NULL DEFAULT '{}',
    adopted_semantic_draft_titles text[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.messages (
    id text PRIMARY KEY,
    conversation_id text NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
    run_id text,
    role text NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.analysis_runs (
    id text PRIMARY KEY,
    conversation_id text NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
    thread_id text NOT NULL,
    question text NOT NULL,
    data_source_id text NOT NULL DEFAULT 'olist',
    status text NOT NULL DEFAULT 'queued',
    current_step text,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.conversation_semantic_assets (
    id text PRIMARY KEY,
    conversation_id text NOT NULL REFERENCES app.conversations(id) ON DELETE CASCADE,
    draft_id text NOT NULL,
    asset_type text NOT NULL,
    asset_snapshot jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_conversation_semantic_assets_conversation_draft'
    ) THEN
        ALTER TABLE app.conversation_semantic_assets
        ADD CONSTRAINT uq_conversation_semantic_assets_conversation_draft
        UNIQUE (conversation_id, draft_id);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS corpus.documents (
    id text PRIMARY KEY,
    file_name text NOT NULL,
    file_size text,
    document_type text NOT NULL,
    status text NOT NULL DEFAULT 'uploaded',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS semantic.semantic_drafts (
    id text PRIMARY KEY,
    document_id text REFERENCES corpus.documents(id) ON DELETE SET NULL,
    kind text NOT NULL,
    status text NOT NULL DEFAULT 'pending',
    title text NOT NULL,
    description text NOT NULL,
    mapping_target text NOT NULL,
    confidence numeric(5, 4) NOT NULL DEFAULT 0.8,
    source_document text NOT NULL,
    source_snippet text NOT NULL,
    fields jsonb NOT NULL DEFAULT '[]',
    adopted_scope text,
    vector_status text NOT NULL DEFAULT 'pending',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vector.semantic_asset_embeddings (
    id text PRIMARY KEY,
    tenant_id text NOT NULL DEFAULT 'default',
    asset_type text NOT NULL,
    asset_id text NOT NULL,
    asset_version integer NOT NULL DEFAULT 1,
    embedding_text text NOT NULL,
    embedding_vector double precision[] NOT NULL,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, asset_type, asset_id, asset_version)
);

CREATE TABLE IF NOT EXISTS vector.user_memory_embeddings (
    id text PRIMARY KEY,
    tenant_id text NOT NULL DEFAULT 'default',
    user_id text NOT NULL,
    memory_id text NOT NULL,
    memory_type text NOT NULL,
    embedding_text text NOT NULL,
    embedding_vector double precision[] NOT NULL,
    importance numeric(4, 3) NOT NULL DEFAULT 0.5,
    expires_at timestamptz,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS vector.embedding_jobs (
    id text PRIMARY KEY,
    job_type text NOT NULL,
    asset_type text,
    asset_id text,
    status text NOT NULL DEFAULT 'pending',
    retry_count integer NOT NULL DEFAULT 0,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_app_messages_conversation_id
    ON app.messages(conversation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_semantic_drafts_status
    ON semantic.semantic_drafts(status, kind);

CREATE INDEX IF NOT EXISTS idx_vector_asset_embeddings_asset
    ON vector.semantic_asset_embeddings(asset_type, asset_id, status);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_jobs_status
    ON vector.embedding_jobs(status, created_at);
