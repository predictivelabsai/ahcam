"""
Beneficiary Bank Accounts module — Manage bank details per production/stakeholder.
Account numbers and IBANs are masked on display.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from config.settings import CURRENCIES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask(value):
    """Mask a bank account number/IBAN, showing only last 4 chars."""
    if not value:
        return "\u2014"
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_bank_accounts(query: str = "") -> str:
    """Search beneficiary bank accounts. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT ba.bank_account_id, ba.beneficiary_name, ba.bank_name,
                           ba.currency, ba.swift_bic, ba.status, p.title
                    FROM ahcam.beneficiary_bank_accounts ba
                    LEFT JOIN ahcam.productions p ON p.production_id = ba.production_id
                    WHERE ba.beneficiary_name ILIKE :q OR ba.bank_name ILIKE :q
                       OR p.title ILIKE :q
                    ORDER BY ba.created_at DESC LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT ba.bank_account_id, ba.beneficiary_name, ba.bank_name,
                           ba.currency, ba.swift_bic, ba.status, p.title
                    FROM ahcam.beneficiary_bank_accounts ba
                    LEFT JOIN ahcam.productions p ON p.production_id = ba.production_id
                    ORDER BY ba.created_at DESC LIMIT 20
                """)).fetchall()
        if not rows:
            return "No bank accounts found."
        header = "| Beneficiary | Bank | Currency | SWIFT/BIC | Status | Production |\n|-------------|------|----------|-----------|--------|------------|\n"
        lines = []
        for r in rows:
            lines.append(f"| {r[1]} | {r[2] or '\u2014'} | {r[3]} | {r[4] or '\u2014'} | {r[5] or 'active'} | {r[6] or '\u2014'} |")
        return f"## Bank Accounts\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/bank-accounts")
    def module_bank_accounts(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT ba.bank_account_id, ba.beneficiary_name, ba.bank_name,
                           ba.currency, ba.swift_bic, ba.status,
                           ba.account_number, ba.iban,
                           p.title AS production_title
                    FROM ahcam.beneficiary_bank_accounts ba
                    LEFT JOIN ahcam.productions p ON p.production_id = ba.production_id
                    ORDER BY ba.created_at DESC LIMIT 50
                """)).fetchall()
                totals = s.execute(text("""
                    SELECT COUNT(*),
                           COUNT(*) FILTER (WHERE status = 'active' OR status IS NULL)
                    FROM ahcam.beneficiary_bank_accounts
                """)).fetchone()
        except Exception:
            rows, totals = [], (0, 0)

        table_rows = []
        for r in rows:
            acct_masked = _mask(r[6])
            iban_masked = _mask(r[7])
            status = r[5] or "active"
            status_cls = "badge-green" if status == "active" else "badge-amber" if status == "pending" else "badge-red"

            table_rows.append(Tr(
                Td(r[8] or "\u2014"),
                Td(r[1]),
                Td(r[2] or "\u2014"),
                Td(r[3] or "USD"),
                Td(Span(acct_masked, style="font-family:monospace;font-size:0.85rem;"),
                   title="Account number masked"),
                Td(Span(iban_masked, style="font-family:monospace;font-size:0.85rem;"),
                   title="IBAN masked"),
                Td(r[4] or "\u2014"),
                Td(Span(status.title(), cls=status_cls)),
            ))

        content_table = Table(
            Thead(Tr(
                Th("Production"), Th("Beneficiary"), Th("Bank"), Th("Currency"),
                Th("Account #"), Th("IBAN"), Th("SWIFT/BIC"), Th("Status"),
            )),
            Tbody(*table_rows) if table_rows else Tbody(Tr(Td("No bank accounts found.", colspan="8", style="text-align:center;"))),
            cls="module-table",
        )

        return Div(
            Div(
                Div(Div(str(totals[0]), cls="stat-value"), Div("Total Accounts", cls="stat-label"), cls="stat-card"),
                Div(Div(str(totals[1]), cls="stat-value positive"), Div("Active", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Beneficiary Bank Accounts"),
                    Button("+ Add Bank Account",
                           hx_get="/module/bank-account/new",
                           hx_target="#center-content",
                           hx_swap="innerHTML",
                           cls="module-action-btn"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                content_table,
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/bank-account/new")
    def bank_account_new_form(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                prods = s.execute(text("""
                    SELECT production_id, title FROM ahcam.productions ORDER BY title
                """)).fetchall()
                stakeholders = s.execute(text("""
                    SELECT stakeholder_id, name FROM ahcam.stakeholders ORDER BY name
                """)).fetchall()
        except Exception:
            prods, stakeholders = [], []

        return Div(
            H3("Add Bank Account"),
            Form(
                Div(
                    Div(Select(Option("Select Production (optional)", value=""),
                               *[Option(p[1], value=str(p[0])) for p in prods],
                               name="production_id"), cls="form-group"),
                    Div(Select(Option("Select Stakeholder (optional)", value=""),
                               *[Option(s[1], value=str(s[0])) for s in stakeholders],
                               name="stakeholder_id"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="beneficiary_name", placeholder="Beneficiary Name", required=True), cls="form-group"),
                    Div(Input(type="text", name="bank_name", placeholder="Bank Name"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="bank_address", placeholder="Bank Address"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="account_number", placeholder="Account Number"), cls="form-group"),
                    Div(Input(type="text", name="iban", placeholder="IBAN"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="swift_bic", placeholder="SWIFT/BIC"), cls="form-group"),
                    Div(Select(*[Option(c, value=c) for c in CURRENCIES], name="currency"), cls="form-group"),
                    cls="form-row",
                ),
                Button("Add Bank Account", type="submit", cls="module-action-btn"),
                hx_post="/module/bank-account/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/bank-account/create", methods=["POST"])
    def bank_account_create(session, beneficiary_name: str, production_id: str = "",
                            stakeholder_id: str = "", bank_name: str = "",
                            bank_address: str = "", account_number: str = "",
                            iban: str = "", swift_bic: str = "", currency: str = "USD"):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.beneficiary_bank_accounts
                        (production_id, stakeholder_id, beneficiary_name, bank_name,
                         bank_address, account_number, iban, swift_bic, currency,
                         status, created_by)
                    VALUES (:pid, :sid, :bname, :bank, :baddr, :acct, :iban, :swift,
                            :currency, 'active', :uid)
                """), {
                    "pid": production_id or None,
                    "sid": stakeholder_id or None,
                    "bname": beneficiary_name,
                    "bank": bank_name or None,
                    "baddr": bank_address or None,
                    "acct": account_number or None,
                    "iban": iban or None,
                    "swift": swift_bic or None,
                    "currency": currency,
                    "uid": session.get("user_id"),
                })
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
        return module_bank_accounts(session)
