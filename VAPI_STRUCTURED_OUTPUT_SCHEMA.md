# VAPI Structured Output Schema
## Custom Template for VoiceTrace Business Assistant

**Last Updated:** March 29, 2026  
**Purpose:** Capture conversation outcomes, clarifications, and business insights

---

## Why Custom Structured Output?

### Problem Without Structured Output
- Conversation data is unstructured text
- Hard to extract actionable insights
- Can't track what was clarified/confirmed
- No metrics on conversation effectiveness
- Difficult to analyze patterns across sessions

### Benefits of Structured Output
✅ **Trackable Outcomes** - Know exactly what was accomplished  
✅ **Data Quality** - Capture clarifications and confirmations  
✅ **Analytics** - Measure conversation effectiveness  
✅ **Automation** - Trigger follow-up actions based on outcomes  
✅ **Audit Trail** - Record what agent learned/updated  

---

## VoiceTrace Custom Schema

### Schema Design

```json
{
  "schema_version": "1.0",
  "session_metadata": {
    "session_id": "string",
    "user_id": "string",
    "vendor_name": "string",
    "session_type": "recording | clarification | follow_up | query",
    "started_at": "ISO8601 timestamp",
    "ended_at": "ISO8601 timestamp",
    "duration_seconds": "number",
    "language_used": "hi | en | hi-en (hinglish)"
  },
  
  "conversation_summary": {
    "total_turns": "number",
    "user_turns": "number",
    "agent_turns": "number",
    "functions_called": "number",
    "clarifications_requested": "number",
    "clarifications_resolved": "number"
  },
  
  "business_data_captured": {
    "recording_processed": "boolean",
    "transcription_id": "string | null",
    "summary_provided": "boolean",
    "daily_summary": {
      "total_earnings": "number | null",
      "total_expenses": "number | null",
      "net_profit": "number | null",
      "items_count": "number | null"
    }
  },
  
  "clarifications": [
    {
      "clarification_id": "string",
      "item_type": "item_sold | expense | other",
      "original_value": "string",
      "clarified_value": {
        "item_name": "string",
        "quantity": "number | null",
        "unit_price": "number | null",
        "total_amount": "number | null"
      },
      "confidence_before": "number (0-1)",
      "confidence_after": "number (0-1)",
      "status": "resolved | pending | skipped"
    }
  ],
  
  "insights_shared": {
    "best_sellers_shown": "boolean",
    "best_sellers": [
      {
        "item_name": "string",
        "quantity_sold": "number",
        "revenue": "number"
      }
    ],
    "stock_suggestions_given": "boolean",
    "stock_suggestions": [
      {
        "item_name": "string",
        "suggested_quantity": "number",
        "reason": "string"
      }
    ],
    "expense_analysis_shown": "boolean",
    "anomalies_discussed": "boolean",
    "anomaly_count": "number"
  },
  
  "sentiment_analysis": {
    "vendor_mood": "positive | neutral | negative",
    "mood_score": "number (1-5)",
    "mood_trend": "improving | stable | declining",
    "empathy_shown": "boolean",
    "encouragement_given": "boolean"
  },
  
  "personalization": {
    "name_known": "boolean",
    "name_used": "string | null",
    "name_asked_this_session": "boolean",
    "name_saved_this_session": "boolean",
    "business_context_used": "boolean"
  },
  
  "issues_identified": [
    {
      "issue_type": "stock_out | low_profit | high_expense | negative_mood | data_quality",
      "severity": "low | medium | high",
      "description": "string",
      "resolved": "boolean",
      "follow_up_needed": "boolean"
    }
  ],
  
  "actions_taken": [
    {
      "action_type": "item_confirmed | name_saved | suggestion_given | insight_shared | issue_resolved",
      "description": "string",
      "timestamp": "ISO8601 timestamp",
      "success": "boolean"
    }
  ],
  
  "follow_up_required": {
    "needed": "boolean",
    "reason": "string | null",
    "priority": "low | medium | high",
    "suggested_timing": "immediate | next_day | next_week",
    "follow_up_type": "clarification | mood_check | stock_alert | anomaly_investigation"
  },
  
  "conversation_quality": {
    "user_satisfaction_inferred": "satisfied | neutral | unsatisfied",
    "conversation_completed": "boolean",
    "premature_end": "boolean",
    "technical_issues": "boolean",
    "agent_performance": "excellent | good | fair | poor"
  },
  
  "metadata": {
    "functions_used": ["function_name_1", "function_name_2"],
    "errors_encountered": ["error_description"],
    "retry_count": "number",
    "backend_processing_time_ms": "number"
  }
}
```

