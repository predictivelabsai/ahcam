"""
Financial Overview module — Aggregated dashboard with progress bars per title.
Modeled after Freeway Entertainment's Financial Overview page.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tools
# ---------------------------------------------------------------------------

def get_financial_overview(query: str = "") -> str:
    """Get financial overview across all productions. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            rows = session.execute(text("""
                SELECT
                    p.production_id, p.title, p.genre, p.director, p.budget, p.currency,
                    COALESCE(SUM(CASE WHEN t.transaction_type = 'inflow' THEN t.amount ELSE 0 END), 0) AS gross_receipts,
                    COALESCE(SUM(CASE WHEN t.transaction_type = 'outflow' THEN t.amount ELSE 0 END), 0) AS disbursed,
                    COALESCE(a.total_balance, 0) AS account_balance,
                    COALESCE(da.total_mg, 0) AS total_mg,
                    COALESCE(da.mg_received, 0) AS mg_received,
                    COALESCE(da.deal_count, 0) AS deal_count
                FROM ahcam.productions p
                LEFT JOIN ahcam.collection_accounts ca ON ca.production_id = p.production_id
                LEFT JOIN ahcam.transactions t ON t.account_id = ca.account_id
                LEFT JOIN (
                    SELECT production_id, SUM(balance) AS total_balance
                    FROM ahcam.collection_accounts GROUP BY production_id
                ) a ON a.production_id = p.production_id
                LEFT JOIN (
                    SELECT production_id,
                           COALESCE(SUM(mg_amount), 0) AS total_mg,
                           COALESCE(SUM(mg_paid), 0) AS mg_received,
                           COUNT(*) AS deal_count
                    FROM ahcam.distribution_agreements GROUP BY production_id
                ) da ON da.production_id = p.production_id
                GROUP BY p.production_id, p.title, p.genre, p.director, p.budget, p.currency,
                         a.total_balance, da.total_mg, da.mg_received, da.deal_count
                ORDER BY gross_receipts DESC
            """)).fetchall()
        if not rows:
            return "No productions found."
        header = "| Title | Genre | Budget | Gross Receipts | Outstanding | MG Sales | Deals |\n|-------|-------|--------|---------------|-------------|----------|-------|\n"
        lines = []
        for r in rows:
            budget = f"${r[4]:,.0f}" if r[4] else "—"
            gross = f"${r[6]:,.2f}"
            outstanding = f"${r[8]:,.2f}"
            mg = f"${r[9]:,.2f}"
            lines.append(f"| {r[1]} | {r[2] or '—'} | {budget} | {gross} | {outstanding} | {mg} | {r[11]} |")
        return f"## Financial Overview\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/financial-overview")
    def module_financial_overview(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                # Aggregate stats
                stats = s.execute(text("""
                    SELECT
                        (SELECT COUNT(*) FROM ahcam.productions) AS total_titles,
                        (SELECT COALESCE(SUM(balance), 0) FROM ahcam.collection_accounts) AS total_balance,
                        (SELECT COALESCE(SUM(amount), 0) FROM ahcam.transactions WHERE transaction_type = 'inflow') AS total_inflows,
                        (SELECT COALESCE(SUM(amount), 0) FROM ahcam.transactions WHERE transaction_type = 'outflow') AS total_outflows
                """)).fetchone()

                # Per-title breakdown
                rows = s.execute(text("""
                    SELECT
                        p.production_id, p.title, p.genre, p.director, p.budget, p.currency, p.status,
                        COALESCE(inflows.total, 0) AS gross_receipts,
                        COALESCE(outflows.total, 0) AS disbursed,
                        COALESCE(acct.total_balance, 0) AS account_balance,
                        COALESCE(da.total_mg, 0) AS total_mg,
                        COALESCE(da.mg_received, 0) AS mg_received,
                        COALESCE(da.deal_count, 0) AS deal_count
                    FROM ahcam.productions p
                    LEFT JOIN (
                        SELECT ca.production_id, SUM(t.amount) AS total
                        FROM ahcam.transactions t
                        JOIN ahcam.collection_accounts ca ON ca.account_id = t.account_id
                        WHERE t.transaction_type = 'inflow'
                        GROUP BY ca.production_id
                    ) inflows ON inflows.production_id = p.production_id
                    LEFT JOIN (
                        SELECT ca.production_id, SUM(t.amount) AS total
                        FROM ahcam.transactions t
                        JOIN ahcam.collection_accounts ca ON ca.account_id = t.account_id
                        WHERE t.transaction_type = 'outflow'
                        GROUP BY ca.production_id
                    ) outflows ON outflows.production_id = p.production_id
                    LEFT JOIN (
                        SELECT production_id, SUM(balance) AS total_balance
                        FROM ahcam.collection_accounts GROUP BY production_id
                    ) acct ON acct.production_id = p.production_id
                    LEFT JOIN (
                        SELECT production_id,
                               COALESCE(SUM(mg_amount), 0) AS total_mg,
                               COALESCE(SUM(mg_paid), 0) AS mg_received,
                               COUNT(*) AS deal_count
                        FROM ahcam.distribution_agreements GROUP BY production_id
                    ) da ON da.production_id = p.production_id
                    ORDER BY gross_receipts DESC
                """)).fetchall()
        except Exception:
            stats = (0, 0, 0, 0)
            rows = []

        total_titles = stats[0]
        total_balance = stats[1]
        total_inflows = stats[2]
        total_outflows = stats[3]
        outstanding = total_inflows - total_outflows

        # Stat cards
        stat_grid = Div(
            Div(Div(str(total_titles), cls="stat-value"), Div("Total Titles", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${total_inflows:,.2f}", cls="stat-value positive"), Div("Gross Receipts", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${outstanding:,.2f}", cls="stat-value"), Div("Outstanding", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${total_balance:,.2f}", cls="stat-value"), Div("Account Balance", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        # Build table rows with progress bars
        table_rows = []
        for r in rows:
            prod_id = r[0]
            title = r[1]
            genre = r[2] or "—"
            director = r[3] or "—"
            budget = r[4] or 0
            gross_receipts = r[7]
            disbursed = r[8]
            balance = r[9]
            total_mg = r[10]
            mg_received = r[11]
            deal_count = r[12]

            # Progress: gross receipts vs budget
            pct_budget = min(100, (gross_receipts / budget * 100)) if budget > 0 else 0
            # Progress: MG received vs total MG
            pct_mg = min(100, (mg_received / total_mg * 100)) if total_mg > 0 else 0

            budget_bar_color = "#22c55e" if pct_budget >= 100 else "#3b82f6" if pct_budget >= 50 else "#f59e0b"
            mg_bar_color = "#22c55e" if pct_mg >= 100 else "#3b82f6" if pct_mg >= 50 else "#f59e0b"

            table_rows.append(Tr(
                Td(A(title, href="#", onclick=f"loadModule(this,'/module/production/{prod_id}', '{title}'); return false;",
                     style="color:#60a5fa;text-decoration:none;font-weight:500;")),
                Td(genre),
                Td(director, style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"),
                Td(f"${budget:,.0f}" if budget else "—", style="text-align:right;"),
                Td(
                    Div(
                        Div(f"${gross_receipts:,.0f}", style="font-size:0.8rem;margin-bottom:2px;"),
                        Div(
                            Div(style=f"width:{pct_budget:.0f}%;height:100%;background:{budget_bar_color};border-radius:3px;transition:width 0.3s;"),
                            style="width:100%;height:6px;background:#374151;border-radius:3px;overflow:hidden;",
                        ),
                        style="min-width:100px;",
                    ),
                ),
                Td(f"${balance:,.0f}", style="text-align:right;"),
                Td(
                    Div(
                        Div(f"${mg_received:,.0f} / ${total_mg:,.0f}", style="font-size:0.8rem;margin-bottom:2px;"),
                        Div(
                            Div(style=f"width:{pct_mg:.0f}%;height:100%;background:{mg_bar_color};border-radius:3px;transition:width 0.3s;"),
                            style="width:100%;height:6px;background:#374151;border-radius:3px;overflow:hidden;",
                        ),
                        style="min-width:120px;",
                    ) if total_mg > 0 else Span("—"),
                ),
                Td(str(deal_count), style="text-align:center;"),
                style="cursor:pointer;",
                hx_get=f"/module/production/{prod_id}",
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        # Export buttons
        export_bar = Div(
            Button("Export Excel",
                   hx_get="/export/financial-overview?fmt=excel",
                   hx_swap="none",
                   cls="module-action-btn",
                   style="font-size:0.8rem;padding:4px 12px;margin-right:8px;"),
            Button("Export PDF",
                   hx_get="/export/financial-overview?fmt=pdf",
                   hx_swap="none",
                   cls="module-action-btn",
                   style="font-size:0.8rem;padding:4px 12px;background:#6b7280;"),
            style="display:flex;gap:8px;",
        )

        content_table = Table(
            Thead(Tr(
                Th("Title"), Th("Genre"), Th("Director"), Th("Budget"),
                Th("Gross Receipts"), Th("Balance"), Th("MG Sales"), Th("Deals"),
            )),
            Tbody(*table_rows) if table_rows else Tbody(Tr(Td("No productions found.", colspan="8", style="text-align:center;"))),
            cls="module-table",
        )

        return Div(
            stat_grid,
            Div(
                Div(
                    H3("Financial Overview"),
                    export_bar,
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                content_table,
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/export/financial-overview")
    def export_financial_overview(session, fmt: str = "excel"):
        """Export financial overview data."""
        from starlette.responses import Response
        from utils.export import export_table_to_excel, export_html_to_pdf

        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT
                        p.title, p.genre, p.director,
                        COALESCE(p.budget, 0) AS budget,
                        COALESCE(inflows.total, 0) AS gross_receipts,
                        COALESCE(acct.total_balance, 0) AS balance,
                        COALESCE(da.total_mg, 0) AS total_mg,
                        COALESCE(da.mg_received, 0) AS mg_received,
                        COALESCE(da.deal_count, 0) AS deal_count
                    FROM ahcam.productions p
                    LEFT JOIN (
                        SELECT ca.production_id, SUM(t.amount) AS total
                        FROM ahcam.transactions t
                        JOIN ahcam.collection_accounts ca ON ca.account_id = t.account_id
                        WHERE t.transaction_type = 'inflow'
                        GROUP BY ca.production_id
                    ) inflows ON inflows.production_id = p.production_id
                    LEFT JOIN (
                        SELECT production_id, SUM(balance) AS total_balance
                        FROM ahcam.collection_accounts GROUP BY production_id
                    ) acct ON acct.production_id = p.production_id
                    LEFT JOIN (
                        SELECT production_id,
                               COALESCE(SUM(mg_amount), 0) AS total_mg,
                               COALESCE(SUM(mg_paid), 0) AS mg_received,
                               COUNT(*) AS deal_count
                        FROM ahcam.distribution_agreements GROUP BY production_id
                    ) da ON da.production_id = p.production_id
                    ORDER BY gross_receipts DESC
                """)).fetchall()
        except Exception:
            rows = []

        headers = ["Title", "Genre", "Director", "Budget", "Gross Receipts", "Balance", "Total MG", "MG Received", "Deals"]
        data = []
        for r in rows:
            data.append([r[0], r[1] or "", r[2] or "", float(r[3]), float(r[4]), float(r[5]), float(r[6]), float(r[7]), int(r[8])])

        if fmt == "pdf":
            # Build simple HTML table for PDF
            html = "<html><head><style>body{font-family:Arial;font-size:12px;}table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ccc;padding:6px 8px;text-align:left;}th{background:#2C3E50;color:#fff;}</style></head><body>"
            html += "<h2>Financial Overview — Ashland Hill CAM</h2><table><tr>"
            for h in headers:
                html += f"<th>{h}</th>"
            html += "</tr>"
            for row in data:
                html += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>"
            html += "</table></body></html>"
            pdf_bytes = export_html_to_pdf(html)
            return Response(pdf_bytes, media_type="application/pdf",
                          headers={"Content-Disposition": "attachment; filename=financial_overview.pdf"})
        else:
            xlsx_bytes = export_table_to_excel(headers, data, "Financial Overview")
            return Response(xlsx_bytes,
                          media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          headers={"Content-Disposition": "attachment; filename=financial_overview.xlsx"})
