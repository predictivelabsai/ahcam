"""
Transactions module — Immutable ledger with hash chain.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from utils.ledger import record_transaction, verify_chain


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_transactions(query: str = "") -> str:
    """Search the transaction ledger. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT t.transaction_id, t.transaction_type, t.amount, t.description,
                           t.status, t.created_at, a.account_name
                    FROM ahcam.transactions t
                    LEFT JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                    WHERE t.description ILIKE :q OR t.reference ILIKE :q
                       OR a.account_name ILIKE :q OR t.transaction_type ILIKE :q
                    ORDER BY t.created_at DESC LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT t.transaction_id, t.transaction_type, t.amount, t.description,
                           t.status, t.created_at, a.account_name
                    FROM ahcam.transactions t
                    LEFT JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                    ORDER BY t.created_at DESC LIMIT 20
                """)).fetchall()
        if not rows:
            return "No transactions found."
        header = "| Account | Type | Amount | Description | Status | Date |\n|---------|------|--------|-------------|--------|------|\n"
        lines = []
        for r in rows:
            lines.append(f"| {r[6] or '\u2014'} | {r[1]} | ${r[2]:,.2f} | {r[3] or '\u2014'} | {r[4]} | {str(r[5])[:10]} |")
        return f"## Transaction Ledger\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/transactions")
    def module_transactions(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT t.transaction_id, t.transaction_type, t.amount, t.description,
                           t.status, t.created_at, a.account_name
                    FROM ahcam.transactions t
                    LEFT JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                    ORDER BY t.created_at DESC LIMIT 30
                """)).fetchall()
                totals = s.execute(text("""
                    SELECT COUNT(*),
                           COALESCE(SUM(amount) FILTER (WHERE transaction_type = 'inflow'), 0),
                           COALESCE(SUM(amount) FILTER (WHERE transaction_type = 'outflow'), 0)
                    FROM ahcam.transactions
                """)).fetchone()
        except Exception:
            rows, totals = [], (0, 0, 0)

        txn_rows = []
        for r in rows:
            color = "positive" if r[1] == "inflow" else "negative" if r[1] == "outflow" else ""
            txn_rows.append(Tr(
                Td(r[6] or "\u2014"),
                Td(r[1].title()),
                Td(f"${r[2]:,.2f}", cls=color),
                Td(r[3] or "\u2014"),
                Td(r[4].title()),
                Td(str(r[5])[:16]),
            ))

        return Div(
            Div(
                Div(Div(str(totals[0]), cls="stat-value"), Div("Total Transactions", cls="stat-label"), cls="stat-card"),
                Div(Div(f"${totals[1]:,.2f}", cls="stat-value positive"), Div("Total Inflows", cls="stat-label"), cls="stat-card"),
                Div(Div(f"${totals[2]:,.2f}", cls="stat-value negative"), Div("Total Outflows", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Transaction Ledger"),
                    Button("+ Record Transaction",
                           hx_get="/module/transaction/new",
                           hx_target="#center-content",
                           hx_swap="innerHTML",
                           cls="module-action-btn"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                Table(
                    Thead(Tr(Th("Account"), Th("Type"), Th("Amount"), Th("Description"), Th("Status"), Th("Date"))),
                    Tbody(*txn_rows) if txn_rows else Tbody(Tr(Td("No transactions yet", colspan="6"))),
                    cls="module-table",
                ),
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/transaction/new")
    def transaction_new_form(session):
        pool = get_pool()
        with pool.get_session() as s:
            accounts = s.execute(text("""
                SELECT a.account_id, a.account_name, p.title
                FROM ahcam.collection_accounts a
                LEFT JOIN ahcam.productions p ON p.production_id = a.production_id
                WHERE a.status = 'active' ORDER BY a.account_name
            """)).fetchall()
            stakeholders = s.execute(text("SELECT stakeholder_id, name FROM ahcam.stakeholders ORDER BY name")).fetchall()
        return Div(
            H3("Record Transaction"),
            Form(
                Div(
                    Div(Select(Option("Select Account", value=""),
                               *[Option(f"{a[1]} ({a[2] or 'N/A'})", value=str(a[0])) for a in accounts],
                               name="account_id", required=True), cls="form-group"),
                    Div(Select(Option("Inflow", value="inflow"), Option("Outflow", value="outflow"),
                               Option("Adjustment", value="adjustment"), name="transaction_type"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="number", name="amount", placeholder="Amount", step="0.01", required=True), cls="form-group"),
                    Div(Select(Option("Source (optional)", value=""),
                               *[Option(s[1], value=str(s[0])) for s in stakeholders],
                               name="source_stakeholder_id"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="reference", placeholder="Reference #"), cls="form-group"),
                    Div(Input(type="text", name="description", placeholder="Description"), cls="form-group"),
                    cls="form-row",
                ),
                Button("Record Transaction", type="submit", cls="module-action-btn"),
                hx_post="/module/transaction/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/transaction/create", methods=["POST"])
    def transaction_create(session, account_id: str, transaction_type: str = "inflow",
                           amount: float = 0, source_stakeholder_id: str = "",
                           reference: str = "", description: str = ""):
        try:
            record_transaction(
                account_id=account_id,
                transaction_type=transaction_type,
                amount=amount,
                description=description or None,
                source_stakeholder_id=source_stakeholder_id or None,
                reference=reference or None,
                created_by=session.get("user_id"),
            )
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
        return module_transactions(session)