---

## Implementation in VAPI

### Step 1: Configure in VAPI Dashboard

Go to **VAPI Dashboard → Assistant Settings → Structured Data**

**Enable:** Structured Output  
**Schema Type:** Custom JSON Schema

**Paste this schema:**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "session_metadata",
    "conversation_summary",
    "business_data_captured"
  ],
  "properties": {
    "session_metadata": {
      "type": "object",
      "properties": {
        "session_id": {"type": "string"},
        "user_id": {"type": "string"},
        "vendor_name": {"type": ["string", "null"]},
        "session_type": {
          "type": "string",
          "enum": ["recording", "clarification", "follow_up", "query"]
        },
        "started_at": {"type": "string", "format": "date-time"},
        "ended_at": {"type": "string", "format": "date-time"},
        "duration_seconds": {"type": "number"},
        "language_used": {
          "type": "string",
          "enum": ["hi", "en", "hi-en"]
        }
      }
    },
    
    "conversation_summary": {
      "type": "object",
      "properties": {
        "total_turns": {"type": "integer"},
        "user_turns": {"type": "integer"},
        "agent_turns": {"type": "integer"},
        "functions_called": {"type": "integer"},
        "clarifications_requested": {"type": "integer"},
        "clarifications_resolved": {"type": "integer"}
      }
    },
    
    "business_data_captured": {
      "type": "object",
      "properties": {
        "recording_processed": {"type": "boolean"},
        "transcription_id": {"type": ["string", "null"]},
        "summary_provided": {"type": "boolean"},
        "daily_summary": {
          "type": "object",
          "properties": {
            "total_earnings": {"type": ["number", "null"]},
            "total_expenses": {"type": ["number", "null"]},
            "net_profit": {"type": ["number", "null"]},
            "items_count": {"type": ["integer", "null"]}
          }
        }
      }
    },
    
    "clarifications": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "clarification_id": {"type": "string"},
          "item_type": {
            "type": "string",
            "enum": ["item_sold", "expense", "other"]
          },
          "original_value": {"type": "string"},
          "clarified_value": {
            "type": "object",
            "properties": {
              "item_name": {"type": "string"},
              "quantity": {"type": ["number", "null"]},
              "unit_price": {"type": ["number", "null"]},
              "total_amount": {"type": ["number", "null"]}
            }
          },
          "confidence_before": {"type": "number", "minimum": 0, "maximum": 1},
          "confidence_after": {"type": "number", "minimum": 0, "maximum": 1},
          "status": {
            "type": "string",
            "enum": ["resolved", "pending", "skipped"]
          }
        }
      }
    },
    
    "insights_shared": {
      "type": "object",
      "properties": {
        "best_sellers_shown": {"type": "boolean"},
        "best_sellers": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "item_name": {"type": "string"},
              "quantity_sold": {"type": "number"},
              "revenue": {"type": "number"}
            }
          }
        },
        "stock_suggestions_given": {"type": "boolean"},
        "stock_suggestions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "item_name": {"type": "string"},
              "suggested_quantity": {"type": "number"},
              "reason": {"type": "string"}
            }
          }
        },
        "expense_analysis_shown": {"type": "boolean"},
        "anomalies_discussed": {"type": "boolean"},
        "anomaly_count": {"type": "integer"}
      }
    },
    
    "sentiment_analysis": {
      "type": "object",
      "properties": {
        "vendor_mood": {
          "type": "string",
          "enum": ["positive", "neutral", "negative"]
        },
        "mood_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "mood_trend": {
          "type": "string",
          "enum": ["improving", "stable", "declining"]
        },
        "empathy_shown": {"type": "boolean"},
        "encouragement_given": {"type": "boolean"}
      }
    },
    
    "personalization": {
      "type": "object",
      "properties": {
        "name_known": {"type": "boolean"},
        "name_used": {"type": ["string", "null"]},
        "name_asked_this_session": {"type": "boolean"},
        "name_saved_this_session": {"type": "boolean"},
        "business_context_used": {"type": "boolean"}
      }
    },
    
    "issues_identified": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "issue_type": {
            "type": "string",
            "enum": ["stock_out", "low_profit", "high_expense", "negative_mood", "data_quality"]
          },
          "severity": {
            "type": "string",
            "enum": ["low", "medium", "high"]
          },
          "description": {"type": "string"},
          "resolved": {"type": "boolean"},
          "follow_up_needed": {"type": "boolean"}
        }
      }
    },
    
    "actions_taken": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "action_type": {
            "type": "string",
            "enum": ["item_confirmed", "name_saved", "suggestion_given", "insight_shared", "issue_resolved"]
          },
          "description": {"type": "string"},
          "timestamp": {"type": "string", "format": "date-time"},
          "success": {"type": "boolean"}
        }
      }
    },
    
    "follow_up_required": {
      "type": "object",
      "properties": {
        "needed": {"type": "boolean"},
        "reason": {"type": ["string", "null"]},
        "priority": {
          "type": "string",
          "enum": ["low", "medium", "high"]
        },
        "suggested_timing": {
          "type": "string",
          "enum": ["immediate", "next_day", "next_week"]
        },
        "follow_up_type": {
          "type": "string",
          "enum": ["clarification", "mood_check", "stock_alert", "anomaly_investigation"]
        }
      }
    },
    
    "conversation_quality": {
      "type": "object",
      "properties": {
        "user_satisfaction_inferred": {
          "type": "string",
          "enum": ["satisfied", "neutral", "unsatisfied"]
        },
        "conversation_completed": {"type": "boolean"},
        "premature_end": {"type": "boolean"},
        "technical_issues": {"type": "boolean"},
        "agent_performance": {
          "type": "string",
          "enum": ["excellent", "good", "fair", "poor"]
        }
      }
    },
    
    "metadata": {
      "type": "object",
      "properties": {
        "functions_used": {
          "type": "array",
          "items": {"type": "string"}
        },
        "errors_encountered": {
          "type": "array",
          "items": {"type": "string"}
        },
        "retry_count": {"type": "integer"},
        "backend_processing_time_ms": {"type": "integer"}
      }
    }
  }
}
```


### Step 2: Update System Prompt to Generate Structured Output

Add this to the end of your VAPI system prompt:

```
═══════════════════════════════════════════════════════════
STRUCTURED OUTPUT REQUIREMENTS
═══════════════════════════════════════════════════════════

