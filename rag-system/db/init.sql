-- pgvector initialization
CREATE EXTENSION IF NOT EXISTS vector;

-- Application tables are created by SQLAlchemy on backend startup,
-- but the chunks table needs the vector type so it is defined here.
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_version_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    visibility_level INTEGER NOT NULL DEFAULT 1,
    filename TEXT,
    version INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_docver ON chunks(document_version_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks
    USING hnsw (embedding vector_cosine_ops);
