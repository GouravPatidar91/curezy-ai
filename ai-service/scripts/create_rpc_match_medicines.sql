-- Supabase RPC Function for Medicine Vector Search
-- Run this in your Supabase SQL Editor

CREATE OR REPLACE FUNCTION match_medicines (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  name text,
  short_composition1 text,
  price decimal,
  substitute0 text,
  substitute1 text,
  is_discontinued boolean,
  habit_forming boolean,
  therapeutic_action_class text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id,
    name,
    short_composition1,
    price,
    substitute0,
    substitute1,
    is_discontinued,
    habit_forming,
    therapeutic_action_class,
    1 - (use_embedding <=> query_embedding) AS similarity
  FROM public.medicines
  WHERE 
    is_discontinued = false 
    AND habit_forming = false
    -- Keep only results that actually match the vector closely
    AND 1 - (use_embedding <=> query_embedding) > match_threshold
  ORDER BY use_embedding <=> query_embedding
  LIMIT match_count;
$$;
