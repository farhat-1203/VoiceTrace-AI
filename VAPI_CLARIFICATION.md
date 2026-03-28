# VAPI Integration Clarification

## What is VAPI in VoiceTrace AI?

VAPI is a **custom voice agent** (NOT phone-based) that provides real-time conversational interactions with vendors.

---

## Key Points

### ❌ NOT Phone Calls
- No phone numbers involved
- No traditional calling
- No telecom infrastructure

### ✅ Custom Voice Agent
- Real-time voice interactions
- Fires automatically based on triggers
- Inbound: Vendor asks questions, agent responds
- Outbound: Agent proactively asks for clarifications
- Web/app-based voice interface

---

## How It Works

### 1. Vendor Records 3-Min Summary
```
Vendor speaks into app:
"आज 60 केले बेचे, कुछ आम भी बेचे, खर्च में 500 रुपये गए"
(Sold 60 bananas today, also sold some mangoes, spent 500 rupees)
```

### 2. System Processes & Detects Issues
```
Transcription: ✅ "60 केले बेचे"
Extraction: ✅ Item: Banana, Qty: 60
Confidence: ✅ 0.9 (high)

Transcription: ⚠️ "कुछ आम भी बेचे"
Extraction: ⚠️ Item: Mango, Qty: unknown
Confidence: ⚠️ 0.4 (low - needs clarification)
```

### 3. VAPI Agent Triggers
```
System detects: Low confidence item
Trigger: VAPI custom agent
```

### 4. Real-Time Conversation
```
🤖 Agent: "आपने कहा कि कुछ आम बेचे। कितने आम बेचे?"
          (You said you sold some mangoes. How many mangoes?)

👤 Vendor: "20 आम बेचे 40 रुपये में"
           (Sold 20 mangoes at 40 rupees)

🤖 Agent: "धन्यवाद! तो 20 आम, 40 रुपये प्रति आम?"
          (Thank you! So 20 mangoes, 40 rupees per mango?)

👤 Vendor: "हाँ, सही है"
           (Yes, that's correct)

🤖 Agent: "बहुत अच्छा! मैंने आपका डेटा अपडेट कर दिया"
          (Great! I've updated your data)
```

### 5. Data Updated
```
Ledger updated:
- Item: Mango
- Quantity: 20
- Unit Price: 40
- Total: 800
- Confidence: 1.0 (confirmed)
```

---

## Trigger Conditions

VAPI agent fires when:

1. **Negative Mood** (mood_score ≤ 2)
   - "आज धंधा बहुत मंदा गया" (Business was very slow)
   - Agent asks: "क्या हुआ? बताइए" (What happened? Tell me)

2. **Low Confidence Items** (≥3 items with confidence < 0.7)
   - Vague names: "कुछ चीज़ें" (some things)
   - Missing quantities
   - Missing prices

3. **Stock-Outs**
   - "आम खत्म हो गए" (Mangoes ran out)
   - Agent asks about impact and next-day planning

---

## Technical Implementation

### Environment Variables
```bash
# Required
VAPI_API_KEY=your-vapi-api-key
VAPI_ASSISTANT_ID=your-assistant-id
VAPI_WEBHOOK_URL=https://your-domain.com/vapi/webhook

# NOT required (removed)
# VAPI_PHONE_NUMBER=... ❌ Not used
```

### Webhooks
```
POST /vapi/webhook/call-start    → Agent session started
POST /vapi/webhook/message        → Each message in conversation
POST /vapi/webhook/call-end       → Agent session ended
```

### API Endpoints
```
POST /vapi/trigger-check          → Check if agent should trigger
GET  /vapi/clarifications         → Get pending clarifications
GET  /vapi/call-history           → Get agent session history
GET  /vapi/mood-trend             → Analyze mood over time
POST /vapi/resolve-clarification  → Manually resolve clarification
```

---

## Integration Points

### Backend (Automatic)
```python
# After audio processing
if should_trigger_vapi:
    # Create pending clarifications
    # Log trigger reason
    # Return trigger flag in response
```

### Frontend (Expo App)
```typescript
// After upload
if (response.should_trigger_vapi) {
    // Show VAPI agent UI
    // Start voice conversation
    // Display messages in real-time
}
```

### VAPI Dashboard
```
1. Create custom assistant
2. Configure Hindi/Hinglish voice
3. Set system prompt for vendor interactions
4. Configure webhook URLs
5. Test with sample conversations
```

---

## Benefits

✅ **Real-time clarifications** - No waiting for follow-up  
✅ **Natural conversations** - Hindi/Hinglish support  
✅ **Automatic triggers** - No manual intervention  
✅ **Mood monitoring** - Proactive support  
✅ **Data accuracy** - Confirm uncertain items  
✅ **Better UX** - Voice is easier than typing  

---

## Example Use Cases

### Use Case 1: Vague Item Names
```
Input: "कुछ फल बेचे" (sold some fruits)
Agent: "कौन से फल?" (which fruits?)
Vendor: "केले और आम" (bananas and mangoes)
Agent: "कितने?" (how many?)
Result: Accurate ledger entry
```

### Use Case 2: Negative Mood
```
Input: "आज बहुत बुरा दिन था" (today was very bad)
Agent: "क्या हुआ? बताइए" (what happened? tell me)
Vendor: "बारिश की वजह से कोई नहीं आया" (no one came due to rain)
Agent: "समझ सकता हूँ। कल बेहतर होगा" (I understand. Tomorrow will be better)
Result: Mood logged, vendor feels supported
```

### Use Case 3: Stock-Out
```
Input: "आम खत्म हो गए दोपहर में" (mangoes ran out at noon)
Agent: "कितने और चाहिए कल के लिए?" (how many more needed for tomorrow?)
Vendor: "30 आम लाऊंगा" (will bring 30 mangoes)
Result: Stock suggestion updated
```

---

## Summary

**VAPI = Custom Voice Agent (Not Phone)**

- Fires automatically after 3-min recording
- Real-time voice conversations
- Clarifies uncertainties
- Monitors mood
- Updates ledger
- All through web/app interface
- No phone numbers needed

---

**Document Created:** March 28, 2026  
**Purpose:** Clarify VAPI usage (custom agent, not phone-based)
