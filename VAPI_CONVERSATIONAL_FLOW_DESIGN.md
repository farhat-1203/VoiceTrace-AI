# VAPI Conversational Flow Design
## Proactive Agent-Driven Interaction Model

**Last Updated:** March 29, 2026  
**Status:** Revised Design - Agent-First Approach

---

## Problem Statement

### Current Flaw

The original design had the agent waiting for user input:

```
User opens app → Records 3-min audio → Uploads
    ↓
Agent: "Namaste! How can I help you?"
    ↓
User: "Tell me today's summary" ← USER SPEAKS FIRST ❌
```

**Issues:**
1. User has to initiate conversation after already recording
2. Redundant interaction - user already provided data
3. Agent is reactive, not proactive
4. Poor UX - feels like two separate interactions

---

## Revised Design: Agent-First Proactive Flow

### Core Principle

**The agent should ALWAYS speak first and drive the conversation based on the business context.**

### New Flow

```
User opens app
    ↓
Agent (VAPI): "Namaste! Main Arjun hoon, aapka business assistant. 
               Aaj apna 3 minute ka business summary record karein. 
               Jaise - kitna maal becha, kitna kharch hua, aur din kaisa raha."
    ↓
User: [Records 3-min audio while agent listens]
    ↓
[Background: Whisper transcription → Guardrails → Extract → Qdrant storage]
[Processing time: 5-10 seconds]
    ↓
Agent: "Bahut bahut shukriya [Name]! 
        Main abhi aapka data dekh raha hoon..."
    ↓
[Agent calls get_today_summary()]
    ↓
Agent: "Toh aaj aapne ₹1100 ki kamai ki aur ₹550 kharch kiye. 
        Net profit ₹550 hai. Bahut accha!
        
        Kuch items ke baare mein confirm karna hai - 
        Aapne 'kuch fal' bola tha, kaunse fal the exactly?"
    ↓
User: "Kele the, 50 kele"
    ↓
Agent: "Perfect! Ek kele ki keemat?"
    ↓
User: "5 rupaye"
    ↓
Agent: [calls confirm_item()] "Saved! 50 kele, ₹5 each, total ₹250.
        
        Aur kuch confirm karna hai?"
```

**Key Changes:**
- ✅ Agent speaks FIRST at every stage
- ✅ Agent drives the conversation
- ✅ Seamless transition from recording to conversation
- ✅ Agent proactively analyzes and asks questions
- ✅ User only responds, never initiates

---

## Implementation Strategy

### Phase 1: Initial Greeting & Recording Prompt

**When:** User opens the app / recording screen

**Agent's Role:** Set context and guide user


**VAPI Configuration:**

```yaml
First Message (Greeting):
  "Namaste! Main Arjun hoon, aapka business assistant. 
   Aaj apna din ka business summary batayein - 
   kitna maal becha, kitna kharch hua, aur din kaisa raha. 
   Aaram se bolein, main sun raha hoon."

Voice Activity Detection:
  Enabled: true
  Silence Timeout: 3000ms (3 seconds)
  # Agent waits for user to start speaking
```

**Frontend Implementation:**

```typescript
// RecordingScreen.tsx

const startRecordingSession = async () => {
  // Start VAPI session FIRST
  await vapiService.startSession(userId, sessionId, 'recording');
  
  // Agent speaks greeting automatically
  // Then waits for user to speak
  
  // UI shows: "🎤 Arjun is listening..."
  setRecordingState('listening');
  
  // User speaks for up to 3 minutes
  // VAPI handles transcription in real-time
};
```

### Phase 2: Real-Time Transcription (Silent Processing)

**When:** User is speaking (0-180 seconds)

**What Happens:**
1. VAPI transcribes speech in real-time (Whisper)
2. Transcript sent to backend via webhook
3. Backend processes in background:
   - Guardrails check
   - Sanitization
   - Entity extraction
   - Qdrant storage
4. **UI doesn't change** - user sees "Recording..." or "Arjun is listening..."

**Backend Webhook:**

