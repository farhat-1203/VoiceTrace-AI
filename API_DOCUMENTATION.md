# VoiceTrace AI - API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication

All endpoints (except `/health` and VAPI webhooks) require authentication via JWT Bearer token.

```bash
Authorization: Bearer YOUR_SUPABASE_ACCESS_TOKEN
```

---

## Core Endpoints

### Health Check

#### `GET /health`
Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "backend": "running",
    "qdrant_cloud": "connected",
    "supabase": "connected"
  }
}
```

---

### Audio Processing

#### `POST /process`
Upload audio and run full pipeline (transcription → extraction → ledger creation).

**Headers:**
- `Authorization: Bearer TOKEN`

**Body:**
- `file`: Audio file (wav, mp3, m4a, ogg, flac, webm)

**Response:**
```json
{
  "session_id": "uuid",
  "transcript": "आज 60 केले बेचे...",
  "extracted_data": {
    "items_sold": [...],
    "expenses": [...]
  },
  "ledger_entry_id": "uuid",
  "audio_url": "https://...",
  "final_response": "Great day!",
  "processing_time_seconds": 3.5
}
```

---

#### `POST /transcribe`
Standalone transcription (no full pipeline).

**Headers:**
- `Authorization: Bearer TOKEN`

**Body:**
- `file`: Audio file

**Response:**
```json
{
  "session_id": "uuid",
  "text": "transcribed text",
  "language": "hinglish",
  "segments": [...],
  "duration_seconds": 180.5,
  "processing_time_seconds": 1.2
}
```

---

#### `POST /analyze`
Analyze text without audio upload.

**Headers:**
- `Authorization: Bearer TOKEN`

**Body:**
```json
{
  "text": "आज 60 केले बेचे 5 रुपये में",
  "include_response": true
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "safety_status": "SAFE",
  "extracted_data": {...},
  "response": "AI-generated summary",
  "processing_time_seconds": 0.8
}
```

---

### Transcription History

#### `GET /transcriptions`
Get user's transcription history.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `limit`: Number of results (default: 20)

**Response:**
```json
[
  {
    "id": "uuid",
    "transcript": "...",
    "created_at": "2026-03-28T10:00:00Z",
    ...
  }
]
```

---

#### `GET /transcriptions/{id}`
Get single transcription by ID.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "id": "uuid",
  "transcript": "...",
  "extracted_data": {...},
  "audio_url": "https://...",
  ...
}
```

---

#### `GET /memories`
Get important memories (stored in Qdrant).

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `limit`: Number of results (default: 10)

---

## Ledger Endpoints

### `GET /ledger/entries`
Get ledger entries for a date range.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `start_date`: YYYY-MM-DD (required)
- `end_date`: YYYY-MM-DD (required)

**Response:**
```json
{
  "entries": [
    {
      "id": "uuid",
      "entry_date": "2026-03-28",
      "total_earnings": 1100,
      "total_expenses": 550,
      "ledger_items": [...],
      "ledger_expenses": [...]
    }
  ],
  "count": 5
}
```

---

### `GET /ledger/entries/{entry_id}`
Get single ledger entry.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "id": "uuid",
  "entry_date": "2026-03-28",
  "ledger_items": [...],
  "ledger_expenses": [...],
  ...
}
```

---

### `GET /ledger/summary`
Get aggregated summary.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `period`: "week" or "month" (default: "week")

**Response:**
```json
{
  "total_earnings": 7700,
  "total_expenses": 3850,
  "net_profit": 3850,
  "days_count": 7,
  "avg_daily_earnings": 1100,
  "top_items": [
    {
      "name": "केला",
      "count": 7,
      "revenue": 2100
    }
  ],
  "top_expenses": [...]
}
```

---

### `GET /ledger/unconfirmed`
Get items needing confirmation (confidence < 0.7).

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "item_name": "something",
      "confidence_score": 0.5,
      "needs_confirmation": true
    }
  ],
  "count": 3
}
```

---

### `POST /ledger/confirm/{item_id}`
Confirm and update uncertain item.

**Headers:**
- `Authorization: Bearer TOKEN`

**Body:**
```json
{
  "item_name": "Apple",
  "quantity": 50,
  "unit_price": 10,
  "total_amount": 500
}
```

**Response:**
```json
{
  "success": true,
  "message": "Item confirmed successfully"
}
```

---

