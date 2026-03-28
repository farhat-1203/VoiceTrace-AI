"""
Anomaly Detection API Routes - Detect unusual business activity
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from services.pattern_service import pattern_service
from services.supabase_service import supabase_service


router = APIRouter(prefix="/anomalies", tags=["anomalies"])


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

@router.get("/recent")
async def get_recent_anomalies(
    limit: int = Query(20, ge=1, le=100, description="Number of anomalies to return"),
    severity: Optional[str] = Query(None, regex="^(low|medium|high)$", description="Filter by severity"),
    authorization: str = Depends(lambda: None),
):
    """
    Get recent anomaly alerts.
    
    Returns detected anomalies sorted by date (newest first).
    """
    user = await get_current_user(authorization)
    
    try:
        query = supabase_service._client.table("anomaly_alerts")\
            .select("*")\
            .eq("user_id", user["id"])\
            .order("detected_at", desc=True)\
            .limit(limit)
        
        if severity:
            query = query.eq("severity", severity)
        
        result = query.execute()
        
        return {
            "anomalies": result.data or [],
            "count": len(result.data) if result.data else 0,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unresolved")
async def get_unresolved_anomalies(
    authorization: str = Depends(lambda: None),
):
    """
    Get unresolved anomaly alerts.
    
    Returns anomalies that haven't been acknowledged or resolved.
    """
    user = await get_current_user(authorization)
    
    try:
        result = supabase_service._client.table("anomaly_alerts")\
            .select("*")\
            .eq("user_id", user["id"])\
            .eq("is_resolved", False)\
            .order("severity", desc=True)\
            .order("detected_at", desc=True)\
            .execute()
        
        return {
            "anomalies": result.data or [],
            "count": len(result.data) if result.data else 0,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resolve/{anomaly_id}")
async def resolve_anomaly(
    anomaly_id: str,
    authorization: str = Depends(lambda: None),
):
    """
    Mark an anomaly as resolved.
    
    Updates the anomaly status to resolved.
    """
    user = await get_current_user(authorization)
    
    try:
        # Verify ownership
        check = supabase_service._client.table("anomaly_alerts")\
            .select("id")\
            .eq("id", anomaly_id)\
            .eq("user_id", user["id"])\
            .single()\
            .execute()
        
        if not check.data:
            raise HTTPException(status_code=404, detail="Anomaly not found")
        
        # Update status
        from datetime import datetime
        supabase_service._client.table("anomaly_alerts")\
            .update({
                "is_resolved": True,
                "resolved_at": datetime.utcnow().isoformat(),
            })\
            .eq("id", anomaly_id)\
            .execute()
        
        return {
            "success": True,
            "message": "Anomaly marked as resolved",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect")
async def detect_anomalies(
    ledger_entry_id: str = Query(..., description="Ledger entry ID to check"),
    authorization: str = Depends(lambda: None),
):
    """
    Run anomaly detection on a specific ledger entry.
    
    Checks for unusual earnings, expenses, or patterns.
    """
    user = await get_current_user(authorization)
    
    anomalies = pattern_service.detect_anomalies(
        user_id=user["id"],
        ledger_entry_id=ledger_entry_id,
    )
    
    return {
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies,
    }


@router.get("/stats")
async def get_anomaly_stats(
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    authorization: str = Depends(lambda: None),
):
    """
    Get anomaly statistics over a period.
    
    Returns count by severity and type.
    """
    user = await get_current_user(authorization)
    
    try:
        from datetime import date, timedelta
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        result = supabase_service._client.table("anomaly_alerts")\
            .select("*")\
            .eq("user_id", user["id"])\
            .gte("detected_at", start_date)\
            .execute()
        
        anomalies = result.data or []
        
        # Count by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0}
        type_counts = {}
        resolved_count = 0
        
        for anomaly in anomalies:
            severity = anomaly.get("severity", "medium")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            anomaly_type = anomaly.get("anomaly_type", "unknown")
            type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1
            
            if anomaly.get("is_resolved"):
                resolved_count += 1
        
        return {
            "total_anomalies": len(anomalies),
            "by_severity": severity_counts,
            "by_type": type_counts,
            "resolved": resolved_count,
            "unresolved": len(anomalies) - resolved_count,
            "period_days": days,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
