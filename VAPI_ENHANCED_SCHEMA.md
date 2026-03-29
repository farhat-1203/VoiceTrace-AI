# VAPI Enhanced Schema with Descriptions and Regex

## Complete JSON Schema with Descriptions

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "VoiceTrace VAPI Structured Output",
  "description": "Captures complete conversation outcomes, business data, clarifications, insights, and follow-up requirements for vendor business assistant interactions.",
  "required": ["session_metadata", "conversation_summary", "business_data_captured"],
  "properties": {
    "session_metadata": {
      "type": "object",
      "description": "Core session information including identifiers, timing, and language",
      "properties": {
        "session_id": {
          "type": "string",
          "description": "Unique session identifier (format: 'vapi-session-{timestamp}' or UUID)"
        },
        "user_id": {
          "type": "string",
          "description": "Vendor's unique user identifier (UUID format)"
        },
        "vendor_name": {
          "type": ["string", "null"],
          "description": "Vendor's preferred name (e.g., 'Rajesh', 'Priya'). Null if not captured."
        },
        "session_type": {
          "type": "string",
          "enum": ["recording", "clarification", "follow_up", "query"],
          "description": "Conversation type: 'recording' (initial summary), 'clarification' (resolving items), 'follow_up' (addressing issues), 'query' (vendor questions)"
        },
        "started_at": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp when conversation started (e.g., '2026-03-29T10:30:00Z')"
        },
        "ended_at": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp when conversation ended"
        },
        "duration_seconds": {
          "type": "number",
          "description": "Total conversation duration in seconds (e.g., 330 for 5.5 minutes)"
        },
        "language_used": {
          "type": "string",
          "enum": ["hi", "en", "hi-en"],
          "description": "Primary language: 'hi' (Hindi), 'en' (English), 'hi-en' (Hinglish)"
        }
      }
    }
  }
}
```

## Field Descriptions and Allowed Values

### session_metadata

| Field | Type | Allowed Values | Description |
|-------|------|----------------|-------------|
| `session_id` | string | Any string | Unique session identifier |
| `user_id` | string | UUID format | Vendor's user ID |
| `vendor_name` | string/null | Any name or null | Vendor's name for personalization |
| `session_type` | enum | `recording`, `clarification`, `follow_up`, `query` | Type of conversation |
| `started_at` | datetime | ISO 8601 format | Start timestamp |
| `ended_at` | datetime | ISO 8601 format | End timestamp |
| `duration_seconds` | number | Positive number | Duration in seconds |
| `language_used` | enum | `hi`, `en`, `hi-en` | Language used |

### conversation_summary

| Field | Type | Description |
|-------|------|-------------|
| `total_turns` | integer | Total conversation turns (user + agent) |
| `user_turns` | integer | Number of times vendor spoke |
| `agent_turns` | integer | Number of times agent spoke |
| `functions_called` | integer | Backend functions called (typical: 3-8) |
| `clarifications_requested` | integer | Items needing clarification |
| `clarifications_resolved` | integer | Successfully resolved clarifications |

### business_data_captured.daily_summary

| Field | Type | Description |
|-------|------|-------------|
| `total_earnings` | number/null | Revenue in rupees (e.g., 1100 = ₹1100) |
| `total_expenses` | number/null | Expenses in rupees |
| `net_profit` | number/null | Profit (earnings - expenses) |
| `items_count` | integer/null | Number of different items sold |

### clarifications[].status

**Allowed Values:**
- `resolved` - Successfully clarified and confirmed
- `pending` - Needs follow-up
- `skipped` - Vendor chose not to clarify now

### insights_shared

| Field | Type | Description |
|-------|------|-------------|
| `best_sellers_shown` | boolean | Whether best sellers were shared |
| `stock_suggestions_given` | boolean | Whether stock recommendations given |
| `expense_analysis_shown` | boolean | Whether expense breakdown shown |
| `anomalies_discussed` | boolean | Whether anomalies discussed |
| `anomaly_count` | integer | Number of anomalies found |

### sentiment_analysis

| Field | Allowed Values | Description |
|-------|----------------|-------------|
| `vendor_mood` | `positive`, `neutral`, `negative` | Overall mood classification |
| `mood_score` | 1, 2, 3, 4, 5 | Numerical rating (1=very negative, 5=very positive) |
| `mood_trend` | `improving`, `stable`, `declining` | Trend over recent conversations |
| `empathy_shown` | boolean | Whether agent showed empathy |
| `encouragement_given` | boolean | Whether agent gave encouragement |

### issues_identified[].issue_type

**Allowed Values:**
- `stock_out` - Items ran out
- `low_profit` - Earnings below threshold
- `high_expense` - Costs above normal
- `negative_mood` - Vendor upset
- `data_quality` - Missing/unclear data

### issues_identified[].severity

**Allowed Values:**
- `low` - Minor concern
- `medium` - Needs attention
- `high` - Urgent, requires immediate action

### actions_taken[].action_type

**Allowed Values:**
- `item_confirmed` - Clarified item saved
- `name_saved` - Vendor name stored
- `suggestion_given` - Recommendation provided
- `insight_shared` - Analysis presented
- `issue_resolved` - Problem fixed

### follow_up_required

| Field | Allowed Values | Description |
|-------|----------------|-------------|
| `needed` | boolean | Whether follow-up required |
| `priority` | `low`, `medium`, `high` | Follow-up priority |
| `suggested_timing` | `immediate`, `next_day`, `next_week` | When to follow up |
| `follow_up_type` | `clarification`, `mood_check`, `stock_alert`, `anomaly_investigation` | Type of follow-up |

### conversation_quality

| Field | Allowed Values | Description |
|-------|----------------|-------------|
| `user_satisfaction_inferred` | `satisfied`, `neutral`, `unsatisfied` | Inferred satisfaction |
| `conversation_completed` | boolean | Reached natural conclusion |
| `premature_end` | boolean | Ended unexpectedly early |
| `technical_issues` | boolean | Technical problems occurred |
| `agent_performance` | `excellent`, `good`, `fair`, `poor` | Overall performance rating |

---

## Regex Pattern for Validation

### Basic Structure Validation

```regex
^\s*\{\s*"session_metadata"\s*:\s*\{[^}]+\}\s*,\s*"conversation_summary"\s*:\s*\{[^}]+\}\s*,\s*"business_data_captured"\s*:\s*\{.*?\}.*\}\s*$
```

**What it validates:**
- ✅ Starts with `{`
- ✅ Contains `session_metadata` object
- ✅ Contains `conversation_summary` object  
- ✅ Contains `business_data_captured` object
- ✅ Ends with `}`

### Enum Value Validation Patterns

```regex
# session_type validation
"session_type"\s*:\s*"(recording|clarification|follow_up|query)"

