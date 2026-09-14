-- AskDuka initial database schema
-- Owner: Member 2 - Ingestion Pipeline + Database

CREATE EXTENSION IF NOT EXISTS vector;

-- Businesses
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Uploaded documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    business_id UUID NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_documents_business
        FOREIGN KEY (business_id)
        REFERENCES businesses(id)
        ON DELETE CASCADE
);

-- Individual pieces of documents
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(384),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_chunks_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE,

    CONSTRAINT unique_document_chunk
        UNIQUE (document_id, chunk_index)
);

-- Useful index for document lookups
CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx
    ON document_chunks(document_id);

-- Vector similarity index
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
