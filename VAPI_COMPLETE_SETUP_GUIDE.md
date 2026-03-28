# VAPI Complete Setup Guide - VoiceTrace AI

## Overview

This guide walks you through setting up VAPI custom voice agent (Arjun) that integrates with your VoiceTrace AI backend to provide real-time voice interactions with vendors in Hindi/Hinglish.

---

## Architecture Flow

### Two Types of VAPI Calls

#### 1. First Call (Always Happens)
```
User completes 3-min audio recording
    ↓
Backend processes via LangGraph pipeline
    ↓
Data stored in database (transcriptions + ledger)
    ↓
Backend ALWAYS triggers VAPI for first call
    ↓
Backend calls: POST /vapi/session/start
    ├─ call_type: "initial"
    ├─ Returns: session_id, context, functions, system_prompt
    └─ Frontend receives trigger signal
    ↓
Frontend starts VAPI session (Arjun)
    ├─ Passes: assistant_id, session_id, user_id
    └─ VAPI agent (Arjun) activates
    ↓
VAPI calls webhook: POST /vapi/webhook/call-start
    └─ Backend logs session start
    ↓
User talks to Arjun in Hindi/Hinglish
    ├─ "आज का सारांश बताओ" (Tell me today's summary)
    ├─ "कौन सी चीज़ सबसे ज्यादा बिकी?" (What sold the most?)
    └─ Arjun clarifies any uncertain items
    ↓
Arjun calls functions via: POST /vapi/functions/execute
    ├─ get_today_summary
    ├─ get_unconfirmed_items
    ├─ confirm_item (if needed)
    └─ ... (other functions as needed)
    ↓
Backend executes functions and returns data
    ↓
Arjun speaks responses in Hindi/Hinglish
    ↓
First call ends
    ↓
VAPI calls webhook: POST /vapi/webhook/call-end
    └─ Backend processes clarifications and updates database
    ↓
Backend analyzes first call data:
    ├─ Check for anomalies
    ├─ Analyze mood/sentiment
    ├─ Detect stock-outs
    └─ Calculate confidence scores
```

#### 2. Follow-up Calls (Conditional - Only if Issues Detected)
```
After first call ends:
    ↓
Backend checks for triggers:
    ├─ Negative sentiment detected (mood_score < 2.5)
    ├─ Anomalies found (unusual expenses/revenue)
    ├─ Stock-outs detected (items ran out)
    └─ Low confidence items still unresolved (< 0.7)
    ↓
If ANY trigger detected:
    ↓
Backend schedules follow-up call (after 5 minutes)
    ↓
Backend calls: POST /vapi/session/start
    ├─ call_type: "follow_up"
    ├─ trigger_reason: "negative_sentiment" | "anomaly" | "stock_out"
    └─ Returns: session_id, context, specific_issue_data
    ↓
Frontend shows notification:
    "Arjun wants to talk about something important"
    ↓
User accepts → VAPI session starts
    ↓
Arjun addresses specific issue:
    ├─ Negative mood: "Aaj thoda upset lag rahe ho. Kya hua?"
    ├─ Anomaly: "Aaj ke expenses bahut zyada hain. Kuch special hua?"
    ├─ Stock-out: "Kele khatam ho gaye the. Kal zyada stock rakhein?"
    └─ Unconfirmed items: "Kuch items abhi bhi confirm nahi hue..."
    ↓
Arjun uses targeted functions:
    ├─ get_mood_trend (for sentiment issues)
    ├─ get_recent_anomalies (for unusual patterns)
    ├─ get_stock_suggestions (for stock-outs)
    └─ get_unconfirmed_items (for clarifications)
    ↓
Issue resolved → Call ends
    ↓
Backend marks issue as resolved
```

---

## Prerequisites

1. **VAPI Account** - Sign up at https://vapi.ai
2. **Backend Deployed** - Your VoiceTrace AI backend running on EC2
3. **Public URL** - Backend accessible via HTTPS (use ngrok for testing)
4. **Environment Variables** - `.env` file configured

---

## Part 1: Backend Configuration

### Step 1: Verify Backend Endpoints

Ensure these endpoints are working:

```bash
# Health check
curl https://your-domain.com/health

# Function definitions
curl https://your-domain.com/vapi/functions/definitions

# Test function execution
curl -X POST https://your-domain.com/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "test-user"},
    "user_id": "test-user",
    "session_id": "test-session"
  }'
```

### Step 2: Configure Environment Variables

Add to `.env`:

