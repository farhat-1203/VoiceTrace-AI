"""
Pattern Detection Service - Analyzes vendor business patterns
Identifies trends, best sellers, high-earning days, and anomalies
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
from collections import Counter, defaultdict
from typing import Optional
from loguru import logger

from services.supabase_service import supabase_service


class PatternService:
    """Analyzes vendor business patterns and generates insights."""

    def analyze_all_patterns(self, user_id: str) -> dict:
        """
        Run all pattern analyses for a vendor.
        Requires at least 4 days of data.
        
        Returns summary of patterns detected.
        """
        try:
            # Get last 30 days of ledger entries
            cutoff = (datetime.now() - timedelta(days=30)).date()
            
            entries = supabase_service._client.table("ledger_entries")\
                .select("*, ledger_items(*), ledger_expenses(*)")\
                .eq("user_id", user_id)\
                .gte("entry_date", cutoff.isoformat())\
                .order("entry_date", desc=False)\
                .execute()
            
            if not entries.data or len(entries.data) < 4:
                logger.info(f"Not enough data for pattern analysis (need 4+ days, have {len(entries.data) if entries.data else 0})")
                return {
                    "status": "insufficient_data",
                    "days_available": len(entries.data) if entries.data else 0,
                    "days_required": 4,
                }
            
            logger.info(f"Analyzing patterns for user {user_id} with {len(entries.data)} days of data")
            
            # Run all analyses
            best_sellers = self._analyze_best_sellers(user_id, entries.data)
            high_days = self._analyze_high_days(user_id, entries.data)
            expense_trends = self._analyze_expense_trends(user_id, entries.data)
            anomalies = self._detect_anomalies(user_id, entries.data)
            
            return {
                "status": "success",
                "days_analyzed": len(entries.data),
                "best_sellers": best_sellers,
                "high_days": high_days,
                "expense_trends": expense_trends,
                "anomalies_detected": len(anomalies),
            }
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def _analyze_best_sellers(self, user_id: str, entries: list) -> list[dict]:
        """
        Identify most frequently sold items and highest revenue items.
        
        Returns list of best-selling items with metrics.
        """
        try:
            item_counter = Counter()
            item_revenue = defaultdict(float)
            item_quantities = defaultdict(float)
            
            for entry in entries:
                for item in entry.get("ledger_items", []):
                    name = item["item_name"]
                    item_counter[name] += 1
                    item_revenue[name] += float(item.get("total_amount", 0))
                    item_quantities[name] += float(item.get("quantity", 0))
            
            # Store top 10 best sellers
            best_sellers = []
            for item_name, frequency in item_counter.most_common(10):
                pattern = {
                    "user_id": user_id,
                    "pattern_type": "best_seller",
                    "item_name": item_name,
                    "metric_value": item_revenue[item_name],
                    "frequency": frequency,
                    "last_computed": datetime.now().isoformat(),
                }
                
                # Upsert pattern
                supabase_service._client.table("vendor_patterns").upsert(
                    pattern,
                    on_conflict="user_id,pattern_type,item_name,day_of_week"
                ).execute()
                
                best_sellers.append({
                    "item_name": item_name,
                    "times_sold": frequency,
                    "total_revenue": item_revenue[item_name],
                    "total_quantity": item_quantities[item_name],
                })
            
            logger.info(f"Identified {len(best_sellers)} best-selling items")
            return best_sellers
            
        except Exception as e:
            logger.error(f"Best seller analysis failed: {e}")
            return []

    def _analyze_high_days(self, user_id: str, entries: list) -> list[dict]:
        """
        Find which days of week have highest earnings.
        
        Returns list of days with average earnings.
        """
        try:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_earnings = defaultdict(list)
            
            for entry in entries:
                entry_date = datetime.fromisoformat(entry["entry_date"])
                day_of_week = entry_date.weekday()  # 0=Monday, 6=Sunday
                earnings = float(entry.get("total_earnings", 0))
                day_earnings[day_of_week].append(earnings)
            
            # Calculate average per day and store
            high_days = []
            for day, earnings_list in day_earnings.items():
                if earnings_list:
                    avg_earnings = sum(earnings_list) / len(earnings_list)
                    
                    pattern = {
                        "user_id": user_id,
                        "pattern_type": "high_day",
                        "day_of_week": day,
                        "metric_value": avg_earnings,
                        "frequency": len(earnings_list),
                        "last_computed": datetime.now().isoformat(),
                    }
                    
                    supabase_service._client.table("vendor_patterns").upsert(
                        pattern,
                        on_conflict="user_id,pattern_type,item_name,day_of_week"
                    ).execute()
                    
                    high_days.append({
                        "day_name": day_names[day],
                        "day_of_week": day,
                        "avg_earnings": avg_earnings,
                        "data_points": len(earnings_list),
                    })
            
            # Sort by earnings
            high_days.sort(key=lambda x: x["avg_earnings"], reverse=True)
            
            logger.info(f"Analyzed earnings for {len(high_days)} days of week")
            return high_days
            
        except Exception as e:
            logger.error(f"High days analysis failed: {e}")
            return []

    def _analyze_expense_trends(self, user_id: str, entries: list) -> dict:
        """
        Detect if expenses are trending up or down.
        
        Returns trend analysis.
        """
        try:
            if len(entries) < 7:
                return {"status": "insufficient_data"}
            
            # Split into first half and second half
            mid = len(entries) // 2
            first_half = entries[:mid]
            second_half = entries[mid:]
            
            first_avg = sum(float(e.get("total_expenses", 0)) for e in first_half) / len(first_half)
            second_avg = sum(float(e.get("total_expenses", 0)) for e in second_half) / len(second_half)
            
            change_pct = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
            
            trend = "increasing" if change_pct > 10 else "decreasing" if change_pct < -10 else "stable"
            
            # Store trend pattern
            pattern = {
                "user_id": user_id,
                "pattern_type": "expense_trend",
                "metric_value": change_pct,
                "frequency": len(entries),
                "last_computed": datetime.now().isoformat(),
            }
            
            supabase_service._client.table("vendor_patterns").upsert(
                pattern,
                on_conflict="user_id,pattern_type,item_name,day_of_week"
            ).execute()
            
            logger.info(f"Expense trend: {trend} ({change_pct:+.1f}%)")
            
            return {
                "trend": trend,
                "change_percentage": change_pct,
                "first_period_avg": first_avg,
                "second_period_avg": second_avg,
            }
            
        except Exception as e:
            logger.error(f"Expense trend analysis failed: {e}")
            return {"status": "error"}

    def _detect_anomalies(self, user_id: str, entries: list) -> list[dict]:
        """
        Detect unusual business activity (earnings/expenses outside normal range).
        
        Returns list of anomalies detected.
        """
        try:
            if len(entries) < 4:
                return []
            
            # Calculate statistics
            earnings_list = [float(e.get("total_earnings", 0)) for e in entries]
            expenses_list = [float(e.get("total_expenses", 0)) for e in entries]
            
            avg_earnings = sum(earnings_list) / len(earnings_list)
            avg_expenses = sum(expenses_list) / len(expenses_list)
            
            # Simple standard deviation
            import math
            earnings_std = math.sqrt(sum((x - avg_earnings) ** 2 for x in earnings_list) / len(earnings_list))
            expenses_std = math.sqrt(sum((x - avg_expenses) ** 2 for x in expenses_list) / len(expenses_list))
            
            anomalies = []
            
            # Check last 3 entries for anomalies
            for entry in entries[-3:]:
                entry_date = entry["entry_date"]
                earnings = float(entry.get("total_earnings", 0))
                expenses = float(entry.get("total_expenses", 0))
                
                # High earnings anomaly
                if earnings > avg_earnings + 2 * earnings_std and earnings_std > 0:
                    anomaly = self._create_anomaly_alert(
                        user_id,
                        entry["id"],
                        "high_earning",
                        "info",
                        f"Earnings on {entry_date} (₹{earnings:.0f}) were significantly higher than usual (avg: ₹{avg_earnings:.0f})"
                    )
                    if anomaly:
                        anomalies.append(anomaly)
                
                # Low earnings anomaly
                elif earnings < avg_earnings - 2 * earnings_std and earnings_std > 0 and avg_earnings > 0:
                    anomaly = self._create_anomaly_alert(
                        user_id,
                        entry["id"],
                        "low_earning",
                        "warning",
                        f"Earnings on {entry_date} (₹{earnings:.0f}) were significantly lower than usual (avg: ₹{avg_earnings:.0f})"
                    )
                    if anomaly:
                        anomalies.append(anomaly)
                
                # High expenses anomaly
                if expenses > avg_expenses + 2 * expenses_std and expenses_std > 0:
                    anomaly = self._create_anomaly_alert(
                        user_id,
                        entry["id"],
                        "high_expense",
                        "warning",
                        f"Expenses on {entry_date} (₹{expenses:.0f}) were significantly higher than usual (avg: ₹{avg_expenses:.0f})"
                    )
                    if anomaly:
                        anomalies.append(anomaly)
            
            logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

    def _create_anomaly_alert(
        self,
        user_id: str,
        ledger_entry_id: str,
        alert_type: str,
        severity: str,
        message: str,
    ) -> Optional[dict]:
        """Create an anomaly alert in the database."""
        try:
            alert = {
                "user_id": user_id,
                "ledger_entry_id": ledger_entry_id,
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "is_acknowledged": False,
            }
            
            result = supabase_service._client.table("anomaly_alerts")\
                .insert(alert)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to create anomaly alert: {e}")
            return None

    def get_best_sellers(self, user_id: str, limit: int = 10) -> list[dict]:
        """Get best-selling items for a vendor."""
        try:
            result = supabase_service._client.table("vendor_patterns")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("pattern_type", "best_seller")\
                .order("metric_value", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get best sellers: {e}")
            return []

    def get_high_days(self, user_id: str) -> list[dict]:
        """Get high-earning days of week for a vendor."""
        try:
            result = supabase_service._client.table("vendor_patterns")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("pattern_type", "high_day")\
                .order("metric_value", desc=True)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get high days: {e}")
            return []

    def get_anomalies(self, user_id: str, unacknowledged_only: bool = True) -> list[dict]:
        """Get anomaly alerts for a vendor."""
        try:
            query = supabase_service._client.table("anomaly_alerts")\
                .select("*")\
                .eq("user_id", user_id)
            
            if unacknowledged_only:
                query = query.eq("is_acknowledged", False)
            
            result = query.order("created_at", desc=True).limit(20).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get anomalies: {e}")
            return []

    def acknowledge_anomaly(self, anomaly_id: str, user_id: str) -> bool:
        """Mark an anomaly as acknowledged."""
        try:
            result = supabase_service._client.table("anomaly_alerts")\
                .update({
                    "is_acknowledged": True,
                    "acknowledged_at": datetime.now().isoformat(),
                })\
                .eq("id", anomaly_id)\
                .eq("user_id", user_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Failed to acknowledge anomaly: {e}")
            return False


# Module-level singleton
pattern_service = PatternService()
