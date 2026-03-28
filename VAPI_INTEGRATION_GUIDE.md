# VAPI Custom Voice Agent Integration Guide

## Overview

VoiceTrace AI uses VAPI as a **custom voice agent** (not phone-based) for real-time vendor interactions. The agent fires automatically based on triggers and engages with vendors to clarify uncertainties, check mood, and provide assistance.

---

## How It Works

### 1. Initial Recording (3 minutes)

```
Vendor records daily summary
    ↓
Audio uploaded to backend
    ↓
Transcription + Entity Extraction
    ↓
Confidence scoring + Mood detection
    ↓
Check if VAPI agent should be triggered
```

### 2. VAPI Agent Triggers

The custom agent is triggered when:

- **Negative Mood Detected**
  - Sentiment = "bad"
  - Mood score ≤ 2
  - Mood trigger flag = true
  - Example: "आज धंधा बहुत मंदा गया" (Business was very slow today)

- **Low Confidence Items** (≥3 items with confidence < 0.7)
  - Vague item names: "कुछ चीज़ें" (some things)
  - Missing quantities
  - Missing prices
  - Example: "कुछ फल बेचे" (sold some fruits) - unclear what and how many

- **Stock-Out Mentions**
  - Vendor mentions running out of items
  - Example: "आम खत्म हो गए" (mangoes ran out)

### 3. Agent Interaction Flow

```
Trigger detected
    ↓
VAPI custom agent activated
    ↓
Webhook: /vapi/webhook/call-start
    ↓
Real-time conversation:
  - Agent: "आपने कहा कि कुछ फल बेचे। कौन से फल थे?" 
           (You said you sold some fruits. Which fruits?)
  - Vendor: "60 केले बेचे 5 रुपये में"
            (Sold 60 bananas at 5 rupees)
  - Agent: "धन्यवाद! और कितने आम बेचे?"
           (Thank you! And how many mangoes?)
    ↓
Webhook: /vapi/webhook/message (for each message)
    ↓
Conversation ends
    ↓
Webhook: /vapi/webhook/call-end
    ↓
Clarifications resolved
    ↓
Ledger updated with confirmed data
```

---

## Configuration

### Environment Variables

```bash
# VAPI API Key (required)
VAPI_API_KEY=your-vapi-api-key

# VAPI Assistant ID (required)
# This is your custom agent configuration in VAPI dashboard
VAPI_ASSISTANT_ID=your-vapi-assistant-id

# VAPI Webhook URL (required)
# Your backend URL where VAPI sends callbacks
VAPI_WEBHOOK_URL=https://your-domain.com/vapi/webhook
```

### VAPI Dashboard Setup

1. **Create Custom Assistant**
   - Go to VAPI Dashboard → Assistants
   - Create new assistant
   - Configure voice (Hindi/English support)
   - Set system prompt for vendor interactions

2. **Configure Webhooks**
   - Set webhook URL: `https://your-domain.com/vapi/webhook/call-start`
   - Set webhook URL: `https://your-domain.com/vapi/webhook/call-end`
   - Set webhook URL: `https://your-domain.com/vapi/webhook/message`

3. **Assistant System Prompt Example**

```
You are a helpful business assistant for street vendors in India.
Your job is to clarify uncertain information from their daily business summary.

Guidelines:
- Speak in Hindi or Hinglish (mix of Hindi and English)
- Be friendly and conversational
- Ask one question at a time
- Confirm information before moving to next question
- Keep questions short and simple

When clarifying items:
- Ask for item name if vague
- Ask for quantity if missing
- Ask for price if missing

When checking mood:
- If vendor seems upset, ask what happened
- Show empathy
- Offer encouragement

Example conversation:
Vendor: "आज कुछ फल बेचे"
You: "बहुत अच्छा! कौन से फल बेचे आपने?"
Vendor: "केले और आम"
You: "ठीक है। कितने केले बेचे?"
Vendor: "60 केले"
You: "और कितने रुपये में बेचे?"
Vendor: "5 रुपये प्रति केला"
You: "धन्यवाद! अब आम के बारे में बताइए..."
```

---

## API Integration

### Check if Agent Should Trigger

```bash
POST /vapi/trigger-check?transcription_id=uuid
Authorization: Bearer TOKEN

Response:
{
  "should_trigger": true,
  "reason": "3 items need clarification",
  "extracted_data": {...},
  "confidence_scores": {...}
}
```

### Get Pending Clarifications

