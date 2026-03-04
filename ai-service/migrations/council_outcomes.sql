-- ─────────────────────────────────────────────────────────────────────────────
-- Curezy AI Council — Supabase Migration
-- Run this in Supabase SQL editor (Dashboard → SQL Editor → New Query)
-- Phase 2.1: council_outcomes  (every analysis stored)
-- Phase 2.4: case_library      (curated high-quality cases for few-shot)
-- Phase 3.1: prompt_versions   (prompt evolutionary optimization history)
-- Phase 3.3: knowledge_proposals (auto-discovered knowledge gaps)
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable UUID extension (already enabled in most Supabase projects)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE 1: council_outcomes
-- Every analysis is stored here immediately after completion.
-- Feedback fields are populated later via /feedback/submit endpoint.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS council_outcomes (
  id                    UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  patient_id            UUID        NOT NULL,
  session_id            TEXT,

  -- Analysis outputs
  top_diagnosis         TEXT,
  top_diagnosis_prob    FLOAT,
  all_conditions        JSONB,       -- full top_3_conditions array
  council_votes         JSONB,       -- {doctor_name: top_condition}
  consensus_confidence  FLOAT,
  agreement_score       FLOAT,
  agents_agreed         BOOLEAN,
  execution_time_s      FLOAT,
  safety_flags          TEXT[],
  doctor_review_req     BOOLEAN,
  reasoning_summary     TEXT,
  missing_data          TEXT[],

  -- Q-Score breakdown (from quality_scorer.py)
  q_score               FLOAT,
  q_agreement           FLOAT,
  q_confidence          FLOAT,
  q_evidence            FLOAT,
  q_probability         FLOAT,
  q_rule_alignment      FLOAT,
  q_grade               CHAR(1),

  -- Prompt tracking (for OPRO optimization)
  prompt_version        TEXT        DEFAULT 'v1.0',

  -- System metadata
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  llm_models_used       TEXT[],

  -- Feedback fields (populated by /feedback/submit after analysis)
  user_rating           SMALLINT    CHECK (user_rating BETWEEN 1 AND 5),
  doctor_verified       BOOLEAN     DEFAULT FALSE,
  actual_diagnosis      TEXT,
  feedback_notes        TEXT,
  feedback_timestamp    TIMESTAMPTZ
);

-- Index for pattern analysis
CREATE INDEX IF NOT EXISTS idx_outcomes_patient    ON council_outcomes (patient_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_created    ON council_outcomes (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_outcomes_q_score    ON council_outcomes (q_score DESC);
CREATE INDEX IF NOT EXISTS idx_outcomes_top_diag   ON council_outcomes (top_diagnosis);
CREATE INDEX IF NOT EXISTS idx_outcomes_prompt_ver ON council_outcomes (prompt_version);


-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE 2: case_library
-- Curated high-quality cases promoted from council_outcomes.
-- Used as dynamic few-shot examples in Phase 3.2.
-- Promotion criteria: q_score >= 85 OR user_rating = 5 OR doctor_verified = true
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS case_library (
  id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  outcome_id        UUID        REFERENCES council_outcomes(id),

  -- Anonymized clinical content
  soap_note         TEXT        NOT NULL,
  symptoms          TEXT[]      NOT NULL,
  top_condition     TEXT        NOT NULL,
  probability       FLOAT,
  evidence          TEXT[]      NOT NULL,
  reasoning         TEXT        NOT NULL,
  reasoning_summary TEXT,

  -- Classification for few-shot retrieval
  specialty         TEXT,       -- cardiology | neurology | respiratory | etc.
  urgency           TEXT,       -- EMERGENCY | URGENT | routine
  duration_class    TEXT,       -- acute | subacute | chronic
  onset_type        TEXT,       -- SUDDEN | Acute | Gradual

  -- Quality metadata
  quality_source    TEXT        NOT NULL, -- 'auto_qscore' | 'user_5star' | 'doctor_verified'
  q_score           FLOAT,
  user_rating       SMALLINT,

  created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_library_specialty  ON case_library (specialty);
CREATE INDEX IF NOT EXISTS idx_library_condition  ON case_library (top_condition);
CREATE INDEX IF NOT EXISTS idx_library_urgency    ON case_library (urgency);


-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE 3: prompt_versions
-- Tracks every version of the diagnosis prompt for OPRO optimization.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prompt_versions (
  id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  version           TEXT        NOT NULL UNIQUE,  -- e.g. 'v1.0', 'v1.3'
  prompt_text       TEXT        NOT NULL,
  avg_q_score       FLOAT,
  sample_size       INT         DEFAULT 0,
  is_active         BOOLEAN     DEFAULT FALSE,
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  activated_at      TIMESTAMPTZ,
  notes             TEXT
);

-- Seed the initial version
INSERT INTO prompt_versions (version, prompt_text, is_active, notes)
VALUES ('v1.0', 'Initial few-shot CoT prompt — no schema template', TRUE, 'Baseline prompt after Phase 1 upgrade')
ON CONFLICT (version) DO NOTHING;


-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE 4: knowledge_proposals
-- Auto-discovered knowledge gaps from council analysis patterns.
-- Reviewed by admin before merging into symptom_map.py.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_proposals (
  id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  symptom_cluster     TEXT[]      NOT NULL,   -- triggering symptoms
  proposed_condition  TEXT        NOT NULL,
  probability         FLOAT,
  occurrence_count    INT         DEFAULT 1,
  avg_confidence      FLOAT,
  source_case_ids     UUID[],
  status              TEXT        DEFAULT 'pending',  -- pending | approved | rejected
  reviewed_at         TIMESTAMPTZ,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);


-- ─────────────────────────────────────────────────────────────────────────────
-- ROW LEVEL SECURITY
-- Enable basic RLS so patient data is protected.
-- Service role key (backend) bypasses RLS automatically.
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE council_outcomes   ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_library       ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_versions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_proposals ENABLE ROW LEVEL SECURITY;

-- Only the service role (backend) can read/write council_outcomes
CREATE POLICY "service_role_only_outcomes"
  ON council_outcomes FOR ALL TO service_role USING (true);

-- Only the service role can read/write case_library
CREATE POLICY "service_role_only_library"
  ON case_library FOR ALL TO service_role USING (true);

-- prompt_versions readable by authenticated users (for admin dashboard later)
CREATE POLICY "authenticated_read_prompts"
  ON prompt_versions FOR SELECT TO authenticated USING (true);
CREATE POLICY "service_role_write_prompts"
  ON prompt_versions FOR ALL TO service_role USING (true);