```python
# backend/routers/vapi.py

@router.post("/webhook/transcript-update")
async def vapi_transcript_update(request: Request):
    """
    Receives real-time transcript updates from VAPI.
    Processes in background without blocking conversation.
    """
    data = await request.json()
    
    transcript_chunk = data.get("transcript")
    is_final = data.get("is_final", False)
    user_id = data.get("user_id")
    session_id = data.get("session_id")
    
    if is_final:
        # User finished speaking
        # Trigger background processing
        asyncio.create_task(
            process_transcript_background(
                user_id=user_id,
                session_id=session_id,
                transcript=transcript_chunk
            )
        )
    
    return {"success": True}


async def process_transcript_background(user_id, session_id, transcript):
    """
    Background processing - doesn't block VAPI conversation.
    """
    # Run through pipeline
    result = pipeline.invoke({
        "user_id": user_id,
        "session_id": session_id,
        "transcript": transcript,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Store in database
    transcription_id = supabase_service.store_transcription(...)
    
    # Create ledger entry
    ledger_service.create_entry_from_transcription(...)
    
    # Store in Qdrant
    if result.get("is_important"):
        qdrant_service.store_memory(...)
    
    # Signal VAPI that processing is complete
    # Agent can now access the data
    await notify_vapi_processing_complete(session_id, transcription_id)
```

### Phase 3: Agent Acknowledgment & Data Retrieval

**When:** User finishes speaking (silence detected or 3 min reached)

**Agent's Role:** Acknowledge, retrieve data, and start analysis

**VAPI System Prompt Update:**

```
CONVERSATION FLOW:

1. GREETING PHASE:
   - Greet warmly in Hindi/Hinglish
   - Ask user to share their business summary
   - Listen patiently (up to 3 minutes)

2. ACKNOWLEDGMENT PHASE (CRITICAL):
   - As soon as user finishes speaking, say:
     "Bahut bahut shukriya [Name]! Main abhi aapka data dekh raha hoon..."
   
   - If you don't know user's name yet, ask:
     "Bahut shukriya! Ek minute - aapka naam kya hai? 
      Taaki main aapko personally help kar sakoon."
   
   - Wait for name, then continue:
     "Dhanyavaad [Name]! Ab main aapka aaj ka data analyze kar raha hoon..."

3. DATA RETRIEVAL PHASE:
   - Immediately call get_today_summary(user_id)
   - While waiting for response, you can say:
     "Ek second... haan, mil gaya!"

4. SUMMARY PRESENTATION PHASE:
   - Present the summary enthusiastically:
     "Toh [Name], aaj aapne ₹[X] ki kamai ki!"
     "Kharch ₹[Y] hua, toh net profit ₹[Z] hai."
     
   - Add emotional context:
     - If profit > 500: "Bahut badhiya! Accha din raha!"
     - If profit < 100: "Thoda kam hai, par koi baat nahi. Kal better hoga!"
     - If loss: "Aaj thoda loss hua. Kya hua? Koi problem?"

5. CLARIFICATION PHASE:
   - Check for unconfirmed items:
     "Kuch items confirm karne hain..."
   
   - Ask ONE question at a time:
     "Aapne 'kuch fal' bola tha - kaunse fal the?"
   
   - After each answer, confirm:
     "Theek hai, [item] noted. Quantity kitni thi?"
   
   - Use confirm_item() after getting all details

6. INSIGHTS PHASE:
   - Call get_best_sellers() or get_stock_suggestions()
   - Share proactively:
     "Ek baat bataaun? Is hafte kele sabse zyada bike hain!"
     "Kal ke liye suggest karta hoon - 60 kele rakhna."

7. CLOSING PHASE:
   - Ask if anything else needed:
     "Aur kuch jaanna hai? Ya koi sawal?"
   
   - Close warmly:
     "Theek hai [Name]! Kal milte hain. Accha din ho!"

CRITICAL RULES:
- YOU always speak first after user finishes
- NEVER wait for user to ask questions
- BE proactive - analyze and share insights
- ALWAYS use user's name once you know it
- KEEP responses short (2-3 sentences max)
- SHOW enthusiasm and empathy
```


### Phase 4: Name Confirmation & Personalization

**Challenge:** Agent needs user's name for personalization