```bash
GET /vapi/clarifications
Authorization: Bearer TOKEN

Response:
{
  "clarifications": [
    {
      "id": "uuid",
      "clarification_type": "item",
      "item_data": {
        "name": "कुछ चीज़ें",
        "quantity": null,
        "unit_price": null
      },
      "priority": "high",
      "status": "pending"
    }
  ],
  "count": 3
}
```

### Resolve Clarification

```bash
POST /vapi/resolve-clarification/uuid
Authorization: Bearer TOKEN

Body:
{
  "item_name": "केला",
  "quantity": 60,
  "unit_price": 5,
  "total_amount": 300
}

Response:
{
  "success": true,
  "message": "Clarification resolved successfully"
}
```

### Get Agent Session History

```bash
GET /vapi/call-history?limit=20
Authorization: Bearer TOKEN

Response:
{
  "calls": [
    {
      "call_id": "vapi-session-123",
      "call_type": "clarification",
      "duration_seconds": 120,
      "transcript": "...",
      "outcome": "completed",
      "created_at": "2026-03-28T10:00:00Z"
    }
  ],
  "count": 10
}
```

### Get Mood Trend

```bash
GET /vapi/mood-trend?days=7
Authorization: Bearer TOKEN

Response:
{
  "average_mood_score": 3.8,
  "negative_days": 1,
  "positive_days": 5,
  "trend": "improving",
  "total_days": 7
}
```

---

## Webhook Payloads

### Call Start Webhook

```json
POST /vapi/webhook/call-start

{
  "call_id": "vapi-session-123",
  "user_id": "user-uuid",
  "call_type": "clarification",
  "trigger_reason": "3 items need clarification"
}
```

### Call End Webhook

```json
POST /vapi/webhook/call-end

{
  "call_id": "vapi-session-123",
  "user_id": "user-uuid",
  "duration_seconds": 120,
  "transcript": "Full conversation transcript...",
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

### Message Webhook

```json
POST /vapi/webhook/message

{
  "call_id": "vapi-session-123",
  "user_id": "user-uuid",
  "message": "60 केले बेचे 5 रुपये में",
  "role": "user"
}
```

---

## Database Schema

### vapi_calls Table

```sql
CREATE TABLE vapi_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    call_id TEXT NOT NULL,
    call_type TEXT NOT NULL, -- 'clarification', 'mood_check', 'stock_alert'
    trigger_reason TEXT,
    duration_seconds INTEGER,
    transcript TEXT,
    outcome TEXT, -- 'completed', 'no_answer', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### pending_clarifications Table

```sql
CREATE TABLE pending_clarifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    transcription_id UUID REFERENCES transcriptions(id) ON DELETE CASCADE,
    clarification_type TEXT NOT NULL, -- 'item', 'expense', 'mood', 'stock_out'
    item_data JSONB NOT NULL,
    priority TEXT DEFAULT 'medium', -- 'low', 'medium', 'high'
    status TEXT DEFAULT 'pending', -- 'pending', 'resolved'
    resolved_data JSONB,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Implementation in Backend

### Trigger Check (in main.py after pipeline)

```python
from services.vapi_service import vapi_service

# After ledger creation
if ledger_entry_id:
    # Calculate confidence scores
    confidence_scores = {}
    for idx, item in enumerate(extracted_data.get("items_sold", [])):
        score = ledger_service._calculate_item_confidence(item)
        confidence_scores[f"item_{idx}"] = score
    
    # Check if VAPI agent should be triggered
    should_trigger, reason = vapi_service.should_trigger_call(
        extracted_data=extracted_data,
        confidence_scores=confidence_scores,
    )
    
    if should_trigger:
        # Create pending clarifications
        for idx, item in enumerate(extracted_data.get("items_sold", [])):
            if confidence_scores.get(f"item_{idx}", 1.0) < 0.7:
                vapi_service.create_pending_clarification(
                    user_id=user_id,
                    transcription_id=transcription_id,
                    clarification_type="item",
                    item_data=item,
                    priority="high" if confidence_scores[f"item_{idx}"] < 0.5 else "medium",
                )
        
        # Log that agent should be triggered
        logger.info(f"VAPI agent trigger: {reason}")
        
        # Return trigger info in response
        result["should_trigger_vapi"] = True
        result["vapi_trigger_reason"] = reason
```

---

## Frontend Integration

### Expo App Integration

```typescript
// After audio upload
const response = await fetch('http://backend/process', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
  },
  body: formData,
});