```bash
# VAPI Configuration
VAPI_API_KEY=your-vapi-api-key-here
VAPI_ASSISTANT_ID=your-assistant-id-here
VAPI_WEBHOOK_URL=https://your-domain.com/vapi/webhook

# Backend URL (must be HTTPS for VAPI webhooks)
BACKEND_URL=https://your-domain.com
```

### Step 3: Test Webhook Endpoints

```bash
# Test call-start webhook
curl -X POST https://your-domain.com/vapi/webhook/call-start \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-call-123",
    "user_id": "test-user",
    "call_type": "clarification",
    "trigger_reason": "Testing webhook"
  }'

# Expected response:
# {"success": true, "log_id": "uuid", "message": "Call start logged"}
```

---

## Part 2: Understanding the Two-Call System

### Why Two Types of Calls?

**Initial Call (Always)**
- Happens immediately after audio processing
- General conversation about business
- Clarifies basic uncertainties
- Establishes baseline data

**Follow-up Call (Conditional)**
- Only triggered if issues detected during/after initial call
- Targeted conversation about specific problems
- Proactive support for vendor
- Prevents issues from escalating

### Call Type Comparison

| Aspect | Initial Call | Follow-up Call |
|--------|-------------|----------------|
| **Trigger** | Always after audio upload | Only if issues detected |
| **Timing** | Immediate | 5 minutes after initial call |
| **Purpose** | General business discussion | Address specific issues |
| **Tone** | Friendly, informative | Empathetic, problem-solving |
| **Functions Used** | All 10 functions | Targeted functions |
| **Duration** | 2-5 minutes | 1-3 minutes |
| **User Action** | Automatic | User must accept |

### Initial Call Flow

```
1. User uploads 3-min audio
2. Backend processes → stores data
3. Frontend AUTOMATICALLY starts VAPI
4. Arjun greets: "Namaste! Aaj ka din kaisa raha?"
5. User talks about business
6. Arjun asks about summary, best sellers, etc.
7. Arjun clarifies any uncertain items
8. Call ends naturally
9. Backend analyzes call data
```

### Follow-up Call Triggers

After initial call ends, backend checks:

**1. Negative Sentiment (mood_score < 2.5)**
```python
# Backend detects negative mood
if mood_score < 2.5:
    trigger_follow_up(
        reason='negative_sentiment',
        message='Arjun noticed you seem upset',
        delay=300  # 5 minutes
    )
```

**2. Anomalies Detected**
```python
# Backend finds unusual patterns
if anomalies_found:
    trigger_follow_up(
        reason='anomaly',
        message='Unusual activity in your business',
        delay=300
    )
```

**3. Stock-outs Detected**
```python
# Backend detects items ran out
if stock_outs_found:
    trigger_follow_up(
        reason='stock_out',
        message='Some items ran out today',
        delay=300
    )
```

**4. Unconfirmed Items Remaining**
```python
# Backend finds unresolved uncertainties
if unconfirmed_items_count > 0:
    trigger_follow_up(
        reason='unconfirmed_items',
        message='Need to clarify some items',
        delay=300
    )
```

### Follow-up Call Flow

```
1. Initial call ends
2. Backend analyzes data (30 seconds)
3. Issue detected → schedule follow-up
4. Wait 5 minutes (give vendor time)
5. Frontend shows notification:
   "Arjun wants to talk about something"
6. User clicks "Call Arjun"
7. VAPI session starts with specific context
8. Arjun addresses the specific issue
9. Issue resolved → call ends
10. Backend marks issue as resolved
```

### System Prompt Differences

**Initial Call System Prompt:**
```
You are Arjun, helping vendors understand their daily business.

Focus on:
- Greeting warmly
- Asking about their day
- Providing business summary
- Clarifying uncertain items
- Answering general questions

Keep it conversational and friendly.
```

**Follow-up Call System Prompt (Negative Sentiment):**
```
You are Arjun, following up because the vendor seemed upset.

Focus on:
- Showing empathy: "Aaj thoda upset lag rahe ho"
- Asking what happened: "Kya hua? Kuch problem hai?"
- Listening actively
- Offering support
- Checking mood trend

Be extra caring and supportive.
```

**Follow-up Call System Prompt (Anomaly):**
```
You are Arjun, following up about unusual business activity.

Focus on:
- Mentioning the anomaly: "Aaj ke expenses bahut zyada hain"
- Asking for explanation: "Kuch special hua?"
- Understanding the reason
- Offering insights
- Suggesting actions

Be curious but not alarming.
```

