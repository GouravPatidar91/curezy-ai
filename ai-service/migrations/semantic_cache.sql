-- ─────────────────────────────────────────────────────────────────────────────
-- Curezy AI Council — Supabase Migration
-- Phase 3: Semantic Cache (pgvector)
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the semantic cache table
CREATE TABLE IF NOT EXISTS semantic_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text_rep TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    clinical_analysis JSONB NOT NULL,
    confidence_report JSONB NOT NULL,
    data_gaps JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for HNSW inner product (lightning-fast similarity search)
CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding ON semantic_cache USING hnsw (embedding vector_ip_ops);

-- RPC function for vector similarity search
CREATE OR REPLACE FUNCTION match_semantic_cache (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  clinical_analysis jsonb,
  confidence_report jsonb,
  data_gaps jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.clinical_analysis,
    c.confidence_report,
    c.data_gaps,
    (c.embedding <#> query_embedding) * -1 AS similarity
  FROM semantic_cache c
  WHERE (c.embedding <#> query_embedding) * -1 >= match_threshold
  ORDER BY c.embedding <#> query_embedding
  LIMIT match_count;
END;
$$;

-- RLS Policies
ALTER TABLE semantic_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_only_semantic_cache"
  ON semantic_cache FOR ALL TO service_role USING (true);
