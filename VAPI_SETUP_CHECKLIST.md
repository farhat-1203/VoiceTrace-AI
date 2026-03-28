# VAPI Setup Checklist - Quick Reference

## ✅ Step-by-Step Checklist

### 1. Backend Preparation
- [ ] Backend deployed and accessible via HTTPS
- [ ] Test health endpoint: `curl https://your-domain.com/health`
- [ ] Test function definitions: `curl https://your-domain.com/vapi/functions/definitions`
- [ ] Test function execution: `curl -X POST https://your-domain.com/vapi/functions/execute ...`
- [ ] Test webhooks: `curl -X POST https://your-domain.com/vapi/webhook/call-start ...`

### 2. VAPI Dashboard - Create Assistant
- [ ] Go to https://vapi.ai → Assistants → Create New
- [ ] Name: **VoiceTrace Agent (Arjun)**
- [ ] First Message: `"Namaste! Main Arjun hoon. Aaj ka din kaisa raha?"`

### 3. VAPI Dashboard - Configure Model
- [ ] Provider: **Groq**
- [ ] Model: **llama-3.3-70b-versatile**
- [ ] Temperature: **0.3**
- [ ] Max Tokens: **200**

### 4. VAPI Dashboard - Configure Voice
- [ ] Provider: **ElevenLabs**
- [ ] Voice ID: **pNInz6obpgDQGcFmaJgB** (Hindi male warm)
- [ ] Stability: **0.5**
- [ ] Similarity Boost: **0.8**

### 5. VAPI Dashboard - Configure Transcriber
- [ ] Provider: **Deepgram**
- [ ] Model: **nova-2**
- [ ] Language: **hi** (Hindi)
- [ ] Smart Format: **true**

### 6. VAPI Dashboard - Set Webhooks
- [ ] Server URL: `https://your-domain.com/vapi/webhook/call-start`
- [ ] End Call URL: `https://your-domain.com/vapi/webhook/call-end`
- [ ] Message URL: `https://your-domain.com/vapi/webhook/message` (optional)

### 7. VAPI Dashboard - Add Functions
- [ ] Function Execution URL: `https://your-domain.com/vapi/functions/execute`
- [ ] Add function: **get_today_summary**
- [ ] Add function: **get_weekly_summary**
- [ ] Add function: **get_best_sellers**
- [ ] Add function: **get_stock_suggestions**
- [ ] Add function: **confirm_item**
- [ ] Add function: **get_unconfirmed_items**
- [ ] Add function: **get_recent_anomalies**
- [ ] Add function: **get_expense_breakdown**
- [ ] Add function: **get_mood_trend**
- [ ] Add function: **search_past_records**

### 8. VAPI Dashboard - Copy Assistant ID
- [ ] Copy Assistant ID from dashboard
- [ ] Add to `.env`: `VAPI_ASSISTANT_ID=asst_abc123xyz456`
- [ ] Add to `.env`: `VAPI_API_KEY=your-vapi-api-key`

### 9. Test VAPI Integration
- [ ] Test in VAPI dashboard: Click "Test" button
- [ ] Speak: "आज का सारांश बताओ"
- [ ] Verify Arjun responds with real data
- [ ] Check backend logs for function calls
- [ ] Check database for webhook logs

### 10. Frontend Integration
- [ ] Install VAPI SDK: `npm install @vapi-ai/web`
- [ ] Initialize VAPI client with API key
- [ ] Implement session start logic
- [ ] Implement event listeners (call-start, call-end, message)
- [ ] Test end-to-end flow

---

## 🔍 Quick Tests

### Test 1: Function Execution
```bash
curl -X POST https://your-domain.com/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "test-user"},
    "user_id": "test-user",
    "session_id": "test"
  }'
```

### Test 2: Webhook
```bash
curl -X POST https://your-domain.com/vapi/webhook/call-start \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-123",
    "user_id": "test-user",
    "call_type": "test"
  }'
```

### Test 3: Session Start
```bash
curl -X POST https://your-domain.com/vapi/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "trigger_reason": "Testing"
  }'
```

---

## 📋 Function Definitions (Copy-Paste Ready)

### get_today_summary
```json
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
```