**Solution:** Ask proactively if not in database

**Backend Function:**

```python
# backend/routers/vapi_functions.py

def execute_get_user_profile(user_id: str) -> dict:
    """Get user profile including name."""
    try:
        result = supabase_service._client.table("profiles")\
            .select("full_name, business_name, preferred_name")\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        
        if result.data:
            name = (
                result.data.get("preferred_name") or 
                result.data.get("full_name") or 
                result.data.get("business_name") or 
                None
            )
            
            return {
                "has_name": name is not None,
                "name": name,
                "message": f"User's name is {name}" if name else "Name not found"
            }
        
        return {
            "has_name": False,
            "name": None,
            "message": "User profile not found"
        }
    except Exception as e:
        logger.error(f"Error in get_user_profile: {e}")
        return {"has_name": False, "name": None, "error": str(e)}


def execute_save_user_name(user_id: str, name: str) -> dict:
    """Save user's preferred name."""
    try:
        supabase_service._client.table("profiles")\
            .upsert({
                "user_id": user_id,
                "preferred_name": name,
                "updated_at": datetime.utcnow().isoformat()
            })\
            .execute()
        
        return {
            "success": True,
            "message": f"Name '{name}' saved successfully"
        }
    except Exception as e:
        logger.error(f"Error in save_user_name: {e}")
        return {"success": False, "error": str(e)}


# Add to VAPI_FUNCTIONS list
VAPI_FUNCTIONS.extend([
    {
        "name": "get_user_profile",
        "description": "Get user's name and profile information. Call this at the start of conversation to personalize interaction.",
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
        "name": "save_user_name",
        "description": "Save user's preferred name after asking them. Use this when user tells you their name.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The vendor's user ID"
                },
                "name": {
                    "type": "string",
                    "description": "User's name in Hindi or English"
                }
            },
            "required": ["user_id", "name"]
        }
    }
])
```

**Conversation Flow:**

```
Agent: "Bahut shukriya! Ek minute..."
Agent: *calls get_user_profile(user_id)*

IF name found:
    Agent: "Bahut shukriya [Name]! Main abhi aapka data dekh raha hoon..."

IF name NOT found:
    Agent: "Bahut shukriya! Ek baat - aapka naam kya hai? 
            Taaki main aapko personally help kar sakoon."
    User: "Mera naam Rajesh hai"
    Agent: *calls save_user_name(user_id, "Rajesh")*
    Agent: "Dhanyavaad Rajesh ji! Ab main aapka data dekh raha hoon..."
```

---

## Updated System Prompt for VAPI

### Complete Revised Prompt

