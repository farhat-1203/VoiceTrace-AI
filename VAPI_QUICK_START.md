# VAPI Quick Start - Essential Endpoints

## For VAPI Dashboard Configuration

### 1. Start Point URL (Session Initialization)

```
POST https://your-backend.com/vapi/session/start
```

**Use this to:** Initialize VAPI session with user context and function definitions

**Request Body:**
```json
{
  "user_id": "user-uuid",
  "trigger_reason": "Clarification needed",
  "context_data": {}
}
```

---

### 2. Function Definitions URL

```
GET https://your-backend.com/vapi/functions/definitions
```

**Use this to:** Get all 10 available functions in OpenAI format

**Returns:** Complete function schemas for VAPI configuration

---

### 3. Function Execution URL (End Point)

```
POST https://your-backend.com/vapi/functions/execute
```

**Use this to:** Execute functions called by VAPI during conversation

**Request Body:**
```json
{
  "function_name": "get_today_summary",
  "parameters": {"user_id": "user-uuid"},
  "user_id": "user-uuid",
  "session_id": "vapi-session-id"
}
```

---

### 4. Webhook URLs

**Call Start:**
```
POST https://your-backend.com/vapi/webhook/call-start
```

**Call End:**
```
POST https://your-backend.com/vapi/webhook/call-end
```

**Message:**
```
POST https://your-backend.com/vapi/webhook/message
```

---

## 10 Available Functions

1. **get_today_summary** - Today's business data
2. **get_weekly_summary** - Weekly aggregated data
3. **get_best_sellers** - Top-selling items
4. **get_stock_suggestions** - Tomorrow's recommendations
5. **confirm_item** - Confirm uncertain items
6. **get_unconfirmed_items** - List items needing clarification
7. **get_recent_anomalies** - Unusual activities
8. **get_expense_breakdown** - Expense analysis
9. **get_mood_trend** - Mood over time
10. **search_past_records** - Search historical data

---

## VAPI Dashboard Setup Steps

### Step 1: Create Assistant
- Name: VoiceTrace Business Assistant
- Voice: Hindi/English
- Model: GPT-4 or GPT-3.5-turbo

### Step 2: Set Function Execution URL
```
https://your-backend.com/vapi/functions/execute
```

### Step 3: Import Functions
Get function definitions from:
```
https://your-backend.com/vapi/functions/definitions
```

Copy all 10 function schemas into VAPI dashboard

### Step 4: Configure Webhooks
- Call Start: `https://your-backend.com/vapi/webhook/call-start`
- Call End: `https://your-backend.com/vapi/webhook/call-end`
- Message: `https://your-backend.com/vapi/webhook/message`

### Step 5: Set System Prompt
```
You are a helpful business assistant for street vendors in India.
Speak in Hindi or Hinglish. Be friendly and conversational.
Use the available functions to fetch real-time data.
```

---

## Testing

### Test Function Execution
```bash
curl -X POST https://your-backend.com/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "test-user"},
    "user_id": "test-user",
    "session_id": "test-session"
  }'
```

### Test Session Start
```bash
curl -X POST https://your-backend.com/vapi/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "trigger_reason": "Testing"
  }'
```

---

## Integration Flow

```
User uploads audio
    ↓
LangGraph pipeline processes
    ↓
Data stored in database
    ↓
Check if VAPI should trigger
    ↓
If yes: POST /vapi/session/start
    ↓
VAPI session initialized
    ↓
VAPI calls functions via /vapi/functions/execute
    ↓
Functions return real-time data
    ↓
VAPI speaks to user in Hindi/Hinglish
```

---

## Key URLs Summary

| Purpose | Method | URL |
|---------|--------|-----|
| Session Init | POST | `/vapi/session/start` |
| Get Functions | GET | `/vapi/functions/definitions` |
| Execute Function | POST | `/vapi/functions/execute` |
| Batch Execute | POST | `/vapi/functions/batch-execute` |
| Call Start Hook | POST | `/vapi/webhook/call-start` |
| Call End Hook | POST | `/vapi/webhook/call-end` |
| Message Hook | POST | `/vapi/webhook/message` |

---

**Replace `your-backend.com` with your actual backend domain**

**Status:** ✅ All endpoints implemented and tested  
**Last Updated:** March 29, 2026
