
ALTER TABLE public.transcriptions 
ADD COLUMN IF NOT EXISTS audio_url TEXT,
ADD COLUMN IF NOT EXISTS audio_storage_path TEXT;

COMMENT ON COLUMN public.transcriptions.audio_url IS 'S3 presigned URL for audio playback (expires after 7 days)';
COMMENT ON COLUMN public.transcriptions.audio_storage_path IS 'S3 storage path (user_id/session_id.ext) for regenerating presigned URLs';

ALTER TABLE public.ledger_entries 
ADD COLUMN IF NOT EXISTS audio_url TEXT,
ADD COLUMN IF NOT EXISTS audio_storage_path TEXT;

COMMENT ON COLUMN public.ledger_entries.audio_url IS 'S3 presigned URL for audio playback (expires after 7 days)';
COMMENT ON COLUMN public.ledger_entries.audio_storage_path IS 'S3 storage path for regenerating presigned URLs';

COMMENT ON COLUMN public.audio_segments.audio_url IS 'S3 presigned URL for full audio (expires after 7 days)';

CREATE INDEX IF NOT EXISTS idx_transcriptions_audio_storage_path
    ON public.transcriptions (audio_storage_path)
    WHERE audio_storage_path IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ledger_entries_audio_storage_path
    ON public.ledger_entries (audio_storage_path)
    WHERE audio_storage_path IS NOT NULL;

