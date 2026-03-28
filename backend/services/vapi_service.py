"""
VAPI Service - Handles VAPI custom voice agent integration
Manages mood detection, clarifications, and real-time vendor engagement

VAPI is used as a custom voice agent (not phone-based) that:
- Responds to user queries in real-time during/after 3-min recording
- Handles clarifications for uncertain items (low confidence)
- Detects mood and triggers follow-up conversations
- Provides inbound/outbound voice interactions without phone calls
- Fires automatically based on triggers (mood, confidence, stock-outs)
"""
from __future__ import annotations

import os
from typing import Optional
from datetime import datetime
from loguru import logger

from services.supabase_service import supabase_service


class VAPIService:
    """Manages VAPI custom voice agent interactions and webhooks."""
    
    def __init__(self):
        self.vapi_api_key = os.getenv("VAPI_API_KEY")
        self.vapi_assistant_id = os.getenv("VAPI_ASSISTANT_ID")
        self.vapi_webhook_url = os.getenv("VAPI_WEBHOOK_URL")
        
        if not self.vapi_api_key:
            logger.warning("VAPI_API_KEY not set - VAPI integration will not work")
    
    def should_trigger_call(
        self,
        extracted_data: dict,
        confidence_scores: dict,
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if VAPI agent session should be triggered based on mood or uncertainties.
        
        Args:
            extracted_data: Extracted business data from LLM
            confidence_scores: Confidence scores for items/expenses
        
        Returns:
            (should_trigger, reason)
        """
        # Check for negative mood
        sentiment = extracted_data.get("sentiment", "neutral")
        mood_score = extracted_data.get("mood_score", 3)
        mood_trigger = extracted_data.get("mood_trigger", False)
        
        if mood_trigger or sentiment == "bad" or mood_score <= 2:
            reason = extracted_data.get("mood_trigger_reason", "Vendor expressed negative sentiment")
            logger.info(f"VAPI trigger: Negative mood detected - {reason}")
            return True, reason
        
        # Check for low confidence items
        low_confidence_count = sum(
            1 for score in confidence_scores.values() 
            if score < 0.7
        )
        
        if low_confidence_count >= 3:
            reason = f"{low_confidence_count} items need clarification"
            logger.info(f"VAPI trigger: Multiple uncertainties - {reason}")
            return True, reason
        
        # Check for stock-out mentions
        stock_outs = extracted_data.get("stock_out_mentions", [])
        if stock_outs:
            reason = f"Stock-out mentioned: {', '.join(stock_outs)}"
            logger.info(f"VAPI trigger: Stock-out detected - {reason}")
            return True, reason
        
        return False, None
    
    def trigger_agent_session(
        self,
        user_id: str,
        transcription_id: str,
        session_type: str,
        context_data: dict,
    ) -> Optional[str]:
        """
        Trigger a VAPI custom agent session (not phone-based).
        
        This initiates a real-time voice interaction with the vendor
        through the app interface (not via phone call).
        
        Args:
            user_id: Vendor's user ID
            transcription_id: Reference to transcription
            session_type: 'clarification', 'mood_check', 'stock_alert', 'query'
            context_data: Context for the agent (items to clarify, mood info, etc.)
        
        Returns:
            Session ID or None on failure
        """
        try:
            # In a real implementation, this would call VAPI API to start a session
            # For now, we'll create a pending session record
            
            session_id = f"vapi-session-{datetime.utcnow().timestamp()}"
            
            # Log the session initiation
            self.log_vapi_call(
                user_id=user_id,
                call_id=session_id,
                call_type=session_type,
                trigger_reason=context_data.get("trigger_reason"),
            )
            
            logger.info(f"VAPI agent session triggered: {session_id} for user {user_id}")
            
            # TODO: Actual VAPI API call would go here
            # Example:
            # response = requests.post(
            #     "https://api.vapi.ai/v1/sessions",
            #     headers={"Authorization": f"Bearer {self.vapi_api_key}"},
            #     json={
            #         "assistant_id": self.vapi_assistant_id,
            #         "user_id": user_id,
            #         "context": context_data,
            #         "webhook_url": self.vapi_webhook_url,
            #     }
            # )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to trigger VAPI agent session: {e}")
            return None
    
    def create_pending_clarification(
        self,
        user_id: str,
        transcription_id: str,
        clarification_type: str,
        item_data: dict,
        priority: str = "medium",
    ) -> Optional[str]:
        """
        Create a pending clarification for VAPI to follow up on.
        
        Args:
            user_id: Vendor's user ID
            transcription_id: Reference to transcription
            clarification_type: 'item', 'expense', 'mood', 'stock_out'
            item_data: Data needing clarification
            priority: 'low', 'medium', 'high'
        
        Returns:
            Clarification ID or None
        """
        try:
            clarification = {
                "user_id": user_id,
                "transcription_id": transcription_id,
                "clarification_type": clarification_type,
                "item_data": item_data,
                "priority": priority,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }
            
            result = supabase_service._client.table("pending_clarifications")\
                .insert(clarification)\
                .execute()
            
            if result.data:
                clarification_id = result.data[0]["id"]
                logger.info(f"Created pending clarification: {clarification_id}")
                return clarification_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create pending clarification: {e}")
            return None
    
    def log_vapi_call(
        self,
        user_id: str,
        call_id: str,
        call_type: str,
        trigger_reason: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        transcript: Optional[str] = None,
        outcome: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log a VAPI call for tracking and analytics.
        
        Args:
            user_id: Vendor's user ID
            call_id: VAPI call ID
            call_type: 'clarification', 'mood_check', 'stock_alert'
            trigger_reason: Why the call was triggered
            duration_seconds: Call duration
            transcript: Call transcript
            outcome: 'completed', 'no_answer', 'failed'
        
        Returns:
            Log entry ID or None
        """
        try:
            call_log = {
                "user_id": user_id,
                "call_id": call_id,
                "call_type": call_type,
                "trigger_reason": trigger_reason,
                "duration_seconds": duration_seconds,
                "transcript": transcript,
                "outcome": outcome,
                "created_at": datetime.utcnow().isoformat(),
            }
            
            result = supabase_service._client.table("vapi_calls")\
                .insert(call_log)\
                .execute()
            
            if result.data:
                log_id = result.data[0]["id"]
                logger.info(f"Logged VAPI call: {log_id}")
                return log_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to log VAPI call: {e}")
            return None
    
    def get_pending_clarifications(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """Get pending clarifications for a user."""
        try:
            result = supabase_service._client.table("pending_clarifications")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("status", "pending")\
                .order("priority", desc=True)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get pending clarifications: {e}")
            return []
    
    def resolve_clarification(
        self,
        clarification_id: str,
        resolved_data: dict,
    ) -> bool:
        """Mark a clarification as resolved with updated data."""
        try:
            supabase_service._client.table("pending_clarifications")\
                .update({
                    "status": "resolved",
                    "resolved_data": resolved_data,
                    "resolved_at": datetime.utcnow().isoformat(),
                })\
                .eq("id", clarification_id)\
                .execute()
            
            logger.info(f"Resolved clarification: {clarification_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve clarification: {e}")
            return False
    
    def get_call_history(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """Get VAPI call history for a user."""
        try:
            result = supabase_service._client.table("vapi_calls")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get call history: {e}")
            return []
    
    def analyze_mood_trend(
        self,
        user_id: str,
        days: int = 7,
    ) -> dict:
        """
        Analyze mood trends over time.
        
        Returns:
            {
                "average_mood_score": float,
                "negative_days": int,
                "positive_days": int,
                "trend": "improving" | "declining" | "stable"
            }
        """
        try:
            from datetime import date, timedelta
            
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Get transcriptions with mood data
            result = supabase_service._client.table("transcriptions")\
                .select("extracted_data, created_at")\
                .eq("user_id", user_id)\
                .gte("created_at", start_date)\
                .order("created_at", desc=False)\
                .execute()
            
            if not result.data:
                return {
                    "average_mood_score": 3.0,
                    "negative_days": 0,
                    "positive_days": 0,
                    "trend": "stable",
                }
            
            mood_scores = []
            negative_days = 0
            positive_days = 0
            
            for entry in result.data:
                extracted = entry.get("extracted_data", {})
                mood_score = extracted.get("mood_score", 3)
                mood_scores.append(mood_score)
                
                if mood_score <= 2:
                    negative_days += 1
                elif mood_score >= 4:
                    positive_days += 1
            
            avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 3.0
            
            # Determine trend (compare first half vs second half)
            if len(mood_scores) >= 4:
                mid = len(mood_scores) // 2
                first_half_avg = sum(mood_scores[:mid]) / mid
                second_half_avg = sum(mood_scores[mid:]) / (len(mood_scores) - mid)
                
                if second_half_avg > first_half_avg + 0.5:
                    trend = "improving"
                elif second_half_avg < first_half_avg - 0.5:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"
            
            return {
                "average_mood_score": round(avg_mood, 2),
                "negative_days": negative_days,
                "positive_days": positive_days,
                "trend": trend,
                "total_days": len(mood_scores),
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze mood trend: {e}")
            return {
                "average_mood_score": 3.0,
                "negative_days": 0,
                "positive_days": 0,
                "trend": "stable",
            }


# Module-level singleton
vapi_service = VAPIService()
