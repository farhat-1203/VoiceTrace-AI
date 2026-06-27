<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:7c3aed,50:db2777,100:f59e0b&height=220&section=header&text=VoiceTrace%20AI&fontSize=64&fontColor=ffffff&fontAlignY=40&desc=Hindi%20%2F%20Hinglish%20Voice%20Intelligence%20for%20Street%20Vendor%20Business%20Ledgers&descAlignY=60&descColor=e2e8f0" />

</div>

<div align="center">

[![Pipeline](https://img.shields.io/badge/Pipeline-LangGraph%20Agentic%20%7C%209%20Nodes-7c3aed?style=for-the-badge)](.)
[![Voice](https://img.shields.io/badge/Voice-VAPI%20%7C%20ElevenLabs%20%7C%20Groq%20STT-db2777?style=for-the-badge)](.)
[![Memory](https://img.shields.io/badge/Memory-Qdrant%20Vector%20%7C%20multilingual--e5--small-f59e0b?style=for-the-badge)](.)
[![Language](https://img.shields.io/badge/Language-Hindi%20%7C%20Hinglish%20%7C%20English-10b981?style=for-the-badge)](.)
[![Hackathon](https://img.shields.io/badge/Built%20in-24%20Hours%20%7C%20Hackathon%20MVP-ef4444?style=for-the-badge)](.)
[![License](https://img.shields.io/badge/License-MIT-64748b?style=for-the-badge)](LICENSE)

</div>

---

## The Problem

Street vendors in India — fruit sellers, vegetable vendors, chai stall owners — run businesses generating ₹500 to ₹5000 daily but have no digital financial record. They can't read spreadsheets, don't have time to type entries, and most bookkeeping apps assume literacy in English and comfort with UI. The result: no historical data, no pattern awareness, no ability to optimize stock, and no way to access credit because there's no financial trail to show.

**VoiceTrace AI lets a vendor speak naturally in Hindi or Hinglish for 3 minutes at the end of their day — and the system handles everything else.**

It transcribes, understands, extracts structured financial data, stores memory, detects anomalies, suggests tomorrow's stock, and when clarification is needed, sends a voice agent named **Arjun** to ask follow-up questions in conversational Hindi. No typing. No English. No interface to learn.

---

## System Architecture

```
╔═══════════════════════════════════════════════════════════════════════╗
║                     VENDOR INPUT LAYER                                ║
║  Expo Mobile App (React Native)                                       ║
║  └── Record 3-min audio → POST /process                              ║
╚═══════════════════════════════════════════════════════════════════════╝
                              │
                    Audio file (wav/mp3/m4a)
                              │
╔═══════════════════════════════════════════════════════════════════════╗
║                  LANGGRAPH PIPELINE (9 Nodes)                        ║
║                                                                       ║
║  [1] TRANSCRIBE ──── Groq Whisper (whisper-large-v3)                 ║
║         │            Hindi/Hinglish/English detection                 ║
║         ▼                                                             ║
║  [2] GUARDRAIL ───── LLM safety classification                       ║
║         │            PII detection → STOP if unsafe                  ║
║         ▼                                                             ║
║  [3] SANITIZE ────── Mask phone/address/name                        ║
║         │            [PHONE] [ADDRESS] [NAME] substitution           ║
║         ▼                                                             ║
║  [4] EXTRACT ─────── Groq LLM (llama-3.1-8b-instant)               ║
║         │            items_sold, expenses, sentiment, mood_score      ║
║         ▼                                                             ║
║  [5] MEMORY ANALYSIS → is_important? (0-1 score)                    ║
║         │                                                             ║
║    ┌────┴────┐                                                        ║
║    │         │                                                        ║
║  [6a]      [6b]                                                       ║
║  LONG-TERM  SKIP                                                      ║
║  MEMORY     │                                                         ║
║  Qdrant     │                                                         ║
║  384-dim    │                                                         ║
║  embeddings │                                                         ║
║    │         │                                                        ║
║    └────┬────┘                                                        ║
║         ▼                                                             ║
║  [7] RETRIEVAL ───── Top-3 similar past sessions from Qdrant         ║
║         │                                                             ║
║         ▼                                                             ║
║  [8] DECISION ────── Groq LLM (llama-3.3-70b-versatile)             ║
║         │            Summary + insights + recommendations             ║
║         ▼                                                             ║
║  [9] POST-PROCESS                                                     ║
║      ├── S3 audio upload                                              ║
║      ├── Supabase transcription store                                 ║
║      ├── Ledger entry creation                                        ║
║      └── VAPI trigger check                                           ║
╚═══════════════════════════════════════════════════════════════════════╝
                              │
              ┌───────────────┴───────────────┐
              │                               │
╔═════════════▼══════════╗     ╔═════════════▼══════════╗
║    STORAGE LAYER        ║     ║    VAPI VOICE AGENT     ║
║  Supabase (PostgreSQL)  ║     ║  Arjun — Hindi Agent    ║
║  ├── transcriptions     ║     ║  ElevenLabs TTS         ║
║  ├── ledger_entries     ║     ║  Deepgram STT (Hindi)   ║
║  ├── audio_segments     ║     ║  Groq LLM reasoning     ║
║  └── vapi_analytics     ║     ║  10 Backend Functions   ║
║                         ║     ║  Polygon Webhook         ║
║  Qdrant Cloud           ║     ╚════════════════════════╝
║  └── long_term_memory   ║
║      (384-dim vectors)  ║
║                         ║
║  AWS S3                 ║
║  └── audio files        ║
╚═════════════════════════╝
```

---

## The 9-Stage LangGraph Pipeline

### Node 1 — Transcribe
**Model:** Groq Whisper (`whisper-large-v3`)
**Input:** Raw audio file (max 180 seconds, wav/mp3/m4a/ogg/flac/webm)
**Output:** Full transcript + word-level timestamps + detected language (`hi`/`en`/`auto`)

The transcription handles natural vendor speech — incomplete sentences, Hindi numerals mixed with English numbers, vendor-specific vocabulary like "bisi", "maal", "dukaan". Groq's Whisper implementation gives sub-3-second transcription for a 3-minute recording.

### Node 2 — Guardrail
**Model:** LLM classification
**Checks:** Profanity, PII exposure, sensitive content
**Action:** If unsafe → pipeline terminates immediately, returns safe refusal response

This is a hard stop, not a flag. If guardrail fires, no data is stored, no processing continues, and the vendor gets a safe response explaining what happened.

### Node 3 — Sanitize
**Method:** Regex + LLM hybrid
**Replaces:** Phone numbers → `[PHONE]`, addresses → `[ADDRESS]`, personal names → `[NAME]`
**Output:** Sanitized transcript safe for LLM processing and storage

### Node 4 — Extract
**Model:** Groq LLM (`llama-3.1-8b-instant`)
**Extracts structured JSON:**
```json
{
  "items_sold": [
    {"name": "केला", "quantity": 50, "unit_price": 5, "total_amount": 250}
  ],
  "expenses": [
    {"type": "transport", "amount": 30, "description": "auto fare"}
  ],
  "sentiment": "good",
  "mood_score": 4,
  "mood_trigger": false,
  "mood_trigger_reason": null,
  "stock_out_mentions": ["tomato"]
}
```

### Node 5 — Memory Analysis
**Criteria for long-term storage:**
- Revenue or expense amounts above threshold
- New patterns or anomalies detected
- Mood triggers present
- Stock-out mentions
**Output:** `is_important` (boolean) + `importance_score` (0–1)

### Node 6 — Long-Term Memory (conditional)
**Model:** `multilingual-e5-small` (384-dimensional embeddings)
**Storage:** Qdrant Cloud vector database
**Only fires** when `is_important = true`
**Enables:** Cross-session semantic retrieval ("last time tomatoes ran out, what did the vendor do?")

### Node 7 — Retrieval
**Query:** Current session transcript
**Method:** Qdrant cosine similarity search, top-k=3
**Returns:** Most contextually similar past session summaries
**Purpose:** Grounds the Decision node in real vendor history, not generic advice

### Node 8 — Decision
**Model:** Groq LLM (`llama-3.3-70b-versatile`)
**Inputs:** transcript + extracted_data + retrieved_memories
**Generates:**
- Natural Hindi/English summary of the day
- Business insights based on patterns
- Specific recommendations (restock, pricing, timing)
- Contextually aware response tied to past sessions

### Node 9 — Post-Processing
```
Audio → S3 upload (permanent storage)
Transcript → Supabase transcriptions table
Extracted data → Ledger entry creation
Audio segments → Supabase audio_segments table
VAPI check → Should Arjun follow up?
```

---

## Arjun — The VAPI Voice Agent

When the pipeline detects low-confidence extractions (≥3 items below 0.7 confidence), negative sentiment (mood_score ≤ 2), or stock-out mentions that need clarification, **Arjun** is triggered — a Hindi-speaking voice agent that calls the vendor back through the app.

**Arjun's character:**
- Speaks fluent Hindi/Hinglish — not "Devanagari with English grammar"
- Asks one question at a time, confirms before moving to the next
- Celebrates vendor wins ("Bahut badhiya! Aaj ₹1100 ki kamai!")
- Shows genuine empathy during tough days
- Never makes up data — always calls backend functions for real numbers

### VAPI Configuration

| Parameter | Value |
|-----------|-------|
| Voice Provider | ElevenLabs |
| Voice ID | `pNInz6obpgDQGcFmaJgB` (Adam — warm Hindi male) |
| STT Provider | Deepgram (`nova-2`, language: `hi`) |
| LLM | Groq `llama-3.3-70b-versatile` |
| Temperature | 0.3 (consistent for business conversations) |
| Max Tokens | 200 (2–3 sentences per turn) |
| Smart Format | true (auto-formats ₹ amounts, dates) |

### The 10 Backend Functions Arjun Can Call

```
┌─────────────────────────────────┬──────────────────────────────────────┐
│ Function                        │ When Arjun Uses It                   │
├─────────────────────────────────┼──────────────────────────────────────┤
│ get_today_summary               │ "आज का सारांश बताओ"                 │
│ get_weekly_summary              │ "इस हफ्ते का सारांश"                 │
│ get_best_sellers                │ "कौन सी चीज़ सबसे ज्यादा बिकी?"     │
│ get_stock_suggestions           │ "कल के लिए क्या स्टॉक रखूं?"        │
│ confirm_item                    │ After vendor clarifies vague item     │
│ get_unconfirmed_items           │ Start of clarification session        │
│ get_recent_anomalies            │ "कुछ अजीब हुआ?"                      │
│ get_expense_breakdown           │ "खर्च कहाँ हुआ?"                     │
│ get_mood_trend                  │ Vendor seems stressed — check history │
│ search_past_records             │ "पिछले हफ्ते कितने केले बिके?"       │
└─────────────────────────────────┴──────────────────────────────────────┘
```

### Example Conversation

```
Arjun:  "Namaste! Main Arjun hoon. Aaj aapne kuch items mention kiye jo 
         thoda unclear the. Kya aap thoda help kar sakte hain?"

Vendor: "Haan bolo"

Arjun:  "Aapne 'kuch fal' bola tha — woh kya tha exactly?"

Vendor: "Kele the, 50 kele"

Arjun:  "Aur ek kele ki keemat?"

Vendor: "5 rupaye"

Arjun:  *calls confirm_item(user_id, item_id, "केला", 50, 5)*
        "Perfect! 50 kele at ₹5 each — ₹250 ki kamai. 
         Bahut accha! Aur koi item tha?"
```

---

## API Reference

### Core Pipeline

```http
POST /process
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: audio_file (wav/mp3/m4a/ogg/flac/webm, max 180s)

Response:
{
  "session_id": "uuid",
  "transcription_id": "uuid",
  "transcript": "string",
  "extracted_data": { items_sold, expenses, sentiment, mood_score },
  "final_response": "Hindi/English business summary",
  "vapi_triggered": boolean,
  "vapi_session_id": "string | null",
  "vapi_reason": "string | null"
}
```

### VAPI Endpoints

```http
# Initialize VAPI session — call this first
POST /vapi/session/start
Body: { "user_id": "uuid", "trigger_reason": "string" }

# Get all 10 function schemas (paste into VAPI dashboard)
GET /vapi/functions/definitions

# Execute function called by Arjun during conversation
POST /vapi/functions/execute
Body: { "function_name": "get_today_summary", "parameters": {...}, "user_id": "uuid", "session_id": "uuid" }

# Webhooks (configure in VAPI dashboard)
POST /vapi/webhook/call-start
POST /vapi/webhook/call-end
POST /vapi/webhook/message

# Utilities
POST /vapi/trigger-check       # Should Arjun be triggered for this transcription?
GET  /vapi/clarifications       # Pending items needing clarification
GET  /vapi/call-history         # Session history
GET  /vapi/mood-trend           # Vendor mood trend over time
```

### Ledger & Analytics

```http
GET  /ledger/entries            # All ledger entries for user
GET  /ledger/entries/{id}       # Single entry
GET  /ledger/summary/today      # Today's aggregated totals
GET  /ledger/summary/weekly     # 7-day aggregated totals
GET  /analytics/best-sellers    # Top items by revenue
GET  /analytics/stock-suggestions  # ML-based tomorrow's stock
GET  /analytics/anomalies       # Unusual activity alerts
GET  /health                    # Service health check
```

---

## Repository Structure

```
voicetrace-ai/
├── backend/                        # FastAPI backend (Python 3.11)
│   ├── main.py                     # Entry point — POST /process
│   ├── graph.py                    # LangGraph state machine definition
│   │
│   ├── nodes/                      # Pipeline nodes
│   │   ├── transcribe.py           # Groq Whisper transcription
│   │   ├── guardrail.py            # Content safety classification
│   │   ├── sanitize.py             # PII removal
│   │   ├── extract.py              # Structured data extraction
│   │   ├── memory_analysis.py      # Importance scoring
│   │   ├── memory_router.py        # Conditional routing
│   │   ├── long_term_memory.py     # Qdrant vector storage
│   │   ├── retrieval.py            # Semantic memory retrieval
│   │   └── decision.py             # Final response generation
│   │
│   ├── services/                   # Business logic services
│   │   ├── transcription_service.py     # Groq Whisper wrapper
│   │   ├── groq_llm.py                  # LLM abstraction layer
│   │   ├── guardrail.py                 # Safety classification
│   │   ├── embedding.py                 # multilingual-e5-small embeddings
│   │   ├── qdrant_memory.py             # Vector DB operations
│   │   ├── supabase_service.py          # PostgreSQL operations
│   │   ├── audio_storage_service.py     # S3 file management
│   │   ├── ledger_service.py            # Business ledger CRUD
│   │   ├── pattern_service.py           # Sales pattern analysis
│   │   ├── stock_suggestion_service.py  # ML stock predictions
│   │   ├── vapi_service.py              # VAPI trigger logic
│   │   └── pdf_export.py               # Report generation
│   │
│   └── routers/                    # FastAPI routers
│       ├── vapi.py                 # VAPI webhooks + session management
│       └── vapi_functions.py       # 10 VAPI function implementations
│
├── expo-app/                       # React Native mobile app
│   └── src/
│       ├── screens/
│       │   └── RecordingScreen.tsx # Audio recording + upload
│       └── services/
│           └── vapiService.ts      # VAPI SDK integration
│
├── frontend/                       # Next.js web dashboard
│   └── src/
│       └── app/                    # Analytics + ledger viewer
│
├── migrations/                     # Supabase SQL migrations
│   ├── transcriptions.sql
│   ├── ledger_entries.sql
│   ├── audio_segments.sql
│   ├── vapi_triggers.sql
│   └── vapi_conversation_analytics.sql
│
├── docker-compose.yml              # Full stack orchestration
├── requirements.txt                # Python dependencies
└── .env.example                    # Environment variables template
```

---

## Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Speech-to-Text** | Groq Whisper `whisper-large-v3` | Hindi/Hinglish transcription |
| **LLM (Fast)** | Groq `llama-3.1-8b-instant` | Entity extraction |
| **LLM (Reasoning)** | Groq `llama-3.3-70b-versatile` | Decision + insights |
| **Embeddings** | `multilingual-e5-small` (384-dim) | Semantic memory |
| **Vector DB** | Qdrant Cloud | Long-term memory retrieval |
| **Voice Agent** | VAPI + ElevenLabs + Deepgram | Arjun voice conversations |
| **TTS** | ElevenLabs `pNInz6obpgDQGcFmaJgB` | Hindi vocal output |
| **STT (calls)** | Deepgram `nova-2` (Hindi) | In-call speech recognition |
| **Pipeline** | LangGraph (9-node state machine) | Agentic orchestration |
| **Backend** | FastAPI (Python 3.11) | REST API + webhooks |
| **Database** | Supabase (PostgreSQL) | Structured data + auth |
| **Audio Storage** | AWS S3 | Permanent audio archival |
| **Mobile** | Expo React Native | Vendor-facing app |
| **Frontend** | Next.js | Web analytics dashboard |
| **Container** | Docker Compose | Local + cloud orchestration |
| **Deployment** | AWS EC2 + ngrok | Backend hosting |

</div>

---

## Getting Started

### Prerequisites

```bash
Python 3.11+
Node.js 18+
Docker & Docker Compose
AWS account (S3 bucket)
Supabase project (free tier)
Qdrant Cloud account (free tier)
Groq API key (free tier)
VAPI account (free tier: 100 min/month)
ElevenLabs API key
```

### Environment Setup

```bash
# Clone repository
git clone https://github.com/farhat-1203/VoiceTrace-AI.git
cd VoiceTrace-AI

# Copy environment template
cp .env.example .env
```

```env
# .env — fill in all values before starting

# Groq
GROQ_API_KEY=gsk_your_groq_key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key

# Qdrant Cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_key
QDRANT_COLLECTION=voicetrace_memory

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
S3_BUCKET_NAME=voicetrace-audio

# VAPI
VAPI_API_KEY=vapi_your_key
VAPI_ASSISTANT_ID=asst_your_assistant_id
BACKEND_URL=https://your-ngrok-url.ngrok-free.app

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### Start Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python migrations/run_migrations.py

# Start backend
uvicorn backend.main:app --reload --port 8000

# Or with Docker
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

### Run Mobile App

```bash
cd expo-app
npm install
npx expo start

# For Android
npx expo run:android
```

### Configure VAPI Dashboard

```bash
# Step 1: Get all function schemas
curl http://localhost:8000/vapi/functions/definitions

# Step 2: Go to vapi.ai → Create Assistant → "Arjun"
# Step 3: Set Function Execution URL
#   https://your-backend.com/vapi/functions/execute
# Step 4: Paste all 10 function schemas from Step 1
# Step 5: Set webhook URLs:
#   Call Start: /vapi/webhook/call-start
#   Call End:   /vapi/webhook/call-end
# Step 6: Configure voice: ElevenLabs, voice ID pNInz6obpgDQGcFmaJgB
# Step 7: Test call in VAPI dashboard — speak in Hindi

# Test function execution
curl -X POST http://localhost:8000/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "test-user"},
    "user_id": "test-user",
    "session_id": "test-session"
  }'
```

---

## Database Schema

```sql
-- Core transcription storage
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    transcript TEXT NOT NULL,
    sanitized_transcript TEXT,
    detected_language TEXT,
    extracted_data JSONB,
    final_response TEXT,
    audio_url TEXT,
    duration_seconds INTEGER,
    mood_score INTEGER,
    sentiment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Financial ledger
CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    transcription_id UUID REFERENCES transcriptions(id),
    entry_type TEXT NOT NULL,   -- 'income' | 'expense'
    item_name TEXT,
    quantity DECIMAL,
    unit_price DECIMAL,
    total_amount DECIMAL NOT NULL,
    confidence_score DECIMAL DEFAULT 1.0,
    confirmed BOOLEAN DEFAULT false,
    audio_url TEXT,
    entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- VAPI conversation analytics
CREATE TABLE vapi_conversation_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    session_metadata JSONB NOT NULL,
    conversation_summary JSONB NOT NULL,
    business_data JSONB NOT NULL,
    clarifications JSONB DEFAULT '[]',
    insights_shared JSONB DEFAULT '{}',
    sentiment JSONB DEFAULT '{}',
    issues JSONB DEFAULT '[]',
    actions JSONB DEFAULT '[]',
    follow_up JSONB DEFAULT '{}',
    quality JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- VAPI trigger tracking
CREATE TABLE vapi_triggers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    transcription_id UUID REFERENCES transcriptions(id),
    trigger_reason TEXT NOT NULL,
    trigger_type TEXT NOT NULL,  -- 'initial' | 'follow_up'
    status TEXT NOT NULL DEFAULT 'pending',
    scheduled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Services Status

<div align="center">

| Service | Status | Location |
|---------|--------|----------|
| Audio transcription (Groq Whisper) | ✅ Working | `nodes/transcribe.py` |
| Content guardrails | ✅ Working | `nodes/guardrail.py` |
| PII sanitization | ✅ Working | `nodes/sanitize.py` |
| Entity extraction (llama-3.1-8b) | ✅ Working | `nodes/extract.py` |
| Memory importance scoring | ✅ Working | `nodes/memory_analysis.py` |
| Qdrant vector storage | ✅ Working | `nodes/long_term_memory.py` |
| Semantic retrieval | ✅ Working | `nodes/retrieval.py` |
| Decision generation (llama-3.3-70b) | ✅ Working | `nodes/decision.py` |
| AWS S3 audio storage | ✅ Working | `services/audio_storage_service.py` |
| Supabase persistence | ✅ Working | `services/supabase_service.py` |
| Ledger entry creation | ✅ Working | `services/ledger_service.py` |
| Sales pattern analysis | ✅ Working | `services/pattern_service.py` |
| ML stock suggestions | ✅ Working | `services/stock_suggestion_service.py` |
| PDF report export | ✅ Working | `services/pdf_export.py` |
| VAPI service logic | ✅ Implemented | `services/vapi_service.py` |
| VAPI webhooks (10 endpoints) | ✅ Implemented | `routers/vapi.py` |
| VAPI functions (10 functions) | ✅ Implemented | `routers/vapi_functions.py` |
| Auto VAPI trigger in pipeline | ⚠️ Wiring pending | `main.py` line ~250 |
| Frontend VAPI SDK (Expo) | ⚠️ Integration pending | `expo-app/src/services/` |

</div>

---

## Roadmap

- [x] LangGraph 9-node pipeline (transcribe → guardrail → sanitize → extract → memory → retrieval → decision)
- [x] Groq Whisper Hindi/Hinglish transcription
- [x] Qdrant long-term memory with multilingual-e5-small embeddings
- [x] VAPI Arjun agent with 10 backend functions
- [x] ElevenLabs Hindi voice synthesis
- [x] Deepgram Hindi STT for live calls
- [x] Supabase ledger persistence
- [x] AWS S3 audio archival
- [x] VAPI structured output schema (full conversation analytics)
- [ ] Wire VAPI auto-trigger into main.py pipeline
- [ ] Expo frontend VAPI SDK integration
- [ ] `vapi_triggers` table → real-time app notifications
- [ ] PDF financial report generation (monthly)
- [ ] iOS app support
- [ ] WhatsApp integration (send ledger summaries via WhatsApp Business API)
- [ ] Offline-first audio recording with sync queue
- [ ] Regional language expansion (Marathi, Gujarati, Tamil)

---

## Built At

This project was built in **24 hours** at a hackathon by:

- **Ayaan Amjad** — Pipeline architecture, VAPI integration, FastAPI backend, LangGraph orchestration
- **Farhat** — Expo mobile app, frontend dashboard, Supabase schema, Docker orchestration

Stack: LangGraph · Groq · ElevenLabs · VAPI · Qdrant · Supabase · AWS S3 · FastAPI · Expo · Next.js

---

## Contributing

1. Fork the repository
2. Create your branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m 'feat: your feature'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

Issues welcome — especially around Hindi NLP edge cases and VAPI conversation flow improvements.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

*Built for street vendors who run real businesses but have never had a tool built for them.*

**Ayaan Amjad** · **Farhat** · Mumbai, India

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:f59e0b,50:db2777,100:7c3aed&height=100&section=footer" />

</div>
