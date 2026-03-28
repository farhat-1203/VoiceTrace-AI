# VAPI Setup Guide - Complete Integration

## Overview

This guide shows how to integrate VAPI custom voice agent with VoiceTrace AI backend.

---

## API Endpoints

### Base URL
```
https://your-backend-domain.com
```

### 1. Session Initialization (Start Point)

**Endpoint:** `POST /vapi/session/start`

**Purpose:** Initialize a VAPI session with context and function definitions

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
    "clarifications": [...],
    "unconfirmed": [...]
  },
  "functions": [
    {
      "name": "get_today_summary",
      "description": "Get today's business summary",
      "parameters": {...}
    },
    ...
  ],
  "system_prompt": "You are a helpful business assistant...",
  "webhook_url": "https://your-backend.com/vapi/webhook"
}
```

---

### 2. Function Definitions (For VAPI Configuration)

**Endpoint:** `GET /vapi/functions/definitions`

**Purpose:** Get all available functions that VAPI can call

**Response:**
```json
{
  "functions": [
    {
      "name": "get_today_summary",
      "description": "Get today's business summary including earnings, expenses, and items sold",
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
    },
    {
      "name": "get_weekly_summary",
      "description": "Get weekly business summary with total earnings, expenses, and top items",
      "parameters": {...}
    },
    {
      "name": "get_best_sellers",
      "description": "Get the best-selling items over a period",
      "parameters": {...}
    },
    {
      "name": "get_stock_suggestions",
      "description": "Get stock suggestions for tomorrow based on sales patterns",
      "parameters": {...}
    },
    {
      "name": "confirm_item",
      "description": "Confirm and update an uncertain item with correct details",
      "parameters": {...}
    },
    {
      "name": "get_unconfirmed_items",
      "description": "Get list of items that need clarification (low confidence)",
      "parameters": {...}
    },
    {
      "name": "get_recent_anomalies",
      "description": "Get recent unusual business activities or alerts",
      "parameters": {...}
    },
    {
      "name": "get_expense_breakdown",
      "description": "Get breakdown of expenses by type for a period",
      "parameters": {...}
    },
    {
      "name": "get_mood_trend",
      "description": "Get vendor's mood trend over time",
      "parameters": {...}
    },
    {
      "name": "search_past_records",
      "description": "Search past business records by date or item name",
      "parameters": {...}
    }
  ],
  "count": 10
}
```

---

### 3. Function Execution (Called by VAPI)

**Endpoint:** `POST /vapi/functions/execute`

**Purpose:** Execute a function called by VAPI agent

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

### 4. Batch Function Execution

**Endpoint:** `POST /vapi/functions/batch-execute`

**Purpose:** Execute multiple functions at once

**Request:**
```json
[
  {
    "function_name": "get_today_summary",
    "parameters": {"user_id": "user-uuid"},
    "user_id": "user-uuid",
    "session_id": "vapi-session-123"
  },
  {
    "function_name": "get_best_sellers",
    "parameters": {"user_id": "user-uuid", "days": 7, "limit": 5},
    "user_id": "user-uuid",
    "session_id": "vapi-session-123"
  }
]
```

**Response:**
```json
{
  "results": [
    {
      "function": "get_today_summary",
      "success": true,
      "result": {...}
    },
    {
      "function": "get_best_sellers",
      "success": true,
      "result": {...}
    }
  ],
  "total": 2,
  "successful": 2
}
```

---

### 5. Webhooks (VAPI → Backend)

#### Call Start Webhook
**Endpoint:** `POST /vapi/webhook/call-start`

**Request from VAPI:**
```json
{
  "call_id": "vapi-call-123",
  "user_id": "user-uuid",
  "call_type": "clarification",
  "trigger_reason": "3 items need clarification"
}
```

#### Call End Webhook
**Endpoint:** `POST /vapi/webhook/call-end`

**Request from VAPI:**
```json
{
  "call_id": "vapi-call-123",
  "user_id": "user-uuid",
  "duration_seconds": 120,
  "transcript": "Full conversation...",
  "outcome": "completed",
  "clarifications_resolved": [
    {
      "clarification_id": "uuid",
      "resolved_data": {
        "item_name": "केला",
        "quantity": 60,
        "unit_price": 5
      }
    }
  ]
}
```

#### Message Webhook
**Endpoint:** `POST /vapi/webhook/message`

**Request from VAPI:**
```json
{
  "call_id": "vapi-call-123",
  "user_id": "user-uuid",
  "message": "आज का सारांश बताओ",
  "role": "user"
}
```

---

## VAPI Dashboard Configuration

### Step 1: Create Assistant

1. Go to VAPI Dashboard → Assistants
2. Click "Create New Assistant"
3. Configure:
   - **Name:** VoiceTrace Business Assistant
   - **Voice:** Select Hindi/English voice
   - **Model:** GPT-4 or GPT-3.5-turbo

### Step 2: Set System Prompt

```
You are a helpful business assistant for street vendors in India.
Your job is to help vendors understand their business data and clarify uncertain information.

