"""
Ledger Service - Converts transcription data into structured ledger entries
Handles confidence scoring, uncertainty flagging, and audio linking
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from loguru import logger

from services.supabase_service import supabase_service


class LedgerService:
    """Manages vendor ledger entries, items, and expenses."""

    def create_entry_from_transcription(
        self,
        user_id: str,
        transcription_id: str,
        extracted_data: dict,
        audio_url: Optional[str] = None,
        audio_storage_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a ledger entry from extracted transcription data.
        
        Args:
            user_id: Vendor's user ID
            transcription_id: Reference to transcription
            extracted_data: Parsed business data from LLM
            audio_url: S3 presigned URL to audio file (expires after 7 days)
            audio_storage_path: S3 storage path for regenerating presigned URLs
        
        Returns:
            ledger_entry_id or None on failure
        """
        try:
            entry_date = date.today()
            
            # Create or get today's ledger entry
            ledger_entry = {
                "user_id": user_id,
                "transcription_id": transcription_id,
                "entry_date": entry_date.isoformat(),
                "total_earnings": 0,
                "total_expenses": 0,
                "audio_url": audio_url,
                "audio_storage_path": audio_storage_path,
                "notes": extracted_data.get("notes", ""),
            }
            
            # Upsert ledger entry (merge if exists for today)
            result = supabase_service._client.table("ledger_entries").upsert(
                ledger_entry,
                on_conflict="user_id,entry_date"
            ).execute()
            
            if not result.data:
                logger.error("Failed to create ledger entry")
                return None
            
            ledger_entry_id = result.data[0]["id"]
            logger.info(f"Created ledger entry {ledger_entry_id} for user {user_id}")
            
            # Add items sold
            items = extracted_data.get("items_sold", [])
            has_uncertainties = False
            
            for item in items:
                confidence = self._calculate_item_confidence(item)
                if confidence < 0.7:
                    has_uncertainties = True
                self._add_ledger_item(ledger_entry_id, item, confidence, audio_url)
            
            # Add expenses
            expenses = extracted_data.get("expenses", [])
            for expense in expenses:
                confidence = self._calculate_expense_confidence(expense)
                if confidence < 0.7:
                    has_uncertainties = True
                self._add_ledger_expense(ledger_entry_id, expense, confidence, audio_url)
            
            # Update transcription with uncertainty flag
            if has_uncertainties:
                supabase_service._client.table("transcriptions").update(
                    {"has_uncertainties": True}
                ).eq("id", transcription_id).execute()
            
            return ledger_entry_id
            
        except Exception as e:
            logger.error(f"Failed to create ledger entry: {e}")
            return None

    def _add_ledger_item(
        self,
        ledger_entry_id: str,
        item: dict,
        confidence: float,
        audio_url: Optional[str] = None,
    ):
        """Add a sold item to the ledger."""
        try:
            quantity = item.get("quantity")
            unit_price = item.get("unit_price")
            total_amount = item.get("total_amount")
            
            # Calculate total if not provided
            if total_amount is None and quantity and unit_price:
                total_amount = float(quantity) * float(unit_price)
            
            ledger_item = {
                "ledger_entry_id": ledger_entry_id,
                "item_name": item.get("name", "Unknown item"),
                "quantity": float(quantity) if quantity else None,
                "unit_price": float(unit_price) if unit_price else None,
                "total_amount": float(total_amount) if total_amount else 0,
                "confidence_score": confidence,
                "needs_confirmation": confidence < 0.7,
                "is_confirmed": False,
            }
            
            supabase_service._client.table("ledger_items").insert(ledger_item).execute()
            logger.info(f"Added item: {item.get('name')} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to add ledger item: {e}")

    def _add_ledger_expense(
        self,
        ledger_entry_id: str,
        expense: dict,
        confidence: float,
        audio_url: Optional[str] = None,
    ):
        """Add an expense to the ledger."""
        try:
            ledger_expense = {
                "ledger_entry_id": ledger_entry_id,
                "expense_type": expense.get("type", "other"),
                "description": expense.get("description", ""),
                "amount": float(expense.get("amount", 0)),
                "confidence_score": confidence,
                "needs_confirmation": confidence < 0.7,
                "is_confirmed": False,
            }
            
            supabase_service._client.table("ledger_expenses").insert(ledger_expense).execute()
            logger.info(f"Added expense: {expense.get('description')} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to add ledger expense: {e}")

    def _calculate_item_confidence(self, item: dict) -> float:
        """
        Calculate confidence score for an item based on data completeness.
        
        Returns: 0.0 to 1.0
        """
        score = 0.3  # Base score
        
        # Has specific item name (not vague)
        name = item.get("name", "").lower()
        vague_terms = ["something", "items", "things", "stuff", "kuch", "cheez"]
        if name and not any(term in name for term in vague_terms):
            score += 0.3
        
        # Has quantity
        if item.get("quantity") is not None:
            score += 0.2
        
        # Has price information
        if item.get("unit_price") or item.get("total_amount"):
            score += 0.2
        
        return min(score, 1.0)

    def _calculate_expense_confidence(self, expense: dict) -> float:
        """
        Calculate confidence score for an expense.
        
        Returns: 0.0 to 1.0
        """
        score = 0.4  # Base score
        
        # Has specific description
        desc = expense.get("description", "").lower()
        if desc and len(desc) > 5:
            score += 0.2
        
        # Has amount
        if expense.get("amount") is not None and expense.get("amount") > 0:
            score += 0.3
        
        # Has expense type
        if expense.get("type") and expense.get("type") != "other":
            score += 0.1
        
        return min(score, 1.0)

    def get_entries_by_date_range(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Get ledger entries for a date range."""
        try:
            result = supabase_service._client.table("ledger_entries")\
                .select("*, ledger_items(*), ledger_expenses(*)")\
                .eq("user_id", user_id)\
                .gte("entry_date", start_date)\
                .lte("entry_date", end_date)\
                .order("entry_date", desc=True)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get ledger entries: {e}")
            return []

    def get_summary(
        self,
        user_id: str,
        period: str = "week",  # 'week' or 'month'
    ) -> dict:
        """
        Get aggregated summary for a period.
        
        Returns:
            {
                "total_earnings": float,
                "total_expenses": float,
                "net_profit": float,
                "days_count": int,
                "avg_daily_earnings": float,
                "top_items": list,
                "top_expenses": list,
            }
        """
        try:
            from datetime import timedelta
            
            today = date.today()
            if period == "week":
                start_date = today - timedelta(days=7)
            else:  # month
                start_date = today - timedelta(days=30)
            
            entries = self.get_entries_by_date_range(
                user_id,
                start_date.isoformat(),
                today.isoformat()
            )
            
            total_earnings = sum(float(e.get("total_earnings", 0)) for e in entries)
            total_expenses = sum(float(e.get("total_expenses", 0)) for e in entries)
            net_profit = total_earnings - total_expenses
            days_count = len(entries)
            avg_daily_earnings = total_earnings / days_count if days_count > 0 else 0
            
            # Aggregate items
            from collections import Counter
            item_counter = Counter()
            item_revenue = {}
            
            for entry in entries:
                for item in entry.get("ledger_items", []):
                    name = item["item_name"]
                    item_counter[name] += 1
                    item_revenue[name] = item_revenue.get(name, 0) + float(item.get("total_amount", 0))
            
            top_items = [
                {"name": name, "count": count, "revenue": item_revenue[name]}
                for name, count in item_counter.most_common(5)
            ]
            
            # Aggregate expenses
            expense_counter = Counter()
            for entry in entries:
                for expense in entry.get("ledger_expenses", []):
                    exp_type = expense["expense_type"]
                    expense_counter[exp_type] += float(expense.get("amount", 0))
            
            top_expenses = [
                {"type": exp_type, "total": amount}
                for exp_type, amount in expense_counter.most_common(5)
            ]
            
            return {
                "total_earnings": total_earnings,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "days_count": days_count,
                "avg_daily_earnings": avg_daily_earnings,
                "top_items": top_items,
                "top_expenses": top_expenses,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": today.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {}

    def get_unconfirmed_items(self, user_id: str) -> list[dict]:
        """Get all items that need confirmation."""
        try:
            result = supabase_service._client.table("ledger_items")\
                .select("*, ledger_entries!inner(user_id)")\
                .eq("ledger_entries.user_id", user_id)\
                .eq("needs_confirmation", True)\
                .eq("is_confirmed", False)\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get unconfirmed items: {e}")
            return []

    def confirm_item(self, item_id: str, user_id: str, confirmed_data: dict) -> bool:
        """Confirm and update an uncertain item."""
        try:
            # Verify ownership
            item = supabase_service._client.table("ledger_items")\
                .select("*, ledger_entries!inner(user_id)")\
                .eq("id", item_id)\
                .eq("ledger_entries.user_id", user_id)\
                .single()\
                .execute()
            
            if not item.data:
                return False
            
            # Update item
            update_data = {
                "is_confirmed": True,
                "needs_confirmation": False,
                "confidence_score": 1.0,
                **confirmed_data
            }
            
            supabase_service._client.table("ledger_items")\
                .update(update_data)\
                .eq("id", item_id)\
                .execute()
            
            logger.info(f"Confirmed item {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to confirm item: {e}")
            return False


# Module-level singleton
ledger_service = LedgerService()
