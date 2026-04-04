"""
CRM module — Deals, Contacts, Sales/Collections in one view.
Supports list/table and Kanban views.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool

DEAL_STAGES = ["lead", "negotiation", "term_sheet", "due_diligence", "closing", "closed_won", "closed_lost"]
DEAL_TYPES = ["distribution", "sales", "finance", "co_production", "pre_sale"]
CONTACT_TYPES = ["distributor", "producer", "sales_agent", "investor", "legal", "talent", "guild", "other"]


# ---------------------------------------------------------------------------
# AI Agent Tools
# ---------------------------------------------------------------------------

def search_crm_deals(query: str = "") -> str:
    """Search CRM deals by title, status, stage, or contact. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT d.deal_id, d.title, d.status, d.stage, d.amount, d.territory,
                           c.name AS contact, p.title AS production
                    FROM ahcam.crm_deals d
                    LEFT JOIN ahcam.crm_contacts c ON c.contact_id = d.contact_id
                    LEFT JOIN ahcam.productions p ON p.production_id = d.production_id
                    WHERE d.title ILIKE :q OR d.status ILIKE :q OR d.stage ILIKE :q
                       OR c.name ILIKE :q OR p.title ILIKE :q
                    ORDER BY d.created_at DESC LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT d.deal_id, d.title, d.status, d.stage, d.amount, d.territory,
                           c.name AS contact, p.title AS production
                    FROM ahcam.crm_deals d
                    LEFT JOIN ahcam.crm_contacts c ON c.contact_id = d.contact_id
                    LEFT JOIN ahcam.productions p ON p.production_id = d.production_id
                    ORDER BY d.created_at DESC LIMIT 20
                """)).fetchall()
        if not rows:
            return "No deals found."
        header = "| Deal | Stage | Amount | Contact | Production |\n|------|-------|--------|---------|------------|\n"
        lines = []
        for r in rows:
            amt = f"${r[4]:,.0f}" if r[4] else "\u2014"
            lines.append(f"| {r[1]} | {r[3]} | {amt} | {r[6] or '\u2014'} | {r[7] or '\u2014'} |")
        return f"## CRM Deals\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def search_crm_contacts(query: str = "") -> str:
    """Search CRM contacts by name, type, or company."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT contact_id, name, contact_type, company, email
                    FROM ahcam.crm_contacts
                    WHERE name ILIKE :q OR contact_type ILIKE :q OR company ILIKE :q
                    ORDER BY name LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT contact_id, name, contact_type, company, email
                    FROM ahcam.crm_contacts ORDER BY name LIMIT 20
                """)).fetchall()
        if not rows:
            return "No contacts found."
        header = "| Name | Type | Company | Email |\n|------|------|---------|-------|\n"
        lines = [f"| {r[1]} | {r[2]} | {r[3] or '\u2014'} | {r[4] or '\u2014'} |" for r in rows]
        return f"## CRM Contacts\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    # --- Deals list / table view ---
    @rt("/module/crm")
    def module_crm(session, view: str = "table"):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                deals = s.execute(text("""
                    SELECT d.deal_id, d.title, d.status, d.stage, d.amount, d.currency,
                           d.territory, d.close_date, c.name AS contact, p.title AS production
                    FROM ahcam.crm_deals d
                    LEFT JOIN ahcam.crm_contacts c ON c.contact_id = d.contact_id
                    LEFT JOIN ahcam.productions p ON p.production_id = d.production_id
                    ORDER BY d.created_at DESC LIMIT 50
                """)).fetchall()
                totals = s.execute(text("""
                    SELECT COUNT(*), COALESCE(SUM(amount), 0),
                           COUNT(*) FILTER (WHERE stage = 'closed_won')
                    FROM ahcam.crm_deals
                """)).fetchone()
                contacts_count = s.execute(text("SELECT COUNT(*) FROM ahcam.crm_contacts")).scalar()
        except Exception:
            deals, totals, contacts_count = [], (0, 0, 0), 0

        # View toggle
        view_toggle = Div(
            Button("Table", cls=f"view-toggle-btn {'active' if view != 'kanban' else ''}",
                   hx_get="/module/crm?view=table", hx_target="#center-content", hx_swap="innerHTML"),
            Button("Kanban", cls=f"view-toggle-btn {'active' if view == 'kanban' else ''}",
                   hx_get="/module/crm?view=kanban", hx_target="#center-content", hx_swap="innerHTML"),
            cls="view-toggle",
        )

        stats = Div(
            Div(Div(str(totals[0]), cls="stat-value"), Div("Total Deals", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${totals[1]:,.0f}", cls="stat-value"), Div("Pipeline Value", cls="stat-label"), cls="stat-card"),
            Div(Div(str(totals[2]), cls="stat-value"), Div("Won", cls="stat-label"), cls="stat-card"),
            Div(Div(str(contacts_count), cls="stat-value"), Div("Contacts", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        if view == "kanban":
            content = _kanban_view(deals)
        else:
            content = _table_view(deals)

        return Div(
            stats,
            Div(
                Div(
                    H3("CRM"),
                    Div(
                        view_toggle,
                        Button("+ Deal", hx_get="/module/crm/deal/new", hx_target="#center-content", hx_swap="innerHTML", cls="module-action-btn"),
                        Button("+ Contact", hx_get="/module/crm/contact/new", hx_target="#center-content", hx_swap="innerHTML", cls="module-action-btn", style="margin-left:0.25rem;"),
                        style="display:flex;gap:0.5rem;align-items:center;",
                    ),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                content,
                cls="module-list",
            ),
            cls="module-content",
        )

    def _table_view(deals):
        rows = []
        for d in deals:
            stage_cls = "badge-green" if d[3] == "closed_won" else "badge-red" if d[3] == "closed_lost" else "badge-blue"
            amt = f"${d[4]:,.0f}" if d[4] else "\u2014"
            rows.append(Tr(
                Td(A(d[1], hx_get=f"/module/crm/deal/{d[0]}", hx_target="#center-content", hx_swap="innerHTML",
                     style="color:#0066cc;cursor:pointer;text-decoration:none;font-weight:500;")),
                Td(Span(d[3].replace("_", " ").title(), cls=stage_cls)),
                Td(amt),
                Td(d[8] or "\u2014"),
                Td(d[9] or "\u2014"),
                Td(d[6] or "\u2014"),
                Td(str(d[7])[:10] if d[7] else "\u2014"),
            ))
        return Table(
            Thead(Tr(Th("Deal"), Th("Stage"), Th("Amount"), Th("Contact"), Th("Production"), Th("Territory"), Th("Close Date"))),
            Tbody(*rows) if rows else Tbody(Tr(Td("No deals yet. Create your first deal.", colspan="7"))),
            cls="module-table",
        )

    def _kanban_view(deals):
        columns = []
        for stage in DEAL_STAGES:
            stage_deals = [d for d in deals if d[3] == stage]
            cards = []
            for d in stage_deals:
                amt = f"${d[4]:,.0f}" if d[4] else ""
                cards.append(Div(
                    Div(d[1], cls="kanban-card-title"),
                    Div(f"{d[8] or ''} {amt}", cls="kanban-card-meta"),
                    cls="kanban-card",
                    hx_get=f"/module/crm/deal/{d[0]}", hx_target="#center-content", hx_swap="innerHTML",
                ))
            columns.append(Div(
                Div(
                    Span(stage.replace("_", " ").title(), cls="kanban-col-title"),
                    Span(str(len(stage_deals)), cls="kanban-col-count"),
                    cls="kanban-col-header",
                ),
                Div(*cards, cls="kanban-col-body"),
                cls="kanban-col",
            ))
        return Div(*columns, cls="kanban-board")

    # --- Contacts tab ---
    @rt("/module/crm/contacts")
    def crm_contacts_list(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT contact_id, name, contact_type, company, email, territory
                    FROM ahcam.crm_contacts ORDER BY name LIMIT 50
                """)).fetchall()
        except Exception:
            rows = []
        cards = []
        for r in rows:
            cards.append(Div(
                Div(
                    Span(r[1], cls="deal-card-title"),
                    Span(r[2].replace("_", " ").title(), cls="badge-blue"),
                    style="display:flex;justify-content:space-between;align-items:center;",
                ),
                Div(f"{r[3] or '\u2014'} | {r[4] or '\u2014'}", cls="deal-card-meta"),
                cls="deal-card",
            ))
        return Div(
            Div(
                H3("Contacts"),
                Button("+ Contact", hx_get="/module/crm/contact/new", hx_target="#center-content", hx_swap="innerHTML", cls="module-action-btn"),
                style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
            ),
            *cards if cards else [Div("No contacts yet.", cls="empty-state")],
            cls="module-content",
        )

    # --- New deal form ---
    @rt("/module/crm/deal/new")
    def crm_deal_new(session):
        pool = get_pool()
        with pool.get_session() as s:
            prods = s.execute(text("SELECT production_id, title FROM ahcam.productions ORDER BY title")).fetchall()
            contacts = s.execute(text("SELECT contact_id, name FROM ahcam.crm_contacts ORDER BY name")).fetchall()
        return Div(
            H3("New Deal"),
            Form(
                Div(
                    Div(Input(type="text", name="title", placeholder="Deal Title", required=True), cls="form-group"),
                    Div(Select(*[Option(t.replace("_", " ").title(), value=t) for t in DEAL_TYPES], name="deal_type"), cls="form-group"),
                    Div(Select(*[Option(s.replace("_", " ").title(), value=s) for s in DEAL_STAGES], name="stage"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Select(Option("Select Production", value=""), *[Option(p[1], value=str(p[0])) for p in prods], name="production_id"), cls="form-group"),
                    Div(Select(Option("Select Contact", value=""), *[Option(c[1], value=str(c[0])) for c in contacts], name="contact_id"), cls="form-group"),
                    Div(Input(type="number", name="amount", placeholder="Amount", step="1000"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="territory", placeholder="Territory"), cls="form-group"),
                    Div(Input(type="date", name="close_date"), cls="form-group"),
                    cls="form-row",
                ),
                Button("Create Deal", type="submit", cls="module-action-btn"),
                hx_post="/module/crm/deal/create", hx_target="#center-content", hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/crm/deal/create", methods=["POST"])
    def crm_deal_create(session, title: str, deal_type: str = "distribution", stage: str = "lead",
                        production_id: str = "", contact_id: str = "", amount: float = None,
                        territory: str = "", close_date: str = ""):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.crm_deals
                        (title, deal_type, stage, status, production_id, contact_id, amount, territory, close_date, created_by)
                    VALUES (:title, :dtype, :stage, 'pipeline', :pid, :cid, :amount, :territory, :cdate, :uid)
                """), {
                    "title": title, "dtype": deal_type, "stage": stage,
                    "pid": production_id or None, "cid": contact_id or None,
                    "amount": amount, "territory": territory or None,
                    "cdate": close_date or None, "uid": session.get("user_id"),
                })
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
        return module_crm(session)

    # --- Deal detail ---
    @rt("/module/crm/deal/{deal_id}")
    def crm_deal_detail(deal_id: str, session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                row = s.execute(text("""
                    SELECT d.deal_id, d.title, d.deal_type, d.status, d.stage, d.amount,
                           d.currency, d.territory, d.close_date,
                           c.name AS contact, p.title AS production
                    FROM ahcam.crm_deals d
                    LEFT JOIN ahcam.crm_contacts c ON c.contact_id = d.contact_id
                    LEFT JOIN ahcam.productions p ON p.production_id = d.production_id
                    WHERE d.deal_id = :did
                """), {"did": deal_id}).fetchone()
        except Exception:
            row = None
        if not row:
            return Div("Deal not found.", cls="module-error")
        amt = f"${row[5]:,.0f} {row[6]}" if row[5] else "\u2014"
        return Div(
            Div(H3(row[1]), Span(row[4].replace("_", " ").title(), cls="badge-blue"), style="display:flex;gap:1rem;align-items:center;margin-bottom:1rem;"),
            Div(
                Div(Div("Type", cls="detail-label"), Div(row[2].replace("_", " ").title(), cls="detail-value"), cls="detail-item"),
                Div(Div("Amount", cls="detail-label"), Div(amt, cls="detail-value"), cls="detail-item"),
                Div(Div("Contact", cls="detail-label"), Div(row[9] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Production", cls="detail-label"), Div(row[10] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Territory", cls="detail-label"), Div(row[7] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Close Date", cls="detail-label"), Div(str(row[8])[:10] if row[8] else "\u2014", cls="detail-value"), cls="detail-item"),
                cls="detail-grid",
            ),
            Button("\u2190 Back", hx_get="/module/crm", hx_target="#center-content", hx_swap="innerHTML", cls="back-btn"),
            cls="module-content",
        )

    # --- New contact form ---
    @rt("/module/crm/contact/new")
    def crm_contact_new(session):
        return Div(
            H3("New Contact"),
            Form(
                Div(
                    Div(Input(type="text", name="name", placeholder="Contact Name", required=True), cls="form-group"),
                    Div(Select(*[Option(t.replace("_", " ").title(), value=t) for t in CONTACT_TYPES], name="contact_type"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="company", placeholder="Company"), cls="form-group"),
                    Div(Input(type="email", name="email", placeholder="Email"), cls="form-group"),
                    Div(Input(type="text", name="phone", placeholder="Phone"), cls="form-group"),
                    cls="form-row",
                ),
                Button("Create Contact", type="submit", cls="module-action-btn"),
                hx_post="/module/crm/contact/create", hx_target="#center-content", hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/crm/contact/create", methods=["POST"])
    def crm_contact_create(session, name: str, contact_type: str = "distributor",
                           company: str = "", email: str = "", phone: str = ""):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.crm_contacts (name, contact_type, company, email, phone, created_by)
                    VALUES (:name, :ctype, :company, :email, :phone, :uid)
                """), {
                    "name": name, "ctype": contact_type,
                    "company": company or None, "email": email or None,
                    "phone": phone or None, "uid": session.get("user_id"),
                })
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
        return module_crm(session)
