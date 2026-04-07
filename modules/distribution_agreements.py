"""
Distribution Agreements module — Territory-level distribution deals with MG tracking.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from config.settings import TERRITORIES, AGREEMENT_STATUSES, AGREEMENT_TYPES, FINANCIAL_STATUSES, CURRENCIES


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_distribution_agreements(query: str = "") -> str:
    """Search distribution agreements by territory, distributor, or production title. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT da.agreement_id, p.title, da.territory, da.distributor_name,
                           da.mg_amount, da.mg_paid, da.financial_status, da.expired
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.productions p ON p.production_id = da.production_id
                    WHERE da.territory ILIKE :q OR da.distributor_name ILIKE :q OR p.title ILIKE :q
                    ORDER BY da.created_at DESC LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT da.agreement_id, p.title, da.territory, da.distributor_name,
                           da.mg_amount, da.mg_paid, da.financial_status, da.expired
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.productions p ON p.production_id = da.production_id
                    ORDER BY da.created_at DESC LIMIT 20
                """)).fetchall()
        if not rows:
            return "No distribution agreements found."
        header = "| Title | Territory | Distributor | MG Amount | MG Paid | Status |\n|-------|-----------|-------------|-----------|---------|--------|\n"
        lines = []
        for r in rows:
            mg = f"${r[4]:,.0f}" if r[4] else "\u2014"
            paid = f"${r[5]:,.0f}" if r[5] else "$0"
            lines.append(f"| {r[1] or '\u2014'} | {r[2]} | {r[3]} | {mg} | {paid} | {r[6]} |")
        return f"## Distribution Agreements\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/distribution-agreements")
    def module_distribution_agreements(session, territory: str = "", distributor: str = "", show_expired: str = ""):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                # Build dynamic filter
                where_clauses = []
                params = {}
                if territory:
                    where_clauses.append("da.territory = :territory")
                    params["territory"] = territory
                if distributor:
                    where_clauses.append("da.distributor_name ILIKE :dist")
                    params["dist"] = f"%{distributor}%"
                if not show_expired:
                    where_clauses.append("da.expired = FALSE")

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

                stats = s.execute(text(f"""
                    SELECT
                        COUNT(*) AS total,
                        COUNT(*) FILTER (WHERE da.expired = FALSE) AS active,
                        COUNT(*) FILTER (WHERE da.expired = TRUE) AS expired,
                        COALESCE(SUM(da.mg_amount), 0) AS total_mg
                    FROM ahcam.distribution_agreements da
                """)).fetchone()

                rows = s.execute(text(f"""
                    SELECT da.agreement_id, p.title, p.production_id, da.territory,
                           da.distributor_name, da.signature_date, da.expiry_date,
                           da.mg_amount, da.mg_paid, da.financial_status, da.expired
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.productions p ON p.production_id = da.production_id
                    {where_sql}
                    ORDER BY da.created_at DESC LIMIT 50
                """), params).fetchall()
        except Exception:
            stats = (0, 0, 0, 0)
            rows = []

        # Stat cards
        stat_grid = Div(
            Div(Div(str(stats[0]), cls="stat-value"), Div("Total Agreements", cls="stat-label"), cls="stat-card"),
            Div(Div(str(stats[1]), cls="stat-value positive"), Div("Active", cls="stat-label"), cls="stat-card"),
            Div(Div(str(stats[2]), cls="stat-value negative"), Div("Expired", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${stats[3]:,.0f}", cls="stat-value"), Div("Total MG Value", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        # Filter form
        filter_form = Form(
            Div(
                Div(Select(
                    Option("All Territories", value=""),
                    *[Option(t, value=t, selected=(t == territory)) for t in TERRITORIES],
                    name="territory",
                ), cls="form-group"),
                Div(Input(type="text", name="distributor", placeholder="Search distributor...",
                          value=distributor), cls="form-group"),
                Div(
                    Label(
                        Input(type="checkbox", name="show_expired", value="1",
                              checked=bool(show_expired)),
                        " Show Expired",
                        style="display:flex;align-items:center;gap:4px;color:#94a3b8;font-size:0.85rem;",
                    ),
                    cls="form-group",
                ),
                Div(Button("Filter", type="submit", cls="module-action-btn",
                           style="font-size:0.85rem;padding:6px 16px;"), cls="form-group"),
                cls="form-row",
            ),
            hx_get="/module/distribution-agreements",
            hx_target="#center-content",
            hx_swap="innerHTML",
            style="margin-bottom:1rem;",
        )

        # Table rows
        table_rows = []
        for r in rows:
            agreement_id = r[0]
            title = r[1] or "\u2014"
            prod_id = r[2]
            terr = r[3]
            dist_name = r[4]
            sig_date = str(r[5])[:10] if r[5] else "\u2014"
            exp_date = str(r[6])[:10] if r[6] else "\u2014"
            mg_amount = r[7] or 0
            mg_paid = r[8] or 0
            fin_status = r[9] or "pending"
            expired = r[10]

            # MG progress bar
            pct_mg = min(100, (mg_paid / mg_amount * 100)) if mg_amount > 0 else 0
            bar_color = "#22c55e" if pct_mg >= 100 else "#3b82f6" if pct_mg >= 50 else "#f59e0b"

            mg_bar = Div(
                Div(f"${mg_paid:,.0f} / ${mg_amount:,.0f}", style="font-size:0.75rem;margin-bottom:2px;"),
                Div(
                    Div(style=f"width:{pct_mg:.0f}%;height:100%;background:{bar_color};border-radius:3px;transition:width 0.3s;"),
                    style="width:100%;height:6px;background:#374151;border-radius:3px;overflow:hidden;",
                ),
                style="min-width:140px;",
            ) if mg_amount > 0 else Span("\u2014")

            fin_cls = "badge-green" if fin_status == "paid" else "badge-amber" if fin_status in ("partial", "pending") else "badge-red"

            table_rows.append(Tr(
                Td(A(title, href="#",
                     onclick=f"loadModule(this,'/module/production/{prod_id}', '{title}'); return false;",
                     style="color:#60a5fa;text-decoration:none;font-weight:500;") if prod_id else title),
                Td(terr),
                Td(dist_name),
                Td(sig_date),
                Td(exp_date),
                Td(f"${mg_amount:,.0f}" if mg_amount else "\u2014", style="text-align:right;"),
                Td(mg_bar),
                Td(Span(fin_status.title(), cls=fin_cls)),
                style="cursor:pointer;",
                hx_get=f"/module/distribution-agreement/{agreement_id}",
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        content_table = Table(
            Thead(Tr(
                Th("Title"), Th("Territory"), Th("Distributor"), Th("Signed"),
                Th("Expiry"), Th("MG Amount"), Th("MG Paid"), Th("Financial Status"),
            )),
            Tbody(*table_rows) if table_rows else Tbody(Tr(Td("No agreements found.", colspan="8", style="text-align:center;"))),
            cls="module-table",
        )

        return Div(
            stat_grid,
            filter_form,
            Div(
                Div(
                    H3("Distribution Agreements"),
                    Button("+ New Agreement",
                           hx_get="/module/distribution-agreement/new",
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

    @rt("/module/distribution-agreement/{agreement_id}")
    def distribution_agreement_detail(agreement_id: str, session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                row = s.execute(text("""
                    SELECT da.agreement_id, p.title, p.production_id, da.territory,
                           da.distributor_name, da.agreement_type, da.signature_date,
                           da.expiry_date, da.mg_amount, da.mg_paid, da.mg_currency,
                           da.financial_status, da.expired, da.notes
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.productions p ON p.production_id = da.production_id
                    WHERE da.agreement_id = :aid
                """), {"aid": agreement_id}).fetchone()
        except Exception:
            row = None
        if not row:
            return Div("Agreement not found.", cls="module-error")

        mg_amount = row[8] or 0
        mg_paid = row[9] or 0
        pct = min(100, (mg_paid / mg_amount * 100)) if mg_amount > 0 else 0
        bar_color = "#22c55e" if pct >= 100 else "#3b82f6" if pct >= 50 else "#f59e0b"

        return Div(
            Div(
                H3(f"{row[1] or 'Unknown'} \u2014 {row[3]}"),
                Span("Expired" if row[12] else "Active",
                     cls=f"status-pill status-{'expired' if row[12] else 'active'}"),
                style="display:flex;gap:1rem;align-items:center;margin-bottom:1rem;",
            ),
            Div(
                Div(Div("Territory", cls="detail-label"), Div(row[3] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Distributor", cls="detail-label"), Div(row[4] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Agreement Type", cls="detail-label"), Div((row[5] or "distribution").replace("_", " ").title(), cls="detail-value"), cls="detail-item"),
                Div(Div("Signature Date", cls="detail-label"), Div(str(row[6])[:10] if row[6] else "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Expiry Date", cls="detail-label"), Div(str(row[7])[:10] if row[7] else "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Currency", cls="detail-label"), Div(row[10] or "USD", cls="detail-value"), cls="detail-item"),
                Div(Div("Financial Status", cls="detail-label"), Div((row[11] or "pending").title(), cls="detail-value"), cls="detail-item"),
                cls="detail-grid",
            ),
            Div(
                H4("MG Progress"),
                Div(f"${mg_paid:,.2f} of ${mg_amount:,.2f} ({pct:.1f}%)", style="margin-bottom:6px;font-size:0.9rem;"),
                Div(
                    Div(style=f"width:{pct:.0f}%;height:10px;background:{bar_color};border-radius:5px;transition:width 0.3s;"),
                    style="width:100%;height:10px;background:#374151;border-radius:5px;overflow:hidden;",
                ),
                cls="detail-section",
                style="margin-top:1rem;",
            ),
            Div(
                H4("Notes"),
                P(row[13] or "No notes."),
                cls="detail-section",
            ) if row[13] else "",
            Button("\u2190 Back to Agreements",
                   hx_get="/module/distribution-agreements",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="back-btn"),
            cls="module-content",
        )

    @rt("/module/distribution-agreement/new")
    def distribution_agreement_new_form(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                prods = s.execute(text("""
                    SELECT production_id, title FROM ahcam.productions ORDER BY title
                """)).fetchall()
        except Exception:
            prods = []

        return Div(
            H3("New Distribution Agreement"),
            Form(
                Div(
                    Div(Select(Option("Select Production", value=""),
                               *[Option(p[1], value=str(p[0])) for p in prods],
                               name="production_id", required=True), cls="form-group"),
                    Div(Select(Option("Select Territory", value=""),
                               *[Option(t, value=t) for t in TERRITORIES],
                               name="territory", required=True), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="text", name="distributor_name", placeholder="Distributor Name", required=True), cls="form-group"),
                    Div(Select(*[Option(t.replace("_", " ").title(), value=t) for t in AGREEMENT_TYPES],
                               name="agreement_type"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="date", name="signature_date"), cls="form-group"),
                    Div(Input(type="date", name="expiry_date"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="number", name="mg_amount", placeholder="MG Amount", step="0.01"), cls="form-group"),
                    Div(Select(*[Option(c, value=c) for c in CURRENCIES], name="currency"), cls="form-group"),
                    Div(Select(*[Option(s.replace("_", " ").title(), value=s) for s in FINANCIAL_STATUSES],
                               name="financial_status"), cls="form-group"),
                    cls="form-row",
                ),
                Div(Textarea(name="notes", placeholder="Notes...", rows="3"), cls="form-group"),
                Button("Create Agreement", type="submit", cls="module-action-btn"),
                hx_post="/module/distribution-agreement/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/distribution-agreement/create", methods=["POST"])
    def distribution_agreement_create(session, production_id: str, territory: str,
                                       distributor_name: str, agreement_type: str = "distribution",
                                       signature_date: str = "", expiry_date: str = "",
                                       mg_amount: float = 0, currency: str = "USD",
                                       financial_status: str = "pending", notes: str = ""):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.distribution_agreements
                        (production_id, territory, distributor_name, agreement_type,
                         signature_date, expiry_date, mg_amount, mg_paid, mg_currency,
                         financial_status, expired, notes, created_by)
                    VALUES (:pid, :territory, :dist, :atype,
                            :sig_date, :exp_date, :mg_amount, 0, :currency,
                            :fin_status, FALSE, :notes, :uid)
                """), {
                    "pid": production_id, "territory": territory,
                    "dist": distributor_name, "atype": agreement_type,
                    "sig_date": signature_date or None, "exp_date": expiry_date or None,
                    "mg_amount": mg_amount or 0, "currency": currency,
                    "fin_status": financial_status, "notes": notes or None,
                    "uid": session.get("user_id"),
                })
        except Exception as e:
            return Div(f"Error creating agreement: {e}", cls="module-error")
        return module_distribution_agreements(session)