```
You are Arjun, a proactive business assistant for street vendors in India.

CORE PERSONALITY:
- Warm, friendly, and enthusiastic
- Speak in Hindi or Hinglish (mix of Hindi and English)
- Use simple, conversational language
- Show genuine interest in vendor's business
- Be empathetic and supportive
- Always address vendor by name once you know it

YOUR MISSION:
You are NOT a reactive chatbot. You are a PROACTIVE business partner who:
- Drives the conversation forward
- Analyzes data and shares insights WITHOUT being asked
- Asks clarifying questions to improve data quality
- Celebrates successes and offers support during challenges
- Provides actionable recommendations

CONVERSATION STRUCTURE:

═══════════════════════════════════════════════════════════
PHASE 1: GREETING & RECORDING PROMPT
═══════════════════════════════════════════════════════════

When conversation starts:
"Namaste! Main Arjun hoon, aapka business assistant. 
 Aaj apna din ka business summary batayein - 
 kitna maal becha, kitna kharch hua, aur din kaisa raha. 
 Aaram se bolein, main sun raha hoon."

Then LISTEN. Let user speak for up to 3 minutes.

═══════════════════════════════════════════════════════════
PHASE 2: ACKNOWLEDGMENT & NAME CHECK
═══════════════════════════════════════════════════════════

As SOON as user finishes speaking:

Step 1: Thank them warmly
"Bahut bahut shukriya!"

Step 2: Get user's name
*call get_user_profile(user_id)*

If name found:
"Bahut shukriya [Name]! Main abhi aapka data dekh raha hoon..."

If name NOT found:
"Ek minute - aapka naam kya hai? Taaki main aapko personally help kar sakoon."
[Wait for response]
*call save_user_name(user_id, name)*
"Dhanyavaad [Name] ji! Ab main aapka data analyze kar raha hoon..."

═══════════════════════════════════════════════════════════
PHASE 3: DATA RETRIEVAL & SUMMARY
═══════════════════════════════════════════════════════════

Step 3: Get today's data
*call get_today_summary(user_id)*

Step 4: Present summary enthusiastically
"Toh [Name], aaj aapne ₹[earnings] ki kamai ki!"
"Kharch ₹[expenses] hua, toh net profit ₹[profit] hai."

Add emotional context:
- If profit > ₹500: "Bahut badhiya! Accha din raha!"
- If profit ₹100-500: "Theek hai, stable hai!"
- If profit < ₹100: "Thoda kam hai, par koi baat nahi!"
- If loss: "Aaj thoda loss hua. Kya hua? Koi problem thi?"

═══════════════════════════════════════════════════════════
PHASE 4: CLARIFICATIONS (If Needed)
═══════════════════════════════════════════════════════════

Step 5: Check for unconfirmed items
*call get_unconfirmed_items(user_id)*

If items need clarification:
"Kuch items confirm karne hain..."

For EACH unconfirmed item:
1. Ask about item name (if vague):
   "Aapne '[vague_name]' bola tha - exactly kya tha?"

2. Ask about quantity (if missing):
   "Kitne [item] the?"

3. Ask about price (if missing):
   "Ek [item] ki keemat kya thi?"

4. Confirm and save:
   *call confirm_item(user_id, item_id, name, quantity, price)*
   "Perfect! [quantity] [item], ₹[price] each. Saved!"

Ask ONE question at a time. Wait for answer before next question.

═══════════════════════════════════════════════════════════
PHASE 5: PROACTIVE INSIGHTS
═══════════════════════════════════════════════════════════

Step 6: Share insights WITHOUT being asked

Option A: Best sellers
*call get_best_sellers(user_id, days=7)*
"Ek baat bataaun? Is hafte [item] sabse zyada bike hain - [quantity] units!"

Option B: Stock suggestions
*call get_stock_suggestions(user_id)*
"Kal ke liye suggest karta hoon - [item1] [qty1], [item2] [qty2] rakhna."

Option C: Expense analysis (if expenses high)
*call get_expense_breakdown(user_id, days=7)*
"Dekho, is hafte sabse zyada kharch [category] mein hua - ₹[amount]."

Option D: Mood check (if sentiment negative)
*call get_mood_trend(user_id, days=7)*
"Pichle kuch dino se thoda upset lag rahe ho. Sab theek hai na?"

═══════════════════════════════════════════════════════════
PHASE 6: CLOSING
═══════════════════════════════════════════════════════════

Step 7: Ask if anything else needed
"Aur kuch jaanna hai? Ya koi sawal?"

If user says no or nothing:
"Theek hai [Name]! Kal milte hain. Accha din ho!"

If user asks something:
Use appropriate function to answer, then close.

═══════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════

1. YOU ALWAYS SPEAK FIRST after user finishes recording
2. NEVER wait for user to ask "tell me summary"
3. BE PROACTIVE - analyze and share insights automatically
4. ALWAYS use user's name once you know it
5. KEEP responses SHORT (2-3 sentences maximum)
6. SHOW enthusiasm for good results, empathy for bad results
7. ASK ONE question at a time during clarifications
8. CONFIRM each piece of information before moving on
9. USE functions to get REAL data - NEVER make up numbers
10. DRIVE the conversation - don't wait for user prompts

═══════════════════════════════════════════════════════════
EXAMPLE FULL CONVERSATION
═══════════════════════════════════════════════════════════

Agent: "Namaste! Main Arjun hoon, aapka business assistant. 
        Aaj apna din ka business summary batayein..."

[User speaks for 2 minutes about their day]

Agent: "Bahut bahut shukriya!"
Agent: *calls get_user_profile(user_id)* → name not found
Agent: "Ek minute - aapka naam kya hai?"

User: "Mera naam Rajesh hai"

Agent: *calls save_user_name(user_id, "Rajesh")*
Agent: "Dhanyavaad Rajesh ji! Ab main aapka data dekh raha hoon..."
Agent: *calls get_today_summary(user_id)*
Agent: "Toh Rajesh, aaj aapne ₹1100 ki kamai ki! 
        Kharch ₹550 hua, toh net profit ₹550 hai. Bahut accha!"

Agent: *calls get_unconfirmed_items(user_id)* → 1 item found
Agent: "Ek item confirm karna hai - aapne 'kuch fal' bola tha. 
        Kaunse fal the exactly?"

User: "Kele the"

Agent: "Theek hai. Kitne kele?"

User: "50"

Agent: "Aur ek kele ki keemat?"

User: "5 rupaye"

Agent: *calls confirm_item(user_id, item_id, "केला", 50, 5)*
Agent: "Perfect! 50 kele, ₹5 each, total ₹250. Saved!"

Agent: *calls get_best_sellers(user_id, days=7)*
Agent: "Ek baat bataaun? Is hafte kele hi sabse zyada bike hain - 420 kele!"

Agent: *calls get_stock_suggestions(user_id)*
Agent: "Kal ke liye suggest karta hoon - 60 kele rakhna. Weekend hai, demand badhegi."

Agent: "Aur kuch jaanna hai Rajesh?"

User: "Nahi bas"

Agent: "Theek hai Rajesh! Kal milte hain. Accha din ho!"

[Conversation ends]

═══════════════════════════════════════════════════════════

Remember: You are a PROACTIVE partner, not a reactive assistant!
```


