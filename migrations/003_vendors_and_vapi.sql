-- ═══════════════════════════════════════════════════════════════════════
--  VoiceTrace AI — Vendors & VAPI Integration Schema
--  Adds vendor profiles, clarifications, and VAPI call tracking
-- ═══════════════════════════════════════════════════════════════════════

-- ── Table: vendors ────────────────────────────────────────────────────
-- Vendor profiles (extends auth.users with business info)
CREATE TABLE IF NOT EXISTS public.vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    
    phone TEXT UNIQUE,
    name TEXT,
    business_type TEXT DEFAULT 'general',
    city TEXT DEFAULT 'Mumbai',
    
    -- VAPI/ElevenLabs voice configuration
    elevenlabs_voice_id TEXT DEFAULT 'pNInz6obpgDQGcFmaJgB',
    vapi_assistant_id TEXT,
    
    -- Business metadata
    preferred_language TEXT DEFAULT 'hinglish',  -- 'hindi', 'english', 'hinglish'
    average_daily_revenue DECIMAL(12,2),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Table: pending_clarifications ─────────────────────────────────────
-- Track uncertain extractions that need vendor confirmation
CREATE TABLE IF NOT EXISTS public.pending_clarifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ledger_entry_id UUID REFERENCES public.ledger_entries(id) ON DELETE CASCADE,
    
    field_name TEXT NOT NULL,  -- 'quantity', 'price', 'amount'
    item_name TEXT,
    extracted_value NUMERIC,
    
    -- Questions in Hindi for VAPI to ask
    question_hindi TEXT NOT NULL,
    question_english TEXT,
    question_type TEXT NOT NULL,  -- 'number', 'yesno', 'choice'
    
    -- Resolution
    resolved BOOLEAN DEFAULT FALSE,
    resolved_value NUMERIC,
    resolved_at TIMESTAMPTZ,
    resolved_via TEXT,  -- 'vapi', 'manual', 'auto'
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Table: vapi_calls ─────────────────────────────────────────────────
-- Log all VAPI voice agent calls
CREATE TABLE IF NOT EXISTS public.vapi_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ledger_entry_id UUID REFERENCES public.ledger_entries(id) ON DELETE SET NULL,
    
    vapi_call_id TEXT UNIQUE,
    vapi_assistant_id TEXT,
    
    trigger_reason TEXT NOT NULL,  -- 'anomaly', 'mood', 'clarification', 'manual'
    trigger_metadata JSONB,
    
    call_status TEXT,  -- 'initiated', 'ringing', 'in-progress', 'ended', 'failed'
    call_transcript TEXT,
    call_summary TEXT,
    
    duration_seconds INTEGER,
    cost_usd DECIMAL(10,4),
    
    -- Outcomes
    resolved_anomaly BOOLEAN DEFAULT FALSE,
    resolved_clarifications INT DEFAULT 0,
    extracted_new_data JSONB,
    
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════
--  Indexes
-- ═══════════════════════════════════════════════════════════════════════

-- Vendors
CREATE INDEX IF NOT EXISTS idx_vendors_user_id 
    ON public.vendors (user_id);

CREATE INDEX IF NOT EXISTS idx_vendors_phone 
    ON public.vendors (phone);

-- Pending clarifications
CREATE INDEX IF NOT EXISTS idx_pending_clarifications_user 
    ON public.pending_clarifications (user_id, resolved);

CREATE INDEX IF NOT EXISTS idx_pending_clarifications_ledger 
    ON public.pending_clarifications (ledger_entry_id);

-- VAPI calls
CREATE INDEX IF NOT EXISTS idx_vapi_calls_user 
    ON public.vapi_calls (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vapi_calls_vapi_id 
    ON public.vapi_calls (vapi_call_id);

CREATE INDEX IF NOT EXISTS idx_vapi_calls_trigger 
    ON public.vapi_calls (trigger_reason, call_status);

-- ═══════════════════════════════════════════════════════════════════════
--  Row Level Security
-- ═══════════════════════════════════════════════════════════════════════

-- Vendors
ALTER TABLE public.vendors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own vendor profile"
    ON public.vendors FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own vendor profile"
    ON public.vendors FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own vendor profile"
    ON public.vendors FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Pending clarifications
ALTER TABLE public.pending_clarifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own clarifications"
    ON public.pending_clarifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own clarifications"
    ON public.pending_clarifications FOR UPDATE
    USING (auth.uid() = user_id);

-- VAPI calls
ALTER TABLE public.vapi_calls ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own vapi calls"
    ON public.vapi_calls FOR SELECT
    USING (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════════════════
--  Functions & Triggers
-- ═══════════════════════════════════════════════════════════════════════

-- Update vendors.updated_at on modification
CREATE TRIGGER update_vendors_updated_at
    BEFORE UPDATE ON public.vendors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-create vendor profile when user signs up
CREATE OR REPLACE FUNCTION create_vendor_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.vendors (user_id, name, phone)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
        NEW.phone
    )
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION create_vendor_profile();

-- ═══════════════════════════════════════════════════════════════════════
--  Sample Data (Optional - for testing)
-- ═══════════════════════════════════════════════════════════════════════

-- Uncomment to insert test vendor
-- INSERT INTO public.vendors (user_id, name, phone, business_type, city)
-- VALUES (
--     'your-test-user-uuid',
--     'Rajesh Kumar',
--     '+919876543210',
--     'fruit_cart',
--     'Mumbai'
-- );
