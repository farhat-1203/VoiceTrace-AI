"""
Pattern Detection API Routes - Identify business patterns and trends
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from services.pattern_service import pattern_service
from services.supabase_service import supabase_service


router = APIRouter(prefix="/patterns", tags=["patterns"])


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

@router.get("/best-sellers")
async def get_best_sellers(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Number of items to return"),
    authorization: str = Depends(lambda: None),
):
    """
    Get best-selling items over a period.
    
    Returns items sorted by total revenue or sales count.
    """
    user = await get_current_user(authorization)
    
    best_sellers = pattern_service.get_best_sellers(
        user_id=user["id"],
        days=days,
        limit=limit,
    )
    
    return {
        "best_sellers": best_sellers,
        "period_days": days,
        "count": len(best_sellers),
    }


@router.get("/high-days")
async def get_high_earning_days(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    authorization: str = Depends(lambda: None),
):
    """
    Identify days with highest earnings.
    
    Returns day-of-week analysis and specific high-earning dates.
    """
    user = await get_current_user(authorization)
    
    high_days = pattern_service.get_high_earning_days(
        user_id=user["id"],
        days=days,
    )
    
    return high_days


@router.get("/expense-trends")
async def get_expense_trends(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    authorization: str = Depends(lambda: None),
):
    """
    Analyze expense trends over time.
    
    Returns expense breakdown by type and trend direction.
    """
    user = await get_current_user(authorization)
    
    trends = pattern_service.get_expense_trends(
        user_id=user["id"],
        days=days,
    )
    
    return trends


@router.post("/analyze")
async def analyze_patterns(
    min_days: int = Query(4, ge=4, le=30, description="Minimum days of data required"),
    authorization: str = Depends(lambda: None),
):
    """
    Run full pattern analysis and store results.
    
    Analyzes best sellers, high-earning days, and expense trends.
    Stores results in vendor_patterns table.
    """
    user = await get_current_user(authorization)
    
    pattern_id = pattern_service.analyze_and_store_patterns(
        user_id=user["id"],
        min_days=min_days,
    )
    
    if not pattern_id:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data. Need at least {min_days} days of ledger entries."
        )
    
    return {
        "success": True,
        "pattern_id": pattern_id,
        "message": "Pattern analysis completed successfully",
    }


@router.get("/latest")
async def get_latest_patterns(
    authorization: str = Depends(lambda: None),
):
    """
    Get the most recent pattern analysis results.
    
    Returns stored patterns from vendor_patterns table.
    """
    user = await get_current_user(authorization)
    
    try:
        result = supabase_service._client.table("vendor_patterns")\
            .select("*")\
            .eq("user_id", user["id"])\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=404,
                detail="No pattern analysis found. Run POST /patterns/analyze first."
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_pattern_history(
    limit: int = Query(10, ge=1, le=50, description="Number of analyses to return"),
    authorization: str = Depends(lambda: None),
):
    """
    Get historical pattern analyses.
    
    Returns past pattern analysis results for trend comparison.
    """
    user = await get_current_user(authorization)
    
    try:
        result = supabase_service._client.table("vendor_patterns")\
            .select("*")\
            .eq("user_id", user["id"])\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "patterns": result.data or [],
            "count": len(result.data) if result.data else 0,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
