-- ═══════════════════════════════════════════════════════════════════════
--  VoiceTrace AI — Vendor Ledger Schema Migration
--  Enhanced schema for street vendor business tracking
-- ═══════════════════════════════════════════════════════════════════════

-- ── Add language detection to transcriptions ──────────────────────────
ALTER TABLE public.transcriptions 
ADD COLUMN IF NOT EXISTS detected_language TEXT,
ADD COLUMN IF NOT EXISTS language_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS has_uncertainties BOOLEAN DEFAULT FALSE;

-- ── Table: ledger_entries ─────────────────────────────────────────────
-- Daily business summary for each vendor
CREATE TABLE IF NOT EXISTS public.ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    transcription_id UUID REFERENCES public.transcriptions(id) ON DELETE SET NULL,
    
    entry_date DATE NOT NULL,
    total_earnings DECIMAL(12,2) DEFAULT 0,
    total_expenses DECIMAL(12,2) DEFAULT 0,
    net_profit DECIMAL(12,2) GENERATED ALWAYS AS (total_earnings - total_expenses) STORED,
    
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, entry_date)
);

-- ── Table: ledger_items ───────────────────────────────────────────────
-- Individual items sold (line items)
CREATE TABLE IF NOT EXISTS public.ledger_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ledger_entry_id UUID NOT NULL REFERENCES public.ledger_entries(id) ON DELETE CASCADE,
    
    item_name TEXT NOT NULL,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(12,2),
    
    -- Confidence tracking
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    needs_confirmation BOOLEAN DEFAULT FALSE,
    is_confirmed BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Table: ledger_expenses ────────────────────────────────────────────
-- Individual expense items
CREATE TABLE IF NOT EXISTS public.ledger_expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ledger_entry_id UUID NOT NULL REFERENCES public.ledger_entries(id) ON DELETE CASCADE,
    
    expense_type TEXT NOT NULL, -- 'raw_material', 'transport', 'rent', 'utilities', 'other'
    description TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    
    -- Confidence tracking
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    needs_confirmation BOOLEAN DEFAULT FALSE,
    is_confirmed BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Table: vendor_patterns ────────────────────────────────────────────
-- Computed business patterns (updated daily/weekly)
CREATE TABLE IF NOT EXISTS public.vendor_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    pattern_type TEXT NOT NULL, -- 'best_seller', 'high_day', 'expense_trend', 'stockout'
    item_name TEXT,
    day_of_week INT, -- 0=Sunday, 6=Saturday
    metric_value DECIMAL(12,2),
    frequency INT,
    
    last_computed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, pattern_type, item_name, day_of_week)
);

-- ── Table: anomaly_alerts ─────────────────────────────────────────────
-- Unusual business activity alerts
CREATE TABLE IF NOT EXISTS public.anomaly_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ledger_entry_id UUID REFERENCES public.ledger_entries(id) ON DELETE CASCADE,
    
    alert_type TEXT NOT NULL, -- 'high_expense', 'low_earning', 'unusual_quantity', 'missing_entry'
    severity TEXT NOT NULL DEFAULT 'info', -- 'info', 'warning', 'critical'
    message TEXT NOT NULL,
    
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Table: stock_suggestions ──────────────────────────────────────────
-- Next-day stock recommendations
CREATE TABLE IF NOT EXISTS public.stock_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    item_name TEXT NOT NULL,
    suggested_quantity DECIMAL(10,2) NOT NULL,
    reasoning TEXT NOT NULL,
    confidence DECIMAL(3,2),
    
    suggestion_date DATE NOT NULL,
    is_applied BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, item_name, suggestion_date)
);

-- ── Table: audio_segments ─────────────────────────────────────────────
-- Audio fragments for playback verification
CREATE TABLE IF NOT EXISTS public.audio_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcription_id UUID NOT NULL REFERENCES public.transcriptions(id) ON DELETE CASCADE,
    
    segment_index INT NOT NULL,
    start_time DECIMAL(10,2) NOT NULL,
    end_time DECIMAL(10,2) NOT NULL,
    text TEXT NOT NULL,
    
    -- Link to extracted entity
    entity_type TEXT, -- 'item', 'expense', 'earning'
    entity_id UUID,
    
    audio_url TEXT, -- Supabase Storage URL (optional)
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════════════
--  Indexes for Performance
-- ═══════════════════════════════════════════════════════════════════════

-- Ledger entries
CREATE INDEX IF NOT EXISTS idx_ledger_entries_user_date 
    ON public.ledger_entries (user_id, entry_date DESC);

CREATE INDEX IF NOT EXISTS idx_ledger_entries_date 
    ON public.ledger_entries (entry_date DESC);

