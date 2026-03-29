# VAPI Implementation & Integration Plan
## VoiceTrace AI - Custom Voice Agent Setup

**Last Updated:** March 29, 2026  
**Backend URL:** https://ba02-32-192-28-123.ngrok-free.app  
**Status:** Production Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Backend Pipeline Architecture](#backend-pipeline-architecture)
3. [VAPI Platform Registration](#vapi-platform-registration)
4. [Voice Configuration](#voice-configuration)
5. [Webhook Setup](#webhook-setup)
6. [Function Tools Configuration](#function-tools-configuration)
7. [Testing & Validation](#testing--validation)
8. [Integration Status](#integration-status)

---

## System Overview

### What is VAPI in VoiceTrace?

VAPI (Voice AI Platform Interface) is integrated as a **custom voice agent** (named "Arjun") that provides:

- **Real-time voice interactions** with vendors in Hindi/Hinglish
- **Inbound conversations** - Vendors ask questions, agent responds
- **Outbound clarifications** - Agent proactively asks for missing information
- **NOT phone-based** - Works through app interface, no phone calls

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VoiceTrace Backend                        │
│                  (EC2 + Port 8000 + ngrok)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      VAPI Platform                           │
│              (Voice Agent Orchestration)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket/HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Expo Mobile App                           │
│              (Vendor Interface - Frontend)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Pipeline Architecture

### Complete Processing Flow

The VoiceTrace backend is designed as a **sequential pipeline** that processes raw audio through multiple stages. Here's how everything works together:

#### Stage 1: Audio Upload & Initial Processing

```
User records 3-minute audio in Expo app
    ↓
POST /process (main.py:process_audio)
    ├─ Validates audio format (wav, mp3, m4a, ogg, flac, webm)
    ├─ Checks duration (max 180 seconds)
    ├─ Saves to uploads/ directory
    └─ Generates session_id (UUID)
```

**Status:** ✅ Fully implemented and working

#### Stage 2: LangGraph Pipeline Execution

The core processing happens through a **LangGraph state machine** defined in `backend/graph.py`:

```python
# Pipeline nodes execute in sequence:
transcribe → guardrail → sanitize → extract → memory_analysis
    → [conditional routing]
        → important? YES: long_term_memory → retrieval → decision
        → important? NO:  retrieval → decision
```

**Detailed Node Breakdown:**


**1. Transcribe Node** (`backend/nodes/transcribe.py`)
```
Input: audio_path
Process: Groq Whisper API (whisper-large-v3)
Output: 
  - transcript (full text)
  - segments (word-level timestamps)
  - detected_language (hi/en/auto)
Status: ✅ Working
```

**2. Guardrail Node** (`backend/nodes/guardrail.py`)
```
Input: transcript
Process: LLM-based safety classification
Checks:
  - Profanity/abuse
  - Sensitive information (PII)
  - Inappropriate content
Output: is_safe (boolean), safety_response
Status: ✅ Working
Action: If unsafe → pipeline STOPS (returns END)
```

**3. Sanitize Node** (`backend/nodes/sanitize.py`)
```
Input: transcript
Process: Remove/mask sensitive data
  - Phone numbers → [PHONE]
  - Addresses → [ADDRESS]
  - Personal names → [NAME]
Output: sanitized_transcript
Status: ✅ Working
```

**4. Extract Node** (`backend/nodes/extract.py`)
```
Input: sanitized_transcript
Process: Groq LLM (llama-3.1-8b-instant)
Extracts:
  - items_sold: [{name, quantity, unit_price, total_amount}]
  - expenses: [{type, amount, description}]
  - sentiment: "good" | "neutral" | "bad"
  - mood_score: 1-5 (1=very negative, 5=very positive)
  - mood_trigger: boolean (should VAPI follow up?)
  - mood_trigger_reason: string
  - stock_out_mentions: [item names]
Output: extracted_data (structured JSON)
Status: ✅ Working
```


**5. Memory Analysis Node** (`backend/nodes/memory_analysis.py`)
```
Input: extracted_data
Process: Determine if information is important enough for long-term storage
Criteria:
  - Significant revenue/expense amounts
  - New patterns or anomalies
  - Mood triggers
  - Stock-out mentions
Output: 
  - is_important (boolean)
  - importance_score (0-1)
Status: ✅ Working
```

**6. Memory Router Node** (`backend/nodes/memory_router.py`)
```
Input: is_important
Process: Conditional routing
Routes to:
  - long_term_memory_node (if important)
  - retrieval_node (if not important)
Status: ✅ Working
```

**7. Long-term Memory Node** (`backend/nodes/long_term_memory.py`)
```
Input: extracted_data, transcript
Process: 
  - Generate embedding (multilingual-e5-small, 384 dims)
  - Store in Qdrant vector database
  - Format memory for future retrieval
Output: formatted_memory, memory_id
Status: ✅ Working
Integration: Qdrant Cloud
```

**8. Retrieval Node** (`backend/nodes/retrieval.py`)
```
Input: transcript
Process:
  - Query Qdrant for similar past memories
  - Retrieve top-k (default: 3) relevant memories
Output: retrieved_memories (list of past contexts)
Status: ✅ Working
Purpose: Provides context for decision node
```


**9. Decision Node** (`backend/nodes/decision.py`)
```
Input: 
  - transcript
  - extracted_data
  - retrieved_memories
Process: Groq LLM (llama-3.3-70b-versatile)
Generates:
  - Natural language summary
  - Business insights
  - Recommendations
  - Contextual responses based on past memories
Output: final_response (conversational text)
Status: ✅ Working
```

#### Stage 3: Post-Pipeline Processing (main.py)

After the LangGraph pipeline completes:

```python
# 1. Upload audio to S3
audio_storage_service.upload_audio(file_path, user_id, session_id)
    ↓
# 2. Store transcription in Supabase
supabase_service.store_transcription(
    user_id, transcript, extracted_data, audio_url, ...
)
    ↓
# 3. Create ledger entry
ledger_service.create_entry_from_transcription(
    user_id, transcription_id, extracted_data, audio_url
)
    ↓
# 4. Store audio segments (for playback)
audio_storage_service.store_audio_segments(
    transcription_id, segments, audio_url
)
```

**Status:** ✅ All working

#### Stage 4: VAPI Integration Points

**Current Implementation:**

```python
# In vapi_service.py
def should_trigger_call(extracted_data, confidence_scores):
    """
    Determines if VAPI agent should be activated
    
    Triggers on:
    - Negative sentiment (mood_score <= 2)
    - Low confidence items (>= 3 items with confidence < 0.7)
    - Stock-out mentions
    """
```


**⚠️ NOT YET WIRED UP:**

The VAPI trigger logic exists but is **not automatically called** after audio processing. To complete the integration:

```python
# Add to main.py after ledger creation (line ~250):

# ── Check if VAPI should be triggered ─────────────────────────
if transcription_id and result.get("extracted_data"):
    from services.vapi_service import vapi_service
    
    # Calculate confidence scores
    confidence_scores = {}
    for idx, item in enumerate(result["extracted_data"].get("items_sold", [])):
        score = 0.5
        if item.get("quantity"): score += 0.25
        if item.get("unit_price"): score += 0.25
        confidence_scores[f"item_{idx}"] = score
    
    # Check trigger
    should_trigger, reason = vapi_service.should_trigger_call(
        extracted_data=result["extracted_data"],
        confidence_scores=confidence_scores
    )
    
    if should_trigger:
        logger.info(f"VAPI trigger detected: {reason}")
        # Trigger VAPI session
        session_id = vapi_service.trigger_agent_session(
            user_id=user_id,
            transcription_id=transcription_id,
            session_type="clarification",
            context_data={
                "trigger_reason": reason,
                "extracted_data": result["extracted_data"],
                "confidence_scores": confidence_scores
            }
        )
        # Add to response
        result["vapi_triggered"] = True
        result["vapi_session_id"] = session_id
        result["vapi_reason"] = reason
```

**Status:** ⚠️ Code exists but not integrated into main pipeline

---

### Data Flow Summary

```
Audio File (3 min)
    ↓
[Transcribe] → Raw text + segments
    ↓
[Guardrail] → Safety check (STOP if unsafe)
    ↓
[Sanitize] → Remove PII
    ↓
[Extract] → Structured data (items, expenses, mood)
    ↓
[Memory Analysis] → Is this important?
    ↓
[Conditional]
    ├─ Important → [Long-term Memory] → Store in Qdrant
    └─ Not Important → Skip storage
    ↓
[Retrieval] → Get similar past memories
    ↓
[Decision] → Generate insights + recommendations
    ↓
[Post-Processing]
    ├─ Upload audio to S3
    ├─ Store in Supabase (transcriptions table)
    ├─ Create ledger entry (ledger_entries table)
    └─ Store segments (audio_segments table)
    ↓
[VAPI Check] ⚠️ NOT YET WIRED
    └─ Should trigger? → Start VAPI session
```


### Services Layer

The backend uses a **service-oriented architecture** where each service handles specific functionality:

| Service | Purpose | Status |
|---------|---------|--------|
| `transcription_service.py` | Groq Whisper API integration | ✅ Working |
| `groq_llm.py` | LLM calls (extraction, response generation) | ✅ Working |
| `guardrail.py` | Content safety classification | ✅ Working |
| `embedding.py` | Text → vector embeddings | ✅ Working |
| `qdrant_memory.py` | Vector database operations | ✅ Working |
| `supabase_service.py` | PostgreSQL database operations | ✅ Working |
| `audio_storage_service.py` | S3 audio file management | ✅ Working |
| `ledger_service.py` | Business ledger CRUD | ✅ Working |
| `pattern_service.py` | Sales pattern analysis | ✅ Working |
| `stock_suggestion_service.py` | ML-based stock predictions | ✅ Working |
| `vapi_service.py` | VAPI integration logic | ✅ Implemented, ⚠️ Not wired |
| `pdf_export.py` | Report generation | ✅ Working |

---

## VAPI Platform Registration

### Step 1: Create VAPI Account

1. Go to **https://vapi.ai**
2. Click **"Sign Up"** or **"Get Started"**
3. Choose plan:
   - **Free Tier:** 100 minutes/month (good for testing)
   - **Pro:** $99/month (unlimited)
4. Verify email and complete onboarding

### Step 2: Get API Key

1. Navigate to **Dashboard → Settings → API Keys**
2. Click **"Create New API Key"**
3. Name it: `VoiceTrace Production`
4. Copy the key (starts with `vapi_`)
5. Add to backend `.env`:

```bash
VAPI_API_KEY=vapi_your_api_key_here
```


### Step 3: Create Custom Assistant

1. Go to **Dashboard → Assistants**
2. Click **"+ Create Assistant"**
3. Fill in basic details:

```yaml
Assistant Name: VoiceTrace Business Assistant (Arjun)
Description: Hindi/Hinglish voice agent for street vendors
Type: Custom Assistant (not phone-based)
```

4. Click **"Create"**
5. Copy the **Assistant ID** (format: `asst_xxxxxxxxxxxxx`)
6. Add to `.env`:

```bash
VAPI_ASSISTANT_ID=asst_xxxxxxxxxxxxx
```

---

## Voice Configuration

### Step 1: Select Voice Provider

In VAPI Dashboard → Assistant Settings → **Voice**:

**Recommended: ElevenLabs** (best Hindi support)

```yaml
Provider: ElevenLabs
Voice ID: pNInz6obpgDQGcFmaJgB
Voice Name: Adam (Hindi Male - Warm & Friendly)
```

**Alternative Voice IDs for Hindi:**
- `21m00Tcm4TlvDq8ikWAM` - Rachel (Female, Clear)
- `AZnzlk1XvdvUeBnXmlld` - Domi (Female, Energetic)
- `EXAVITQu4vr4xnSDxMaL` - Bella (Female, Soft)
- `pNInz6obpgDQGcFmaJgB` - Adam (Male, Warm) ⭐ Recommended

### Step 2: Configure Voice Settings

```yaml
Stability: 0.5
  # Lower = more expressive, Higher = more consistent
  # 0.5 is balanced for conversational Hindi

Similarity Boost: 0.8
  # How closely to match the original voice
  # 0.8 provides natural Hindi pronunciation

Speed: 1.0
  # Speaking rate (0.5 = slow, 2.0 = fast)
  # 1.0 is natural conversational pace

Style: 0.0
  # Exaggeration level (0 = neutral, 1 = dramatic)
  # 0 for business conversations
```


### Step 3: Configure Transcriber (Speech-to-Text)

In VAPI Dashboard → Assistant Settings → **Transcriber**:

```yaml
Provider: Deepgram
Model: nova-2
Language: hi (Hindi)
  # Also supports: hi-Latn (Hinglish), en (English)

Smart Format: true
  # Automatically formats numbers, dates, currency

Punctuate: true
  # Adds punctuation for better readability

Profanity Filter: false
  # Keep false for authentic vendor language

Keywords: []
  # Optional: Add business-specific terms
  # Example: ["केला", "आम", "सब्जी", "फल"]
```

### Step 4: Configure LLM Model

In VAPI Dashboard → Assistant Settings → **Model**:

```yaml
Provider: Groq
Model: llama-3.3-70b-versatile
  # Best for multilingual (Hindi/English)
  # Alternative: llama-3.1-8b-instant (faster, cheaper)

Temperature: 0.3
  # Lower = more consistent, Higher = more creative
  # 0.3 for business conversations

Max Tokens: 200
  # Limit response length (keep conversations concise)
  # 200 tokens ≈ 2-3 sentences

Top P: 0.9
  # Nucleus sampling (0.9 is standard)

Frequency Penalty: 0.0
  # Reduce repetition (0 = no penalty)

Presence Penalty: 0.0
  # Encourage topic diversity (0 = no penalty)
```


### Step 5: Set First Message

In VAPI Dashboard → Assistant Settings → **First Message**:

```
Namaste! Main Arjun hoon, aapka business assistant. Aaj ka din kaisa raha? Kya main aapki koi madad kar sakta hoon?
```

**Translation:** Hello! I'm Arjun, your business assistant. How was your day? Can I help you with anything?

### Step 6: Configure System Prompt

In VAPI Dashboard → Assistant Settings → **System Prompt**:

```
You are Arjun, a helpful business assistant for street vendors in India.

PERSONALITY:
- Friendly, warm, and conversational
- Speak in Hindi or Hinglish (mix of Hindi and English)
- Use simple language, avoid complex business terms
- Show empathy and understanding
- Be patient and encouraging

YOUR JOB:
- Help vendors understand their business data
- Clarify uncertain information from audio recordings
- Provide insights and recommendations
- Answer questions about sales, expenses, and patterns

CONVERSATION GUIDELINES:
- Ask ONE question at a time
- Confirm information before moving to next question
- Use the available functions to fetch real-time data
- Keep responses SHORT (2-3 sentences maximum)
- Show empathy when vendor seems upset or stressed
- Celebrate vendor's successes with enthusiasm

WHEN CLARIFYING ITEMS:
1. Ask for item name if vague or missing
2. Ask for quantity if not clear
3. Ask for price if missing
4. Use confirm_item function to update database

EXAMPLE CONVERSATIONS:

Vendor: "आज का सारांश बताओ"
You: *calls get_today_summary* "Aaj aapne ₹1100 ki kamai ki aur ₹550 kharch kiye. Net profit ₹550 hai. Bahut accha! Kya aur kuch jaanna chahenge?"

Vendor: "कौन सी चीज़ सबसे ज्यादा बिकी?"
You: *calls get_best_sellers* "Is hafte kele sabse zyada bike - 420 kele, ₹2100 ki kamai. Bahut badhiya!"

Vendor: "कल के लिए क्या स्टॉक रखूं?"
You: *calls get_stock_suggestions* "Kal ke liye main suggest karta hoon: 65 kele, 25 aam, aur 40 seb. Ye aapke sales pattern ke basis par hai."

IMPORTANT RULES:
- ALWAYS use functions to get accurate data
- NEVER make up numbers or information
- If you don't know something, say so politely
- Celebrate vendor's successes
- Offer encouragement during tough times
- Keep responses conversational and natural
```


---

## Webhook Configuration

### Current Backend URL

```
Base URL: https://ba02-32-192-28-123.ngrok-free.app
Port: 8000 (exposed via ngrok)
Protocol: HTTPS (required by VAPI)
```

**⚠️ Important:** This ngrok URL changes when you restart ngrok. For production, use a permanent domain.

### Step 1: Configure Server URL (Start Point)

In VAPI Dashboard → Assistant Settings → **Server URL**:

```yaml
Server URL Type: Request Start
URL: https://ba02-32-192-28-123.ngrok-free.app/vapi/session/start
Method: POST
```

**What this does:**
- Called when VAPI session is about to start
- Backend returns session context, function definitions, and dynamic system prompt
- Allows customization per user/session

**Request format VAPI sends:**
```json
{
  "call": {
    "id": "call_xxxxx",
    "assistantId": "asst_xxxxx",
    "customer": {
      "number": null
    }
  },
  "message": {
    "type": "request-start"
  }
}
```

**Response format backend should return:**
```json
{
  "success": true,
  "session_id": "vapi-session-1234567890",
  "context": {
    "user_id": "user-uuid",
    "trigger_reason": "Clarification needed",
    "pending_clarifications": 3,
    "unconfirmed_items": 2
  },
  "functions": [...],
  "system_prompt": "...",
  "webhook_url": "https://ba02-32-192-28-123.ngrok-free.app/vapi/webhook"
}
```


### Step 2: Configure Webhook URLs

In VAPI Dashboard → Assistant Settings → **Webhooks**:

#### Call Start Webhook
```yaml
Event: call.started
URL: https://ba02-32-192-28-123.ngrok-free.app/vapi/webhook/call-start
Method: POST
```

**When triggered:** VAPI session begins  
**Purpose:** Log session start, track analytics

**Payload VAPI sends:**
```json
{
  "call_id": "call_xxxxx",
  "user_id": "user-uuid",
  "call_type": "clarification",
  "trigger_reason": "Low confidence items detected"
}
```

#### Call End Webhook
```yaml
Event: call.ended
URL: https://ba02-32-192-28-123.ngrok-free.app/vapi/webhook/call-end
Method: POST
```

**When triggered:** VAPI session ends  
**Purpose:** Process clarifications, update database, log outcome

**Payload VAPI sends:**
```json
{
  "call_id": "call_xxxxx",
  "user_id": "user-uuid",
  "duration_seconds": 120,
  "transcript": "Full conversation transcript...",
  "outcome": "completed",
  "clarifications_resolved": [
    {
      "clarification_id": "uuid",
      "resolved_data": {
        "item_name": "केला",
        "quantity": 50,
        "unit_price": 5
      }
    }
  ]
}
```

#### Message Webhook (Optional)
```yaml
Event: message.received
URL: https://ba02-32-192-28-123.ngrok-free.app/vapi/webhook/message
Method: POST
```

**When triggered:** Each message in conversation  
**Purpose:** Real-time message logging, analytics


### Step 3: Test Webhooks

```bash
# Test call-start webhook
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/vapi/webhook/call-start \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-call-123",
    "user_id": "test-user-uuid",
    "call_type": "clarification",
    "trigger_reason": "Testing webhook integration"
  }'

# Expected response:
# {
#   "success": true,
#   "log_id": "uuid",
#   "message": "Call start logged"
# }

# Test call-end webhook
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/vapi/webhook/call-end \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-call-123",
    "user_id": "test-user-uuid",
    "duration_seconds": 120,
    "transcript": "Test conversation",
    "outcome": "completed",
    "clarifications_resolved": []
  }'

# Expected response:
# {
#   "success": true,
#   "message": "Call end processed",
#   "clarifications_resolved": 0
# }
```

---

## Function Tools Configuration

### Overview

VAPI can call **10 backend functions** to fetch real-time data during conversations. These functions are defined in `backend/routers/vapi_functions.py`.

### Step 1: Set Function Execution URL (End Point)

In VAPI Dashboard → Assistant Settings → **Function Calling**:

```yaml
Function Execution URL: https://ba02-32-192-28-123.ngrok-free.app/vapi/functions/execute
Method: POST
```

**What this does:**
- VAPI sends function name + parameters
- Backend executes function
- Returns result to VAPI
- VAPI speaks the result to user


### Step 2: Get Function Definitions

Fetch all function schemas from backend:

```bash
curl https://ba02-32-192-28-123.ngrok-free.app/vapi/functions/definitions
```

**Response:**
```json
{
  "functions": [
    {
      "name": "get_today_summary",
      "description": "Get today's business summary...",
      "parameters": {...}
    },
    ...
  ],
  "count": 10
}
```

### Step 3: Add Functions to VAPI Dashboard

In VAPI Dashboard → Assistant Settings → **Functions**, add each function:

#### Function 1: get_today_summary

```json
{
  "name": "get_today_summary",
  "description": "Get today's business summary including total earnings, expenses, net profit, and items sold. Use this when vendor asks about today's performance or 'aaj ka saarانsh'.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID (UUID format)"
      }
    },
    "required": ["user_id"]
  }
}
```

**When to use:** Vendor asks "आज का सारांश बताओ", "today's summary", "aaj ki kamai"

**Example response:**
```json
{
  "message": "आज का सारांश (Today's summary)",
  "has_data": true,
  "total_earnings": 1100,
  "total_expenses": 550,
  "net_profit": 550,
  "items_count": 5,
  "items": [
    {"name": "केला", "quantity": 50, "amount": 250},
    {"name": "आम", "quantity": 20, "amount": 800}
  ]
}
```


#### Function 2: get_weekly_summary

```json
{
  "name": "get_weekly_summary",
  "description": "Get weekly business summary with total earnings, expenses, net profit, average daily earnings, and top-selling items. Use when vendor asks about this week's performance.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      }
    },
    "required": ["user_id"]
  }
}
```

**When to use:** "इस हफ्ते का सारांश", "weekly summary", "is hafte ki kamai"

#### Function 3: get_best_sellers

```json
{
  "name": "get_best_sellers",
  "description": "Get the best-selling items over a specified period. Shows which items generate the most revenue. Use when vendor asks what sells the most.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      },
      "days": {
        "type": "integer",
        "description": "Number of days to analyze (default: 7)",
        "default": 7
      },
      "limit": {
        "type": "integer",
        "description": "Number of items to return (default: 5)",
        "default": 5
      }
    },
    "required": ["user_id"]
  }
}
```

**When to use:** "कौन सी चीज़ सबसे ज्यादा बिकी?", "best sellers", "sabse zyada kya bika"


#### Function 4: get_stock_suggestions

```json
{
  "name": "get_stock_suggestions",
  "description": "Get stock suggestions for tomorrow based on sales patterns and trends. Use when vendor asks what to stock for tomorrow.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      }
    },
    "required": ["user_id"]
  }
}
```

**When to use:** "कल के लिए क्या स्टॉक रखूं?", "tomorrow's stock", "kal kya rakhun"

#### Function 5: confirm_item

```json
{
  "name": "confirm_item",
  "description": "Confirm and update an uncertain item with correct details. Use after vendor provides clarification for a vague or uncertain item.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      },
      "item_id": {
        "type": "string",
        "description": "The ID of the item to confirm (UUID)"
      },
      "item_name": {
        "type": "string",
        "description": "Confirmed item name in Hindi or English"
      },
      "quantity": {
        "type": "number",
        "description": "Confirmed quantity (can be decimal)"
      },
      "unit_price": {
        "type": "number",
        "description": "Confirmed unit price in rupees"
      }
    },
    "required": ["user_id", "item_id", "item_name", "quantity", "unit_price"]
  }
}
```

**When to use:** After asking clarifying questions and getting answers

**Example flow:**
```
Arjun: "Kaunse fal the?" (Which fruits?)
Vendor: "Kele, 50 kele" (Bananas, 50 bananas)
Arjun: "Ek kela ki keemat?" (Price per banana?)
Vendor: "5 rupaye" (5 rupees)
Arjun: *calls confirm_item(user_id, item_id, "केला", 50, 5)*
```


#### Function 6: get_unconfirmed_items

```json
{
  "name": "get_unconfirmed_items",
  "description": "Get list of items that need clarification due to low confidence scores. Use to find out what needs to be confirmed with the vendor.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      }
    },
    "required": ["user_id"]
  }
}
```

**When to use:** At start of clarification session, or when vendor asks "kya confirm karna hai?"

#### Function 7: get_recent_anomalies

```json
{
  "name": "get_recent_anomalies",
  "description": "Get recent unusual business activities or alerts like sudden expense spikes or revenue drops. Use when vendor asks if anything unusual happened.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      },
      "limit": {
        "type": "integer",
        "description": "Number of anomalies to return (default: 5)",
        "default": 5
      }
    },
    "required": ["user_id"]
  }
}
```

**When to use:** "कुछ अजीब हुआ?", "anything unusual?", "koi problem?"

#### Function 8: get_expense_breakdown

```json
{
  "name": "get_expense_breakdown",
  "description": "Get breakdown of expenses by type (raw materials, transport, rent, etc.) for a specified period. Use when vendor asks about expenses.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      },
      "days": {
        "type": "integer",
        "description": "Number of days to analyze (default: 7)",
        "default": 7
      }
    },
    "required": ["user_id"]
  }
}
```

**When to use:** "खर्च कहाँ हुआ?", "expense breakdown", "kharch ka details"


#### Function 9: get_mood_trend

```json
{
  "name": "get_mood_trend",
  "description": "Get vendor's mood trend over time based on sentiment analysis of their recordings. Use to understand vendor's emotional state.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      },
      "days": {
        "type": "integer",
        "description": "Number of days to analyze (default: 7)",
        "default": 7
      }
    },
    "required": ["user_id"]
  }
}
```

**When to use:** Follow-up calls for negative sentiment, or when vendor seems upset

#### Function 10: search_past_records

```json
{
  "name": "search_past_records",
  "description": "Search past business records by date or item name. Use when vendor asks about historical data or specific items from the past.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      },
      "query": {
        "type": "string",
        "description": "Search query (item name or date in Hindi/English)"
      },
      "days": {
        "type": "integer",
        "description": "Number of days to search back (default: 30)",
        "default": 30
      }
    },
    "required": ["user_id", "query"]
  }
}
```

**When to use:** "पिछले हफ्ते कितने केले बिके?", "last week bananas", "pichhle mahine ka data"

### Step 4: Test Function Execution

```bash
# Test individual function
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "test-user-uuid"},
    "user_id": "test-user-uuid",
    "session_id": "test-session"
  }'

# Expected response:
# {
#   "success": true,
#   "result": {
#     "message": "आज का सारांश (Today's summary)",
#     "has_data": true,
#     "total_earnings": 1100,
#     "total_expenses": 550,
#     "net_profit": 550
#   },
#   "error": null
# }
```


---

## Testing & Validation

### Test 1: Backend Health Check

```bash
curl https://ba02-32-192-28-123.ngrok-free.app/health

# Expected response:
# {
#   "status": "healthy",
#   "services": {
#     "backend": "running",
#     "qdrant_cloud": "connected",
#     "supabase": "connected"
#   }
# }
```

### Test 2: Function Definitions

```bash
curl https://ba02-32-192-28-123.ngrok-free.app/vapi/functions/definitions

# Should return all 10 functions with complete schemas
```

### Test 3: Session Initialization

```bash
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/vapi/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-uuid",
    "trigger_reason": "Testing VAPI integration"
  }'

# Expected response:
# {
#   "success": true,
#   "session_id": "vapi-session-xxxxx",
#   "context": {...},
#   "functions": [...],
#   "system_prompt": "..."
# }
```

### Test 4: VAPI Dashboard Test Call

1. Go to **VAPI Dashboard → Your Assistant**
2. Click **"Test"** button in top right
3. Speak: **"आज का सारांश बताओ"** (Tell me today's summary)
4. Arjun should:
   - Understand Hindi speech
   - Call `get_today_summary` function
   - Receive data from backend
   - Speak response in Hindi

**Expected flow:**
```
You: "आज का सारांश बताओ"
Arjun: *calls get_today_summary(user_id)*
Arjun: "Aaj aapne ₹1100 ki kamai ki aur ₹550 kharch kiye. Net profit ₹550 hai."
```


### Test 5: End-to-End Integration Test

**Prerequisites:**
- User account created in Supabase
- At least one audio recording processed
- Ledger entries exist for the user

**Steps:**

1. **Upload Audio** (via Expo app or API)
```bash
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_audio.mp3"
```

2. **Wait for Processing** (10-30 seconds)

3. **Check if VAPI Should Trigger**
```bash
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/vapi/trigger-check \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transcription_id": "transcription-uuid"}'

# Response:
# {
#   "should_trigger": true,
#   "reason": "3 items need clarification",
#   "extracted_data": {...},
#   "confidence_scores": {...}
# }
```

4. **Start VAPI Session** (if triggered)
```bash
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/vapi/start-session \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transcription_id": "transcription-uuid",
    "session_type": "clarification"
  }'

# Response:
# {
#   "success": true,
#   "session_id": "vapi-session-xxxxx",
#   "message": "Agent session started successfully"
# }
```

5. **Frontend Starts VAPI Call** (using VAPI SDK)

6. **Conversation Happens**

7. **Call Ends** → Backend receives webhook → Updates database

8. **Verify Updates**
```bash
# Check if items were confirmed
curl https://ba02-32-192-28-123.ngrok-free.app/ledger/entries \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check call history
curl https://ba02-32-192-28-123.ngrok-free.app/vapi/call-history \
  -H "Authorization: Bearer YOUR_TOKEN"
```


---

## Integration Status

### ✅ Fully Implemented & Working

| Component | Status | Location |
|-----------|--------|----------|
| Audio transcription | ✅ Working | `backend/nodes/transcribe.py` |
| Content guardrails | ✅ Working | `backend/nodes/guardrail.py` |
| Data sanitization | ✅ Working | `backend/nodes/sanitize.py` |
| Entity extraction | ✅ Working | `backend/nodes/extract.py` |
| Memory analysis | ✅ Working | `backend/nodes/memory_analysis.py` |
| Vector storage (Qdrant) | ✅ Working | `backend/nodes/long_term_memory.py` |
| Memory retrieval | ✅ Working | `backend/nodes/retrieval.py` |
| Response generation | ✅ Working | `backend/nodes/decision.py` |
| Ledger creation | ✅ Working | `backend/services/ledger_service.py` |
| Audio storage (S3) | ✅ Working | `backend/services/audio_storage_service.py` |
| VAPI service logic | ✅ Implemented | `backend/services/vapi_service.py` |
| VAPI webhooks | ✅ Implemented | `backend/routers/vapi.py` |
| VAPI functions (10) | ✅ Implemented | `backend/routers/vapi_functions.py` |

### ⚠️ Not Yet Wired Up

| Component | Status | Action Required |
|-----------|--------|-----------------|
| Auto VAPI trigger | ⚠️ Not wired | Add trigger check to `main.py` after ledger creation |
| Frontend VAPI SDK | ⚠️ Not integrated | Install `@vapi-ai/web` in Expo app |
| VAPI session start | ⚠️ Not called | Frontend needs to call VAPI when triggered |
| Follow-up call logic | ⚠️ Not implemented | Backend needs to schedule follow-up calls |

### 🔧 Required Changes

#### 1. Wire VAPI Trigger in main.py

**Location:** `backend/main.py` (after line ~250, after ledger creation)

**Add this code:**

```python
# ── Check if VAPI should be triggered ─────────────────────────
if transcription_id and result.get("extracted_data"):
    from services.vapi_service import vapi_service
    
    # Calculate confidence scores
    confidence_scores = {}
    for idx, item in enumerate(result["extracted_data"].get("items_sold", [])):
        score = 0.5
        if item.get("quantity"): score += 0.25
        if item.get("unit_price"): score += 0.25
        confidence_scores[f"item_{idx}"] = score
    
    # Check trigger
    should_trigger, reason = vapi_service.should_trigger_call(
        extracted_data=result["extracted_data"],
        confidence_scores=confidence_scores
    )
    
    if should_trigger:
        logger.info(f"VAPI trigger detected: {reason}")
        # Store trigger info for frontend
        supabase_service._client.table("vapi_triggers")\
            .insert({
                "user_id": user_id,
                "transcription_id": transcription_id,
                "trigger_reason": reason,
                "trigger_type": "initial",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            })\
            .execute()
```


#### 2. Create vapi_triggers Table in Supabase

```sql
CREATE TABLE vapi_triggers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    transcription_id UUID REFERENCES transcriptions(id),
    trigger_reason TEXT NOT NULL,
    trigger_type TEXT NOT NULL, -- 'initial' or 'follow_up'
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'accepted', 'declined', 'completed'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_transcription FOREIGN KEY (transcription_id) REFERENCES transcriptions(id) ON DELETE SET NULL
);

CREATE INDEX idx_vapi_triggers_user_status ON vapi_triggers(user_id, status);
CREATE INDEX idx_vapi_triggers_created ON vapi_triggers(created_at DESC);
```

#### 3. Frontend Integration (Expo App)

**Install VAPI SDK:**

```bash
cd expo-app
npm install @vapi-ai/web
```

**Add VAPI Client:**

Create `expo-app/src/services/vapiService.ts`:

```typescript
import Vapi from '@vapi-ai/web';

const VAPI_API_KEY = process.env.EXPO_PUBLIC_VAPI_API_KEY;
const VAPI_ASSISTANT_ID = process.env.EXPO_PUBLIC_VAPI_ASSISTANT_ID;

class VAPIService {
  private vapi: Vapi;
  private currentCallType: 'initial' | 'follow_up' | null = null;

  constructor() {
    this.vapi = new Vapi(VAPI_API_KEY);
    this.setupEventListeners();
  }

  private setupEventListeners() {
    this.vapi.on('call-start', () => {
      console.log('VAPI call started');
    });

    this.vapi.on('call-end', () => {
      console.log('VAPI call ended');
      this.currentCallType = null;
    });

    this.vapi.on('message', (message) => {
      console.log('VAPI message:', message);
    });

    this.vapi.on('error', (error) => {
      console.error('VAPI error:', error);
    });
  }

  async startSession(userId: string, sessionId: string, callType: 'initial' | 'follow_up') {
    this.currentCallType = callType;
    
    await this.vapi.start({
      assistantId: VAPI_ASSISTANT_ID,
      metadata: {
        userId,
        sessionId,
        callType
      }
    });
  }

  stopSession() {
    this.vapi.stop();
  }

  isActive() {
    return this.currentCallType !== null;
  }
}

export const vapiService = new VAPIService();
```


**Add to Recording Screen:**

In `expo-app/src/screens/RecordingScreen.tsx`:

```typescript
import { vapiService } from '../services/vapiService';

// After audio upload succeeds:
const handleUploadSuccess = async (response) => {
  // ... existing code ...
  
  // Check if VAPI should trigger
  const triggerCheck = await fetch(
    `${API_URL}/vapi/trigger-check`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        transcription_id: response.transcription_id
      })
    }
  );
  
  const triggerData = await triggerCheck.json();
  
  if (triggerData.should_trigger) {
    // Show VAPI modal
    setShowVAPIModal(true);
    setVAPIReason(triggerData.reason);
    setVAPISessionId(response.session_id);
  }
};

// VAPI Modal Component
const VAPIModal = () => (
  <Modal visible={showVAPIModal}>
    <View>
      <Text>Arjun wants to talk</Text>
      <Text>{vapiReason}</Text>
      <Button 
        title="Start Call"
        onPress={async () => {
          await vapiService.startSession(
            userId,
            vapiSessionId,
            'initial'
          );
          setShowVAPIModal(false);
        }}
      />
      <Button 
        title="Later"
        onPress={() => setShowVAPIModal(false)}
      />
    </View>
  </Modal>
);
```

#### 4. Environment Variables

**Backend `.env`:**
```bash
# Existing variables...

# VAPI Configuration
VAPI_API_KEY=vapi_your_api_key_here
VAPI_ASSISTANT_ID=asst_xxxxxxxxxxxxx
VAPI_WEBHOOK_URL=https://ba02-32-192-28-123.ngrok-free.app/vapi/webhook
BACKEND_URL=https://ba02-32-192-28-123.ngrok-free.app
```

**Frontend `.env`:**
```bash
EXPO_PUBLIC_VAPI_API_KEY=vapi_your_api_key_here
EXPO_PUBLIC_VAPI_ASSISTANT_ID=asst_xxxxxxxxxxxxx
EXPO_PUBLIC_API_URL=https://ba02-32-192-28-123.ngrok-free.app
```


---

## Summary Checklist

### VAPI Platform Setup

- [ ] Create VAPI account at https://vapi.ai
- [ ] Get API key and add to `.env`
- [ ] Create custom assistant
- [ ] Copy Assistant ID and add to `.env`
- [ ] Configure voice (ElevenLabs - Hindi)
- [ ] Configure transcriber (Deepgram - Hindi)
- [ ] Configure LLM model (Groq - llama-3.3-70b)
- [ ] Set first message in Hindi
- [ ] Set system prompt with Hindi/Hinglish instructions
- [ ] Add Server URL: `https://ba02-32-192-28-123.ngrok-free.app/vapi/session/start`
- [ ] Add webhook URLs (call-start, call-end, message)
- [ ] Set function execution URL: `https://ba02-32-192-28-123.ngrok-free.app/vapi/functions/execute`
- [ ] Add all 10 functions to VAPI dashboard
- [ ] Test assistant in VAPI dashboard

### Backend Integration

- [ ] Verify all endpoints are accessible via ngrok URL
- [ ] Test `/health` endpoint
- [ ] Test `/vapi/functions/definitions` endpoint
- [ ] Test `/vapi/functions/execute` with sample data
- [ ] Test `/vapi/webhook/call-start` webhook
- [ ] Test `/vapi/webhook/call-end` webhook
- [ ] Add VAPI trigger logic to `main.py`
- [ ] Create `vapi_triggers` table in Supabase
- [ ] Test end-to-end audio processing → VAPI trigger

### Frontend Integration

- [ ] Install `@vapi-ai/web` package
- [ ] Create `vapiService.ts`
- [ ] Add VAPI modal to RecordingScreen
- [ ] Add trigger check after audio upload
- [ ] Add environment variables
- [ ] Test VAPI session start from app
- [ ] Test conversation flow
- [ ] Test call end and data updates

### Production Readiness

- [ ] Replace ngrok URL with permanent domain
- [ ] Set up SSL certificate
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging
- [ ] Test with real user data
- [ ] Verify Hindi/Hinglish conversations work
- [ ] Verify all 10 functions work correctly
- [ ] Test error handling
- [ ] Set up rate limiting (if needed)
- [ ] Document for team

---

## Quick Reference

### Key URLs (Update with your ngrok URL)

```
Base URL: https://ba02-32-192-28-123.ngrok-free.app

Health: GET /health
Session Start: POST /vapi/session/start
Function Definitions: GET /vapi/functions/definitions
Function Execute: POST /vapi/functions/execute
Webhook Call Start: POST /vapi/webhook/call-start
Webhook Call End: POST /vapi/webhook/call-end
Webhook Message: POST /vapi/webhook/message
Trigger Check: POST /vapi/trigger-check
Start Session: POST /vapi/start-session
Call History: GET /vapi/call-history
Clarifications: GET /vapi/clarifications
Mood Trend: GET /vapi/mood-trend
```

### 10 Available Functions

1. `get_today_summary` - Today's business data
2. `get_weekly_summary` - Weekly aggregated data
3. `get_best_sellers` - Top-selling items
4. `get_stock_suggestions` - Tomorrow's recommendations
5. `confirm_item` - Confirm uncertain items
6. `get_unconfirmed_items` - List items needing clarification
7. `get_recent_anomalies` - Unusual activities
8. `get_expense_breakdown` - Expense analysis
9. `get_mood_trend` - Mood over time
10. `search_past_records` - Search historical data

---

**Document Version:** 1.0  
**Last Updated:** March 29, 2026  
**Status:** Ready for Implementation  
**Next Steps:** Complete checklist items and test end-to-end