**Follow-up Call System Prompt (Stock-out):**
```
You are Arjun, following up about stock issues.

Focus on:
- Mentioning stock-out: "Kele khatam ho gaye the"
- Asking about impact: "Kitne customers ko mana karna pada?"
- Providing suggestions: "Kal zyada stock rakhein?"
- Offering recommendations

Be helpful and proactive.
```

---

## Part 3: VAPI Dashboard Setup

### Step 1: Create Assistant

1. Go to VAPI Dashboard → **Assistants**
2. Click **"Create New Assistant"**
3. Configure:

```yaml
Name: VoiceTrace Agent (Arjun)

First Message: 
  "Namaste! Main Arjun hoon. Aaj ka din kaisa raha? Kya main aapki koi madad kar sakta hoon?"
  (Hello! I'm Arjun. How was your day? Can I help you with anything?)

Voice:
  Provider: ElevenLabs
  Voice ID: pNInz6obpgDQGcFmaJgB (Hindi male warm)
  Stability: 0.5
  Similarity Boost: 0.8
  Speed: 1.0

Model:
  Provider: Groq
  Model: llama-3.3-70b-versatile
  Temperature: 0.3
  Max Tokens: 200

Transcriber:
  Provider: Deepgram
  Model: nova-2
  Language: hi (Hindi)
  Smart Format: true
  Punctuate: true
```

### Step 2: Configure System Prompt

**IMPORTANT:** The system prompt is dynamically injected via `/vapi/session/start`, but you can set a fallback:

```
You are Arjun, a helpful business assistant for street vendors in India.

Your personality:
- Friendly, warm, and conversational
- Speak in Hindi or Hinglish (mix of Hindi and English)
- Use simple language, avoid complex terms
- Show empathy and understanding
- Be patient and encouraging

Your job:
- Help vendors understand their business data
- Clarify uncertain information from audio recordings
- Provide insights and recommendations
- Answer questions about sales, expenses, and patterns

Guidelines:
- Ask ONE question at a time
- Confirm information before moving to next question
- Use the available functions to fetch real-time data
- Keep responses short (2-3 sentences max)
- Show empathy when vendor seems upset or stressed

When clarifying items:
1. Ask for item name if vague or missing
2. Ask for quantity if not clear
3. Ask for price if missing
4. Use confirm_item function to update database

Example conversation:
Vendor: "आज का सारांश बताओ"
You: *calls get_today_summary* "Aaj aapne ₹1100 ki kamai ki aur ₹550 kharch kiye. Net profit ₹550 hai. Kya aur kuch jaanna chahenge?"

Vendor: "कौन सी चीज़ सबसे ज्यादा बिकी?"
You: *calls get_best_sellers* "Is hafte kele sabse zyada bike - 420 kele, ₹2100 ki kamai. Bahut accha!"

Vendor: "कल के लिए क्या स्टॉक रखूं?"
You: *calls get_stock_suggestions* "Kal ke liye main suggest karta hoon: 65 kele, 25 aam, aur 40 seb. Ye aapke sales pattern ke basis par hai."

Remember:
- Always use functions to get accurate data
- Never make up numbers or information
- If you don't know something, say so politely
- Celebrate vendor's successes
- Offer encouragement during tough times
```

### Step 3: Configure Server URLs (Webhooks)

In VAPI Dashboard → Assistant Settings → **Server URLs**:

```yaml
Server URL (Call Start):
  https://your-domain.com/vapi/webhook/call-start
  
End Call URL:
  https://your-domain.com/vapi/webhook/call-end
  
Message URL (Optional):
  https://your-domain.com/vapi/webhook/message
```

**Important:** URLs must be HTTPS. For testing, use ngrok:
```bash
ngrok http 8000
# Use the HTTPS URL: https://abc123.ngrok.io
```

### Step 4: Configure Functions

In VAPI Dashboard → Assistant Settings → **Functions**:

#### Function Execution URL
```
https://your-domain.com/vapi/functions/execute
```

#### Add All 10 Functions