At the END of every conversation, you MUST generate a structured output JSON that captures:

1. SESSION METADATA:
   - session_id, user_id, vendor_name
   - session_type (recording/clarification/follow_up/query)
   - timestamps and duration
   - language used (hi/en/hi-en)

2. CONVERSATION SUMMARY:
   - Count of turns (total, user, agent)
   - Functions called count
   - Clarifications requested and resolved

3. BUSINESS DATA:
   - Was recording processed?
   - Transcription ID
   - Daily summary (earnings, expenses, profit, items count)

4. CLARIFICATIONS:
   For EACH item clarified:
   - Original vague value
   - Clarified details (name, quantity, price)
   - Confidence before/after
   - Status (resolved/pending/skipped)

5. INSIGHTS SHARED:
   - Best sellers shown? List them
   - Stock suggestions given? List them
   - Expense analysis shown?
   - Anomalies discussed? Count

6. SENTIMENT:
   - Vendor mood (positive/neutral/negative)
   - Mood score (1-5)
   - Mood trend (improving/stable/declining)
   - Did you show empathy?
   - Did you give encouragement?

7. PERSONALIZATION:
   - Name known? Name used?
   - Did you ask for name this session?
   - Did you save name this session?
   - Did you use business context?

8. ISSUES IDENTIFIED:
   For EACH issue:
   - Type (stock_out/low_profit/high_expense/negative_mood/data_quality)
   - Severity (low/medium/high)
   - Description
   - Resolved?
   - Follow-up needed?

9. ACTIONS TAKEN:
   For EACH action:
   - Type (item_confirmed/name_saved/suggestion_given/insight_shared/issue_resolved)
   - Description
   - Timestamp
   - Success?

10. FOLLOW-UP:
    - Is follow-up needed?
    - Reason
    - Priority (low/medium/high)
    - Timing (immediate/next_day/next_week)
    - Type (clarification/mood_check/stock_alert/anomaly_investigation)

11. CONVERSATION QUALITY:
    - User satisfaction (satisfied/neutral/unsatisfied)
    - Conversation completed?
    - Premature end?
    - Technical issues?
    - Your performance (excellent/good/fair/poor)