-- Ledger items
CREATE INDEX IF NOT EXISTS idx_ledger_items_entry 
    ON public.ledger_items (ledger_entry_id);

CREATE INDEX IF NOT EXISTS idx_ledger_items_name 
    ON public.ledger_items (item_name);

CREATE INDEX IF NOT EXISTS idx_ledger_items_confirmation 
    ON public.ledger_items (needs_confirmation) 
    WHERE needs_confirmation = TRUE;

-- Ledger expenses
CREATE INDEX IF NOT EXISTS idx_ledger_expenses_entry 
    ON public.ledger_expenses (ledger_entry_id);

CREATE INDEX IF NOT EXISTS idx_ledger_expenses_type 
    ON public.ledger_expenses (expense_type);

-- Patterns
CREATE INDEX IF NOT EXISTS idx_vendor_patterns_user 
    ON public.vendor_patterns (user_id, pattern_type);

-- Anomalies
CREATE INDEX IF NOT EXISTS idx_anomaly_alerts_user_unack 
    ON public.anomaly_alerts (user_id, is_acknowledged) 
    WHERE is_acknowledged = FALSE;

-- Stock suggestions
CREATE INDEX IF NOT EXISTS idx_stock_suggestions_user_date 
    ON public.stock_suggestions (user_id, suggestion_date DESC);

-- Audio segments
CREATE INDEX IF NOT EXISTS idx_audio_segments_transcription 
    ON public.audio_segments (transcription_id, segment_index);

-- ═══════════════════════════════════════════════════════════════════════
--  Row Level Security
-- ═══════════════════════════════════════════════════════════════════════

-- Ledger entries
ALTER TABLE public.ledger_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own ledger entries"
    ON public.ledger_entries FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own ledger entries"
    ON public.ledger_entries FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own ledger entries"
    ON public.ledger_entries FOR UPDATE
    USING (auth.uid() = user_id);

-- Ledger items
ALTER TABLE public.ledger_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own ledger items"
    ON public.ledger_items FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.ledger_entries 
        WHERE id = ledger_items.ledger_entry_id 
        AND user_id = auth.uid()
    ));

-- Ledger expenses
ALTER TABLE public.ledger_expenses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own ledger expenses"
    ON public.ledger_expenses FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.ledger_entries 
        WHERE id = ledger_expenses.ledger_entry_id 
        AND user_id = auth.uid()
    ));

-- Vendor patterns
ALTER TABLE public.vendor_patterns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own patterns"
    ON public.vendor_patterns FOR SELECT
    USING (auth.uid() = user_id);

-- Anomaly alerts
ALTER TABLE public.anomaly_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own alerts"
    ON public.anomaly_alerts FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own alerts"
    ON public.anomaly_alerts FOR UPDATE
    USING (auth.uid() = user_id);

-- Stock suggestions
ALTER TABLE public.stock_suggestions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own suggestions"
    ON public.stock_suggestions FOR SELECT
    USING (auth.uid() = user_id);

-- Audio segments
ALTER TABLE public.audio_segments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own audio segments"
    ON public.audio_segments FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.transcriptions 
        WHERE id = audio_segments.transcription_id 
        AND user_id = auth.uid()
    ));

-- ═══════════════════════════════════════════════════════════════════════
--  Functions & Triggers
-- ═══════════════════════════════════════════════════════════════════════

-- Update ledger_entries.updated_at on modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_ledger_entries_updated_at
    BEFORE UPDATE ON public.ledger_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-update ledger_entries totals when items/expenses change
CREATE OR REPLACE FUNCTION recalculate_ledger_totals()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.ledger_entries
    SET 
        total_earnings = COALESCE((
            SELECT SUM(total_amount) 
            FROM public.ledger_items 
            WHERE ledger_entry_id = COALESCE(NEW.ledger_entry_id, OLD.ledger_entry_id)
        ), 0),
        total_expenses = COALESCE((
            SELECT SUM(amount) 
            FROM public.ledger_expenses 
            WHERE ledger_entry_id = COALESCE(NEW.ledger_entry_id, OLD.ledger_entry_id)
        ), 0)
    WHERE id = COALESCE(NEW.ledger_entry_id, OLD.ledger_entry_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER recalc_totals_on_item_change
    AFTER INSERT OR UPDATE OR DELETE ON public.ledger_items
    FOR EACH ROW
    EXECUTE FUNCTION recalculate_ledger_totals();

CREATE TRIGGER recalc_totals_on_expense_change
    AFTER INSERT OR UPDATE OR DELETE ON public.ledger_expenses
    FOR EACH ROW
    EXECUTE FUNCTION recalculate_ledger_totals();