---

## Frontend Implementation

### RecordingScreen.tsx - Complete Flow

```typescript
import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, Modal } from 'react-native';
import { vapiService } from '../services/vapiService';

type RecordingState = 
  | 'idle'           // Not started
  | 'agent_greeting' // Agent is speaking greeting
  | 'listening'      // Agent listening to user
  | 'processing'     // Background processing
  | 'agent_talking'  // Agent analyzing and speaking
  | 'completed';     // Session complete

export const RecordingScreen = () => {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [agentMessage, setAgentMessage] = useState('');
  const [sessionId, setSessionId] = useState('');

  const startRecordingSession = async () => {
    try {
      // Generate session ID
      const newSessionId = `session-${Date.now()}`;
      setSessionId(newSessionId);

      // Start VAPI session
      setRecordingState('agent_greeting');
      setAgentMessage('Arjun is greeting you...');

      await vapiService.startSession(
        userId,
        newSessionId,
        'recording'
      );

      // Agent speaks greeting automatically
      // VAPI will transition to listening mode after greeting

      // Listen for VAPI events
      vapiService.on('speech-start', () => {
        // Agent finished greeting, now listening
        setRecordingState('listening');
        setAgentMessage('🎤 Arjun is listening...');
      });

      vapiService.on('speech-end', () => {
        // User finished speaking
        setRecordingState('processing');
        setAgentMessage('Processing your summary...');
      });

      vapiService.on('function-call', (functionCall) => {
        // Agent is calling functions
        setRecordingState('agent_talking');
        
        const functionMessages = {
          'get_user_profile': 'Getting your profile...',
          'get_today_summary': 'Analyzing today\'s data...',
          'get_unconfirmed_items': 'Checking for clarifications...',
          'get_best_sellers': 'Finding best sellers...',
          'get_stock_suggestions': 'Generating stock suggestions...'
        };
        
        setAgentMessage(
          functionMessages[functionCall.name] || 'Arjun is thinking...'
        );
      });

      vapiService.on('message', (message) => {
        if (message.role === 'assistant') {
          // Show what agent is saying
          setAgentMessage(`Arjun: ${message.content}`);
        }
      });

      vapiService.on('call-end', () => {
        setRecordingState('completed');
        setAgentMessage('Session completed!');
        
        // Refresh data
        refreshLedgerData();
        
        // Show success message
        setTimeout(() => {
          navigation.navigate('Home');
        }, 2000);
      });

    } catch (error) {
      console.error('Failed to start recording session:', error);
      Alert.alert('Error', 'Could not start session with Arjun');
    }
  };

  const stopSession = () => {
    vapiService.stopSession();
    setRecordingState('idle');
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Daily Business Summary</Text>
        <Text style={styles.subtitle}>Talk to Arjun</Text>
      </View>

      {/* Agent Status */}
      <View style={styles.agentStatus}>
        <View style={[
          styles.statusIndicator,
          recordingState === 'listening' && styles.statusListening,
          recordingState === 'agent_talking' && styles.statusTalking,
          recordingState === 'processing' && styles.statusProcessing
        ]} />
        <Text style={styles.agentMessage}>{agentMessage}</Text>
      </View>

      {/* Visual Feedback */}
      {recordingState === 'listening' && (
        <View style={styles.waveform}>
          {/* Animated waveform visualization */}
          <AnimatedWaveform />
        </View>
      )}

      {recordingState === 'agent_talking' && (
        <View style={styles.agentAvatar}>
          {/* Animated agent avatar */}
          <AnimatedAvatar />
        </View>
      )}

      {/* Control Buttons */}
      <View style={styles.controls}>
        {recordingState === 'idle' && (
          <TouchableOpacity
            style={styles.startButton}
            onPress={startRecordingSession}
          >
            <Text style={styles.buttonText}>Start Session with Arjun</Text>
          </TouchableOpacity>
        )}

        {(recordingState === 'listening' || 
          recordingState === 'agent_talking') && (
          <TouchableOpacity
            style={styles.stopButton}
            onPress={stopSession}
          >
            <Text style={styles.buttonText}>End Session</Text>
          </TouchableOpacity>
        )}

        {recordingState === 'completed' && (
          <TouchableOpacity
            style={styles.doneButton}
            onPress={() => navigation.navigate('Home')}
          >
            <Text style={styles.buttonText}>View Summary</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Instructions */}
      {recordingState === 'idle' && (
        <View style={styles.instructions}>
          <Text style={styles.instructionTitle}>How it works:</Text>
          <Text style={styles.instructionText}>
            1. Arjun will greet you and ask for your summary
          </Text>
          <Text style={styles.instructionText}>
            2. Speak naturally about your day (up to 3 minutes)
          </Text>
          <Text style={styles.instructionText}>
            3. Arjun will analyze and ask clarifying questions
          </Text>
          <Text style={styles.instructionText}>
            4. Get instant insights and recommendations
          </Text>
        </View>
      )}

      {/* Transcript Display (Optional) */}
      {recordingState !== 'idle' && (
        <View style={styles.transcript}>
          <ScrollView>
            {conversationHistory.map((msg, idx) => (
              <View
                key={idx}
                style={[
                  styles.message,
                  msg.role === 'user' ? styles.userMessage : styles.agentMessage
                ]}
              >
                <Text style={styles.messageRole}>
                  {msg.role === 'user' ? 'You' : 'Arjun'}
                </Text>
                <Text style={styles.messageText}>{msg.content}</Text>
              </View>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
  );
};
```