12. METADATA:
    - List of functions used
    - Errors encountered
    - Retry count
    - Backend processing time

EXAMPLE STRUCTURED OUTPUT:

{
  "session_metadata": {
    "session_id": "vapi-session-1234567890",
    "user_id": "user-uuid-123",
    "vendor_name": "Rajesh",
    "session_type": "recording",
    "started_at": "2026-03-29T10:30:00Z",
    "ended_at": "2026-03-29T10:35:30Z",
    "duration_seconds": 330,
    "language_used": "hi-en"
  },
  "conversation_summary": {
    "total_turns": 12,
    "user_turns": 6,
    "agent_turns": 6,
    "functions_called": 5,
    "clarifications_requested": 2,
    "clarifications_resolved": 2
  },
  "business_data_captured": {
    "recording_processed": true,
    "transcription_id": "trans-uuid-456",
    "summary_provided": true,
    "daily_summary": {
      "total_earnings": 1100,
      "total_expenses": 550,
      "net_profit": 550,
      "items_count": 5
    }
  },
  "clarifications": [
    {
      "clarification_id": "clarif-1",
      "item_type": "item_sold",
      "original_value": "kuch fal",
      "clarified_value": {
        "item_name": "केला",
        "quantity": 50,
        "unit_price": 5,
        "total_amount": 250
      },
      "confidence_before": 0.3,
      "confidence_after": 1.0,
      "status": "resolved"
    }
  ],
  "insights_shared": {
    "best_sellers_shown": true,
    "best_sellers": [
      {
        "item_name": "केला",
        "quantity_sold": 420,
        "revenue": 2100
      }
    ],
    "stock_suggestions_given": true,
    "stock_suggestions": [
      {
        "item_name": "केला",
        "suggested_quantity": 60,
        "reason": "Weekend demand increase"
      }
    ],
    "expense_analysis_shown": false,
    "anomalies_discussed": false,
    "anomaly_count": 0
  },
  "sentiment_analysis": {
    "vendor_mood": "positive",
    "mood_score": 4,
    "mood_trend": "stable",
    "empathy_shown": true,
    "encouragement_given": true
  },
  "personalization": {
    "name_known": true,
    "name_used": "Rajesh",
    "name_asked_this_session": false,
    "name_saved_this_session": false,
    "business_context_used": true
  },
  "issues_identified": [],
  "actions_taken": [
    {
      "action_type": "item_confirmed",
      "description": "Confirmed 50 bananas at ₹5 each",
      "timestamp": "2026-03-29T10:32:15Z",
      "success": true
    },
    {
      "action_type": "suggestion_given",
      "description": "Suggested 60 bananas for tomorrow",
      "timestamp": "2026-03-29T10:34:00Z",
      "success": true
    }
  ],
  "follow_up_required": {
    "needed": false,
    "reason": null,
    "priority": "low",
    "suggested_timing": "next_day",
    "follow_up_type": "clarification"
  },
  "conversation_quality": {
    "user_satisfaction_inferred": "satisfied",
    "conversation_completed": true,
    "premature_end": false,
    "technical_issues": false,
    "agent_performance": "excellent"
  },
  "metadata": {
    "functions_used": [
      "get_user_profile",
      "get_today_summary",
      "get_unconfirmed_items",
      "confirm_item",
      "get_best_sellers",
      "get_stock_suggestions"
    ],
    "errors_encountered": [],
    "retry_count": 0,
    "backend_processing_time_ms": 2500
  }
}
```

---

## Backend Integration

### Step 1: Receive Structured Output via Webhook

```python
# backend/routers/vapi.py

from pydantic import BaseModel
from typing import List, Optional

class StructuredOutputData(BaseModel):
    """Structured output from VAPI conversation."""
    session_metadata: dict
    conversation_summary: dict
    business_data_captured: dict
    clarifications: List[dict]
    insights_shared: dict
    sentiment_analysis: dict
    personalization: dict
    issues_identified: List[dict]
    actions_taken: List[dict]
    follow_up_required: dict
    conversation_quality: dict
    metadata: dict


