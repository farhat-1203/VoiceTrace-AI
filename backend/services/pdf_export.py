"""
PDF Export Service - Generates income statements and business reports
Uses WeasyPrint for HTML to PDF conversion
"""
from __future__ import annotations

import io
from datetime import date, datetime
from typing import Optional
from loguru import logger

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint not installed. PDF export will not work. Install with: pip install weasyprint")


class PDFExportService:
    """Generates PDF reports from ledger data."""
    
    def __init__(self):
        if not WEASYPRINT_AVAILABLE:
            logger.warning("PDF export service initialized without WeasyPrint")
    
    def generate_income_statement(
        self,
        user_name: str,
        summary_data: dict,
        period: str = "week",
    ) -> Optional[bytes]:
        """
        Generate income statement PDF.
        
        Args:
            user_name: Vendor's name
            summary_data: Summary from ledger_service.get_summary()
            period: 'week' or 'month'
        
        Returns:
            PDF bytes or None on failure
        """
        if not WEASYPRINT_AVAILABLE:
            logger.error("Cannot generate PDF: WeasyPrint not installed")
            return None
        
        try:
            html_content = self._generate_income_statement_html(
                user_name=user_name,
                summary_data=summary_data,
                period=period,
            )
            
            # Convert HTML to PDF
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            logger.info(f"Generated income statement PDF for {user_name} ({period})")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return None
    
    def _generate_income_statement_html(
        self,
        user_name: str,
        summary_data: dict,
        period: str,
    ) -> str:
        """Generate HTML for income statement."""
        
        # Extract data
        total_earnings = summary_data.get("total_earnings", 0)
        total_expenses = summary_data.get("total_expenses", 0)
        net_profit = summary_data.get("net_profit", 0)
        days_count = summary_data.get("days_count", 0)
        avg_daily_earnings = summary_data.get("avg_daily_earnings", 0)
        top_items = summary_data.get("top_items", [])
        top_expenses = summary_data.get("top_expenses", [])
        start_date = summary_data.get("start_date", "")
        end_date = summary_data.get("end_date", "")
        
        # Format period name
        period_name = "साप्ताहिक (Weekly)" if period == "week" else "मासिक (Monthly)"
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <title>Income Statement - {user_name}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        
        body {{
            font-family: 'Noto Sans', 'Arial', sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
        }}
        
        .header h1 {{
            color: #1e40af;
            margin: 0;
            font-size: 24pt;
        }}
        
        .header .subtitle {{
            color: #64748b;
            font-size: 14pt;
            margin-top: 5px;
        }}
        
        .period-info {{
            background: #f1f5f9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .period-info p {{
            margin: 5px 0;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        
        .summary-box h2 {{
            margin-top: 0;
            font-size: 18pt;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }}
        
        .summary-item {{
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 8px;
        }}
        
        .summary-item .label {{
            font-size: 10pt;
            opacity: 0.9;
        }}
        
        .summary-item .value {{
            font-size: 20pt;
            font-weight: bold;
            margin-top: 5px;
        }}
        
        .net-profit {{
            grid-column: 1 / -1;
            background: rgba(255, 255, 255, 0.3);
            text-align: center;
        }}
        
        .net-profit .value {{
            font-size: 28pt;
            color: {"#10b981" if net_profit >= 0 else "#ef4444"};
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section h3 {{
            color: #1e40af;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        th {{
            background: #f1f5f9;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #cbd5e1;
        }}
        
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        tr:hover {{
            background: #f8fafc;
        }}
        
        .amount {{
            text-align: right;
            font-weight: 600;
        }}
        
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            text-align: center;
            color: #64748b;
            font-size: 10pt;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 9pt;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>आय विवरण (Income Statement)</h1>
        <div class="subtitle">{user_name}</div>
    </div>
    
    <div class="period-info">
        <p><strong>अवधि (Period):</strong> {period_name}</p>
        <p><strong>तिथि (Date Range):</strong> {start_date} से {end_date}</p>
        <p><strong>कुल दिन (Total Days):</strong> {days_count} दिन</p>
        <p><strong>रिपोर्ट तिथि (Report Date):</strong> {datetime.now().strftime("%d %B %Y")}</p>
    </div>
    
    <div class="summary-box">
        <h2>सारांश (Summary)</h2>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="label">कुल आय (Total Earnings)</div>
                <div class="value">₹{total_earnings:,.2f}</div>
            </div>
            <div class="summary-item">
                <div class="label">कुल खर्च (Total Expenses)</div>
                <div class="value">₹{total_expenses:,.2f}</div>
            </div>
            <div class="summary-item">
                <div class="label">औसत दैनिक आय (Avg Daily)</div>
                <div class="value">₹{avg_daily_earnings:,.2f}</div>
            </div>
            <div class="summary-item">
                <div class="label">दिनों की संख्या (Days)</div>
                <div class="value">{days_count}</div>
            </div>
            <div class="summary-item net-profit">
                <div class="label">शुद्ध लाभ (Net Profit)</div>
                <div class="value">₹{net_profit:,.2f}</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h3>सबसे अधिक बिकने वाली वस्तुएं (Top Selling Items)</h3>
        <table>
            <thead>
                <tr>
                    <th>वस्तु (Item)</th>
                    <th style="text-align: center;">बिक्री संख्या (Sales Count)</th>
                    <th class="amount">कुल राजस्व (Revenue)</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add top items
        if top_items:
            for item in top_items[:10]:
                html += f"""
                <tr>
                    <td>{item['name']}</td>
                    <td style="text-align: center;">{item['count']}</td>
                    <td class="amount">₹{item['revenue']:,.2f}</td>
                </tr>
"""
        else:
            html += """
                <tr>
                    <td colspan="3" style="text-align: center; color: #64748b;">कोई डेटा उपलब्ध नहीं (No data available)</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h3>प्रमुख खर्चे (Top Expenses)</h3>
        <table>
            <thead>
                <tr>
                    <th>खर्च का प्रकार (Expense Type)</th>
                    <th class="amount">कुल राशि (Total Amount)</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add top expenses
        if top_expenses:
            for expense in top_expenses[:10]:
                expense_type_map = {
                    "raw_material": "कच्चा माल (Raw Material)",
                    "transport": "परिवहन (Transport)",
                    "rent": "किराया (Rent)",
                    "utilities": "उपयोगिताएं (Utilities)",
                    "labor": "श्रम (Labor)",
                    "other": "अन्य (Other)",
                }
                expense_label = expense_type_map.get(expense['type'], expense['type'])
                
                html += f"""
                <tr>
                    <td>{expense_label}</td>
                    <td class="amount">₹{expense['total']:,.2f}</td>
                </tr>
"""
        else:
            html += """
                <tr>
                    <td colspan="2" style="text-align: center; color: #64748b;">कोई डेटा उपलब्ध नहीं (No data available)</td>
                </tr>
"""
        
        html += f"""
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>यह दस्तावेज़ VoiceTrace AI द्वारा स्वचालित रूप से उत्पन्न किया गया है</p>
        <p>This document was automatically generated by VoiceTrace AI</p>
        <p style="margin-top: 10px;">
            <span class="badge badge-success">✓ Verified</span>
            <span class="badge badge-warning">For Reference Only</span>
        </p>
    </div>
</body>
</html>
"""
        
        return html


# Module-level singleton
pdf_export_service = PDFExportService()
