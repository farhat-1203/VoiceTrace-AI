"""
Ledger API Routes - Access and manage vendor ledger entries
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.ledger_service import ledger_service
from services.supabase_service import supabase_service


router = APIRouter(prefix="/ledger", tags=["ledger"])


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
#  Request/Response Models
# ═══════════════════════════════════════════════════════════════════════

class ConfirmItemRequest(BaseModel):
    item_name: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════

@router.get("/entries")
async def get_ledger_entries(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    authorization: str = Depends(lambda: None),
):
    """
    Get ledger entries for a date range.
    
    Returns entries with items and expenses included.
    """
    user = await get_current_user(authorization)
    
    entries = ledger_service.get_entries_by_date_range(
        user_id=user["id"],
        start_date=start_date,
        end_date=end_date,
    )
    
    return {
        "entries": entries,
        "count": len(entries),
    }


@router.get("/entries/{entry_id}")
async def get_ledger_entry(
    entry_id: str,
    authorization: str = Depends(lambda: None),
):
    """Get a single ledger entry by ID."""
    user = await get_current_user(authorization)
    
    try:
        result = supabase_service._client.table("ledger_entries")\
            .select("*, ledger_items(*), ledger_expenses(*)")\
            .eq("id", entry_id)\
            .eq("user_id", user["id"])\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Ledger entry not found")
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_ledger_summary(
    period: str = Query("week", regex="^(week|month)$"),
    authorization: str = Depends(lambda: None),
):
    """
    Get aggregated summary for a period.
    
    Returns total earnings, expenses, net profit, top items, and top expenses.
    """
    user = await get_current_user(authorization)
    
    summary = ledger_service.get_summary(
        user_id=user["id"],
        period=period,
    )
    
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to generate summary")
    
    return summary


@router.get("/unconfirmed")
async def get_unconfirmed_items(
    authorization: str = Depends(lambda: None),
):
    """
    Get items that need confirmation (confidence < 0.7).
    
    These items should be clarified via VAPI or manual review.
    """
    user = await get_current_user(authorization)
    
    items = ledger_service.get_unconfirmed_items(user_id=user["id"])
    
    return {
        "items": items,
        "count": len(items),
    }


@router.post("/confirm/{item_id}")
async def confirm_item(
    item_id: str,
    data: ConfirmItemRequest,
    authorization: str = Depends(lambda: None),
):
    """
    Confirm and update an uncertain item.
    
    Updates the item with confirmed data and sets confidence to 1.0.
    """
    user = await get_current_user(authorization)
    
    # Build update dict from provided fields
    confirmed_data = {}
    if data.item_name is not None:
        confirmed_data["item_name"] = data.item_name
    if data.quantity is not None:
        confirmed_data["quantity"] = data.quantity
    if data.unit_price is not None:
        confirmed_data["unit_price"] = data.unit_price
    if data.total_amount is not None:
        confirmed_data["total_amount"] = data.total_amount
    
    success = ledger_service.confirm_item(
        item_id=item_id,
        user_id=user["id"],
        confirmed_data=confirmed_data,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Item not found or update failed")
    
    return {
        "success": True,
        "message": "Item confirmed successfully",
    }


@router.get("/stats")
async def get_ledger_stats(
    authorization: str = Depends(lambda: None),
):
    """
    Get overall ledger statistics.
    
    Returns total entries, total items, total expenses, and date range.
    """
    user = await get_current_user(authorization)
    
    try:
        # Get entry count
        entries_result = supabase_service._client.table("ledger_entries")\
            .select("id", count="exact")\
            .eq("user_id", user["id"])\
            .execute()
        
        # Get item count
        items_result = supabase_service._client.table("ledger_items")\
            .select("id", count="exact")\
            .eq("ledger_entries.user_id", user["id"])\
            .execute()
        
        # Get expense count
        expenses_result = supabase_service._client.table("ledger_expenses")\
            .select("id", count="exact")\
            .eq("ledger_entries.user_id", user["id"])\
            .execute()
        
        # Get date range
        date_range_result = supabase_service._client.table("ledger_entries")\
            .select("entry_date")\
            .eq("user_id", user["id"])\
            .order("entry_date", desc=False)\
            .limit(1)\
            .execute()
        
        first_date = date_range_result.data[0]["entry_date"] if date_range_result.data else None
        
        return {
            "total_entries": entries_result.count or 0,
            "total_items": items_result.count or 0,
            "total_expenses": expenses_result.count or 0,
            "first_entry_date": first_date,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
