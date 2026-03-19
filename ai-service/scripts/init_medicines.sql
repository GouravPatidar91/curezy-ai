-- Run this file in your Supabase SQL Editor
-- It creates the medicines table and enables the vector extension for RAG.

-- 1. Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the medicines table matching the CSV columns
CREATE TABLE public.medicines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    csv_id INTEGER,
    name TEXT NOT NULL,
    price DECIMAL,
    is_discontinued BOOLEAN,
    manufacturer_name TEXT,
    type TEXT,
    pack_size_label TEXT,
    short_composition1 TEXT,
    short_composition2 TEXT,
    substitute0 TEXT,
    substitute1 TEXT,
    substitute2 TEXT,
    substitute3 TEXT,
    substitute4 TEXT,
    consolidate_use0 TEXT,
    use1 TEXT,
    use2 TEXT,
    use3 TEXT,
    use4 TEXT,
    chemical_class TEXT,
    habit_forming BOOLEAN,
    therapeutic_action_class TEXT,
    
    -- The text string we will embed (e.g. "Consolidate use0: Treatment of Bacterial... | Comp: Amoxycillin")
    search_text TEXT, 
    
    -- We use sentence-transformers/all-MiniLM-L6-v2, which has 384 dimensions
    use_embedding vector(384)
);

-- 3. Create a vector index for lightning fast similarity search
-- Adjust the lists parameter depending on total rows (100 is good for ~50k rows)
CREATE INDEX IF NOT EXISTS medicines_embedding_idx 
    ON public.medicines 
    USING ivfflat (use_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Enable Row Level Security (RLS)
ALTER TABLE public.medicines ENABLE ROW LEVEL SECURITY;

-- Allow public read access (the AI needs to query this table)
CREATE POLICY "Allow public read access to medicines" 
    ON public.medicines
    FOR SELECT
    USING (true);

-- Allow public insert access (since the ingestion script uses anon key)
CREATE POLICY "Allow public insert to medicines" 
    ON public.medicines
    FOR INSERT
    WITH CHECK (true);
