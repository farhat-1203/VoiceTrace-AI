"""
Stock Suggestion API Routes - Inventory recommendations for next day
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from services.stock_suggestion_service import stock_suggestion_service
from services.supabase_service import supabase_service


router = APIRouter(prefix="/suggestions", tags=["suggestions"])


# ═══════════════════════════════════════════════════════════════════════
#  Auth Dependency
# ═══════════════════════════════════════════════════════════════════════

async def get_current_user(authorization: Optional[str] = None) -> dict:
    """Extract and validate user from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.replace("Bearer ", "")
    user = supabase_service.get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


# ═══════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════

@router.get("/next-day")
async def get_next_day_suggestions(
    authorization: str = Depends(lambda: None),
):
    """
    Get stock suggestions for the next day.
    
    Based on sell-through rates, stock-outs, and historical patterns.
    Returns recommended quantities for each item.
    """
    user = await get_current_user(authorization)
    
    suggestions = stock_suggestion_service.generate_next_day_suggestions(
        user_id=user["id"]
    )
    
    if not suggestions:
        raise HTTPException(
            status_code=400,
            detail="Insufficient data to generate suggestions. Need at least 3 days of ledger entries."
        )
    
    return {
        "suggestions": suggestions,
        "count": len(suggestions),
        "generated_at": suggestions[0].get("created_at") if suggestions else None,
    }


@router.get("/latest")
async def get_latest_suggestions(
    authorization: str = Depends(lambda: None),
):
    """
    Get the most recent stock suggestions.
    
    Returns stored suggestions from stock_suggestions table.
    """
    user = await get_current_user(authorization)
    
    try:
        result = supabase_service._client.table("stock_suggestions")\
            .select("*")\
            .eq("user_id", user["id"])\
            .order("created_at", desc=True)\
            .limit(20)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="No suggestions found. Run GET /suggestions/next-day first."
            )
        
        return {
            "suggestions": result.data,
            "count": len(result.data),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/item/{item_name}")
async def get_item_suggestion(
    item_name: str,
    authorization: str = Depends(lambda: None),
):
    """
    Get suggestion for a specific item.
    
    Returns the most recent suggestion for the given item.
    """
    user = await get_current_user(authorization)
    
    try:
        result = supabase_service._client.table("stock_suggestions")\
            .select("*")\
            .eq("user_id", user["id"])\
            .eq("item_name", item_name)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"No suggestion found for item: {item_name}"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_suggestions(
    days: int = Query(7, ge=3, le=30, description="Number of days to analyze"),
    authorization: str = Depends(lambda: None),
):
    """
    Generate fresh stock suggestions.
    
    Analyzes recent sales data and creates new suggestions.
    """
    user = await get_current_user(authorization)
    
    suggestions = stock_suggestion_service.generate_next_day_suggestions(
        user_id=user["id"],
        lookback_days=days,
    )
    
    if not suggestions:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data. Need at least 3 days of ledger entries."
        )
    
    return {
        "success": True,
        "suggestions": suggestions,
        "count": len(suggestions),
        "message": "Stock suggestions generated successfully",
    }


@router.get("/accuracy")
async def get_suggestion_accuracy(
    days: int = Query(7, ge=3, le=30, description="Number of days to analyze"),
    authorization: str = Depends(lambda: None),
):
    """
    Analyze suggestion accuracy.
    
    Compares suggested quantities with actual sales.
    """
    user = await get_current_user(authorization)
    
    accuracy = stock_suggestion_service.calculate_suggestion_accuracy(
        user_id=user["id"],
        days=days,
    )
    
    return accuracy


@router.get("/stock-outs")
async def get_stock_out_history(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    authorization: str = Depends(lambda: None),
):
    """
    Get history of stock-out incidents.
    
    Returns items that ran out of stock and when.
    """
    user = await get_current_user(authorization)
    
    stock_outs = stock_suggestion_service.get_stock_out_history(
        user_id=user["id"],
        days=days,
    )
    
    return {
        "stock_outs": stock_outs,
        "count": len(stock_outs),
        "period_days": days,
    }