Guidelines:
- Speak in Hindi or Hinglish (mix of Hindi and English)
- Be friendly, warm, and conversational
- Ask one question at a time
- Confirm information before moving to next question
- Use the available functions to fetch real-time data
- Show empathy when vendor seems upset

When clarifying items:
1. Ask for item name if vague
2. Ask for quantity if missing
3. Ask for price if missing
4. Use confirm_item function to update

Example conversation:
Vendor: "आज का सारांश बताओ"
You: *calls get_today_summary* "आज आपने ₹1100 की कमाई की और ₹550 खर्च किए। शुद्ध लाभ ₹550 है।"
```

### Step 3: Configure Functions

Add all 10 functions from `/vapi/functions/definitions`:

1. **get_today_summary**
2. **get_weekly_summary**
3. **get_best_sellers**
4. **get_stock_suggestions**
5. **confirm_item**
6. **get_unconfirmed_items**
7. **get_recent_anomalies**
8. **get_expense_breakdown**
9. **get_mood_trend**
10. **search_past_records**

For each function:
- Copy the function definition from the API response
- Set the execution URL: `https://your-backend.com/vapi/functions/execute`
- Set method: POST

### Step 4: Configure Webhooks

Set webhook URLs:
- **Call Start:** `https://your-backend.com/vapi/webhook/call-start`
- **Call End:** `https://your-backend.com/vapi/webhook/call-end`
- **Message:** `https://your-backend.com/vapi/webhook/message`

### Step 5: Test Configuration

Use VAPI's test interface to:
1. Start a test session
2. Try calling functions: "आज का सारांश बताओ"
3. Verify function responses
4. Check webhook delivery

---

## Integration Flow

### 1. After Audio Processing

```python
# In backend/main.py after pipeline completes

# Check if VAPI should be triggered
should_trigger, reason = vapi_service.should_trigger_call(
    extracted_data=extracted_data,
    confidence_scores=confidence_scores
)

if should_trigger:
    # Initialize VAPI session
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
    
    session_data = session_response.json()
    
    # Return session info to frontend
    result["should_trigger_vapi"] = True
    result["vapi_session_id"] = session_data["session_id"]
    result["vapi_context"] = session_data["context"]
```

### 2. Frontend Integration

```typescript
// In Expo app after audio upload

const response = await uploadAudio(audioFile);

if (response.should_trigger_vapi) {
  // Start VAPI session
  const vapi = new Vapi(VAPI_API_KEY);
  
  await vapi.start({
    assistantId: VAPI_ASSISTANT_ID,
    metadata: {
      userId: currentUser.id,
      sessionId: response.vapi_session_id,
      context: response.vapi_context
    }
  });
  
  // Show VAPI UI
  showVAPIModal({
    sessionId: response.vapi_session_id,
    reason: response.vapi_trigger_reason
  });
}
```

### 3. VAPI Calls Functions

```
User: "आज का सारांश बताओ"
  ↓
VAPI recognizes intent
  ↓
VAPI calls: POST /vapi/functions/execute
  {
    "function_name": "get_today_summary",
    "parameters": {"user_id": "user-uuid"}
  }
  ↓
Backend executes function
  ↓
Returns: {
  "success": true,
  "result": {
    "message": "आज का सारांश",
    "total_earnings": 1100,
    "total_expenses": 550,
    "net_profit": 550
  }
}
  ↓
VAPI speaks: "आज आपने ₹1100 की कमाई की और ₹550 खर्च किए। शुद्ध लाभ ₹550 है।"
```

