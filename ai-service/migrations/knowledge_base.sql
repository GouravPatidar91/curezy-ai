-- migrations/knowledge_base.sql
-- Run this in your Supabase SQL Editor

-- 1. Enable the vector extension if not already done
create extension if not exists vector;

-- 2. Create the knowledge base table
create table if not exists medical_knowledge_base (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  content text not null,
  source text not null,          -- e.g., 'PubMed', 'AIIMS', 'WHO'
  disease_category text,         -- e.g., 'Infectious', 'Cardiology'
  metadata jsonb default '{}',   -- URL, date published, authors, etc.
  embedding vector(384) not null, -- using all-MiniLM-L6-v2 (384 dims)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Create HNSW index for ultra-fast vector search (pgvector 0.5.0+)
create index if not exists medical_knowledge_base_embedding_idx 
on medical_knowledge_base 
using hnsw (embedding vector_cosine_ops)
with (m = 16, ef_construction = 64);

-- 4. Create the match RPC function
create or replace function match_medical_knowledge (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  title text,
  content text,
  source text,
  disease_category text,
  similarity float
)
language sql stable
as $$
  select
    medical_knowledge_base.id,
    medical_knowledge_base.title,
    medical_knowledge_base.content,
    medical_knowledge_base.source,
    medical_knowledge_base.disease_category,
    1 - (medical_knowledge_base.embedding <=> query_embedding) as similarity
  from medical_knowledge_base
  where 1 - (medical_knowledge_base.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
