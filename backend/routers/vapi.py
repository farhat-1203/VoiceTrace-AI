"""
VAPI Webhook API Routes - Handle VAPI custom voice agent callbacks

VAPI Integration Flow:
1. User completes 3-min audio recording
2. System processes and extracts data
3. If triggers detected (mood, confidence, stock-outs):
   - VAPI custom agent is activated
   - Agent engages with user in real-time
   - Clarifications are collected
   - Data is updated
4. Webhooks notify backend of agent interactions

Note: VAPI is a custom voice agent (not phone-based)
- Inbound: User asks questions, agent responds
- Outbound: Agent proactively asks for clarifications
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from services.vapi_service import vapi_service
from services.supabase_service import supabase_service


router = APIRouter(prefix="/vapi", tags=["vapi"])


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

class VAPICallStartRequest(BaseModel):
    call_id: str
    user_id: str
    call_type: str  # 'clarification', 'mood_check', 'stock_alert'
    trigger_reason: Optional[str] = None


class VAPICallEndRequest(BaseModel):
    call_id: str
    user_id: str
    duration_seconds: int
    transcript: Optional[str] = None
    outcome: str  # 'completed', 'no_answer', 'failed'
    clarifications_resolved: Optional[list[dict]] = None


class VAPIMessageRequest(BaseModel):
    call_id: str
    user_id: str
    message: str
    role: str  # 'user' or 'assistant'


# ═══════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════

@router.post("/webhook/call-start")
async def vapi_call_start(
    data: VAPICallStartRequest,
    request: Request,
):
    """
    VAPI webhook: Custom agent session started.
    
    Called when VAPI custom agent begins interaction with the vendor.
    This is NOT a phone call - it's a real-time voice agent session.
    """
    logger.info(f"VAPI agent session started: {data.call_id} for user {data.user_id}")
    
    # Log the call
    log_id = vapi_service.log_vapi_call(
        user_id=data.user_id,
        call_id=data.call_id,
        call_type=data.call_type,
        trigger_reason=data.trigger_reason,
    )
    
    return {
        "success": True,
        "log_id": log_id,
        "message": "Call start logged",
    }


@router.post("/webhook/call-end")
async def vapi_call_end(
    data: VAPICallEndRequest,
    request: Request,
):
    """
    VAPI webhook: Custom agent session ended.
    
    Called when VAPI agent session completes. Updates session log and processes clarifications.
    """
    logger.info(f"VAPI agent session ended: {data.call_id} - outcome: {data.outcome}")
    
    # Update call log
    try:
        supabase_service._client.table("vapi_calls")\
            .update({
                "duration_seconds": data.duration_seconds,
                "transcript": data.transcript,
                "outcome": data.outcome,
            })\
            .eq("call_id", data.call_id)\
            .execute()
    except Exception as e:
        logger.error(f"Failed to update call log: {e}")
    
    # Process clarifications if provided
    if data.clarifications_resolved:
        for clarification in data.clarifications_resolved:
            clarification_id = clarification.get("clarification_id")
            resolved_data = clarification.get("resolved_data")
            
            if clarification_id and resolved_data:
                vapi_service.resolve_clarification(
                    clarification_id=clarification_id,
                    resolved_data=resolved_data,
                )
    
    return {
        "success": True,
        "message": "Call end processed",
        "clarifications_resolved": len(data.clarifications_resolved or []),
    }


@router.post("/webhook/message")
async def vapi_message(
    data: VAPIMessageRequest,
    request: Request,
):
    """
    VAPI webhook: Message received during agent session.
    
    Called for each message in the real-time conversation between vendor and agent.
    Can be used for real-time processing or logging.
    """
    logger.debug(f"VAPI message: {data.call_id} - {data.role}: {data.message[:50]}...")
    
    # Could store messages for analysis
    # For now, just acknowledge
    
    return {
        "success": True,
        "message": "Message received",
    }


@router.get("/clarifications")
async def get_pending_clarifications(
    authorization: str = Depends(lambda: None),
):
    """
    Get pending clarifications for the current user.
    
    Returns items that need VAPI follow-up.
    """
    user = await get_current_user(authorization)
    
    clarifications = vapi_service.get_pending_clarifications(
        user_id=user["id"],
        limit=20,
    )
    
    return {
        "clarifications": clarifications,
        "count": len(clarifications),
    }


@router.get("/call-history")
async def get_call_history(
    limit: int = 20,
    authorization: str = Depends(lambda: None),
):
    """
    Get VAPI agent session history for the current user.
    
    Returns past agent sessions with outcomes and transcripts.
    """
    user = await get_current_user(authorization)
    
    history = vapi_service.get_call_history(
        user_id=user["id"],
        limit=limit,
    )
    
    return {
        "calls": history,
        "count": len(history),
    }


@router.get("/mood-trend")
async def get_mood_trend(
    days: int = 7,
    authorization: str = Depends(lambda: None),
):
    """
    Analyze mood trends over time.
    
    Returns average mood score and trend direction.
    """
    user = await get_current_user(authorization)
    
    trend = vapi_service.analyze_mood_trend(
        user_id=user["id"],
        days=days,
    )
    
    return trend


@router.post("/trigger-check")
async def check_vapi_trigger(
    transcription_id: str,
    authorization: str = Depends(lambda: None),
):
    """
    Check if VAPI custom agent should be triggered for a transcription.
    
    Analyzes mood and confidence scores to determine if real-time agent interaction is needed.
    """
    user = await get_current_user(authorization)
    
    try:
        # Get transcription
        result = supabase_service._client.table("transcriptions")\
            .select("extracted_data")\
            .eq("id", transcription_id)\
            .eq("user_id", user["id"])\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        extracted_data = result.data.get("extracted_data", {})
        
        # Calculate confidence scores
        confidence_scores = {}
        for idx, item in enumerate(extracted_data.get("items_sold", [])):
            # Simple confidence calculation
            score = 0.5
            if item.get("quantity"):
                score += 0.25
            if item.get("unit_price"):
                score += 0.25
            confidence_scores[f"item_{idx}"] = score
        
        # Check if trigger needed
        should_trigger, reason = vapi_service.should_trigger_call(
            extracted_data=extracted_data,
            confidence_scores=confidence_scores,
        )
        
        return {
            "should_trigger": should_trigger,
            "reason": reason,
            "extracted_data": extracted_data,
            "confidence_scores": confidence_scores,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resolve-clarification/{clarification_id}")
async def resolve_clarification(
    clarification_id: str,
    resolved_data: dict,
    authorization: str = Depends(lambda: None),
):
    """
    Manually resolve a clarification.
    
    Updates the clarification with resolved data.
    """
    user = await get_current_user(authorization)
    
    # Verify ownership
    try:
        check = supabase_service._client.table("pending_clarifications")\
            .select("id")\
            .eq("id", clarification_id)\
            .eq("user_id", user["id"])\
            .single()\
            .execute()
        
        if not check.data:
            raise HTTPException(status_code=404, detail="Clarification not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Resolve
    success = vapi_service.resolve_clarification(
        clarification_id=clarification_id,
        resolved_data=resolved_data,
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to resolve clarification")
    
    return {
        "success": True,
        "message": "Clarification resolved successfully",
    }


@router.post("/start-session")
async def start_agent_session(
    transcription_id: str,
    session_type: str,
    authorization: str = Depends(lambda: None),
):
    """
    Start a VAPI custom agent session (not phone-based).
    
    Initiates a real-time voice interaction through the app interface.
    The agent can ask clarifying questions, provide insights, or respond to queries.
    
    Session types:
    - clarification: Ask about uncertain items
    - mood_check: Follow up on negative sentiment
    - stock_alert: Discuss stock-out issues
    - query: General vendor questions
    """
    user = await get_current_user(authorization)
    
    try:
        # Get transcription data
        result = supabase_service._client.table("transcriptions")\
            .select("extracted_data")\
            .eq("id", transcription_id)\
            .eq("user_id", user["id"])\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        extracted_data = result.data.get("extracted_data", {})
        
        # Prepare context for agent
        context_data = {
            "transcription_id": transcription_id,
            "extracted_data": extracted_data,
            "session_type": session_type,
        }
        
        # Get pending clarifications if clarification session
        if session_type == "clarification":
            clarifications = vapi_service.get_pending_clarifications(
                user_id=user["id"],
                limit=10,
            )
            context_data["clarifications"] = clarifications
        
        # Trigger agent session
        session_id = vapi_service.trigger_agent_session(
            user_id=user["id"],
            transcription_id=transcription_id,
            session_type=session_type,
            context_data=context_data,
        )
        
        if not session_id:
            raise HTTPException(status_code=500, detail="Failed to start agent session")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Agent session started successfully",
            "context": context_data,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
