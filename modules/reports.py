"""
Reports module — Stakeholder-specific collection reports, waterfall position statements.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def generate_report(production_id: str) -> str:
    """Generate a collection account report for a production."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            prod = session.execute(text("""
                SELECT title, status, budget, currency FROM ahcam.productions WHERE production_id = :pid
            """), {"pid": production_id}).fetchone()

            if not prod:
                return f"Production `{production_id}` not found."

            accounts = session.execute(text("""
                SELECT account_name, balance, currency, status FROM ahcam.collection_accounts
                WHERE production_id = :pid
            """), {"pid": production_id}).fetchall()

            txn_summary = session.execute(text("""
                SELECT transaction_type, COUNT(*), COALESCE(SUM(amount), 0)
                FROM ahcam.transactions t
                JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                WHERE a.production_id = :pid
                GROUP BY transaction_type
            """), {"pid": production_id}).fetchall()

            disbursements = session.execute(text("""
                SELECT s.name, SUM(d.amount), d.status
                FROM ahcam.disbursements d
                LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = d.stakeholder_id
                WHERE d.production_id = :pid
                GROUP BY s.name, d.status
            """), {"pid": production_id}).fetchall()

        report = f"## Collection Account Report: {prod[0]}\n\n"
        report += f"**Status:** {prod[1]} | **Budget:** ${prod[2]:,.0f} {prod[3]}\n\n" if prod[2] else f"**Status:** {prod[1]}\n\n"

        if accounts:
            report += "### Accounts\n\n| Account | Balance | Currency | Status |\n|---------|---------|----------|--------|\n"
            for a in accounts:
                report += f"| {a[0]} | ${a[1]:,.2f} | {a[2]} | {a[3]} |\n"

        if txn_summary:
            report += "\n### Transaction Summary\n\n| Type | Count | Total |\n|------|-------|-------|\n"
            for t in txn_summary:
                report += f"| {t[0].title()} | {t[1]} | ${t[2]:,.2f} |\n"

        if disbursements:
            report += "\n### Disbursements\n\n| Stakeholder | Amount | Status |\n|-------------|--------|--------|\n"
            for d in disbursements:
                report += f"| {d[0] or '\u2014'} | ${d[1]:,.2f} | {d[2]} |\n"

        return report
    except Exception as e:
        return f"Error generating report: {e}"


def get_recoupment_position(stakeholder_name: str) -> str:
    """Get a stakeholder's recoupment position across all productions."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            rows = session.execute(text("""
                SELECT p.title, rp.total_owed, rp.total_received, rp.outstanding
                FROM ahcam.recoupment_positions rp
                JOIN ahcam.productions p ON p.production_id = rp.production_id
                JOIN ahcam.stakeholders s ON s.stakeholder_id = rp.stakeholder_id
                WHERE s.name ILIKE :q
            """), {"q": f"%{stakeholder_name}%"}).fetchall()
        if not rows:
            return f"No recoupment positions found for '{stakeholder_name}'."
        header = "| Production | Total Owed | Received | Outstanding |\n|-----------|-----------|----------|-------------|\n"
        lines = [f"| {r[0]} | ${r[1]:,.2f} | ${r[2]:,.2f} | ${r[3]:,.2f} |" for r in rows]
        return f"## Recoupment Position: {stakeholder_name}\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/reports")
    def module_reports(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT r.report_id, r.report_type, r.created_at,
                           p.title, s.name AS stakeholder
                    FROM ahcam.reports r
                    LEFT JOIN ahcam.productions p ON p.production_id = r.production_id
                    LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = r.stakeholder_id
                    ORDER BY r.created_at DESC LIMIT 20
                """)).fetchall()
                prods = s.execute(text("""
                    SELECT production_id, title FROM ahcam.productions ORDER BY title
                """)).fetchall()
        except Exception:
            rows, prods = [], []

        cards = []
        for r in rows:
            cards.append(Div(
                Div(
                    Span(r[3] or "General", cls="deal-card-title"),
                    Span(r[1].replace("_", " ").title(), cls="badge-blue"),
                    style="display:flex;justify-content:space-between;align-items:center;",
                ),
                Div(f"{r[4] or 'All stakeholders'} | {str(r[2])[:10]}", cls="deal-card-meta"),
                cls="deal-card",
            ))

        # Quick-generate buttons for each production
        gen_buttons = []
        for p in prods:
            gen_buttons.append(
                Button(f"Generate: {p[1]}",
                       hx_post=f"/module/report/generate/{p[0]}",
                       hx_target="#report-result",
                       hx_swap="innerHTML",
                       cls="suggestion-btn",
                       style="margin:0.25rem;")
            )

        return Div(
            Div(
                H3("Reports"),
                cls="module-header",
            ),
            Div(*gen_buttons, style="margin-bottom:1rem;") if gen_buttons else "",
            Div(id="report-result"),
            Div(
                *cards if cards else [Div("No reports generated yet. Select a production above to generate a report.", cls="empty-state")],
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/report/generate/{production_id}", methods=["POST"])
    def report_generate(production_id: str, session):
        result = generate_report(production_id)
        return Div(Pre(result, cls="chat-message-content marked"), cls="report-result-box",
                   style="margin-bottom:1rem;border:1px solid #e2e8f0;border-radius:8px;padding:1rem;")