---

## Available Functions Details

### 1. get_today_summary
**Purpose:** Get today's business data
**Parameters:** `user_id`
**Returns:** Earnings, expenses, items sold today

### 2. get_weekly_summary
**Purpose:** Get weekly aggregated data
**Parameters:** `user_id`
**Returns:** Weekly totals, averages, top items

### 3. get_best_sellers
**Purpose:** Find top-selling items
**Parameters:** `user_id`, `days` (default: 7), `limit` (default: 5)
**Returns:** List of best-selling items with revenue

### 4. get_stock_suggestions
**Purpose:** Get tomorrow's stock recommendations
**Parameters:** `user_id`
**Returns:** Suggested quantities for each item

### 5. confirm_item
**Purpose:** Confirm uncertain item details
**Parameters:** `user_id`, `item_id`, `item_name`, `quantity`, `unit_price`
**Returns:** Confirmation status

### 6. get_unconfirmed_items
**Purpose:** List items needing clarification
**Parameters:** `user_id`
**Returns:** Items with low confidence scores

### 7. get_recent_anomalies
**Purpose:** Check for unusual activities
**Parameters:** `user_id`, `limit` (default: 5)
**Returns:** Recent anomaly alerts

### 8. get_expense_breakdown
**Purpose:** Analyze expenses by type
**Parameters:** `user_id`, `days` (default: 7)
**Returns:** Expense breakdown and trends

### 9. get_mood_trend
**Purpose:** Analyze mood over time
**Parameters:** `user_id`, `days` (default: 7)
**Returns:** Mood scores and trend direction

### 10. search_past_records
**Purpose:** Search historical data
**Parameters:** `user_id`, `query`, `days` (default: 30)
**Returns:** Matching records

---

## Testing

### Test Function Execution

```bash
# Get function definitions
curl https://your-backend.com/vapi/functions/definitions

# Execute a function
curl -X POST https://your-backend.com/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "user-uuid"},
    "user_id": "user-uuid",
    "session_id": "test-session"
  }'
```

### Test Session Initialization

```bash
curl -X POST https://your-backend.com/vapi/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "trigger_reason": "Testing VAPI integration"
  }'
```

---

## Environment Variables

```bash
# Required
VAPI_API_KEY=your-vapi-api-key
VAPI_ASSISTANT_ID=your-assistant-id
VAPI_WEBHOOK_URL=https://your-backend.com/vapi/webhook
BACKEND_URL=https://your-backend.com
```

---

## Troubleshooting

### Functions Not Working

**Check:**
1. Function definitions match VAPI configuration
2. Execution URL is correct
3. Backend is accessible from VAPI servers

**Debug:**
```bash
# Check function definitions
curl https://your-backend.com/vapi/functions/definitions

# Test function execution
curl -X POST https://your-backend.com/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{"function_name": "get_today_summary", "parameters": {"user_id": "test"}, "user_id": "test", "session_id": "test"}'
```

### Webhooks Not Received

**Check:**
1. Webhook URLs configured in VAPI dashboard
2. Backend is publicly accessible
3. Webhook endpoints return 200 OK

**Debug:**
```bash
# Test webhook endpoints
curl -X POST https://your-backend.com/vapi/webhook/call-start \
  -H "Content-Type: application/json" \
  -d '{"call_id": "test", "user_id": "test", "call_type": "test"}'
```

---

## Summary

**Start Point:** `POST /vapi/session/start`  
**Function Definitions:** `GET /vapi/functions/definitions`  
**Function Execution:** `POST /vapi/functions/execute`  
**Webhooks:** `/vapi/webhook/*`

**Total Functions:** 10  
**All functions support Hindi/Hinglish responses**  
**Real-time data access from ledger, patterns, and analytics**

---

**Last Updated:** March 28, 2026  
**Version:** 1.0