**Function 1: get_today_summary**
```json
{
  "name": "get_today_summary",
  "description": "Get today's business summary including total earnings, expenses, net profit, and items sold. Use this when vendor asks about today's performance.",
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

**Function 2: get_weekly_summary**
```json
{
  "name": "get_weekly_summary",
  "description": "Get weekly business summary with total earnings, expenses, net profit, average daily earnings, and top-selling items. Use this when vendor asks about this week's performance.",
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

**Function 3: get_best_sellers**
```json
{
  "name": "get_best_sellers",
  "description": "Get the best-selling items over a specified period. Shows which items generate the most revenue. Use this when vendor asks what sells the most.",
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

**Function 4: get_stock_suggestions**
```json
{
  "name": "get_stock_suggestions",
  "description": "Get stock suggestions for tomorrow based on sales patterns and trends. Use this when vendor asks what to stock for tomorrow.",
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

**Function 5: confirm_item**
```json
{
  "name": "confirm_item",
  "description": "Confirm and update an uncertain item with correct details. Use this after vendor provides clarification for a vague or uncertain item.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      },
      "item_id": {
        "type": "string",
        "description": "The ID of the item to confirm"
      },
      "item_name": {
        "type": "string",
        "description": "Confirmed item name"
      },
      "quantity": {
        "type": "number",
        "description": "Confirmed quantity"
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

**Function 6: get_unconfirmed_items**
```json
{
  "name": "get_unconfirmed_items",
  "description": "Get list of items that need clarification due to low confidence scores. Use this to find out what needs to be confirmed with the vendor.",
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

**Function 7: get_recent_anomalies**
```json
{
  "name": "get_recent_anomalies",
  "description": "Get recent unusual business activities or alerts like sudden expense spikes or revenue drops. Use this when vendor asks if anything unusual happened.",
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

**Function 8: get_expense_breakdown**
```json
{
  "name": "get_expense_breakdown",
  "description": "Get breakdown of expenses by type (raw materials, transport, rent, etc.) for a specified period. Use this when vendor asks about expenses.",
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

**Function 9: get_mood_trend**
```json
{
  "name": "get_mood_trend",
  "description": "Get vendor's mood trend over time based on sentiment analysis of their recordings. Use this to understand vendor's emotional state.",
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

**Function 10: search_past_records**
```json
{
  "name": "search_past_records",
  "description": "Search past business records by date or item name. Use this when vendor asks about historical data or specific items from the past.",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "description": "The vendor's user ID"
      },
      "query": {
        "type": "string",
        "description": "Search query (item name or date)"
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

### Step 5: Get Assistant ID

1. After creating the assistant, copy the **Assistant ID** from the dashboard
2. It looks like: `asst_abc123xyz456`
3. Add to your `.env` file:

```bash
VAPI_ASSISTANT_ID=asst_abc123xyz456
```

---

## Part 3: Frontend Integration

### Step 1: Install VAPI SDK

In your Expo app or web frontend:

```bash
npm install @vapi-ai/web
```

### Step 2: Initialize VAPI Client

```typescript
import Vapi from '@vapi-ai/web';

const vapi = new Vapi(process.env.VAPI_API_KEY);
```

### Step 3: Start VAPI Session

#### For Initial Call (Always After Audio Processing)

```typescript
// After uploading audio
const response = await uploadAudio(audioFile);

// ALWAYS start initial VAPI call
await vapi.start({
  assistantId: process.env.VAPI_ASSISTANT_ID,
  metadata: {
    userId: currentUser.id,
    sessionId: response.session_id,
    callType: 'initial',
    transcriptionId: response.transcription_id
  }
});

// Show VAPI UI
showVAPIModal({
  title: 'Talk to Arjun',
  message: 'Arjun is ready to discuss your business',
  callType: 'initial'
});
```

#### For Follow-up Call (Only if Issues Detected)

```typescript
// Listen for follow-up trigger from backend
socket.on('vapi_follow_up_needed', (data) => {
  // Show notification
  showNotification({
    title: 'Arjun wants to talk',
    message: getFollowUpMessage(data.trigger_reason),
    action: 'Call Arjun',
    onAccept: () => startFollowUpCall(data)
  });
});

async function startFollowUpCall(data) {
  await vapi.start({
    assistantId: process.env.VAPI_ASSISTANT_ID,
    metadata: {
      userId: currentUser.id,
      sessionId: data.session_id,
      callType: 'follow_up',
      triggerReason: data.trigger_reason,
      issueData: data.issue_data
    }
  });
  
  showVAPIModal({
    title: getFollowUpTitle(data.trigger_reason),
    message: data.message,
    callType: 'follow_up'
  });
}

function getFollowUpMessage(reason) {
  const messages = {
    'negative_sentiment': 'Arjun noticed you seem upset. Want to talk?',
    'anomaly': 'Arjun found something unusual in your business data',
    'stock_out': 'Arjun has suggestions about your stock',
    'unconfirmed_items': 'Arjun needs to clarify some items'
  };
  return messages[reason] || 'Arjun wants to discuss something';
}

function getFollowUpTitle(reason) {
  const titles = {
    'negative_sentiment': 'How are you feeling?',
    'anomaly': 'Unusual Activity Detected',
    'stock_out': 'Stock Recommendations',
    'unconfirmed_items': 'Need Clarification'
  };
  return titles[reason] || 'Follow-up Call';
}
```

### Step 4: Handle VAPI Events

```typescript
// Listen for call start
vapi.on('call-start', () => {
  console.log('VAPI call started');
  setCallStatus('active');
  
  // Track call type
  const callType = getCurrentCallType(); // 'initial' or 'follow_up'
  trackCallStart(callType);
});

// Listen for call end
vapi.on('call-end', () => {
  console.log('VAPI call ended');
  setCallStatus('ended');
  
  const callType = getCurrentCallType();
  
  if (callType === 'initial') {
    // After initial call, backend will analyze and may trigger follow-up
    console.log('Initial call ended. Waiting for follow-up trigger...');
    
    // Refresh data to show updated items
    refreshLedgerData();
    
    // Show completion message
    showMessage('Call completed! Arjun may call back if needed.');
  } else {
    // Follow-up call ended
    console.log('Follow-up call ended. Issue resolved.');
    showMessage('Issue resolved! Thank you for talking to Arjun.');
    refreshLedgerData();
  }
});

// Listen for messages
vapi.on('message', (message) => {
  console.log('Message:', message);
  addMessageToChat(message);
  
  // Detect if Arjun is addressing specific issues
  if (message.role === 'assistant') {
    detectIssueResolution(message.content);
  }
});

// Listen for function calls
vapi.on('function-call', (functionCall) => {
  console.log('Function called:', functionCall.name);
  showFunctionCallIndicator(functionCall.name);
  
  // Track which functions are being used
  trackFunctionUsage(functionCall.name, getCurrentCallType());
});

// Listen for errors
vapi.on('error', (error) => {
  console.error('VAPI error:', error);
  showErrorMessage(error.message);
  
  // Retry logic for initial call
  if (getCurrentCallType() === 'initial' && retryCount < 3) {
    setTimeout(() => retryVAPICall(), 5000);
  }
});

// Helper functions
function getCurrentCallType() {
  return sessionStorage.getItem('current_call_type') || 'initial';
}

function detectIssueResolution(message) {
  // Detect if specific issues are being resolved
  const resolutionKeywords = {
    'negative_sentiment': ['better', 'accha', 'theek'],
    'anomaly': ['samajh', 'clear', 'resolved'],
    'stock_out': ['stock', 'rakhenge', 'order'],
    'unconfirmed_items': ['confirm', 'save', 'update']
  };
  
  // Check if issue is being addressed
  const currentIssue = sessionStorage.getItem('current_issue');
  if (currentIssue && resolutionKeywords[currentIssue]) {
    const keywords = resolutionKeywords[currentIssue];
    const isResolved = keywords.some(kw => message.toLowerCase().includes(kw));
    
    if (isResolved) {
      console.log(`Issue ${currentIssue} appears to be resolved`);
      markIssueAsResolved(currentIssue);
    }
  }
}
```

---

## Part 4: Testing

### Test 1: Backend Function Execution

```bash
# Test get_today_summary
curl -X POST https://your-domain.com/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "test-user-uuid"},
    "user_id": "test-user-uuid",
    "session_id": "test-session"
  }'

# Expected response:
{
  "success": true,
  "result": {
    "message": "आज का सारांश (Today's summary)",
    "has_data": true,
    "total_earnings": 1100,
    "total_expenses": 550,
    "net_profit": 550
  }
}
```

### Test 2: Session Initialization

```bash
curl -X POST https://your-domain.com/vapi/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-uuid",
    "trigger_reason": "Testing VAPI integration"
  }'

# Expected response:
{
  "success": true,
  "session_id": "vapi-session-123",
  "context": {...},
  "functions": [...],
  "system_prompt": "..."
}
```

### Test 3: VAPI Dashboard Test

1. Go to VAPI Dashboard → Your Assistant
2. Click **"Test"** button
3. Speak: "आज का सारांश बताओ" (Tell me today's summary)
4. Arjun should:
   - Call `get_today_summary` function
   - Receive data from your backend
   - Speak the response in Hindi/Hinglish

### Test 4: End-to-End Test

1. Upload 3-minute audio via frontend
2. Wait for processing to complete
3. If VAPI triggers, modal should appear
4. Click to start voice call with Arjun
5. Ask: "आज कितनी कमाई हुई?" (How much did I earn today?)
6. Arjun should respond with actual data
7. End call
8. Check database - clarifications should be saved

---

## Part 6: Conversation Examples

### Initial Call Examples

#### Example 1: Daily Summary (Initial Call)

```
[Initial call starts automatically after audio upload]

Arjun: "Namaste! Main Arjun hoon. Aaj ka din kaisa raha?"
       (Hello! I'm Arjun. How was your day?)

Vendor: "Theek tha. Aaj ka saarانش bataओ"
        (It was okay. Tell me today's summary)

Arjun: *calls get_today_summary(user_id)*
       "Aaj aapne ₹1100 ki kamai ki aur ₹550 kharch kiye. 
        Net profit ₹550 hai. Bahut accha!"
        (Today you earned ₹1100 and spent ₹550. Net profit is ₹550. Very good!)

Vendor: "Kaunsi cheez sabse zyada biki?"
        (Which item sold the most?)

Arjun: *calls get_best_sellers(user_id, days=7, limit=3)*
       "Is hafte kele sabse zyada bike - 420 kele, ₹2100 ki kamai. 
        Uske baad aam aur seb."
        (This week bananas sold the most - 420 bananas, ₹2100 revenue. 
         After that mangoes and apples.)

Vendor: "Theek hai, dhanyavaad"
        (Okay, thank you)

Arjun: "Koi aur sawal? Kal ke liye stock suggestion chahiye?"
       (Any other questions? Want stock suggestions for tomorrow?)

Vendor: "Nahi, bas itna hi"
        (No, that's all)

Arjun: "Theek hai! Kal milte hain. Accha din ho!"
       (Okay! See you tomorrow. Have a good day!)

[Call ends. Backend analyzes data for follow-up triggers]
```

#### Example 2: Item Clarification (Initial Call)

```
Arjun: "Namaste! Aaj ka business kaisa raha?"
       (Hello! How was business today?)

Vendor: "Accha tha"
        (It was good)

Arjun: *calls get_unconfirmed_items(user_id)*
       "Ek baat confirm karni hai. Aapne 'kuch fal' bola tha. 
        Kaunse fal the exactly?"
        (Need to confirm one thing. You said 'some fruits'. 
         Which fruits exactly?)

Vendor: "Aam the, 20 aam"
        (Mangoes, 20 mangoes)

Arjun: "Theek hai. Ek aam ki keemat kya thi?"
       (Okay. What was the price per mango?)

Vendor: "40 rupaye"
        (40 rupees)

Arjun: *calls confirm_item(user_id, item_id, "आम", 20, 40)*
       "Perfect! 20 aam, ₹40 per piece, total ₹800. Save ho gaya!"
       (Perfect! 20 mangoes, ₹40 per piece, total ₹800. Saved!)

Vendor: "Haan, sahi hai"
        (Yes, that's correct)

Arjun: "Koi aur item confirm karna hai?"
       (Any other items to confirm?)

Vendor: "Nahi, bas itna"
        (No, that's all)

[Call ends normally]
```

### Follow-up Call Examples

#### Example 3: Negative Sentiment Follow-up

```
[5 minutes after initial call]
[Notification: "Arjun noticed you seem upset. Want to talk?"]
[User accepts call]

Arjun: "Hello! Aaj thoda upset lag rahe the. Sab theek hai?"
       (Hello! You seemed a bit upset today. Is everything okay?)

Vendor: "Haan, aaj bahut kam kamai hui"
        (Yes, today's earnings were very low)

Arjun: *calls get_mood_trend(user_id, days=7)*
       "Main samajh sakta hoon. Pichle hafte se aapka mood thoda down hai. 
        Lekin dekho, is hafte average ₹1000 per day hai. Aaj thoda kam tha 
        par kal better hoga."
        (I understand. Your mood has been a bit down since last week. 
         But look, this week's average is ₹1000 per day. Today was a bit low 
         but tomorrow will be better.)

Vendor: "Haan, shayad"
        (Yes, maybe)

Arjun: *calls get_stock_suggestions(user_id)*
       "Kal ke liye main suggest karta hoon - kele aur aam zyada rakhna. 
        Weekend hai, demand badhegi. Positive socho!"
        (For tomorrow I suggest - keep more bananas and mangoes. 
         It's weekend, demand will increase. Think positive!)

Vendor: "Theek hai, try karunga"
        (Okay, I'll try)

Arjun: "Bilkul! Aur koi problem ho toh mujhe batana. Main hoon na!"
       (Absolutely! And if there's any problem, tell me. I'm here!)

[Call ends. Backend marks sentiment issue as addressed]
```

#### Example 4: Anomaly Detection Follow-up

```
[Notification: "Arjun found something unusual in your business data"]
[User accepts call]

Arjun: "Hello! Aaj ke expenses dekhe maine. ₹1200 hai, usually ₹500 hote hain. 
        Kuch special hua?"
        (Hello! I saw today's expenses. ₹1200, usually it's ₹500. 
         Something special happened?)

Vendor: "Haan, aaj transport ka truck hire kiya tha"
        (Yes, today I hired a transport truck)

Arjun: *calls get_recent_anomalies(user_id, limit=3)*
       "Achha! Samajh gaya. Toh ye one-time expense hai?"
       (Oh! I understand. So this is a one-time expense?)

Vendor: "Haan, har mahine ek baar hota hai"
        (Yes, it happens once a month)

Arjun: "Theek hai. Toh main isko normal mark kar deta hoon. 
        Next month reminder de dunga."
        (Okay. So I'll mark this as normal. 
         I'll remind you next month.)

Vendor: "Haan, accha hai"
        (Yes, that's good)

Arjun: "Koi aur unusual activity nahi hai. Sab normal hai!"
       (No other unusual activity. Everything is normal!)

[Call ends. Backend marks anomaly as explained]
```

#### Example 5: Stock-out Follow-up

```
[Notification: "Arjun has suggestions about your stock"]
[User accepts call]

Arjun: "Hello! Dekha maine aaj kele khatam ho gaye the. 
        Kitne customers ko mana karna pada?"
        (Hello! I saw bananas ran out today. 
         How many customers did you have to turn away?)

Vendor: "4-5 customers"
        (4-5 customers)

Arjun: *calls get_stock_suggestions(user_id)*
       "Toh lagbhag ₹200-250 ka loss hua. Kal ke liye main suggest karta hoon 
        70 kele rakhna instead of 60. Weekend hai, demand zyada hogi."
        (So approximately ₹200-250 loss. For tomorrow I suggest 
         keeping 70 bananas instead of 60. It's weekend, demand will be higher.)

Vendor: "Haan, theek hai. 70 rakhenge"
        (Yes, okay. Will keep 70)

Arjun: "Perfect! Aur aam bhi 5 extra rakh lena. Pattern dekh ke lag raha hai 
        demand badh rahi hai."
        (Perfect! And keep 5 extra mangoes too. Looking at the pattern, 
         demand seems to be increasing.)

Vendor: "Okay, kar dunga"
        (Okay, will do)

Arjun: "Bahut accha! Kal ka business accha hoga!"
       (Very good! Tomorrow's business will be good!)

[Call ends. Backend marks stock-out issue as resolved]
```

#### Example 6: Unconfirmed Items Follow-up

```
[Notification: "Arjun needs to clarify some items"]
[User accepts call]

Arjun: "Hello! Kuch items abhi bhi confirm nahi hue hain. 
        2 minute doge?"
        (Hello! Some items are still not confirmed. 
         Can you give 2 minutes?)

Vendor: "Haan, bolo"
        (Yes, tell me)

Arjun: *calls get_unconfirmed_items(user_id)*
       "Pehla item - 'sabzi'. Kaunsi sabzi thi?"
       (First item - 'vegetables'. Which vegetables?)

Vendor: "Aloo aur pyaaz"
        (Potatoes and onions)

Arjun: "Kitne kilo?"
       (How many kilos?)

Vendor: "Aloo 10 kilo, pyaaz 5 kilo"
        (Potatoes 10 kg, onions 5 kg)

Arjun: "Rate kya tha?"
       (What was the rate?)

Vendor: "Aloo ₹30 per kilo, pyaaz ₹40 per kilo"
        (Potatoes ₹30 per kg, onions ₹40 per kg)

Arjun: *calls confirm_item for both items*
       "Perfect! Aloo ₹300 aur pyaaz ₹200, total ₹500. Save ho gaya!"
       (Perfect! Potatoes ₹300 and onions ₹200, total ₹500. Saved!)

Vendor: "Haan, sahi hai"
        (Yes, that's correct)

Arjun: "Bas ek aur item hai. Baad mein kar lenge?"
       (Just one more item. Should we do it later?)

Vendor: "Nahi, abhi kar lete hain"
        (No, let's do it now)

[Continues until all items confirmed]
[Call ends. Backend marks all items as confirmed]
```

---

## Part 6: Troubleshooting

### Issue 1: Functions Not Being Called

**Check:**
1. Function execution URL is correct in VAPI dashboard
2. Backend is accessible via HTTPS
3. Function definitions match exactly (names, parameters)

**Debug:**
```bash
# Test function execution directly
curl -X POST https://your-domain.com/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_today_summary",
    "parameters": {"user_id": "test"},
    "user_id": "test",
    "session_id": "test"
  }'
```

### Issue 2: Webhooks Not Received

**Check:**
1. Webhook URLs are HTTPS (not HTTP)
2. Backend is publicly accessible
3. Firewall/security group allows incoming connections

**Debug:**
```bash
# Test webhook endpoint
curl -X POST https://your-domain.com/vapi/webhook/call-start \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test",
    "user_id": "test",
    "call_type": "test"
  }'
```

### Issue 3: Arjun Not Speaking Hindi

**Check:**
1. Transcriber language is set to "hi" (Hindi)
2. Voice is Hindi-capable (ElevenLabs voice ID correct)
3. System prompt includes Hindi/Hinglish instructions

### Issue 4: Responses Too Long

**Adjust:**
- Max Tokens: 200 → 150
- Temperature: 0.3 → 0.2
- Add to system prompt: "Keep responses under 2 sentences"

### Issue 5: Function Returns Empty Data

**Check:**
1. User has data in database
2. user_id is correct
3. Date range is appropriate

**Debug:**
```bash
# Check if user has ledger entries
curl https://your-domain.com/ledger/entries?start_date=2026-03-01&end_date=2026-03-31 \
  -H "Authorization: Bearer USER_TOKEN"
```

---

## Part 7: Production Checklist

### Before Going Live

- [ ] Backend deployed with HTTPS
- [ ] All 10 functions tested individually
- [ ] Webhooks tested and logging correctly
- [ ] VAPI assistant configured with all functions
- [ ] System prompt optimized for Hindi/Hinglish
- [ ] Voice tested and sounds natural
- [ ] Transcriber accurately recognizes Hindi
- [ ] Frontend integration tested end-to-end
- [ ] Error handling implemented
- [ ] Logging and monitoring set up
- [ ] Rate limiting configured (if needed)
- [ ] Security group/firewall rules configured
- [ ] SSL certificate valid and not expiring soon
- [ ] Environment variables set correctly
- [ ] Database has sample data for testing
- [ ] User authentication working

### Monitoring

```bash
# Check VAPI call logs
docker compose logs backend | grep "VAPI"

# Check function execution logs
docker compose logs backend | grep "function call"

# Check webhook logs
docker compose logs backend | grep "webhook"

# Monitor database for clarifications
psql -c "SELECT * FROM pending_clarifications WHERE status = 'pending';"
```

---

## Part 8: Cost Estimation

### VAPI Costs (Approximate)

**For 100 users, 1 call per day:**

- **Groq LLM:** $0.10 per 1M tokens
  - Average: 200 tokens per call
  - Monthly: 100 users × 30 days × 200 tokens = 600K tokens
  - Cost: ~$0.06/month

- **ElevenLabs Voice:** $0.30 per 1K characters
  - Average: 300 characters per call
  - Monthly: 100 users × 30 days × 300 chars = 900K chars
  - Cost: ~$270/month

- **Deepgram Transcription:** $0.0043 per minute
  - Average: 2 minutes per call
  - Monthly: 100 users × 30 days × 2 min = 6000 minutes
  - Cost: ~$26/month

**Total VAPI Cost: ~$296/month** for 100 active users

---

## Summary

✅ **Backend Endpoints Ready** - All 10 functions + webhooks implemented  
✅ **VAPI Dashboard Configured** - Assistant, functions, webhooks set up  
✅ **Frontend Integration** - VAPI SDK integrated with trigger logic  
✅ **Hindi/Hinglish Support** - Voice, transcriber, and prompts optimized  
✅ **Real-time Data Access** - Functions fetch live data from database  
✅ **Clarification Flow** - Uncertain items automatically flagged and resolved  
✅ **Production Ready** - Error handling, logging, monitoring in place  

---

**Status:** ✅ COMPLETE  
**Last Updated:** March 29, 2026  
**Version:** 1.0
