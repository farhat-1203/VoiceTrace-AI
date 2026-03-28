# VoiceTrace AI - Street Vendor Enhancement Plan

## Problem Statement
Build an AI system for 10M+ Indian street vendors to convert daily voice narrations (Hindi/English/Hinglish) into structured business records, patterns, and actionable insights.

## Current Architecture
- **Frontend**: Streamlit (demo) → Expo App (production)
- **Backend**: FastAPI + LangGraph pipeline
- **STT**: Groq Whisper API
- **LLM**: Groq LLaMA 3.1/3.3
- **Vector DB**: Qdrant Cloud (long-term memory)
- **Database**: Supabase (ledger, transcriptions, auth)
- **Voice Agent**: VAPI (for querying)

## Required Features

### ✅ Already Implemented
- Voice transcription (Groq Whisper)
- Entity extraction (earnings, expenses, items)
- Safety guardrails
- Memory importance classification
- Vector memory storage (Qdrant)
- User authentication (Supabase Auth)
- Multi-user support with RLS

### 🔨 To Implement

#### 1. Language Detection
- Add `detected_language` field to transcriptions
- Support: Hindi, English, Hinglish (code-mixed)
- Store in DB for analytics

#### 2. Enhanced Ledger System
- Daily ledger entries with line items
- Weekly/monthly aggregations
- Item-level tracking (quantity, price, profit margin)
- Vendor-specific inventory patterns

#### 3. Confidence Flags
- Mark uncertain extractions (e.g., "sold some bananas")
- Store confidence scores per field
- Prompt for clarification on next session

#### 4. Pattern Detection (4+ days)
- Best-selling items
- High-earning days (day-of-week analysis)
- Expense trends
- Stock-out patterns

#### 5. Anomaly Alerts
- Earnings/expenses outside normal range
- Unusual item quantities
- Missing expected entries

#### 6. Next-Day Stock Suggestions
- Based on sell-through rates
- Consider stock-out mentions
- Simple one-line suggestions with reasoning

#### 7. Income Statement Export
- Weekly/monthly PDF generation
- Plain language, bank-ready format
- Include: total earnings, expenses, net profit, item breakdown

#### 8. Voice Playback with Highlights
- Store audio segments with timestamps
- Link extracted entities to audio fragments
- Allow playback verification

#### 9. VAPI Integration
- Query endpoints for voice agent
- Natural language queries to ledger
- Recent transaction retrieval
- Vendor-specific insights

## Database Schema Changes

### New Tables

```sql
-- Daily ledger entries
CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    transcription_id UUID REFERENCES transcriptions(id),
    entry_date DATE NOT NULL,
    total_earnings DECIMAL(10,2),
    total_expenses DECIMAL(10,2),
    net_profit DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Line items (sold items)
CREATE TABLE ledger_items (
    id UUID PRIMARY KEY,
    ledger_entry_id UUID REFERENCES ledger_entries(id),
    item_name TEXT NOT NULL,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    needs_confirmation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Expense items
CREATE TABLE ledger_expenses (
    id UUID PRIMARY KEY,
    ledger_entry_id UUID REFERENCES ledger_entries(id),
    expense_type TEXT, -- 'raw_material', 'transport', 'rent', 'other'
    description TEXT,
    amount DECIMAL(10,2),
    confidence_score DECIMAL(3,2),
    needs_confirmation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pattern insights (computed daily)
CREATE TABLE vendor_patterns (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    pattern_type TEXT, -- 'best_seller', 'high_day', 'expense_trend'
    item_name TEXT,
    metric_value DECIMAL(10,2),
    frequency INT,
    last_computed TIMESTAMPTZ DEFAULT NOW()
);

-- Anomaly alerts
CREATE TABLE anomaly_alerts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    ledger_entry_id UUID REFERENCES ledger_entries(id),
    alert_type TEXT, -- 'high_expense', 'low_earning', 'unusual_quantity'
    message TEXT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audio segments (for playback)
CREATE TABLE audio_segments (
    id UUID PRIMARY KEY,
    transcription_id UUID REFERENCES transcriptions(id),
    segment_index INT,
    start_time DECIMAL(10,2),
    end_time DECIMAL(10,2),
    text TEXT,
    audio_url TEXT, -- S3/Supabase Storage URL
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Modified Tables

```sql
-- Add to transcriptions table
ALTER TABLE transcriptions ADD COLUMN detected_language TEXT;
ALTER TABLE transcriptions ADD COLUMN language_confidence DECIMAL(3,2);
ALTER TABLE transcriptions ADD COLUMN has_uncertainties BOOLEAN DEFAULT FALSE;
```

## API Endpoints to Add

### Ledger Management
- `POST /ledger/entry` - Create/update daily entry
- `GET /ledger/entries` - Get entries (date range)
- `GET /ledger/summary` - Weekly/monthly summary
- `GET /ledger/items/{item_name}` - Item history
- `POST /ledger/confirm` - Confirm uncertain entries

### Pattern & Insights
- `GET /patterns/best-sellers` - Top selling items
- `GET /patterns/high-days` - Best performing days
- `GET /patterns/expense-trends` - Expense analysis
- `GET /anomalies` - Recent alerts

### Stock Suggestions
- `GET /suggestions/next-day` - Tomorrow's stock recommendations

### Export
- `GET /export/income-statement` - PDF generation (weekly/monthly)

### VAPI Integration
- `POST /vapi/query` - Natural language query endpoint
- `GET /vapi/recent-transactions` - Last N transactions
- `GET /vapi/vendor-summary` - Quick stats for voice response

## Implementation Priority

### Phase 1 (Immediate)
1. Fix OAuth issue
2. Add language detection
3. Create new database schema
4. Implement ledger entry creation

### Phase 2 (Core Features)
5. Confidence flags and uncertainty tracking
6. Pattern detection (4+ days logic)
7. Anomaly detection
8. Stock suggestions

### Phase 3 (Advanced)
9. PDF export generation
10. Audio segment storage and playback
11. VAPI integration endpoints

### Phase 4 (Expo App)
12. Migrate frontend to Expo
13. Voice recording in mobile app
14. Push notifications for anomalies
15. Offline support

## Next Steps
1. Fix OAuth authentication
2. Update database schema
3. Enhance transcription service with language detection
4. Implement ledger system
5. Build pattern detection engine
6. Create VAPI query endpoints