# language_used validation
"language_used"\s*:\s*"(hi|en|hi-en)"

# vendor_mood validation
"vendor_mood"\s*:\s*"(positive|neutral|negative)"

# mood_score validation (1-5)
"mood_score"\s*:\s*[1-5]

# mood_trend validation
"mood_trend"\s*:\s*"(improving|stable|declining)"

# issue_type validation
"issue_type"\s*:\s*"(stock_out|low_profit|high_expense|negative_mood|data_quality)"

# severity validation
"severity"\s*:\s*"(low|medium|high)"

# status validation (clarifications)
"status"\s*:\s*"(resolved|pending|skipped)"

# priority validation
"priority"\s*:\s*"(low|medium|high)"

# suggested_timing validation
"suggested_timing"\s*:\s*"(immediate|next_day|next_week)"

# follow_up_type validation
"follow_up_type"\s*:\s*"(clarification|mood_check|stock_alert|anomaly_investigation)"

# action_type validation
"action_type"\s*:\s*"(item_confirmed|name_saved|suggestion_given|insight_shared|issue_resolved)"

# user_satisfaction validation
"user_satisfaction_inferred"\s*:\s*"(satisfied|neutral|unsatisfied)"

# agent_performance validation
"agent_performance"\s*:\s*"(excellent|good|fair|poor)"
```

### ISO 8601 DateTime Validation

```regex
# Validates ISO 8601 datetime format
"(started_at|ended_at|timestamp)"\s*:\s*"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?"
```

### UUID Validation

```regex
# Validates UUID format for user_id, session_id, etc.
"(user_id|session_id|transcription_id|clarification_id)"\s*:\s*"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
```

### Number Range Validations

```regex
# Confidence score (0.0 to 1.0)
"confidence_(before|after)"\s*:\s*(0(\.\d+)?|1(\.0+)?)

# Mood score (1-5)
"mood_score"\s*:\s*[1-5]

# Positive numbers (earnings, expenses, etc.)
"(total_earnings|total_expenses|net_profit|revenue|quantity_sold)"\s*:\s*\d+(\.\d+)?
```

---

## Complete Validation Regex (Combined)

```regex
(?=.*"session_metadata"\s*:\s*\{)(?=.*"conversation_summary"\s*:\s*\{)(?=.*"business_data_captured"\s*:\s*\{)(?=.*"session_type"\s*:\s*"(recording|clarification|follow_up|query)")(?=.*"language_used"\s*:\s*"(hi|en|hi-en)")^\s*\{.*\}\s*$
```

**This validates:**
- ✅ Required top-level fields present
- ✅ session_type has valid enum value
- ✅ language_used has valid enum value
- ✅ Valid JSON structure

---

## Recommended: Use JSON Schema Validator Instead

**Python:**
```bash
pip install jsonschema
```

```python
import jsonschema
from jsonschema import validate

schema = {...}  # Your full schema
data = {...}    # VAPI output

try:
    validate(instance=data, schema=schema)
    print("✅ Valid")
except jsonschema.ValidationError as e:
    print(f"❌ Invalid: {e.message}")
```

**JavaScript:**
```bash
npm install ajv
```

```javascript
const Ajv = require('ajv');
const ajv = new Ajv();

const validate = ajv.compile(schema);
const valid = validate(data);

if (!valid) {
  console.log('❌ Errors:', validate.errors);
}
```

---

## Summary

**For VAPI Configuration:**
- Use the enhanced JSON schema with descriptions
- VAPI will validate against this schema automatically
- Descriptions help the LLM understand what to generate

**For Backend Validation:**
- Use `jsonschema` library (Python) or `ajv` (JavaScript)
- Don't rely on regex for complex JSON validation
- Regex is only for quick sanity checks

**Regex Limitations:**
- ❌ Can't validate nested structures properly
- ❌ Can't check all enum values reliably
- ❌ Can't validate array structures
- ✅ Good for quick presence checks only

Use proper JSON Schema validators for production!