@router.post("/webhook/structured-output")
async def receive_structured_output(
    call_id: str,
    user_id: str,
    structured_data: StructuredOutputData
):
    """
    Receive structured output from VAPI at end of conversation.
    Store in database for analytics and follow-up actions.
    """
    try:
        # Store in Supabase
        result = supabase_service._client.table("vapi_conversation_analytics")\
            .insert({
                "call_id": call_id,
                "user_id": user_id,
                "session_metadata": structured_data.session_metadata,
                "conversation_summary": structured_data.conversation_summary,
                "business_data": structured_data.business_data_captured,
                "clarifications": structured_data.clarifications,
                "insights_shared": structured_data.insights_shared,
                "sentiment": structured_data.sentiment_analysis,
                "personalization": structured_data.personalization,
                "issues": structured_data.issues_identified,
                "actions": structured_data.actions_taken,
                "follow_up": structured_data.follow_up_required,
                "quality": structured_data.conversation_quality,
                "metadata": structured_data.metadata,
                "created_at": datetime.utcnow().isoformat()
            })\
            .execute()
        
        # Check if follow-up needed
        if structured_data.follow_up_required.get("needed"):
            await schedule_follow_up(
                user_id=user_id,
                reason=structured_data.follow_up_required.get("reason"),
                priority=structured_data.follow_up_required.get("priority"),
                timing=structured_data.follow_up_required.get("suggested_timing"),
                follow_up_type=structured_data.follow_up_required.get("follow_up_type")
            )
        
        # Update user profile with sentiment trend
        await update_sentiment_trend(
            user_id=user_id,
            mood_score=structured_data.sentiment_analysis.get("mood_score"),
            mood_trend=structured_data.sentiment_analysis.get("mood_trend")
        )
        
        logger.info(f"Structured output stored for call {call_id}")
        
        return {
            "success": True,
            "message": "Structured output processed successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to process structured output: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def schedule_follow_up(user_id, reason, priority, timing, follow_up_type):
    """Schedule a follow-up call based on structured output."""
    timing_map = {
        "immediate": 0,
        "next_day": 86400,  # 24 hours
        "next_week": 604800  # 7 days
    }
    
    delay_seconds = timing_map.get(timing, 86400)
    scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
    
    supabase_service._client.table("vapi_triggers")\
        .insert({
            "user_id": user_id,
            "trigger_reason": reason,
            "trigger_type": "follow_up",
            "follow_up_type": follow_up_type,
            "priority": priority,
            "status": "scheduled",
            "scheduled_at": scheduled_at.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        })\
        .execute()


async def update_sentiment_trend(user_id, mood_score, mood_trend):
    """Update user's sentiment trend in profile."""
    supabase_service._client.table("profiles")\
        .update({
            "last_mood_score": mood_score,
            "mood_trend": mood_trend,
            "last_interaction_at": datetime.utcnow().isoformat()
        })\
        .eq("user_id", user_id)\
        .execute()
```

### Step 2: Create Database Table

```sql
-- Store structured conversation analytics
CREATE TABLE vapi_conversation_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    
    -- Structured data fields
    session_metadata JSONB NOT NULL,
    conversation_summary JSONB NOT NULL,
    business_data JSONB NOT NULL,
    clarifications JSONB DEFAULT '[]'::jsonb,
    insights_shared JSONB DEFAULT '{}'::jsonb,
    sentiment JSONB DEFAULT '{}'::jsonb,
    personalization JSONB DEFAULT '{}'::jsonb,
    issues JSONB DEFAULT '[]'::jsonb,
    actions JSONB DEFAULT '[]'::jsonb,
    follow_up JSONB DEFAULT '{}'::jsonb,
    quality JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Indexes for analytics queries
CREATE INDEX idx_vapi_analytics_user ON vapi_conversation_analytics(user_id);
CREATE INDEX idx_vapi_analytics_created ON vapi_conversation_analytics(created_at DESC);
CREATE INDEX idx_vapi_analytics_call ON vapi_conversation_analytics(call_id);

-- Index for sentiment analysis
CREATE INDEX idx_vapi_analytics_sentiment ON vapi_conversation_analytics 
    USING GIN ((sentiment));

-- Index for follow-up queries
CREATE INDEX idx_vapi_analytics_follow_up ON vapi_conversation_analytics 
    USING GIN ((follow_up));
```

---

## Analytics & Insights

### Query Examples

```python
# Get conversation effectiveness metrics
def get_conversation_metrics(user_id: str, days: int = 30):
    """Analyze conversation effectiveness."""
    start_date = (date.today() - timedelta(days=days)).isoformat()
    
    result = supabase_service._client.table("vapi_conversation_analytics")\
        .select("*")\
        .eq("user_id", user_id)\
        .gte("created_at", start_date)\
        .execute()
    
    conversations = result.data or []
    
    if not conversations:
        return None
    
    # Calculate metrics
    total_conversations = len(conversations)
    total_clarifications = sum(
        len(c.get("clarifications", [])) for c in conversations
    )
    clarifications_resolved = sum(
        sum(1 for cl in c.get("clarifications", []) if cl.get("status") == "resolved")
        for c in conversations
    )
    
    avg_duration = sum(
        c.get("session_metadata", {}).get("duration_seconds", 0)
        for c in conversations
    ) / total_conversations
    
    satisfaction_counts = {
        "satisfied": 0,
        "neutral": 0,
        "unsatisfied": 0
    }
    for c in conversations:
        satisfaction = c.get("quality", {}).get("user_satisfaction_inferred", "neutral")
        satisfaction_counts[satisfaction] += 1
    
    return {
        "total_conversations": total_conversations,
        "avg_duration_seconds": round(avg_duration, 1),
        "total_clarifications": total_clarifications,
        "clarifications_resolved": clarifications_resolved,
        "resolution_rate": round(clarifications_resolved / total_clarifications * 100, 1) if total_clarifications > 0 else 0,
        "satisfaction_distribution": satisfaction_counts,
        "satisfaction_rate": round(satisfaction_counts["satisfied"] / total_conversations * 100, 1)
    }


# Get insights shared analysis
def get_insights_analysis(user_id: str, days: int = 30):
    """Analyze what insights were shared."""
    start_date = (date.today() - timedelta(days=days)).isoformat()
    
    result = supabase_service._client.table("vapi_conversation_analytics")\
        .select("insights_shared")\
        .eq("user_id", user_id)\
        .gte("created_at", start_date)\
        .execute()
    
    conversations = result.data or []
    
    best_sellers_shown = sum(
        1 for c in conversations 
        if c.get("insights_shared", {}).get("best_sellers_shown", False)
    )
    
    stock_suggestions_given = sum(
        1 for c in conversations 
        if c.get("insights_shared", {}).get("stock_suggestions_given", False)
    )
    
    expense_analysis_shown = sum(
        1 for c in conversations 
        if c.get("insights_shared", {}).get("expense_analysis_shown", False)
    )
    
    return {
        "best_sellers_shown_count": best_sellers_shown,
        "stock_suggestions_given_count": stock_suggestions_given,
        "expense_analysis_shown_count": expense_analysis_shown,
        "total_conversations": len(conversations)
    }


# Get sentiment trends
def get_sentiment_trends(user_id: str, days: int = 30):
    """Analyze sentiment over time."""
    start_date = (date.today() - timedelta(days=days)).isoformat()
    
    result = supabase_service._client.table("vapi_conversation_analytics")\
        .select("sentiment, session_metadata")\
        .eq("user_id", user_id)\
        .gte("created_at", start_date)\
        .order("created_at", desc=False)\
        .execute()
    
    conversations = result.data or []
    
    mood_scores = [
        c.get("sentiment", {}).get("mood_score", 3)
        for c in conversations
    ]
    
    return {
        "mood_scores": mood_scores,
        "average_mood": round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else 3.0,
        "trend": conversations[-1].get("sentiment", {}).get("mood_trend", "stable") if conversations else "stable"
    }
```

---

## Summary

### Recommendation: **Create Custom Schema** ✅

**Why NOT use templates:**
- ❌ Revenue amount template - too generic
- ❌ Upsell opportunity - not relevant for vendors
- ❌ Issue resolve - too narrow

**Why custom schema:**
- ✅ Captures vendor-specific data (items, expenses, stock)
- ✅ Tracks clarifications and data quality
- ✅ Measures sentiment and mood trends
- ✅ Enables follow-up automation
- ✅ Provides actionable analytics
- ✅ Tailored to VoiceTrace business model

### Implementation Steps

1. **VAPI Dashboard:**
   - Enable Structured Output
   - Paste custom JSON schema
   - Update system prompt with output requirements

2. **Backend:**
   - Create `vapi_conversation_analytics` table
   - Add webhook endpoint for structured output
   - Implement analytics queries

3. **Testing:**
   - Run test conversation
   - Verify structured