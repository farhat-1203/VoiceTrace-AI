"""
VAPI Function Calling - Tools/Functions that VAPI agent can call
These functions are exposed to VAPI for real-time data access and operations
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Any, Literal
from datetime import date, timedelta
from loguru import logger

from services.ledger_service import ledger_service
from services.pattern_service import pattern_service
from services.stock_suggestion_service import stock_suggestion_service
from services.vapi_service import vapi_service
from services.supabase_service import supabase_service


router = APIRouter(prefix="/vapi/functions", tags=["vapi-functions"])


# ═══════════════════════════════════════════════════════════════════════
#  Request/Response Models
# ═══════════════════════════════════════════════════════════════════════

class FunctionCallRequest(BaseModel):
    """Request from VAPI to execute a function."""
    function_name: str
    parameters: dict[str, Any]
    user_id: str
    session_id: str


class FunctionCallResponse(BaseModel):
    """Response to VAPI after function execution."""
    success: bool
    result: Any
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════
#  VAPI Function Definitions (OpenAI Function Calling Format)
# ═══════════════════════════════════════════════════════════════════════

VAPI_FUNCTIONS = [
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
        "name": "get_best_sellers",
        "description": "Get the best-selling items over a period",
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
    },
    {
        "name": "get_stock_suggestions",
        "description": "Get stock suggestions for tomorrow based on sales patterns",
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
        "name": "confirm_item",
        "description": "Confirm and update an uncertain item with correct details",
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
                    "description": "Confirmed unit price"
                }
            },
            "required": ["user_id", "item_id", "item_name", "quantity", "unit_price"]
        }
    },
    {
        "name": "get_unconfirmed_items",
        "description": "Get list of items that need clarification (low confidence)",
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
        "name": "get_recent_anomalies",
        "description": "Get recent unusual business activities or alerts",
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
    },
    {
        "name": "get_expense_breakdown",
        "description": "Get breakdown of expenses by type for a period",
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
    },
    {
        "name": "get_mood_trend",
        "description": "Get vendor's mood trend over time",
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
    },
    {
        "name": "search_past_records",
        "description": "Search past business records by date or item name",
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
]


# ═══════════════════════════════════════════════════════════════════════
#  Function Implementations
# ═══════════════════════════════════════════════════════════════════════

def execute_get_today_summary(user_id: str) -> dict:
    """Get today's business summary."""
    try:
        today = date.today()
        entries = ledger_service.get_entries_by_date_range(
            user_id=user_id,
            start_date=today.isoformat(),
            end_date=today.isoformat()
        )
        
        if not entries:
            return {
                "message": "आज का कोई डेटा नहीं मिला (No data found for today)",
                "has_data": False
            }
        
        entry = entries[0]
        items = entry.get("ledger_items", [])
        expenses = entry.get("ledger_expenses", [])
        
        return {
            "message": "आज का सारांश (Today's summary)",
            "has_data": True,
            "date": today.isoformat(),
            "total_earnings": entry.get("total_earnings", 0),
            "total_expenses": entry.get("total_expenses", 0),
            "net_profit": entry.get("total_earnings", 0) - entry.get("total_expenses", 0),
            "items_count": len(items),
            "expenses_count": len(expenses),
            "items": [
                {
                    "name": item.get("item_name"),
                    "quantity": item.get("quantity"),
                    "amount": item.get("total_amount")
                }
                for item in items[:5]
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_today_summary: {e}")
        return {"error": str(e), "has_data": False}


def execute_get_weekly_summary(user_id: str) -> dict:
    """Get weekly business summary."""
    try:
        summary = ledger_service.get_summary(user_id=user_id, period="week")
        
        if not summary or summary.get("days_count", 0) == 0:
            return {
                "message": "इस हफ्ते का कोई डेटा नहीं मिला (No data found for this week)",
                "has_data": False
            }
        
        return {
            "message": "इस हफ्ते का सारांश (This week's summary)",
            "has_data": True,
            "total_earnings": summary.get("total_earnings", 0),
            "total_expenses": summary.get("total_expenses", 0),
            "net_profit": summary.get("net_profit", 0),
            "days_count": summary.get("days_count", 0),
            "avg_daily_earnings": summary.get("avg_daily_earnings", 0),
            "top_items": summary.get("top_items", [])[:3]
        }
    except Exception as e:
        logger.error(f"Error in get_weekly_summary: {e}")
        return {"error": str(e), "has_data": False}


def execute_get_best_sellers(user_id: str, days: int = 7, limit: int = 5) -> dict:
    """Get best-selling items."""
    try:
        best_sellers = pattern_service.get_best_sellers(
            user_id=user_id,
            days=days,
            limit=limit
        )
        
        if not best_sellers:
            return {
                "message": "कोई बेस्ट सेलर नहीं मिला (No best sellers found)",
                "has_data": False
            }
        
        return {
            "message": f"पिछले {days} दिनों के बेस्ट सेलर (Best sellers from last {days} days)",
            "has_data": True,
            "items": best_sellers
        }
    except Exception as e:
        logger.error(f"Error in get_best_sellers: {e}")
        return {"error": str(e), "has_data": False}


def execute_get_stock_suggestions(user_id: str) -> dict:
    """Get stock suggestions for tomorrow."""
    try:
        suggestions = stock_suggestion_service.generate_next_day_suggestions(user_id=user_id)
        
        if not suggestions:
            return {
                "message": "स्टॉक सुझाव बनाने के लिए पर्याप्त डेटा नहीं है (Insufficient data for suggestions)",
                "has_data": False
            }
        
        return {
            "message": "कल के लिए स्टॉक सुझाव (Stock suggestions for tomorrow)",
            "has_data": True,
            "suggestions": [
                {
                    "item": s.get("item_name"),
                    "quantity": s.get("suggested_quantity"),
                    "reason": s.get("reason")
                }
                for s in suggestions[:5]
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_stock_suggestions: {e}")
        return {"error": str(e), "has_data": False}


def execute_confirm_item(user_id: str, item_id: str, item_name: str, quantity: float, unit_price: float) -> dict:
    """Confirm an uncertain item."""
    try:
        confirmed_data = {
            "item_name": item_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": quantity * unit_price
        }
        
        success = ledger_service.confirm_item(
            item_id=item_id,
            user_id=user_id,
            confirmed_data=confirmed_data
        )
        
        if success:
            return {
                "message": f"धन्यवाद! {item_name} का डेटा अपडेट हो गया (Thank you! {item_name} data updated)",
                "success": True,
                "confirmed_item": confirmed_data
            }
        else:
            return {
                "message": "आइटम अपडेट नहीं हो सका (Could not update item)",
                "success": False
            }
    except Exception as e:
        logger.error(f"Error in confirm_item: {e}")
        return {"error": str(e), "success": False}


def execute_get_unconfirmed_items(user_id: str) -> dict:
    """Get items needing clarification."""
    try:
        items = ledger_service.get_unconfirmed_items(user_id=user_id)
        
        if not items:
            return {
                "message": "सभी आइटम कन्फर्म हैं (All items are confirmed)",
                "has_data": False,
                "items": []
            }
        
        return {
            "message": f"{len(items)} आइटम को कन्फर्म करना है ({len(items)} items need confirmation)",
            "has_data": True,
            "items": [
                {
                    "id": item.get("id"),
                    "name": item.get("item_name"),
                    "quantity": item.get("quantity"),
                    "price": item.get("unit_price"),
                    "confidence": item.get("confidence_score")
                }
                for item in items[:5]
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_unconfirmed_items: {e}")
        return {"error": str(e), "has_data": False}


def execute_get_recent_anomalies(user_id: str, limit: int = 5) -> dict:
    """Get recent anomalies."""
    try:
        result = supabase_service._client.table("anomaly_alerts")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_resolved", False)\
            .order("detected_at", desc=True)\
            .limit(limit)\
            .execute()
        
        anomalies = result.data or []
        
        if not anomalies:
            return {
                "message": "कोई असामान्य गतिविधि नहीं मिली (No unusual activity found)",
                "has_data": False
            }
        
        return {
            "message": f"{len(anomalies)} असामान्य गतिविधियां मिलीं ({len(anomalies)} unusual activities found)",
            "has_data": True,
            "anomalies": [
                {
                    "type": a.get("anomaly_type"),
                    "description": a.get("description"),
                    "severity": a.get("severity"),
                    "date": a.get("detected_at")
                }
                for a in anomalies
            ]
        }
    except Exception as e:
        logger.error(f"Error in get_recent_anomalies: {e}")
        return {"error": str(e), "has_data": False}


def execute_get_expense_breakdown(user_id: str, days: int = 7) -> dict:
    """Get expense breakdown."""
    try:
        trends = pattern_service.get_expense_trends(user_id=user_id, days=days)
        
        if not trends or not trends.get("by_type"):
            return {
                "message": "खर्च का डेटा नहीं मिला (No expense data found)",
                "has_data": False
            }
        
        return {
            "message": f"पिछले {days} दिनों का खर्च (Expenses from last {days} days)",
            "has_data": True,
            "total_expenses": trends.get("total_expenses", 0),
            "by_type": trends.get("by_type", {}),
            "trend": trends.get("trend", "stable")
        }
    except Exception as e:
        logger.error(f"Error in get_expense_breakdown: {e}")
        return {"error": str(e), "has_data": False}


def execute_get_mood_trend(user_id: str, days: int = 7) -> dict:
    """Get mood trend."""
    try:
        trend = vapi_service.analyze_mood_trend(user_id=user_id, days=days)
        
        return {
            "message": f"पिछले {days} दिनों का मूड ट्रेंड (Mood trend from last {days} days)",
            "has_data": True,
            "average_mood": trend.get("average_mood_score", 3.0),
            "trend": trend.get("trend", "stable"),
            "negative_days": trend.get("negative_days", 0),
            "positive_days": trend.get("positive_days", 0)
        }
    except Exception as e:
        logger.error(f"Error in get_mood_trend: {e}")
        return {"error": str(e), "has_data": False}


def execute_search_past_records(user_id: str, query: str, days: int = 30) -> dict:
    """Search past records."""
    try:
        start_date = (date.today() - timedelta(days=days)).isoformat()
        end_date = date.today().isoformat()
        
        entries = ledger_service.get_entries_by_date_range(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Search in items
        matching_items = []
        for entry in entries:
            for item in entry.get("ledger_items", []):
                if query.lower() in item.get("item_name", "").lower():
                    matching_items.append({
                        "date": entry.get("entry_date"),
                        "item": item.get("item_name"),
                        "quantity": item.get("quantity"),
                        "amount": item.get("total_amount")
                    })
        
        if not matching_items:
            return {
                "message": f"'{query}' के लिए कोई रिकॉर्ड नहीं मिला (No records found for '{query}')",
                "has_data": False
            }
        
        return {
            "message": f"'{query}' के {len(matching_items)} रिकॉर्ड मिले (Found {len(matching_items)} records for '{query}')",
            "has_data": True,
            "records": matching_items[:10]
        }
    except Exception as e:
        logger.error(f"Error in search_past_records: {e}")
        return {"error": str(e), "has_data": False}


# Function dispatcher
FUNCTION_HANDLERS = {
    "get_today_summary": execute_get_today_summary,
    "get_weekly_summary": execute_get_weekly_summary,
    "get_best_sellers": execute_get_best_sellers,
    "get_stock_suggestions": execute_get_stock_suggestions,
    "confirm_item": execute_confirm_item,
    "get_unconfirmed_items": execute_get_unconfirmed_items,
    "get_recent_anomalies": execute_get_recent_anomalies,
    "get_expense_breakdown": execute_get_expense_breakdown,
    "get_mood_trend": execute_get_mood_trend,
    "search_past_records": execute_search_past_records,
}


# ═══════════════════════════════════════════════════════════════════════
#  API Routes
# ═══════════════════════════════════════════════════════════════════════

@router.get("/definitions")
async def get_function_definitions():
    """
    Get all available function definitions for VAPI.
    
    VAPI will call this to know what functions it can use.
    Returns OpenAI function calling format.
    """
    return {
        "functions": VAPI_FUNCTIONS,
        "count": len(VAPI_FUNCTIONS)
    }


@router.post("/execute")
async def execute_function(request: FunctionCallRequest = Body(...)):
    """
    Execute a function called by VAPI.
    
    VAPI sends function name and parameters, we execute and return result.
    """
    try:
        function_name = request.function_name
        parameters = request.parameters
        
        logger.info(f"VAPI function call: {function_name} with params: {parameters}")
        
        # Get handler
        handler = FUNCTION_HANDLERS.get(function_name)
        if not handler:
            return FunctionCallResponse(
                success=False,
                result=None,
                error=f"Unknown function: {function_name}"
            )
        
        # Execute function
        result = handler(**parameters)
        
        return FunctionCallResponse(
            success=True,
            result=result,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Error executing VAPI function: {e}")
        return FunctionCallResponse(
            success=False,
            result=None,
            error=str(e)
        )


@router.post("/batch-execute")
async def batch_execute_functions(
    functions: list[FunctionCallRequest] = Body(...)
):
    """
    Execute multiple functions in batch.
    
    Useful when VAPI needs to call multiple functions at once.
    """
    results = []
    
    for func_request in functions:
        try:
            handler = FUNCTION_HANDLERS.get(func_request.function_name)
            if handler:
                result = handler(**func_request.parameters)
                results.append({
                    "function": func_request.function_name,
                    "success": True,
                    "result": result
                })
            else:
                results.append({
                    "function": func_request.function_name,
                    "success": False,
                    "error": "Unknown function"
                })
        except Exception as e:
            results.append({
                "function": func_request.function_name,
                "success": False,
                "error": str(e)
            })
    
    return {
        "results": results,
        "total": len(results),
        "successful": sum(1 for r in results if r.get("success"))
    }
