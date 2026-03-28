# VAPI Endpoints Summary - Quick Reference

## 🎯 Start Point (Initialize VAPI Session)

```
POST /vapi/session/start
```

**Purpose:** Initialize VAPI session with context and functions

**Request:**
```json
{
  "user_id": "user-uuid",
  "trigger_reason": "3 items need clarification"
}
```

**Returns:**
- Session ID
- Context data (pending clarifications, unconfirmed items)
- Function definitions (10 functions)
- System prompt
- Webhook URL

---

## 📋 Function Definitions (For VAPI Configuration)

```
GET /vapi/functions/definitions
```

**Returns:** All 10 available functions in OpenAI format

---

## ⚡ Function Execution (Called by VAPI)

```
POST /vapi/functions/execute
```

**Purpose:** Execute functions called by VAPI agent

**Request:**
```json
{
  "function_name": "get_today_summary",
  "parameters": {"user_id": "user-uuid"},
  "user_id": "user-uuid",
  "session_id": "vapi-session-123"
}
```

---

## 🔄 Batch Execution

```
POST /vapi/functions/batch-execute
```

**Purpose:** Execute multiple functions at once

---

## 📞 Webhooks (VAPI → Backend)

```
POST /vapi/webhook/call-start    # Session started
POST /vapi/webhook/call-end      # Session ended
POST /vapi/webhook/message       # Each message
```

---

## 🛠️ Available Functions (10 Total)

### Business Data
1. **get_today_summary** - Today's earnings, expenses, items
2. **get_weekly_summary** - Weekly aggregated data
3. **search_past_records** - Search historical data

### Analytics
4. **get_best_sellers** - Top-selling items
5. **get_expense_breakdown** - Expense analysis
6. **get_mood_trend** - Mood over time
7. **get_recent_anomalies** - Unusual activities

### Inventory
8. **get_stock_suggestions** - Tomorrow's stock recommendations

### Clarifications
9. **get_unconfirmed_items** - Items needing clarification
10. **confirm_item** - Confirm uncertain item

---

## 🚀 Integration Flow

```
1. User uploads 3-min audio
   ↓
2. Backend processes → detects trigger
   ↓
3. Call: POST /vapi/session/start
   ↓
4. Frontend starts VAPI with session data
   ↓
5. User talks to VAPI agent
   ↓
6. VAPI calls functions via /vapi/functions/execute
   ↓
7. Backend returns real-time data
   ↓
8. VAPI speaks response in Hindi/Hinglish
   ↓
9. Webhooks notify backend of session events
```

---

## 📝 Example Conversation

```
User: "आज का सारांश बताओ"
  ↓
VAPI calls: get_today_summary(user_id)
  ↓
Backend returns: {earnings: 1100, expenses: 550, profit: 550}
  ↓
VAPI: "आज आपने ₹1100 की कमाई की और ₹550 खर्च किए। शुद्ध लाभ ₹550 है।"

User: "कल के लिए क्या स्टॉक रखूं?"
  ↓
VAPI calls: get_stock_suggestions(user_id)
  ↓
Backend returns: [{item: "केला", quantity: 65, reason: "..."}]
  ↓
VAPI: "कल के लिए 65 केले रखें। आपकी औसत बिक्री 60 है और ट्रेंड बढ़ रहा है।"
```

---

## 🔧 VAPI Dashboard Setup

1. **Create Assistant** with Hindi/English voice
2. **Add System Prompt** (provided in session/start response)
3. **Configure 10 Functions** from /vapi/functions/definitions
4. **Set Function Execution URL:** `https://your-backend.com/vapi/functions/execute`
5. **Set Webhooks:** `/vapi/webhook/*`

---

## ✅ Testing

```bash
# Test session initialization
curl -X POST https://your-backend.com/vapi/session/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "trigger_reason": "Testing"}'

# Test function execution
curl -X POST https://your-backend.com/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "test"},
    "user_id": "test",
    "session_id": "test"
  }'

# Get function definitions
curl https://your-backend.com/vapi/functions/definitions
```

---

## 📊 All Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/vapi/session/start` | POST | Initialize session |
| `/vapi/functions/definitions` | GET | Get function list |
| `/vapi/functions/execute` | POST | Execute function |
| `/vapi/functions/batch-execute` | POST | Execute multiple |
| `/vapi/webhook/call-start` | POST | Session started |
| `/vapi/webhook/call-end` | POST | Session ended |
| `/vapi/webhook/message` | POST | Message received |
| `/vapi/clarifications` | GET | Pending clarifications |
| `/vapi/call-history` | GET | Session history |
| `/vapi/mood-trend` | GET | Mood analysis |
| `/vapi/trigger-check` | POST | Check if trigger needed |

---

**Quick Start:** Call `/vapi/session/start` to get everything VAPI needs!

**Documentation:** See `VAPI_SETUP_GUIDE.md` for detailed setup

**Last Updated:** March 28, 2026