const data = await response.json();

// Check if VAPI agent should be triggered
if (data.should_trigger_vapi) {
  // Show UI to start agent conversation
  showVAPIAgentModal({
    reason: data.vapi_trigger_reason,
    clarifications: data.pending_clarifications,
  });
}
```

### VAPI Web SDK Integration

```typescript
import { useVapi } from '@vapi-ai/web';

function VAPIAgentModal({ reason, clarifications }) {
  const { start, stop, messages } = useVapi({
    apiKey: process.env.VAPI_API_KEY,
    assistantId: process.env.VAPI_ASSISTANT_ID,
  });
  
  const startConversation = async () => {
    await start({
      metadata: {
        userId: currentUser.id,
        clarifications: clarifications,
        triggerReason: reason,
      },
    });
  };
  
  return (
    <View>
      <Text>Agent needs to clarify some information</Text>
      <Text>Reason: {reason}</Text>
      <Button onPress={startConversation}>
        Start Conversation
      </Button>
      
      {messages.map(msg => (
        <Text key={msg.id}>{msg.content}</Text>
      ))}
    </View>
  );
}
```

---

## Testing

### Test Trigger Detection

```bash
# Upload audio with vague items
curl -X POST http://localhost:8000/process \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@vague_recording.wav"

# Response should include:
{
  "should_trigger_vapi": true,
  "vapi_trigger_reason": "3 items need clarification"
}
```

### Test Webhook Endpoints

```bash
# Simulate call start
curl -X POST http://localhost:8000/vapi/webhook/call-start \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-123",
    "user_id": "user-uuid",
    "call_type": "clarification",
    "trigger_reason": "Low confidence items"
  }'

# Simulate call end
curl -X POST http://localhost:8000/vapi/webhook/call-end \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-123",
    "user_id": "user-uuid",
    "duration_seconds": 120,
    "outcome": "completed",
    "clarifications_resolved": [...]
  }'
```

---

## Best Practices

### 1. Agent Personality
- Keep tone friendly and conversational
- Use Hindi/Hinglish naturally
- Show empathy for vendor's situation
- Celebrate good days, support on bad days

### 2. Clarification Strategy
- Ask one question at a time
- Confirm before moving to next item
- Repeat back information for verification
- Use simple, clear language

### 3. Error Handling
- If vendor doesn't understand, rephrase
- Provide examples when needed
- Allow vendor to skip if they don't remember
- Don't force answers

### 4. Privacy & Security
- Don't store sensitive personal information
- Use secure webhooks (HTTPS only)
- Validate webhook signatures
- Implement rate limiting

---

## Troubleshooting

### Agent Not Triggering

**Check:**
1. Confidence scores calculated correctly?
2. Trigger thresholds configured properly?
3. VAPI_API_KEY set in environment?
4. VAPI_ASSISTANT_ID correct?

**Debug:**
```bash
# Check trigger logic
curl -X POST http://localhost:8000/vapi/trigger-check?transcription_id=uuid \
  -H "Authorization: Bearer TOKEN"
```

### Webhooks Not Received

**Check:**
1. Webhook URL configured in VAPI dashboard?
2. Backend accessible from internet (use ngrok for local testing)?
3. Webhook endpoints returning 200 OK?

**Debug:**
```bash
# Test webhook locally
curl -X POST http://localhost:8000/vapi/webhook/call-start \
  -H "Content-Type: application/json" \
  -d '{"call_id": "test", "user_id": "uuid", "call_type": "test"}'
```

### Clarifications Not Resolving

**Check:**
1. Clarification IDs correct?
2. Resolved data format matches schema?
3. User has permission to resolve?

**Debug:**
```bash
# Check pending clarifications
curl http://localhost:8000/vapi/clarifications \
  -H "Authorization: Bearer TOKEN"
```

---

## Conclusion

VAPI custom voice agent integration provides real-time, conversational clarification of uncertain data, mood checking, and proactive vendor engagement - all without phone calls. The agent fires automatically based on triggers and seamlessly integrates with the ledger system to ensure data accuracy.

**Key Benefits:**
- ✅ Real-time clarifications
- ✅ Natural Hindi/Hinglish conversations
- ✅ Automatic trigger detection
- ✅ Mood monitoring and support
- ✅ Improved data accuracy
- ✅ Better vendor experience

---

**Last Updated:** March 28, 2026  
**VAPI Version:** Custom Agent (Non-Phone)