### `GET /ledger/stats`
Get overall ledger statistics.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "total_entries": 30,
  "total_items": 150,
  "total_expenses": 90,
  "first_entry_date": "2026-03-01"
}
```

---

## Pattern Detection Endpoints

### `GET /patterns/best-sellers`
Get best-selling items.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `days`: Number of days to analyze (default: 7, max: 90)
- `limit`: Number of items (default: 10, max: 50)

**Response:**
```json
{
  "best_sellers": [
    {
      "item_name": "केला",
      "total_quantity": 420,
      "total_revenue": 2100,
      "avg_daily_sales": 60
    }
  ],
  "period_days": 7,
  "count": 10
}
```

---

### `GET /patterns/high-days`
Identify high-earning days.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `days`: Number of days to analyze (default: 30)

**Response:**
```json
{
  "best_day_of_week": "Saturday",
  "avg_earnings_by_day": {
    "Monday": 950,
    "Saturday": 1500
  },
  "top_earning_dates": [...]
}
```

---

### `GET /patterns/expense-trends`
Analyze expense trends.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `days`: Number of days to analyze (default: 30)

**Response:**
```json
{
  "total_expenses": 15400,
  "by_type": {
    "raw_material": 10000,
    "transport": 3500,
    "rent": 1900
  },
  "trend": "increasing"
}
```

---

### `POST /patterns/analyze`
Run full pattern analysis.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `min_days`: Minimum days required (default: 4)

**Response:**
```json
{
  "success": true,
  "pattern_id": "uuid",
  "message": "Pattern analysis completed successfully"
}
```

---

### `GET /patterns/latest`
Get most recent pattern analysis.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "id": "uuid",
  "best_sellers": [...],
  "high_earning_days": {...},
  "expense_trends": {...},
  "created_at": "2026-03-28T10:00:00Z"
}
```

---

### `GET /patterns/history`
Get historical pattern analyses.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `limit`: Number of analyses (default: 10, max: 50)

---

## Anomaly Detection Endpoints

### `GET /anomalies/recent`
Get recent anomaly alerts.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `limit`: Number of anomalies (default: 20, max: 100)
- `severity`: Filter by "low", "medium", or "high"

**Response:**
```json
{
  "anomalies": [
    {
      "id": "uuid",
      "anomaly_type": "high_expense",
      "severity": "high",
      "description": "Expenses 2x higher than usual",
      "detected_at": "2026-03-28T10:00:00Z",
      "is_resolved": false
    }
  ],
  "count": 5
}
```

---

### `GET /anomalies/unresolved`
Get unresolved anomalies.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "anomalies": [...],
  "count": 3
}
```

---

### `POST /anomalies/resolve/{anomaly_id}`
Mark anomaly as resolved.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "success": true,
  "message": "Anomaly marked as resolved"
}
```

---

### `POST /anomalies/detect`
Run anomaly detection on specific entry.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `ledger_entry_id`: Entry ID to check (required)

**Response:**
```json
{
  "anomalies_detected": 2,
  "anomalies": [...]
}
```

---

### `GET /anomalies/stats`
Get anomaly statistics.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `days`: Number of days (default: 30)

**Response:**
```json
{
  "total_anomalies": 15,
  "by_severity": {
    "low": 5,
    "medium": 8,
    "high": 2
  },
  "by_type": {
    "high_expense": 7,
    "low_earnings": 5,
    "unusual_pattern": 3
  },
  "resolved": 10,
  "unresolved": 5
}
```

---

## Stock Suggestion Endpoints

### `GET /suggestions/next-day`
Get stock suggestions for next day.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "suggestions": [
    {
      "item_name": "केला",
      "suggested_quantity": 65,
      "reason": "Avg daily sales: 60, trending up",
      "confidence": 0.85
    }
  ],
  "count": 10,
  "generated_at": "2026-03-28T10:00:00Z"
}
```

---

### `GET /suggestions/latest`
Get most recent suggestions.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "suggestions": [...],
  "count": 10
}
```

---

