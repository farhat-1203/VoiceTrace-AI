"""
Stock Suggestion Service - Generates next-day inventory recommendations
Based on sell-through rates, stock-out patterns, and historical data
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
from collections import defaultdict
from typing import Optional
from loguru import logger

from services.supabase_service import supabase_service


class StockSuggestionService:
    """Generates intelligent stock recommendations for vendors."""

    def generate_suggestions(self, user_id: str) -> list[dict]:
        """
        Generate next-day stock suggestions based on historical patterns.
        
        Returns list of suggested items with quantities and reasoning.
        """
        try:
            # Get last 14 days of data
            cutoff = (datetime.now() - timedelta(days=14)).date()
            
            entries = supabase_service._client.table("ledger_entries")\
                .select("*, ledger_items(*)")\
                .eq("user_id", user_id)\
                .gte("entry_date", cutoff.isoformat())\
                .order("entry_date", desc=False)\
                .execute()
            
            if not entries.data or len(entries.data) < 3:
                logger.info(f"Not enough data for stock suggestions (need 3+ days)")
                return []
            
            # Analyze item patterns
            item_sales = defaultdict(list)
            item_stockouts = defaultdict(int)
            
            for entry in entries.data:
                for item in entry.get("ledger_items", []):
                    item_name = item["item_name"]
                    quantity = float(item.get("quantity", 0))
                    item_sales[item_name].append(quantity)
                    
                    # Check if vendor mentioned running out (low confidence items)
                    if item.get("needs_confirmation") and quantity == 0:
                        item_stockouts[item_name] += 1
            
            suggestions = []
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            
            for item_name, quantities in item_sales.items():
                if not quantities:
                    continue
                
                # Calculate average daily sales
                avg_quantity = sum(quantities) / len(quantities)
                
                # Calculate trend (recent vs older)
                if len(quantities) >= 4:
                    recent_avg = sum(quantities[-3:]) / 3
                    older_avg = sum(quantities[:-3]) / len(quantities[:-3])
                    trend_factor = recent_avg / older_avg if older_avg > 0 else 1.0
                else:
                    trend_factor = 1.0
                
                # Adjust for stockouts
                stockout_factor = 1.0 + (item_stockouts[item_name] * 0.2)
                
                # Calculate suggested quantity
                suggested_qty = avg_quantity * trend_factor * stockout_factor
                
                # Round to reasonable numbers
                if suggested_qty < 5:
                    suggested_qty = round(suggested_qty, 1)
                else:
                    suggested_qty = round(suggested_qty)
                
                # Generate reasoning
                reasoning = self._generate_reasoning(
                    item_name,
                    avg_quantity,
                    trend_factor,
                    item_stockouts[item_name],
                    len(quantities)
                )
                
                # Calculate confidence
                confidence = self._calculate_confidence(
                    len(quantities),
                    trend_factor,
                    item_stockouts[item_name]
                )
                
                suggestion = {
                    "user_id": user_id,
                    "item_name": item_name,
                    "suggested_quantity": suggested_qty,
                    "reasoning": reasoning,
                    "confidence": confidence,
                    "suggestion_date": tomorrow,
                    "is_applied": False,
                }
                
                # Store in database
                supabase_service._client.table("stock_suggestions").upsert(
                    suggestion,
                    on_conflict="user_id,item_name,suggestion_date"
                ).execute()
                
                suggestions.append(suggestion)
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            
            logger.info(f"Generated {len(suggestions)} stock suggestions for user {user_id}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Stock suggestion generation failed: {e}")
            return []

    def _generate_reasoning(
        self,
        item_name: str,
        avg_quantity: float,
        trend_factor: float,
        stockouts: int,
        days_count: int,
    ) -> str:
        """Generate human-readable reasoning for the suggestion."""
        reasons = []
        
        # Base reason
        reasons.append(f"You typically sell {avg_quantity:.1f} units per day")
        
        # Trend
        if trend_factor > 1.2:
            reasons.append("sales are increasing")
        elif trend_factor < 0.8:
            reasons.append("sales are decreasing")
        
        # Stockouts
        if stockouts > 0:
            reasons.append(f"you ran out {stockouts} time(s) recently")
        
        # Data quality
        if days_count < 5:
            reasons.append("(limited data)")
        
        return f"{item_name}: " + ", ".join(reasons)

    def _calculate_confidence(
        self,
        days_count: int,
        trend_factor: float,
        stockouts: int,
    ) -> float:
        """Calculate confidence score for the suggestion."""
        confidence = 0.5  # Base
        
        # More data = higher confidence
        if days_count >= 7:
            confidence += 0.3
        elif days_count >= 5:
            confidence += 0.2
        else:
            confidence += 0.1
        
        # Stable trend = higher confidence
        if 0.8 <= trend_factor <= 1.2:
            confidence += 0.2
        else:
            confidence += 0.1
        
        # Stockouts reduce confidence slightly
        confidence -= stockouts * 0.05
        
        return max(0.0, min(1.0, confidence))

    def get_suggestions(self, user_id: str, date_str: Optional[str] = None) -> list[dict]:
        """Get stock suggestions for a specific date (default: tomorrow)."""
        try:
            if not date_str:
                date_str = (date.today() + timedelta(days=1)).isoformat()
            
            result = supabase_service._client.table("stock_suggestions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("suggestion_date", date_str)\
                .order("confidence", desc=True)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get stock suggestions: {e}")
            return []

    def mark_applied(self, suggestion_id: str, user_id: str) -> bool:
        """Mark a suggestion as applied by the vendor."""
        try:
            result = supabase_service._client.table("stock_suggestions")\
                .update({"is_applied": True})\
                .eq("id", suggestion_id)\
                .eq("user_id", user_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Failed to mark suggestion as applied: {e}")
            return False


# Module-level singleton
stock_suggestion_service = StockSuggestionService()
