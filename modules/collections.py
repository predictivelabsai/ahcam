"""
Collection Accounts module — Core CAM: segregated accounts per production.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from config.settings import ACCOUNT_STATUSES, CURRENCIES


# ---------------------------------------------------------------------------
# AI Agent Tools
# ---------------------------------------------------------------------------

def search_accounts(query: str = "") -> str:
    """Search collection accounts by name, status, or production. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT a.account_id, a.account_name, a.balance, a.currency, a.status,
                           p.title AS production_title
                    FROM ahcam.collection_accounts a
                    LEFT JOIN ahcam.productions p ON p.production_id = a.production_id
                    WHERE a.account_name ILIKE :q OR a.status ILIKE :q OR p.title ILIKE :q
                    ORDER BY a.created_at DESC LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT a.account_id, a.account_name, a.balance, a.currency, a.status,
                           p.title AS production_title
                    FROM ahcam.collection_accounts a
                    LEFT JOIN ahcam.productions p ON p.production_id = a.production_id
                    ORDER BY a.created_at DESC LIMIT 20
                """)).fetchall()
        if not rows:
            return "No collection accounts found."
        header = "| Account | Production | Balance | Currency | Status |\n|---------|-----------|---------|----------|--------|\n"
        lines = []
        for r in rows:
            bal = f"${r[2]:,.2f}" if r[2] is not None else "$0.00"
            lines.append(f"| {r[1]} | {r[5] or '\u2014'} | {bal} | {r[3]} | {r[4]} |")
        return f"## Collection Accounts\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def get_account_balance(account_id: str) -> str:
    """Get the balance and details of a specific collection account."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            row = session.execute(text("""
                SELECT a.account_id, a.account_name, a.balance, a.currency, a.status,
                       a.bank_name, p.title
                FROM ahcam.collection_accounts a
                LEFT JOIN ahcam.productions p ON p.production_id = a.production_id
                WHERE a.account_id = :aid
            """), {"aid": account_id}).fetchone()
        if not row:
            return f"Account `{account_id}` not found."
        return (
            f"## {row[1]}\n\n"
            f"| Field | Value |\n|-------|-------|\n"
            f"| Production | {row[6] or '\u2014'} |\n"
            f"| Balance | ${row[2]:,.2f} {row[3]} |\n"
            f"| Status | {row[4]} |\n"
            f"| Bank | {row[5] or '\u2014'} |"
        )
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/accounts")
    def module_accounts(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT a.account_id, a.account_name, a.balance, a.currency, a.status,
                           p.title AS production_title
                    FROM ahcam.collection_accounts a
                    LEFT JOIN ahcam.productions p ON p.production_id = a.production_id
                    ORDER BY a.created_at DESC LIMIT 20
                """)).fetchall()
                totals = s.execute(text("""
                    SELECT COUNT(*), COALESCE(SUM(balance), 0),
                           COUNT(*) FILTER (WHERE status = 'active')
                    FROM ahcam.collection_accounts
                """)).fetchone()
        except Exception:
            rows, totals = [], (0, 0, 0)

        cards = []
        for r in rows:
            bal = f"${r[2]:,.2f}" if r[2] is not None else "$0.00"
            status_cls = "badge-green" if r[4] == "active" else "badge-amber" if r[4] == "frozen" else "badge-red"
            cards.append(Div(
                Div(
                    Span(r[1], cls="deal-card-title"),
                    Span(r[4].title(), cls=status_cls),
                    style="display:flex;justify-content:space-between;align-items:center;",
                ),
                Div(f"{r[5] or '\u2014'} | {bal} {r[3]}", cls="deal-card-meta"),
                cls="deal-card",
                hx_get=f"/module/account/{r[0]}",
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        return Div(
            Div(
                Div(Div(str(totals[0]), cls="stat-value"), Div("Total Accounts", cls="stat-label"), cls="stat-card"),
                Div(Div(f"${totals[1]:,.2f}", cls="stat-value"), Div("Total Balance", cls="stat-label"), cls="stat-card"),
                Div(Div(str(totals[2]), cls="stat-value"), Div("Active", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Collection Accounts"),
                    Button("+ New Account",
                           hx_get="/module/account/new",
                           hx_target="#center-content",
                           hx_swap="innerHTML",
                           cls="module-action-btn"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                *cards if cards else [Div("No collection accounts yet.", cls="empty-state")],
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/account/new")
    def account_new_form(session):
        pool = get_pool()
        with pool.get_session() as s:
            prods = s.execute(text("""
                SELECT production_id, title FROM ahcam.productions ORDER BY title
            """)).fetchall()
        return Div(
            H3("New Collection Account"),
            Form(
                Div(
                    Div(Input(type="text", name="account_name", placeholder="Account Name", required=True), cls="form-group"),
                    Div(Select(Option("Select Production", value=""), *[Option(p[1], value=str(p[0])) for p in prods], name="production_id"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="bank_name", placeholder="Bank Name"), cls="form-group"),
                    Div(Select(*[Option(c, value=c) for c in CURRENCIES], name="currency"), cls="form-group"),
                    cls="form-row",
                ),
                Button("Create Account", type="submit", cls="module-action-btn"),
                hx_post="/module/account/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/account/create", methods=["POST"])
    def account_create(session, account_name: str, production_id: str = "",
                       bank_name: str = "", currency: str = "USD"):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.collection_accounts
                        (account_name, production_id, bank_name, currency, created_by)
                    VALUES (:name, :pid, :bank, :currency, :uid)
                """), {
                    "name": account_name,
                    "pid": production_id or None,
                    "bank": bank_name or None,
                    "currency": currency,
                    "uid": session.get("user_id"),
                })
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
        return module_accounts(session)

    @rt("/module/account/{account_id}")
    def account_detail(account_id: str, session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                row = s.execute(text("""
                    SELECT a.account_id, a.account_name, a.balance, a.currency, a.status,
                           a.bank_name, p.title
                    FROM ahcam.collection_accounts a
                    LEFT JOIN ahcam.productions p ON p.production_id = a.production_id
                    WHERE a.account_id = :aid
                """), {"aid": account_id}).fetchone()
                recent_txns = s.execute(text("""
                    SELECT transaction_type, amount, description, created_at
                    FROM ahcam.transactions
                    WHERE account_id = :aid
                    ORDER BY created_at DESC LIMIT 5
                """), {"aid": account_id}).fetchall()
        except Exception:
            row, recent_txns = None, []
        if not row:
            return Div("Account not found.", cls="module-error")

        txn_rows = []
        for t in recent_txns:
            color = "positive" if t[0] == "inflow" else "negative"
            txn_rows.append(Tr(
                Td(t[0].title()), Td(f"${t[1]:,.2f}", cls=color),
                Td(t[2] or "\u2014"), Td(str(t[3])[:16]),
            ))

        return Div(
            H3(row[1]),
            Div(
                Div(Div("Production", cls="detail-label"), Div(row[6] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Balance", cls="detail-label"), Div(f"${row[2]:,.2f} {row[3]}", cls="detail-value"), cls="detail-item"),
                Div(Div("Status", cls="detail-label"), Div(row[4].title(), cls="detail-value"), cls="detail-item"),
                Div(Div("Bank", cls="detail-label"), Div(row[5] or "\u2014", cls="detail-value"), cls="detail-item"),
                cls="detail-grid",
            ),
            Div(
                H4("Recent Transactions"),
                Table(
                    Thead(Tr(Th("Type"), Th("Amount"), Th("Description"), Th("Date"))),
                    Tbody(*txn_rows) if txn_rows else Tbody(Tr(Td("No transactions yet", colspan="4"))),
                    cls="module-table",
                ) if True else "",
                cls="detail-section",
            ),
            Button("\u2190 Back",
                   hx_get="/module/accounts",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="back-btn"),
            cls="module-content",
        )