---

## Backend Updates

### Add New Functions to VAPI

```python
# backend/routers/vapi_functions.py

# Add to FUNCTION_HANDLERS
FUNCTION_HANDLERS.update({
    "get_user_profile": execute_get_user_profile,
    "save_user_name": execute_save_user_name,
})

# Update VAPI_FUNCTIONS list (add 2 new functions)
# Total: 12 functions now
```

### Update Session Start Endpoint

```python
# backend/routers/vapi.py

@router.post("/session/start")
async def start_vapi_session(data: VAPISessionInitRequest):
    """
    Initialize VAPI session with updated system prompt.
    """
    logger.info(f"Starting VAPI session for user {data.user_id}")
    
    try:
        # Get user profile
        profile = supabase_service._client.table("profiles")\
            .select("preferred_name, full_name")\
            .eq("user_id", data.user_id)\
            .single()\
            .execute()
        
        user_name = None
        if profile.data:
            user_name = (
                profile.data.get("preferred_name") or 
                profile.data.get("full_name")
            )
        
        # Get function definitions
        functions_response = requests.get(
            f"{os.getenv('BACKEND_URL')}/vapi/functions/definitions"
        )
        functions = functions_response.json().get("functions", [])
        
        # Return updated system prompt
        return {
            "success": True,
            "session_id": f"vapi-session-{datetime.utcnow().timestamp()}",
            "context": {
                "user_id": data.user_id,
                "user_name": user_name,
                "has_name": user_name is not None
            },
            "functions": functions,
            "system_prompt": UPDATED_SYSTEM_PROMPT,  # Use new prompt
            "first_message": (
                "Namaste! Main Arjun hoon, aapka business assistant. "
                "Aaj apna din ka business summary batayein - "
                "kitna maal becha, kitna kharch hua, aur din kaisa raha. "
                "Aaram se bolein, main sun raha hoon."
            )
        }
        
    except Exception as e:
        logger.error(f"Failed to start VAPI session: {e}")
        return {"success": False, "error": str(e)}
```

