# VoiceTrace AI - Immediate Next Steps

## Current Status

✅ **Completed:**
- Live voice recording feature
- Language detection (Hindi/English/Hinglish)
- Enhanced database schema for vendor ledger
- Transcript-first display
- OAuth improvements

⚠️ **Needs Fixing:**
- OAuth authentication error

🔨 **Ready to Implement:**
- Ledger entry creation
- Pattern detection
- VAPI integration

## Step 1: Fix OAuth (CRITICAL)

### Do This First:

1. **Google Cloud Console** (https://console.cloud.google.com/)
   - Go to: APIs & Services → Credentials
   - Click your OAuth 2.0 Client ID
   - Add these Authorized redirect URIs:
     ```
     https://dgrsyrtupqpmqgxsqcsp.supabase.co/auth/v1/callback
     http://localhost:8501
     ```
     (Replace `dgrsyrtupqpmqgxsqcsp` with your actual Supabase project ref)

2. **Supabase Dashboard** (https://supabase.com/dashboard)
   - Go to: Authentication → Providers → Google
   - Enable it and add your Google Client ID and Secret
   - Go to: Authentication → URL Configuration
   - Site URL: `http://localhost:8501`
   - Redirect URLs: Add `http://localhost:8501` and `http://localhost:8501/**`

3. **Run the migration:**
   - Go to Supabase Dashboard → SQL Editor
   - Create new query
   - Paste contents of `migrations/002_vendor_ledger_schema.sql`
   - Run it

4. **Rebuild containers:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

5. **Test:**
   - Go to http://localhost:8501
   - Click "Sign in with Google"
   - Should work now!

## Step 2: Test Current Features

Once OAuth works, test:

1. **Live Recording:**
   - Click "Record Audio" tab
   - Click microphone icon
   - Speak for 10-20 seconds
   - Click microphone again to stop
   - Click "Process Audio"

2. **Language Detection:**
   - Try recording in English
   - Try recording in Hindi
   - Try recording in Hinglish (mix)
   - Check the detected language in backend logs

3. **File Upload:**
   - Switch to "Upload File" tab
   - Upload a WAV/MP3 file
   - Process it

## Step 3: Implement Ledger Creation

Create `backend/services/ledger_service.py`:

```python
"""
Ledger Service - Converts transcription data into structured ledger entries
"""
from datetime import date
from typing import Optional
from loguru import logger
from services.supabase_service import supabase_service

class LedgerService:
    def create_entry_from_transcription(
        self,
        user_id: str,
        transcription_id: str,
        extracted_data: dict,
    ) -> Optional[str]:
        """
        Create a ledger entry from extracted transcription data.
        
        Returns ledger_entry_id or None on failure.
        """
        # Get or create today's ledger entry
        entry_date = date.today()
        
        # Create ledger entry
        ledger_entry = {
            "user_id": user_id,
            "transcription_id": transcription_id,
            "entry_date": entry_date.isoformat(),
            "total_earnings": 0,
            "total_expenses": 0,
        }
        
        # Insert or update
        result = supabase_service._client.table("ledger_entries").upsert(
            ledger_entry,
            on_conflict="user_id,entry_date"
        ).execute()
        
        ledger_entry_id = result.data[0]["id"]
        
        # Add items sold
        items = extracted_data.get("items_sold", [])
        for item in items:
            self._add_ledger_item(ledger_entry_id, item)
        
        # Add expenses
        expenses = extracted_data.get("expenses", [])
        for expense in expenses:
            self._add_ledger_expense(ledger_entry_id, expense)
        
        logger.info(f"Created ledger entry {ledger_entry_id} for user {user_id}")
        return ledger_entry_id
    
    def _add_ledger_item(self, ledger_entry_id: str, item: dict):
        """Add a sold item to the ledger."""
        confidence = self._calculate_confidence(item)
        
        ledger_item = {
            "ledger_entry_id": ledger_entry_id,
            "item_name": item.get("name", "Unknown item"),
            "quantity": item.get("quantity"),
            "unit_price": item.get("unit_price"),
            "total_amount": item.get("total_amount", 0),
            "confidence_score": confidence,
            "needs_confirmation": confidence < 0.7,
        }
        
        supabase_service._client.table("ledger_items").insert(ledger_item).execute()
    
    def _add_ledger_expense(self, ledger_entry_id: str, expense: dict):
        """Add an expense to the ledger."""
        confidence = self._calculate_confidence(expense)
        
        ledger_expense = {
            "ledger_entry_id": ledger_entry_id,
            "expense_type": expense.get("type", "other"),
            "description": expense.get("description", ""),
            "amount": expense.get("amount", 0),
            "confidence_score": confidence,
            "needs_confirmation": confidence < 0.7,
        }
        
        supabase_service._client.table("ledger_expenses").insert(ledger_expense).execute()
    
    def _calculate_confidence(self, item: dict) -> float:
        """
        Calculate confidence score based on data completeness.
        
        Returns: 0.0 to 1.0
        """
        score = 0.5  # Base score
        
        # Has quantity
        if item.get("quantity") is not None:
            score += 0.2
        
        # Has price
        if item.get("unit_price") or item.get("amount"):
            score += 0.2
        
        # Has specific name (not "something" or "items")
        name = item.get("name", "").lower()
        if name and name not in ["something", "items", "things", "stuff"]:
            score += 0.1
        
        return min(score, 1.0)

ledger_service = LedgerService()
```

Then call it from `main.py` after the pipeline completes.

## Step 4: Add VAPI Query Endpoint

Add to `backend/main.py`:

```python
@app.post("/vapi/query")
async def vapi_query(
    query: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Natural language query endpoint for VAPI voice agent.
    
    Examples:
    - "What did I sell yesterday?"
    - "How much profit did I make this week?"
    - "What are my best-selling items?"
    """
    user_id = current_user["id"]
    
    # Simple keyword matching (enhance with LLM later)
    query_lower = query.lower()
    
    if "yesterday" in query_lower or "today" in query_lower:
        # Get recent ledger entries
        entries = supabase_service._client.table("ledger_entries")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("entry_date", desc=True)\
            .limit(2)\
            .execute()
        
        return {"entries": entries.data}
    
    elif "best" in query_lower or "top" in query_lower:
        # Get best-selling items
        patterns = supabase_service._client.table("vendor_patterns")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("pattern_type", "best_seller")\
            .order("metric_value", desc=True)\
            .limit(5)\
            .execute()
        
        return {"patterns": patterns.data}
    
    else:
        # Default: return recent transcriptions
        transcriptions = supabase_service.get_transcriptions_by_user(
            user_id=user_id,
            limit=5
        )
        
        return {"transcriptions": transcriptions}
```

## Step 5: Build Pattern Detection

Create `backend/services/pattern_service.py`:

```python
"""
Pattern Detection Service - Analyzes vendor business patterns
"""
from datetime import datetime, timedelta
from collections import Counter
from loguru import logger
from services.supabase_service import supabase_service

class PatternService:
    def analyze_patterns(self, user_id: str):
        """
        Analyze business patterns for a vendor.
        Requires at least 4 days of data.
        """
        # Get last 30 days of ledger entries
        cutoff = (datetime.now() - timedelta(days=30)).date()
        
        entries = supabase_service._client.table("ledger_entries")\
            .select("*, ledger_items(*)")\
            .eq("user_id", user_id)\
            .gte("entry_date", cutoff.isoformat())\
            .execute()
        
        if len(entries.data) < 4:
            logger.info(f"Not enough data for pattern analysis (need 4+ days, have {len(entries.data)})")
            return
        
        # Analyze best sellers
        self._analyze_best_sellers(user_id, entries.data)
        
        # Analyze high-earning days
        self._analyze_high_days(user_id, entries.data)
        
        # Analyze expense trends
        self._analyze_expense_trends(user_id, entries.data)
    
    def _analyze_best_sellers(self, user_id: str, entries: list):
        """Find most frequently sold items."""
        item_counter = Counter()
        item_revenue = {}
        
        for entry in entries:
            for item in entry.get("ledger_items", []):
                name = item["item_name"]
                item_counter[name] += 1
                item_revenue[name] = item_revenue.get(name, 0) + float(item.get("total_amount", 0))
        
        # Store top 5 best sellers
        for item_name, frequency in item_counter.most_common(5):
            pattern = {
                "user_id": user_id,
                "pattern_type": "best_seller",
                "item_name": item_name,
                "metric_value": item_revenue.get(item_name, 0),
                "frequency": frequency,
            }
            
            supabase_service._client.table("vendor_patterns").upsert(
                pattern,
                on_conflict="user_id,pattern_type,item_name,day_of_week"
            ).execute()
    
    def _analyze_high_days(self, user_id: str, entries: list):
        """Find which days of week have highest earnings."""
        day_earnings = {i: [] for i in range(7)}  # 0=Sunday, 6=Saturday
        
        for entry in entries:
            entry_date = datetime.fromisoformat(entry["entry_date"])
            day_of_week = entry_date.weekday()
            earnings = float(entry.get("total_earnings", 0))
            day_earnings[day_of_week].append(earnings)
        
        # Calculate average per day
        for day, earnings_list in day_earnings.items():
            if earnings_list:
                avg_earnings = sum(earnings_list) / len(earnings_list)
                
                pattern = {
                    "user_id": user_id,
                    "pattern_type": "high_day",
                    "day_of_week": day,
                    "metric_value": avg_earnings,
                    "frequency": len(earnings_list),
                }
                
                supabase_service._client.table("vendor_patterns").upsert(
                    pattern,
                    on_conflict="user_id,pattern_type,item_name,day_of_week"
                ).execute()
    
    def _analyze_expense_trends(self, user_id: str, entries: list):
        """Detect if expenses are trending up or down."""
        # Implementation here
        pass

pattern_service = PatternService()
```

## Step 6: Run Pattern Detection Daily

Add a cron job or scheduled task:

```python
# In main.py, add endpoint for manual trigger
@app.post("/admin/analyze-patterns")
async def trigger_pattern_analysis(current_user: dict = Depends(get_current_user)):
    """Manually trigger pattern analysis for current user."""
    from services.pattern_service import pattern_service
    pattern_service.analyze_patterns(current_user["id"])
    return {"status": "completed"}
```

## Step 7: Test End-to-End

1. Record 4-5 voice notes over different days
2. Check ledger entries are created
3. Trigger pattern analysis
4. Query via VAPI endpoint
5. Verify patterns are detected

## Step 8: Migrate to Expo App

Once backend is solid:

1. Set up Expo project (already exists in `expoApp/voicetrace/`)
2. Implement voice recording in React Native
3. Connect to backend API
4. Add push notifications for anomalies
5. Implement offline support

## Priority Order

1. **Fix OAuth** ← DO THIS FIRST
2. **Test current features**
3. **Implement ledger creation**
4. **Add VAPI endpoints**
5. **Build pattern detection**
6. **Create anomaly alerts**
7. **Add stock suggestions**
8. **PDF export**
9. **Migrate to Expo**

## Questions to Answer

- [ ] Is OAuth working now?
- [ ] Can you record and transcribe audio?
- [ ] Is language detection showing correct results?
- [ ] Are you ready to implement ledger creation?
- [ ] Do you want to start with VAPI integration or pattern detection first?

## Resources

- **OAuth Fix**: See `OAUTH_FIX_README.md`
- **All Changes**: See `CHANGES_SUMMARY.md`
- **Full Plan**: See `IMPLEMENTATION_PLAN.md`
- **Database Schema**: See `migrations/002_vendor_ledger_schema.sql`

Let me know which step you want to tackle next!