### get_weekly_summary
```json
{
  "name": "get_weekly_summary",
  "description": "Get weekly business summary with total earnings, expenses, and top items",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"}
    },
    "required": ["user_id"]
  }
}
```

### get_best_sellers
```json
{
  "name": "get_best_sellers",
  "description": "Get the best-selling items over a period",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"},
      "days": {"type": "integer", "description": "Number of days (default: 7)", "default": 7},
      "limit": {"type": "integer", "description": "Number of items (default: 5)", "default": 5}
    },
    "required": ["user_id"]
  }
}
```

### get_stock_suggestions
```json
{
  "name": "get_stock_suggestions",
  "description": "Get stock suggestions for tomorrow based on sales patterns",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"}
    },
    "required": ["user_id"]
  }
}
```

### confirm_item
```json
{
  "name": "confirm_item",
  "description": "Confirm and update an uncertain item with correct details",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"},
      "item_id": {"type": "string", "description": "The ID of the item to confirm"},
      "item_name": {"type": "string", "description": "Confirmed item name"},
      "quantity": {"type": "number", "description": "Confirmed quantity"},
      "unit_price": {"type": "number", "description": "Confirmed unit price"}
    },
    "required": ["user_id", "item_id", "item_name", "quantity", "unit_price"]
  }
}
```

### get_unconfirmed_items
```json
{
  "name": "get_unconfirmed_items",
  "description": "Get list of items that need clarification (low confidence)",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"}
    },
    "required": ["user_id"]
  }
}
```

### get_recent_anomalies
```json
{
  "name": "get_recent_anomalies",
  "description": "Get recent unusual business activities or alerts",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"},
      "limit": {"type": "integer", "description": "Number of anomalies (default: 5)", "default": 5}
    },
    "required": ["user_id"]
  }
}
```

### get_expense_breakdown
```json
{
  "name": "get_expense_breakdown",
  "description": "Get breakdown of expenses by type for a period",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"},
      "days": {"type": "integer", "description": "Number of days (default: 7)", "default": 7}
    },
    "required": ["user_id"]
  }
}
```

### get_mood_trend
```json
{
  "name": "get_mood_trend",
  "description": "Get vendor's mood trend over time",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"},
      "days": {"type": "integer", "description": "Number of days (default: 7)", "default": 7}
    },
    "required": ["user_id"]
  }
}
```

### search_past_records
```json
{
  "name": "search_past_records",
  "description": "Search past business records by date or item name",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string", "description": "The vendor's user ID"},
      "query": {"type": "string", "description": "Search query (item name or date)"},
      "days": {"type": "integer", "description": "Number of days to search (default: 30)", "default": 30}
    },
    "required": ["user_id", "query"]
  }
}
```

---

## 🎯 System Prompt (Copy-Paste Ready)

```
You are Arjun, a helpful business assistant for street vendors in India.

Personality: Friendly, warm, conversational. Speak in Hindi or Hinglish.

Your job:
- Help vendors understand their business data
- Clarify uncertain information
- Provide insights and recommendations

Guidelines:
- Ask ONE question at a time
- Keep responses short (2-3 sentences max)
- Use functions to fetch real-time data
- Show empathy and encouragement

When clarifying items:
1. Ask for item name if vague
2. Ask for quantity if missing
3. Ask for price if missing
4. Use confirm_item to update

Example:
Vendor: "आज का सारांश बताओ"
You: *calls get_today_summary* "Aaj aapne ₹1100 ki kamai ki. Net profit ₹550 hai. Bahut accha!"
```

---

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| Functions not called | Check function execution URL is HTTPS |
| Webhooks not received | Verify backend is publicly accessible |
| Arjun not speaking Hindi | Set transcriber language to "hi" |
| Responses too long | Reduce max tokens to 150 |
| Empty function results | Verify user has data in database |

---

## 📞 Support URLs

- **Backend Health:** `https://your-domain.com/health`
- **Function Definitions:** `https://your-domain.com/vapi/functions/definitions`
- **Function Execution:** `https://your-domain.com/vapi/functions/execute`
- **Call Start Webhook:** `https://your-domain.com/vapi/webhook/call-start`
- **Call End Webhook:** `https://your-domain.com/vapi/webhook/call-end`

---

**Print this checklist and check off items as you complete them!**

**Last Updated:** March 29, 2026
