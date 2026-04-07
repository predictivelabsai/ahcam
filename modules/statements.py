"""
Statements module — Periodic collection statements with status tracking.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_statements(query: str = "") -> str:
    """Search collection statements. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT cs.statement_id, p.title, cs.statement_name, cs.period_start,
                           cs.period_end, cs.issued_date, cs.status
                    FROM ahcam.collection_statements cs
                    LEFT JOIN ahcam.productions p ON p.production_id = cs.production_id
                    WHERE cs.statement_name ILIKE :q OR p.title ILIKE :q OR cs.status ILIKE :q
                    ORDER BY cs.issued_date DESC LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT cs.statement_id, p.title, cs.statement_name, cs.period_start,
                           cs.period_end, cs.issued_date, cs.status
                    FROM ahcam.collection_statements cs
                    LEFT JOIN ahcam.productions p ON p.production_id = cs.production_id
                    ORDER BY cs.issued_date DESC LIMIT 20
                """)).fetchall()
        if not rows:
            return "No statements found."
        header = "| Production | Statement | Period | Issued | Status |\n|------------|-----------|--------|--------|--------|\n"
        lines = []
        for r in rows:
            period = f"{str(r[3])[:10]} \u2013 {str(r[4])[:10]}" if r[3] and r[4] else "\u2014"
            lines.append(f"| {r[1] or '\u2014'} | {r[2]} | {period} | {str(r[5])[:10] if r[5] else '\u2014'} | {r[6]} |")
        return f"## Collection Statements\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/statements")
    def module_statements(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT cs.statement_id, p.title, p.production_id,
                           cs.statement_name, cs.period_start, cs.period_end,
                           cs.issued_date, cs.payment_date, cs.next_due_date,
                           cs.status, cs.account_manager
                    FROM ahcam.collection_statements cs
                    LEFT JOIN ahcam.productions p ON p.production_id = cs.production_id
                    ORDER BY cs.issued_date DESC NULLS LAST, cs.created_at DESC
                    LIMIT 50
                """)).fetchall()

                totals = s.execute(text("""
                    SELECT COUNT(*),
                           COUNT(*) FILTER (WHERE status = 'draft'),
                           COUNT(*) FILTER (WHERE status = 'issued'),
                           COUNT(*) FILTER (WHERE status = 'paid')
                    FROM ahcam.collection_statements
                """)).fetchone()
        except Exception:
            rows = []
            totals = (0, 0, 0, 0)

        # Stat cards
        stat_grid = Div(
            Div(Div(str(totals[0]), cls="stat-value"), Div("Total Statements", cls="stat-label"), cls="stat-card"),
            Div(Div(str(totals[1]), cls="stat-value"), Div("Draft", cls="stat-label"), cls="stat-card"),
            Div(Div(str(totals[2]), cls="stat-value"), Div("Issued", cls="stat-label"), cls="stat-card"),
            Div(Div(str(totals[3]), cls="stat-value positive"), Div("Paid", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        # Table rows
        table_rows = []
        for r in rows:
            stmt_id = r[0]
            title = r[1] or "\u2014"
            stmt_name = r[3] or "\u2014"
            period_start = str(r[4])[:10] if r[4] else "\u2014"
            period_end = str(r[5])[:10] if r[5] else "\u2014"
            period = f"{period_start} \u2013 {period_end}" if r[4] else "\u2014"
            issued = str(r[6])[:10] if r[6] else "\u2014"
            payment = str(r[7])[:10] if r[7] else "\u2014"
            next_due = str(r[8])[:10] if r[8] else "\u2014"
            status = r[9] or "draft"
            manager = r[10] or "\u2014"

            status_cls = "badge-blue" if status == "draft" else "badge-amber" if status == "issued" else "badge-green"

            table_rows.append(Tr(
                Td(title),
                Td(stmt_name),
                Td(period),
                Td(issued),
                Td(payment),
                Td(next_due),
                Td(Span(status.title(), cls=status_cls)),
                Td(manager),
                style="cursor:pointer;",
                hx_get=f"/module/statement/{stmt_id}",
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        content_table = Table(
            Thead(Tr(
                Th("Production"), Th("Statement"), Th("Period"),
                Th("Issued"), Th("Payment Date"), Th("Next Due"),
                Th("Status"), Th("Account Manager"),
            )),
            Tbody(*table_rows) if table_rows else Tbody(Tr(Td("No statements found.", colspan="8", style="text-align:center;"))),
            cls="module-table",
        )

        return Div(
            stat_grid,
            Div(
                H3("Collection Statements"),
                content_table,
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/statement/{statement_id}")
    def statement_detail(statement_id: str, session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                row = s.execute(text("""
                    SELECT cs.statement_id, p.title, p.production_id,
                           cs.statement_name, cs.period_start, cs.period_end,
                           cs.issued_date, cs.payment_date, cs.next_due_date,
                           cs.status, cs.account_manager, cs.content, cs.notes
                    FROM ahcam.collection_statements cs
                    LEFT JOIN ahcam.productions p ON p.production_id = cs.production_id
                    WHERE cs.statement_id = :sid
                """), {"sid": statement_id}).fetchone()
        except Exception:
            row = None

        if not row:
            return Div("Statement not found.", cls="module-error")

        status = row[9] or "draft"
        status_cls = "badge-blue" if status == "draft" else "badge-amber" if status == "issued" else "badge-green"

        return Div(
            Div(
                H3(row[3] or "Statement"),
                Span(status.title(), cls=status_cls),
                style="display:flex;gap:1rem;align-items:center;margin-bottom:1rem;",
            ),
            Div(
                Div(Div("Production", cls="detail-label"), Div(row[1] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Period", cls="detail-label"),
                    Div(f"{str(row[4])[:10] if row[4] else '\u2014'} \u2013 {str(row[5])[:10] if row[5] else '\u2014'}", cls="detail-value"),
                    cls="detail-item"),
                Div(Div("Issued Date", cls="detail-label"), Div(str(row[6])[:10] if row[6] else "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Payment Date", cls="detail-label"), Div(str(row[7])[:10] if row[7] else "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Next Due", cls="detail-label"), Div(str(row[8])[:10] if row[8] else "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Account Manager", cls="detail-label"), Div(row[10] or "\u2014", cls="detail-value"), cls="detail-item"),
                cls="detail-grid",
            ),
            Div(
                H4("Content"),
                Div(row[11] or "No content.", style="white-space:pre-wrap;font-size:0.9rem;line-height:1.6;padding:12px;background:#0f172a;border-radius:8px;margin-top:8px;"),
                cls="detail-section",
            ) if row[11] else "",
            Div(
                H4("Notes"),
                P(row[12] or "No notes."),
                cls="detail-section",
            ) if row[12] else "",
            Button("\u2190 Back to Statements",
                   hx_get="/module/statements",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="back-btn"),
            cls="module-content",
        )
