# VAPI Integration - Complete Implementation

## Overview

VAPI custom voice agent is fully integrated with VoiceTrace AI backend. The agent can access real-time business data, clarify uncertain items, and provide insights through 10 callable functions.

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VoiceTrace AI Pipeline                        │
│                                                                  │
│  Audio Upload → LangGraph Pipeline → Database Storage           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ LangGraph Nodes (backend/graph.py):                      │  │
│  │                                                           │  │
│  │  1. transcribe_node      → Groq Whisper transcription    │  │
│  │  2. guardrail_node       → Safety check                  │  │
│  │  3. sanitize_node        → Clean transcript              │  │
│  │  4. extract_node         → Extract business data         │  │
│  │  5. memory_analysis_node → Analyze importance            │  │
│  │  6. memory_router_node   → Route based on importance     │  │
│  │  7. long_term_memory_node→ Store in Qdrant (if important)│  │
│  │  8. retrieval_node       → Retrieve relevant memories    │  │
│  │  9. decision_node        → Generate final response       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  After Pipeline Completes (backend/main.py):                    │
│  ├─ Store transcription in Supabase                             │
│  ├─ Upload audio to Supabase Storage                            │
│  ├─ Create ledger entry (ledger_service)                        │
│  └─ Check if VAPI should be triggered                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    VAPI Trigger Check
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    VAPI Custom Voice Agent                       │
│                                                                  │
│  START POINT: POST /vapi/session/start                          │
│  ├─ Initialize session with context                             │
│  ├─ Load pending clarifications                                 │
│  ├─ Load unconfirmed items                                      │
│  ├─ Provide function definitions                                │
│  └─ Return system prompt                                        │
│                                                                  │
│  FUNCTION CALLING: POST /vapi/functions/execute                 │
│  ├─ get_today_summary      → Today's business data              │
│  ├─ get_weekly_summary     → Weekly aggregated data             │
│  ├─ get_best_sellers       → Top-selling items                  │
│  ├─ get_stock_suggestions  → Tomorrow's recommendations         │
│  ├─ confirm_item           → Confirm uncertain items            │
│  ├─ get_unconfirmed_items  → List items needing clarification  │
│  ├─ get_recent_anomalies   → Unusual activities                 │
│  ├─ get_expense_breakdown  → Expense analysis                   │
│  ├─ get_mood_trend         → Mood over time                     │
│  └─ search_past_records    → Search historical data             │
│                                                                  │
│  WEBHOOKS: /vapi/webhook/*                                      │
│  ├─ call-start  → Log session start                             │
│  ├─ call-end    → Process clarifications, update database       │
│  └─ message     → Real-time message logging                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## VAPI Start Point

### Endpoint: `POST /vapi/session/start`

**Purpose:** Initialize VAPI session after audio processing completes

**When to Call:**
- After `/process` endpoint completes
- When confidence scores are low (< 0.7)
- When vendor expresses negative sentiment
- When stock-outs are detected

**Request:**
```json
{
  "user_id": "user-uuid",
  "trigger_reason": "3 items need clarification",
  "context_data": {
    "transcription_id": "uuid",
    "session_id": "uuid"
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "vapi-session-1234567890",
  "context": {
    "user_id": "user-uuid",
    "trigger_reason": "3 items need clarification",
    "pending_clarifications": 3,
    "unconfirmed_items": 5,
    "clarifications": [
      {
        "id": "uuid",
        "clarification_type": "item",
        "item_data": {
          "item_name": "something",
          "quantity": null,
          "unit_price": null
        },
        "priority": "high"
      }
    ],
    "unconfirmed": [
      {
        "id": "uuid",
        "name": "केला",
        "quantity": 60,
        "confidence": 0.5
      }
    ]
  },
  "functions": [
    {
      "name": "get_today_summary",
      "description": "Get today's business summary including earnings, expenses, and items sold",
      "parameters": {
        "type": "object",
        "properties": {
          "user_id": {"type": "string", "description": "The vendor's user ID"}
        },
        "required": ["user_id"]
      }
    }
    // ... 9 more functions
  ],
  "system_prompt": "You are a helpful business assistant for street vendors in India...",
  "webhook_url": "https://your-backend.com/vapi/webhook"
}
```

---

## VAPI Function Execution (End Point)

### Endpoint: `POST /vapi/functions/execute`

**Purpose:** Execute functions called by VAPI during conversation

**Request:**
```json
{
  "function_name": "get_today_summary",
  "parameters": {
    "user_id": "user-uuid"
  },
  "user_id": "user-uuid",
  "session_id": "vapi-session-123"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "message": "आज का सारांश (Today's summary)",
    "has_data": true,
    "date": "2026-03-28",
    "total_earnings": 1100,
    "total_expenses": 550,
    "net_profit": 550,
    "items_count": 3,
    "expenses_count": 2,
    "items": [
      {
        "name": "केला",
        "quantity": 60,
        "amount": 300
      },
      {
        "name": "आम",
        "quantity": 20,
        "amount": 800
      }
    ]
  },
  "error": null
}
```

---

## 10 Available Functions

### 1. get_today_summary
**Purpose:** Get today's business data  
**Parameters:** `user_id`  
**Returns:** Earnings, expenses, net profit, items sold today  
**Use Case:** "आज का सारांश बताओ" (Tell me today's summary)

### 2. get_weekly_summary
**Purpose:** Get weekly aggregated data  
**Parameters:** `user_id`  
**Returns:** Weekly totals, averages, top items  
**Use Case:** "इस हफ्ते की कमाई कितनी है?" (What's this week's earnings?)

### 3. get_best_sellers
**Purpose:** Find top-selling items  
**Parameters:** `user_id`, `days` (default: 7), `limit` (default: 5)  
**Returns:** List of best-selling items with revenue  
**Use Case:** "कौन सी चीज़ सबसे ज्यादा बिकती है?" (Which item sells the most?)

### 4. get_stock_suggestions
**Purpose:** Get tomorrow's stock recommendations  
**Parameters:** `user_id`  
**Returns:** Suggested quantities for each item  
**Use Case:** "कल के लिए क्या स्टॉक रखूं?" (What stock should I keep for tomorrow?)

### 5. confirm_item
**Purpose:** Confirm uncertain item details  
**Parameters:** `user_id`, `item_id`, `item_name`, `quantity`, `unit_price`  
**Returns:** Confirmation status  
**Use Case:** "हाँ, 60 केले बेचे 5 रुपये में" (Yes, sold 60 bananas at ₹5 each)

### 6. get_unconfirmed_items
**Purpose:** List items needing clarification  
**Parameters:** `user_id`  
**Returns:** Items with low confidence scores  
**Use Case:** "कौन से आइटम कन्फर्म करने हैं?" (Which items need confirmation?)

### 7. get_recent_anomalies
**Purpose:** Check for unusual activities  
**Parameters:** `user_id`, `limit` (default: 5)  
**Returns:** Recent anomaly alerts  
**Use Case:** "कोई असामान्य गतिविधि है?" (Any unusual activity?)

### 8. get_expense_breakdown
**Purpose:** Analyze expenses by type  
**Parameters:** `user_id`, `days` (default: 7)  
**Returns:** Expense breakdown and trends  
**Use Case:** "खर्च का ब्रेकडाउन दिखाओ" (Show expense breakdown)

### 9. get_mood_trend
**Purpose:** Analyze mood over time  
**Parameters:** `user_id`, `days` (default: 7)  
**Returns:** Mood scores and trend direction  
**Use Case:** "मेरा मूड कैसा रहा?" (How has my mood been?)

### 10. search_past_records
**Purpose:** Search historical data  
**Parameters:** `user_id`, `query`, `days` (default: 30)  
**Returns:** Matching records  
**Use Case:** "पिछले महीने केले की बिक्री दिखाओ" (Show banana sales from last month)

---

## Integration with LangGraph Pipeline

### Flow After Audio Processing

```python
# In backend/main.py after pipeline completes

# 1. Pipeline runs (graph.py)
result = pipeline.invoke(initial_state)

# 2. Store transcription
transcription_id = supabase_service.store_transcription(
    user_id=user_id,
    transcript=result.get("transcript", ""),
    extracted_data=result.get("extracted_data", {}),
    # ... other fields
)

# 3. Upload audio to Supabase Storage
audio_url = audio_storage_service.upload_audio(
    file_path=file_path,
    user_id=user_id,
    session_id=session_id,
)

# 4. Create ledger entry
ledger_entry_id = ledger_service.create_entry_from_transcription(
    user_id=user_id,
    transcription_id=transcription_id,
    extracted_data=result.get("extracted_data", {}),
    audio_url=audio_url,
)

# 5. Check if VAPI should be triggered
should_trigger, reason = vapi_service.should_trigger_call(
    extracted_data=result.get("extracted_data", {}),
    confidence_scores=confidence_scores,
)

# 6. If trigger needed, initialize VAPI session
if should_trigger:
    session_response = requests.post(
        f"{BACKEND_URL}/vapi/session/start",
        json={
            "user_id": user_id,
            "trigger_reason": reason,
            "context_data": {
                "transcription_id": transcription_id,
                "session_id": session_id
            }
        }
    )
    
    # Return session info to frontend
    result["should_trigger_vapi"] = True
    result["vapi_session_id"] = session_response.json()["session_id"]
    result["vapi_trigger_reason"] = reason
```

---

## VAPI Trigger Conditions

VAPI is triggered when:

1. **Low Confidence Items** (confidence < 0.7)
   - Missing item names
   - Missing quantities
   - Missing prices
   - Vague descriptions

2. **Negative Sentiment** (mood_score < 2.5)
   - Vendor expresses frustration
   - Complaints about business
   - Stress indicators

3. **Stock-Out Detection**
   - Items that ran out of stock
   - Potential lost sales
   - Need for better planning

4. **Anomalies Detected**
   - Unusual expense patterns
   - Sudden revenue drops
   - Unexpected changes

---

## Example Conversation Flow

### Scenario: Low Confidence Items

```
1. User uploads 3-min audio
   ↓
2. Pipeline processes audio
   ↓
3. Extraction finds uncertain items:
   - "कुछ फल" (some fruits) - vague
   - Quantity missing
   - Price unclear
   ↓
4. Confidence score: 0.45 (< 0.7)
   ↓
5. VAPI triggered with reason: "3 items need clarification"
   ↓
6. VAPI session starts
   ↓
7. VAPI calls: get_unconfirmed_items()
   Returns: [
     {id: "uuid", name: "कुछ फल", quantity: null, confidence: 0.45}
   ]
   ↓
8. VAPI speaks: "मैंने देखा कि आपने 'कुछ फल' बेचे। कौन से फल थे?"
   (I see you sold 'some fruits'. Which fruits were they?)
   ↓
9. User: "आम थे, 20 आम" (Mangoes, 20 mangoes)
   ↓
10. VAPI: "ठीक है। एक आम की कीमत क्या थी?"
    (Okay. What was the price per mango?)
    ↓
11. User: "40 रुपये" (₹40)
    ↓
12. VAPI calls: confirm_item(
      item_id="uuid",
      item_name="आम",
      quantity=20,
      unit_price=40
    )
    ↓
13. Database updated
    ↓
14. VAPI: "धन्यवाद! 20 आम, ₹40 प्रति आम, कुल ₹800 - सेव हो गया।"
    (Thank you! 20 mangoes, ₹40 each, total ₹800 - saved.)
```

---

## Testing VAPI Integration

### 1. Test Session Initialization

```bash
curl -X POST http://localhost:8000/vapi/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-uuid",
    "trigger_reason": "Testing VAPI integration",
    "context_data": {
      "transcription_id": "test-transcription-uuid",
      "session_id": "test-session-uuid"
    }
  }'
```

### 2. Test Function Definitions

```bash
curl http://localhost:8000/vapi/functions/definitions
```

### 3. Test Function Execution

```bash
curl -X POST http://localhost:8000/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {
      "user_id": "test-user-uuid"
    },
    "user_id": "test-user-uuid",
    "session_id": "test-session"
  }'
```

### 4. Test Batch Execution

```bash
curl -X POST http://localhost:8000/vapi/functions/batch-execute \
  -H "Content-Type: application/json" \
  -d '[
    {
      "function_name": "get_today_summary",
      "parameters": {"user_id": "test-user-uuid"},
      "user_id": "test-user-uuid",
      "session_id": "test-session"
    },
    {
      "function_name": "get_best_sellers",
      "parameters": {"user_id": "test-user-uuid", "days": 7, "limit": 5},
      "user_id": "test-user-uuid",
      "session_id": "test-session"
    }
  ]'
```

---

## Environment Variables

```bash
# Required for VAPI integration
VAPI_API_KEY=your-vapi-api-key
VAPI_ASSISTANT_ID=your-assistant-id
VAPI_WEBHOOK_URL=https://your-backend.com/vapi/webhook
BACKEND_URL=https://your-backend.com

# Supabase (for data access)
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Groq (for LLM)
GROQ_API_KEY=your-groq-api-key
```

---

## Files Involved

### Core Implementation
- `backend/main.py` - Main FastAPI app, pipeline orchestration
- `backend/graph.py` - LangGraph pipeline structure
- `backend/models.py` - Pydantic models

### VAPI Integration
- `backend/routers/vapi.py` - Session initialization, webhooks
- `backend/routers/vapi_functions.py` - 10 callable functions
- `backend/services/vapi_service.py` - VAPI business logic

### Services
- `backend/services/ledger_service.py` - Ledger management
- `backend/services/pattern_service.py` - Pattern detection
- `backend/services/stock_suggestion_service.py` - Stock suggestions
- `backend/services/audio_storage_service.py` - Audio storage

### Documentation
- `VAPI_SETUP_GUIDE.md` - Complete setup guide
- `VAPI_ENDPOINTS_SUMMARY.md` - Quick reference
- `API_DOCUMENTATION.md` - Full API docs

---

## Summary

✅ **Start Point:** `POST /vapi/session/start` - Initialize VAPI with context  
✅ **Function Definitions:** `GET /vapi/functions/definitions` - Get all 10 functions  
✅ **Function Execution:** `POST /vapi/functions/execute` - Execute functions  
✅ **Batch Execution:** `POST /vapi/functions/batch-execute` - Execute multiple functions  
✅ **Webhooks:** `/vapi/webhook/*` - Handle VAPI callbacks  

✅ **10 Functions Implemented** - All return Hindi/Hinglish messages  
✅ **Real-time Data Access** - Functions access ledger, patterns, analytics  
✅ **LangGraph Integration** - VAPI triggered after pipeline completes  
✅ **Database Mapping** - All data from 3-min audio is stored and accessible  

---

**Status:** ✅ COMPLETE  
**Last Updated:** March 29, 2026  
**Version:** 1.0
