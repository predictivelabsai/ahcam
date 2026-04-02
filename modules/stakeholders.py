"""
Stakeholders module — Manage all parties in a production.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from config.settings import STAKEHOLDER_ROLES


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_stakeholders(query: str = "") -> str:
    """Search stakeholders by name, role, or company. Returns a markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT stakeholder_id, name, role, company, email
                    FROM ahcam.stakeholders
                    WHERE name ILIKE :q OR role ILIKE :q OR company ILIKE :q
                    ORDER BY name LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT stakeholder_id, name, role, company, email
                    FROM ahcam.stakeholders ORDER BY name LIMIT 20
                """)).fetchall()
        if not rows:
            return "No stakeholders found."
        header = "| Name | Role | Company | Email |\n|------|------|---------|-------|\n"
        lines = [f"| {r[1]} | {r[2]} | {r[3] or '\u2014'} | {r[4] or '\u2014'} |" for r in rows]
        return f"## Stakeholders\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/stakeholders")
    def module_stakeholders(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT stakeholder_id, name, role, company, email
                    FROM ahcam.stakeholders ORDER BY name LIMIT 50
                """)).fetchall()
                role_counts = s.execute(text("""
                    SELECT role, COUNT(*) FROM ahcam.stakeholders GROUP BY role
                """)).fetchall()
            total = sum(r[1] for r in role_counts)
            role_map = {r[0]: r[1] for r in role_counts}
        except Exception:
            rows, total, role_map = [], 0, {}

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
                hx_get=f"/module/stakeholder/{r[0]}",
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        return Div(
            Div(
                Div(Div(str(total), cls="stat-value"), Div("Total Stakeholders", cls="stat-label"), cls="stat-card"),
                Div(Div(str(role_map.get("distributor", 0)), cls="stat-value"), Div("Distributors", cls="stat-label"), cls="stat-card"),
                Div(Div(str(role_map.get("financier", 0)), cls="stat-value"), Div("Financiers", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Stakeholders"),
                    Button("+ New Stakeholder",
                           hx_get="/module/stakeholder/new",
                           hx_target="#center-content",
                           hx_swap="innerHTML",
                           cls="module-action-btn"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                *cards if cards else [Div("No stakeholders yet.", cls="empty-state")],
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/stakeholder/new")
    def stakeholder_new_form(session):
        return Div(
            H3("New Stakeholder"),
            Form(
                Div(
                    Div(Input(type="text", name="name", placeholder="Stakeholder Name", required=True), cls="form-group"),
                    Div(Select(*[Option(r.replace("_", " ").title(), value=r) for r in STAKEHOLDER_ROLES], name="role"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="company", placeholder="Company"), cls="form-group"),
                    Div(Input(type="email", name="email", placeholder="Email"), cls="form-group"),
                    Div(Input(type="text", name="phone", placeholder="Phone"), cls="form-group"),
                    cls="form-row",
                ),
                Button("Create Stakeholder", type="submit", cls="module-action-btn"),
                hx_post="/module/stakeholder/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/stakeholder/create", methods=["POST"])
    def stakeholder_create(session, name: str, role: str = "distributor",
                           company: str = "", email: str = "", phone: str = ""):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.stakeholders (name, role, company, email, phone, created_by)
                    VALUES (:name, :role, :company, :email, :phone, :uid)
                """), {
                    "name": name, "role": role,
                    "company": company or None, "email": email or None,
                    "phone": phone or None, "uid": session.get("user_id"),
                })
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
        return module_stakeholders(session)

    @rt("/module/stakeholder/{stakeholder_id}")
    def stakeholder_detail(stakeholder_id: str, session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                row = s.execute(text("""
                    SELECT stakeholder_id, name, role, company, email, phone
                    FROM ahcam.stakeholders WHERE stakeholder_id = :sid
                """), {"sid": stakeholder_id}).fetchone()
        except Exception:
            row = None
        if not row:
            return Div("Stakeholder not found.", cls="module-error")
        return Div(
            H3(row[1]),
            Div(
                Div(Div("Role", cls="detail-label"), Div(row[2].replace("_", " ").title(), cls="detail-value"), cls="detail-item"),
                Div(Div("Company", cls="detail-label"), Div(row[3] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Email", cls="detail-label"), Div(row[4] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Phone", cls="detail-label"), Div(row[5] or "\u2014", cls="detail-value"), cls="detail-item"),
                cls="detail-grid",
            ),
            Button("\u2190 Back",
                   hx_get="/module/stakeholders",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="back-btn"),
            cls="module-content",
        )
