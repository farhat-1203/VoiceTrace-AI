"""
Export API Routes - Generate PDF reports and exports
"""
from __future__ import annotations

import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import date

from services.pdf_export_service import pdf_export_service
from services.ledger_service import ledger_service
from services.supabase_service import supabase_service


router = APIRouter(prefix="/export", tags=["export"])


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

@router.get("/income-statement")
async def export_income_statement(
    period: str = Query("week", regex="^(week|month)$", description="Period: week or month"),
    authorization: str = Depends(lambda: None),
):
    """
    Generate and download income statement PDF.
    
    Returns a PDF file with earnings, expenses, and profit summary.
    """
    user = await get_current_user(authorization)
    
    # Get user name
    user_name = user.get("user_metadata", {}).get("full_name", "Vendor")
    if not user_name or user_name == "Vendor":
        user_name = user.get("email", "Vendor").split("@")[0]
    
    # Get summary data
    summary_data = ledger_service.get_summary(
        user_id=user["id"],
        period=period,
    )
    
    if not summary_data or summary_data.get("days_count", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail="No ledger data available for the selected period"
        )
    
    # Generate PDF
    pdf_bytes = pdf_export_service.generate_income_statement(
        user_name=user_name,
        summary_data=summary_data,
        period=period,
    )
    
    if not pdf_bytes:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate PDF. Ensure WeasyPrint is installed."
        )
    
    # Return as downloadable file
    filename = f"income_statement_{period}_{date.today().isoformat()}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/ledger-csv")
async def export_ledger_csv(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    authorization: str = Depends(lambda: None),
):
    """
    Export ledger entries as CSV.
    
    Returns a CSV file with all entries, items, and expenses.
    """
    user = await get_current_user(authorization)
    
    # Get ledger entries
    entries = ledger_service.get_entries_by_date_range(
        user_id=user["id"],
        start_date=start_date,
        end_date=end_date,
    )
    
    if not entries:
        raise HTTPException(
            status_code=400,
            detail="No ledger data available for the selected date range"
        )
    
    # Generate CSV
    import csv
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Date",
        "Item Name",
        "Quantity",
        "Unit Price",
        "Total Amount",
        "Type",
        "Expense Type",
        "Expense Description",
        "Expense Amount",
        "Notes",
    ])
    
    # Write data
    for entry in entries:
        entry_date = entry.get("entry_date")
        notes = entry.get("notes", "")
        
        # Write items
        for item in entry.get("ledger_items", []):
            writer.writerow([
                entry_date,
                item.get("item_name", ""),
                item.get("quantity", ""),
                item.get("unit_price", ""),
                item.get("total_amount", ""),
                "Item",
                "",
                "",
                "",
                notes,
            ])
        
        # Write expenses
        for expense in entry.get("ledger_expenses", []):
            writer.writerow([
                entry_date,
                "",
                "",
                "",
                "",
                "Expense",
                expense.get("expense_type", ""),
                expense.get("description", ""),
                expense.get("amount", ""),
                notes,
            ])
    
    # Return as downloadable file
    filename = f"ledger_{start_date}_to_{end_date}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/summary-json")
async def export_summary_json(
    period: str = Query("week", regex="^(week|month)$", description="Period: week or month"),
    authorization: str = Depends(lambda: None),
):
    """
    Export summary data as JSON.
    
    Returns structured JSON with all summary data.
    """
    user = await get_current_user(authorization)
    
    summary_data = ledger_service.get_summary(
        user_id=user["id"],
        period=period,
    )
    
    if not summary_data:
        raise HTTPException(
            status_code=400,
            detail="No ledger data available for the selected period"
        )
    
    return summary_data