### `GET /suggestions/item/{item_name}`
Get suggestion for specific item.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "item_name": "केला",
  "suggested_quantity": 65,
  "reason": "...",
  "confidence": 0.85
}
```

---

### `POST /suggestions/generate`
Generate fresh suggestions.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `days`: Number of days to analyze (default: 7, min: 3, max: 30)

**Response:**
```json
{
  "success": true,
  "suggestions": [...],
  "count": 10,
  "message": "Stock suggestions generated successfully"
}
```

---

### `GET /suggestions/accuracy`
Analyze suggestion accuracy.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `days`: Number of days (default: 7)

**Response:**
```json
{
  "accuracy_rate": 0.82,
  "over_predictions": 3,
  "under_predictions": 2,
  "exact_matches": 12
}
```

---

### `GET /suggestions/stock-outs`
Get stock-out history.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `days`: Number of days (default: 30)

**Response:**
```json
{
  "stock_outs": [
    {
      "item_name": "आम",
      "date": "2026-03-25",
      "estimated_lost_sales": 20
    }
  ],
  "count": 5,
  "period_days": 30
}
```

---

## VAPI Integration Endpoints

### Session Initialization (Start Point)

#### `POST /vapi/session/start`
Initialize a VAPI custom voice agent session with context and function definitions.

**Body:**
```json
{
  "user_id": "uuid",
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
    "user_id": "uuid",
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
    }
  ],
  "system_prompt": "You are a helpful business assistant...",
  "webhook_url": "https://your-backend.com/vapi/webhook"
}
```

---

### Function Calling

#### `GET /vapi/functions/definitions`
Get all available function definitions for VAPI in OpenAI function calling format.

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

#### `POST /vapi/functions/execute`
Execute a function called by VAPI agent.

**Body:**
```json
{
  "function_name": "get_today_summary",
  "parameters": {
    "user_id": "uuid"
  },
  "user_id": "uuid",
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
      }
    ]
  },
  "error": null
}
```

---

#### `POST /vapi/functions/batch-execute`
Execute multiple functions in batch.

**Body:**
```json
[
  {
    "function_name": "get_today_summary",
    "parameters": {"user_id": "uuid"},
    "user_id": "uuid",
    "session_id": "vapi-session-123"
  },
  {
    "function_name": "get_best_sellers",
    "parameters": {"user_id": "uuid", "days": 7, "limit": 5},
    "user_id": "uuid",
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

### VAPI Webhook Endpoints

#### `POST /vapi/webhook/call-start`
VAPI webhook: Call started.

**Body:**
```json
{
  "call_id": "vapi-call-123",
  "user_id": "uuid",
  "call_type": "clarification",
  "trigger_reason": "Low confidence items"
}
```

**Response:**
```json
{
  "success": true,
  "log_id": "uuid",
  "message": "Call start logged"
}
```

---

### `POST /vapi/webhook/call-end`
VAPI webhook: Call ended.

**Body:**
```json
{
  "call_id": "vapi-call-123",
  "user_id": "uuid",
  "duration_seconds": 120,
  "transcript": "...",
  "outcome": "completed",
  "clarifications_resolved": [...]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Call end processed",
  "clarifications_resolved": 3
}
```

---

### `POST /vapi/webhook/message`
VAPI webhook: Message received.

**Body:**
```json
{
  "call_id": "vapi-call-123",
  "user_id": "uuid",
  "message": "हाँ, 60 केले बेचे",
  "role": "user"
}
```

---

### `GET /vapi/clarifications`
Get pending clarifications.

**Headers:**
- `Authorization: Bearer TOKEN`

**Response:**
```json
{
  "clarifications": [
    {
      "id": "uuid",
      "clarification_type": "item",
      "item_data": {...},
      "priority": "high",
      "status": "pending"
    }
  ],
  "count": 5
}
```

---

### `GET /vapi/call-history`
Get VAPI call history.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `limit`: Number of calls (default: 20)

**Response:**
```json
{
  "calls": [
    {
      "call_id": "vapi-call-123",
      "call_type": "clarification",
      "duration_seconds": 120,
      "outcome": "completed",
      "created_at": "2026-03-28T10:00:00Z"
    }
  ],
  "count": 10
}
```

---

### `GET /vapi/mood-trend`
Analyze mood trends.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `days`: Number of days (default: 7)

**Response:**
```json
{
  "average_mood_score": 3.8,
  "negative_days": 1,
  "positive_days": 5,
  "trend": "improving",
  "total_days": 7
}
```

---

### `POST /vapi/trigger-check`
Check if VAPI call should be triggered.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `transcription_id`: Transcription ID (required)

**Response:**
```json
{
  "should_trigger": true,
  "reason": "Vendor expressed negative sentiment",
  "extracted_data": {...},
  "confidence_scores": {...}
}
```

---

### `POST /vapi/resolve-clarification/{clarification_id}`
Manually resolve clarification.

**Headers:**
- `Authorization: Bearer TOKEN`

**Body:**
```json
{
  "item_name": "Apple",
  "quantity": 50,
  "unit_price": 10
}
```

**Response:**
```json
{
  "success": true,
  "message": "Clarification resolved successfully"
}
```

---

## Export Endpoints

### `GET /export/income-statement`
Generate income statement PDF.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `period`: "week" or "month" (default: "week")

**Response:**
- PDF file download

---

### `GET /export/ledger-csv`
Export ledger as CSV.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `start_date`: YYYY-MM-DD (required)
- `end_date`: YYYY-MM-DD (required)

**Response:**
- CSV file download

---

### `GET /export/summary-json`
Export summary as JSON.

**Headers:**
- `Authorization: Bearer TOKEN`

**Query Parameters:**
- `period`: "week" or "month" (default: "week")

**Response:**
```json
{
  "total_earnings": 7700,
  "total_expenses": 3850,
  ...
}
```

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "detail": "Error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Missing or invalid Authorization header"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message"
}
```

---

## Rate Limits

No rate limits currently enforced. Consider implementing rate limiting in production.

---

## Testing with cURL

### Upload Audio
```bash
curl -X POST http://localhost:8000/process \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@audio.wav"
```

### Get Summary
```bash
curl http://localhost:8000/ledger/summary?period=week \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Export PDF
```bash
curl http://localhost:8000/export/income-statement?period=week \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o income_statement.pdf
```

---

## WebSocket Support

Not currently implemented. All endpoints are REST-based.

---

## API Versioning

Current version: v1 (implicit)
No version prefix in URLs yet.

---

**Last Updated:** March 28, 2026  
**API Version:** 1.0