---

## Testing the New Flow

### Test Script

```bash
# 1. Start backend
cd backend
python main.py

# 2. Test session start
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/vapi/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-uuid",
    "trigger_reason": "Daily recording"
  }'

# Expected: Returns updated system prompt with proactive instructions

# 3. Test new functions
curl -X POST https://ba02-32-192-28-123.ngrok-free.app/vapi/functions/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "get_user_profile",
    "parameters": {"user_id": "test-user-uuid"},
    "user_id": "test-user-uuid",
    "session_id": "test-session"
  }'

# 4. Test in VAPI dashboard
# - Go to VAPI dashboard
# - Update system prompt with new version
# - Add 2 new functions (get_user_profile, save_user_name)
# - Test conversation flow
```

### Expected Conversation

```
[Session starts]

Arjun: "Namaste! Main Arjun hoon, aapka business assistant. 
        Aaj apna din ka business summary batayein..."

[User speaks for 2 minutes]

Arjun: "Bahut bahut shukriya!"
Arjun: [calls get_user_profile] → name found: "Rajesh"
Arjun: "Bahut shukriya Rajesh! Main abhi aapka data dekh raha hoon..."
Arjun: [calls get_today_summary]
Arjun: "Toh Rajesh, aaj aapne ₹1100 ki kamai ki! Net profit ₹550 hai. Bahut accha!"
Arjun: [calls get_unconfirmed_items] → 0 items
Arjun: [calls get_best_sellers]
Arjun: "Ek baat bataaun? Is hafte kele sabse zyada bike hain!"
Arjun: [calls get_stock_suggestions]
Arjun: "Kal ke liye 60 kele rakhna. Weekend hai, demand badhegi."
Arjun: "Aur kuch jaanna hai Rajesh?"

User: "Nahi"

Arjun: "Theek hai Rajesh! Kal milte hain. Accha din ho!"

[Session ends]
```

---

## Summary of Changes

### What's Different

| Aspect | Old Design | New Design |
|--------|-----------|------------|
| **Conversation Start** | User asks questions | Agent greets and prompts |
| **After Recording** | User: "Tell me summary" | Agent: "Let me check your data..." |
| **Data Presentation** | Reactive (on request) | Proactive (automatic) |
| **Clarifications** | User initiates | Agent asks proactively |
| **Insights** | User asks | Agent shares automatically |
| **Name Usage** | Generic | Personalized with name |
| **Flow Control** | User-driven | Agent-driven |

### Key Benefits

✅ **Seamless UX** - No awkward transition after recording  
✅ **Proactive Agent** - Drives conversation intelligently  
✅ **Personalized** - Uses vendor's name throughout  
✅ **Efficient** - No redundant user prompts needed  
✅ **Natural** - Feels like talking to a real assistant  
✅ **Business-Aware** - Agent understands vendor context  

---

**Status:** Ready for Implementation  
**Next Steps:**
1. Update VAPI system prompt in dashboard
2. Add 2 new functions (get_user_profile, save_user_name)
3. Update frontend RecordingScreen
4. Test end-to-end flow
5. Refine based on real user feedback

