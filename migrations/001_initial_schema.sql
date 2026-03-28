-- ═══════════════════════════════════════════════════════════════════════
--  VoiceTrace AI — Supabase Initial Schema Migration
--  Run this in: Supabase Dashboard → SQL Editor → New Query → Run
-- ═══════════════════════════════════════════════════════════════════════

-- ── Table: transcriptions ─────────────────────────────────────────────
-- Stores every pipeline run. Linked directly to Supabase's built-in
-- auth.users table so each row belongs to the authenticated user.

CREATE TABLE IF NOT EXISTS public.transcriptions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Auth link — references the built-in Supabase auth table
    user_id               UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Pipeline inputs
    audio_filename        TEXT,
    audio_duration_secs   REAL,

    -- Transcription stage
    transcript            TEXT NOT NULL DEFAULT '',
    sanitized_transcript  TEXT,

    -- Safety stage
    is_safe               BOOLEAN DEFAULT TRUE,
    safety_response       TEXT,
    safety_flag           TEXT DEFAULT 'safe',

    -- Extraction stage (stored as JSONB for flexible querying)
    extracted_data        JSONB DEFAULT '{}'::JSONB,

    -- Memory stage
    is_important          BOOLEAN DEFAULT FALSE,
    formatted_memory      TEXT,

    -- Retrieval stage
    retrieved_memories    JSONB DEFAULT '[]'::JSONB,

    -- Final response
    final_response        TEXT DEFAULT '',

    -- Error (null if success)
    error                 TEXT,

    -- Performance
    processing_time_secs  REAL,

    -- Timestamps
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Indexes ───────────────────────────────────────────────────────────
-- Allow fast lookup of all transcriptions for a given user, sorted newest first
CREATE INDEX IF NOT EXISTS idx_transcriptions_user_id_created
    ON public.transcriptions (user_id, created_at DESC);

-- Allow fast lookup of important memories per user (used for RAG context retrieval)
CREATE INDEX IF NOT EXISTS idx_transcriptions_important
    ON public.transcriptions (user_id, is_important)
    WHERE is_important = TRUE;

-- Allow full-text search on the transcript column
CREATE INDEX IF NOT EXISTS idx_transcriptions_transcript_fts
    ON public.transcriptions USING GIN (to_tsvector('english', transcript));

-- ── Row Level Security ────────────────────────────────────────────────
-- Ensure users can ONLY see their own transcriptions via the client SDK.
-- The backend uses the service_role key which BYPASSES RLS, so inserts
-- from FastAPI will always succeed.
ALTER TABLE public.transcriptions ENABLE ROW LEVEL SECURITY;

-- Policy: a logged-in user can only SELECT their own rows
CREATE POLICY "Users can read own transcriptions"
    ON public.transcriptions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: a logged-in user can only INSERT rows for themselves
CREATE POLICY "Users can insert own transcriptions"
    ON public.transcriptions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ── Realtime ──────────────────────────────────────────────────────────
-- Optional: enable realtime updates so the frontend can live-update
ALTER PUBLICATION supabase_realtime ADD TABLE public.transcriptions;
