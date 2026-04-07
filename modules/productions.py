"""
Productions module — CRUD for film/TV productions.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from config.settings import PRODUCTION_STATUSES, PROJECT_TYPES, GENRES, CURRENCIES


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_productions(query: str = "") -> str:
    """Search productions by title, status, or genre. Returns a markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT production_id, title, status, budget, producer, genre
                    FROM ahcam.productions
                    WHERE title ILIKE :q OR status ILIKE :q OR genre ILIKE :q
                    ORDER BY created_at DESC LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT production_id, title, status, budget, producer, genre
                    FROM ahcam.productions ORDER BY created_at DESC LIMIT 20
                """)).fetchall()
        if not rows:
            return "No productions found."
        header = "| Title | Status | Budget | Producer | Genre |\n|-------|--------|--------|----------|-------|\n"
        lines = []
        for r in rows:
            amt = f"${r[3]:,.0f}" if r[3] else "\u2014"
            lines.append(f"| {r[1]} | {r[2]} | {amt} | {r[4] or '\u2014'} | {r[5] or '\u2014'} |")
        return f"## Productions\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error searching productions: {e}"


def get_production_detail(production_id: str) -> str:
    """Get detailed information about a specific production by its ID."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            row = session.execute(text("""
                SELECT production_id, title, project_type, genre, status, budget,
                       currency, producer, director, cast_summary, synopsis, territory
                FROM ahcam.productions WHERE production_id = :pid
            """), {"pid": production_id}).fetchone()
        if not row:
            return f"Production `{production_id}` not found."
        budget = f"${row[5]:,.0f} {row[6]}" if row[5] else "\u2014"
        return (
            f"## {row[1]}\n\n"
            f"| Field | Value |\n|-------|-------|\n"
            f"| Type | {row[2]} |\n"
            f"| Genre | {row[3] or '\u2014'} |\n"
            f"| Status | {row[4]} |\n"
            f"| Budget | {budget} |\n"
            f"| Producer | {row[7] or '\u2014'} |\n"
            f"| Director | {row[8] or '\u2014'} |\n"
            f"| Cast | {row[9] or '\u2014'} |\n"
            f"| Territory | {row[11] or '\u2014'} |\n\n"
            f"**Synopsis:** {row[10] or 'N/A'}"
        )
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/productions")
    def module_productions(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                stats = s.execute(text("""
                    SELECT status, COUNT(*), COALESCE(SUM(budget), 0)
                    FROM ahcam.productions GROUP BY status
                """)).fetchall()
                recent = s.execute(text("""
                    SELECT production_id, title, status, budget, producer, genre, created_at
                    FROM ahcam.productions ORDER BY created_at DESC LIMIT 10
                """)).fetchall()
            stat_map = {r[0]: (r[1], r[2]) for r in stats}
            total_count = sum(r[1] for r in stats)
            total_budget = sum(r[2] for r in stats)
        except Exception:
            stat_map, total_count, total_budget, recent = {}, 0, 0, []

        prod_cards = []
        for r in recent:
            status_cls = f"status-{r[2]}" if r[2] else "status-development"
            amt = f"${r[3]:,.0f}" if r[3] else "\u2014"
            prod_cards.append(Div(
                Div(
                    Span(r[1], cls="deal-card-title"),
                    Span(r[2].replace("_", " ").title(), cls=f"status-pill {status_cls}"),
                    style="display:flex;justify-content:space-between;align-items:center;",
                ),
                Div(f"{r[4] or '\u2014'} | {r[5] or '\u2014'} | {amt}", cls="deal-card-meta"),
                cls="deal-card",
                hx_get=f"/module/production/{r[0]}",
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        return Div(
            Div(
                Div(
                    Div(str(total_count), cls="stat-value"),
                    Div("Total Productions", cls="stat-label"),
                    cls="stat-card",
                ),
                Div(
                    Div(f"${total_budget:,.0f}", cls="stat-value"),
                    Div("Total Budget", cls="stat-label"),
                    cls="stat-card",
                ),
                Div(
                    Div(str(stat_map.get("production", (0,))[0]), cls="stat-value"),
                    Div("In Production", cls="stat-label"),
                    cls="stat-card",
                ),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Productions"),
                    Button("+ New Production",
                           hx_get="/module/production/new",
                           hx_target="#center-content",
                           hx_swap="innerHTML",
                           cls="module-action-btn"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                *prod_cards if prod_cards else [Div("No productions yet. Create your first production.", cls="empty-state")],
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/production/new")
    def production_new_form(session):
        return Div(
            H3("New Production"),
            Form(
                Div(
                    Div(Input(type="text", name="title", placeholder="Production Title", required=True), cls="form-group"),
                    Div(Select(*[Option(t.replace("_", " ").title(), value=t) for t in PROJECT_TYPES], name="project_type"), cls="form-group"),
                    Div(Select(Option("Select Genre", value=""), *[Option(g, value=g) for g in GENRES], name="genre"), cls="form-group"),
                    Div(Select(*[Option(s.replace("_", " ").title(), value=s) for s in PRODUCTION_STATUSES], name="status"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Input(type="number", name="budget", placeholder="Budget", step="1000"), cls="form-group"),
                    Div(Select(*[Option(c, value=c) for c in CURRENCIES], name="currency"), cls="form-group"),
                    Div(Input(type="text", name="producer", placeholder="Producer"), cls="form-group"),
                    Div(Input(type="text", name="director", placeholder="Director"), cls="form-group"),
                    cls="form-row",
                ),
                Div(Textarea(name="synopsis", placeholder="Synopsis...", rows="3"), cls="form-group"),
                Button("Create Production", type="submit", cls="module-action-btn"),
                hx_post="/module/production/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/production/create", methods=["POST"])
    def production_create(session, title: str, project_type: str = "feature_film",
                          genre: str = "", status: str = "development",
                          budget: float = None, currency: str = "USD",
                          producer: str = "", director: str = "", synopsis: str = ""):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.productions
                        (title, project_type, genre, status, budget, currency, producer, director, synopsis, created_by)
                    VALUES (:title, :type, :genre, :status, :budget, :currency, :producer, :director, :synopsis, :uid)
                """), {
                    "title": title, "type": project_type, "genre": genre or None,
                    "status": status, "budget": budget, "currency": currency,
                    "producer": producer or None, "director": director or None,
                    "synopsis": synopsis or None,
                    "uid": session.get("user_id"),
                })
        except Exception as e:
            return Div(f"Error creating production: {e}", cls="module-error")
        return module_productions(session)

    # -------------------------------------------------------------------
    # CAMA Tab Bar helper
    # -------------------------------------------------------------------

    def _tab_bar(production_id, active_tab="overview"):
        tabs = [
            ("overview", "Overview"), ("cgr", "CGR"), ("receipts", "Receipts"),
            ("outstanding", "Outstanding"), ("das", "DAs"), ("waterfall", "Waterfall"),
            ("disbursements", "Disbursements"), ("statements", "Statements"),
            ("bank-details", "Bank Details"), ("comments", "Comments"),
        ]
        items = []
        for tab_id, label in tabs:
            active = "background:#3b82f6;color:#fff;" if tab_id == active_tab else "background:#1e293b;color:#94a3b8;"
            items.append(
                A(label, href="#",
                  hx_get=f"/module/production/{production_id}/tab/{tab_id}",
                  hx_target="#cama-tab-content",
                  hx_swap="innerHTML",
                  onclick="document.querySelectorAll('.cama-tab').forEach(t=>{t.style.background='#1e293b';t.style.color='#94a3b8'});this.style.background='#3b82f6';this.style.color='#fff';",
                  cls="cama-tab",
                  style=f"padding:8px 16px;border-radius:6px 6px 0 0;text-decoration:none;font-size:0.85rem;cursor:pointer;{active}")
            )
        return Div(*items, style="display:flex;gap:2px;border-bottom:2px solid #3b82f6;margin-bottom:1rem;flex-wrap:wrap;")

    # -------------------------------------------------------------------
    # Production Detail (CAMA-style tabbed page)
    # -------------------------------------------------------------------

    @rt("/module/production/{production_id}")
    def production_detail(production_id: str, session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                row = s.execute(text("""
                    SELECT production_id, title, project_type, genre, status, budget,
                           currency, producer, director, cast_summary, synopsis, territory
                    FROM ahcam.productions WHERE production_id = :pid
                """), {"pid": production_id}).fetchone()
        except Exception:
            row = None
        if not row:
            return Div("Production not found.", cls="module-error")

        budget = f"${row[5]:,.0f} {row[6]}" if row[5] else "\u2014"

        # Fetch stakeholders linked via junction table
        stakeholder_items = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                linked = s.execute(text("""
                    SELECT s.name, s.company, ps.role_in_production
                    FROM ahcam.production_stakeholders ps
                    JOIN ahcam.stakeholders s ON s.stakeholder_id = ps.stakeholder_id
                    WHERE ps.production_id = :pid
                    ORDER BY ps.role_in_production, s.name
                """), {"pid": production_id}).fetchall()
            for lk in linked:
                role_label = (lk[2] or "").replace("_", " ").title() or "Participant"
                company = f" ({lk[1]})" if lk[1] else ""
                stakeholder_items.append(
                    Div(
                        Span(role_label, cls="badge-blue", style="margin-right:6px;font-size:0.75rem;"),
                        Span(f"{lk[0]}{company}"),
                        style="margin-bottom:6px;",
                    )
                )
        except Exception:
            pass

        # --- Header ---
        header = Div(
            Div(
                Button("\u2190 Back",
                       hx_get="/module/productions",
                       hx_target="#center-content",
                       hx_swap="innerHTML",
                       cls="back-btn",
                       style="margin-right:1rem;"),
                H3(row[1], style="margin:0;"),
                Span(row[4].replace("_", " ").title(), cls=f"status-pill status-{row[4]}"),
                style="display:flex;align-items:center;gap:0.75rem;",
            ),
            style="margin-bottom:1rem;",
        )

        # --- Info section: two-column ---
        meta_left = Div(
            H4("Production Details", style="margin-top:0;margin-bottom:0.75rem;"),
            Div(Div("Type", cls="detail-label"), Div(row[2].replace("_", " ").title(), cls="detail-value"), cls="detail-item"),
            Div(Div("Genre", cls="detail-label"), Div(row[3] or "\u2014", cls="detail-value"), cls="detail-item"),
            Div(Div("Budget", cls="detail-label"), Div(budget, cls="detail-value"), cls="detail-item"),
            Div(Div("Director", cls="detail-label"), Div(row[8] or "\u2014", cls="detail-value"), cls="detail-item"),
            Div(Div("Producer", cls="detail-label"), Div(row[7] or "\u2014", cls="detail-value"), cls="detail-item"),
            Div(Div("Territory", cls="detail-label"), Div(row[11] or "\u2014", cls="detail-value"), cls="detail-item"),
            Div(Div("Synopsis", cls="detail-label"), Div(row[10] or "No synopsis provided.", cls="detail-value", style="white-space:pre-wrap;"), cls="detail-item"),
            style="flex:1;min-width:0;",
        )

        companies_content = stakeholder_items if stakeholder_items else [Div("No companies linked yet.", style="color:#64748b;font-size:0.9rem;")]
        meta_right = Div(
            H4("Companies Involved", style="margin-top:0;margin-bottom:0.75rem;"),
            *companies_content,
            style="flex:0 0 280px;background:#0f172a;border-radius:8px;padding:1rem;",
        )

        info_section = Div(
            meta_left,
            meta_right,
            style="display:flex;gap:1.5rem;margin-bottom:1.5rem;",
        )

        # --- Tabs + default content ---
        return Div(
            header,
            info_section,
            _tab_bar(production_id, "overview"),
            Div(id="cama-tab-content",
                hx_get=f"/module/production/{production_id}/tab/overview",
                hx_trigger="load",
                hx_swap="innerHTML"),
            cls="module-content",
        )

    # ===================================================================
    # TAB: Overview
    # ===================================================================

    @rt("/module/production/{production_id}/tab/overview")
    def tab_overview(production_id: str, session):
        total_in = total_out = balance = 0
        active_agreements = 0
        recent_txns = []
        waterfall_summary = []

        try:
            pool = get_pool()
            with pool.get_session() as s:
                # Aggregate inflows / outflows for this production's accounts
                agg = s.execute(text("""
                    SELECT COALESCE(SUM(t.amount) FILTER (WHERE t.transaction_type = 'inflow'), 0),
                           COALESCE(SUM(t.amount) FILTER (WHERE t.transaction_type = 'outflow'), 0)
                    FROM ahcam.transactions t
                    JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                    WHERE a.production_id = :pid
                """), {"pid": production_id}).fetchone()
                if agg:
                    total_in, total_out = float(agg[0]), float(agg[1])

                bal_row = s.execute(text("""
                    SELECT COALESCE(SUM(balance), 0) FROM ahcam.collection_accounts
                    WHERE production_id = :pid AND status = 'active'
                """), {"pid": production_id}).fetchone()
                if bal_row:
                    balance = float(bal_row[0])

                # Active waterfall rules as proxy for "agreements"
                cnt = s.execute(text("""
                    SELECT COUNT(*) FROM ahcam.waterfall_rules
                    WHERE production_id = :pid AND active = TRUE
                """), {"pid": production_id}).fetchone()
                if cnt:
                    active_agreements = cnt[0]

                # Recent transactions
                recent_txns = s.execute(text("""
                    SELECT t.transaction_type, t.amount, t.description, t.status,
                           t.created_at, a.account_name
                    FROM ahcam.transactions t
                    JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                    WHERE a.production_id = :pid
                    ORDER BY t.created_at DESC LIMIT 10
                """), {"pid": production_id}).fetchall()

                # Waterfall summary
                waterfall_summary = s.execute(text("""
                    SELECT r.priority, COALESCE(s.name, r.recipient_label, 'Rule #' || r.priority),
                           r.rule_type, r.percentage, r.cap
                    FROM ahcam.waterfall_rules r
                    LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = r.recipient_stakeholder_id
                    WHERE r.production_id = :pid AND r.active = TRUE
                    ORDER BY r.priority LIMIT 10
                """), {"pid": production_id}).fetchall()
        except Exception:
            pass

        # Stat cards
        stats = Div(
            Div(Div(f"${total_in:,.2f}", cls="stat-value positive"), Div("Total Inflows", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${total_out:,.2f}", cls="stat-value negative"), Div("Total Outflows", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${balance:,.2f}", cls="stat-value"), Div("Balance", cls="stat-label"), cls="stat-card"),
            Div(Div(str(active_agreements), cls="stat-value"), Div("Active Agreements", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        # Recent transactions table
        txn_rows = []
        for t in recent_txns:
            color = "positive" if t[0] == "inflow" else "negative" if t[0] == "outflow" else ""
            txn_rows.append(Tr(
                Td(t[5] or "\u2014"), Td(t[0].title()),
                Td(f"${t[1]:,.2f}", cls=color), Td(t[2] or "\u2014"),
                Td(t[3].title() if t[3] else "\u2014"),
                Td(str(t[4])[:16] if t[4] else "\u2014"),
            ))
        txn_table = Div(
            H4("Recent Transactions"),
            Table(
                Thead(Tr(Th("Account"), Th("Type"), Th("Amount"), Th("Description"), Th("Status"), Th("Date"))),
                Tbody(*txn_rows) if txn_rows else Tbody(Tr(Td("No transactions yet.", colspan="6"))),
                cls="module-table",
            ),
            style="margin-bottom:1.5rem;",
        )

        # Waterfall summary
        wf_rows = []
        for w in waterfall_summary:
            pct = f"{w[3]}%" if w[3] else "\u2014"
            cap = f"${w[4]:,.0f}" if w[4] else "\u2014"
            wf_rows.append(Tr(Td(str(w[0])), Td(w[1]), Td(w[2].title()), Td(pct), Td(cap)))
        wf_table = Div(
            H4("Waterfall Summary"),
            Table(
                Thead(Tr(Th("Priority"), Th("Recipient"), Th("Type"), Th("%"), Th("Cap"))),
                Tbody(*wf_rows) if wf_rows else Tbody(Tr(Td("No waterfall rules defined.", colspan="5"))),
                cls="module-table",
            ),
        )

        return Div(stats, txn_table, wf_table)

    # ===================================================================
    # TAB: CGR (Collection Gross Receipts by Territory)
    # ===================================================================

    @rt("/module/production/{production_id}/tab/cgr")
    def tab_cgr(production_id: str, session):
        rows = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT t.territory,
                           COALESCE(src.name, 'Unknown') AS distributor,
                           SUM(t.amount) AS gross_receipts
                    FROM ahcam.transactions t
                    JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                    LEFT JOIN ahcam.stakeholders src ON src.stakeholder_id = t.source_stakeholder_id
                    WHERE a.production_id = :pid
                      AND t.transaction_type = 'inflow'
                      AND t.territory IS NOT NULL
                    GROUP BY t.territory, src.name
                    ORDER BY t.territory, gross_receipts DESC
                """), {"pid": production_id}).fetchall()
        except Exception:
            pass

        if not rows:
            return Div(
                H4("Collection Gross Receipts by Territory"),
                Div("No territory-level receipts recorded yet.", cls="empty-state"),
            )

        trs = []
        for r in rows:
            gross = float(r[2])
            wht = gross * 0.05
            net = gross - wht
            trs.append(Tr(
                Td(r[0]), Td(r[1]),
                Td(f"${gross:,.2f}"), Td(f"${wht:,.2f}"), Td(f"${net:,.2f}"),
            ))

        return Div(
            H4("Collection Gross Receipts by Territory"),
            Table(
                Thead(Tr(Th("Territory"), Th("Distributor"), Th("Gross Receipts"), Th("WHT (5%)"), Th("Net Receipts"))),
                Tbody(*trs),
                cls="module-table",
            ),
        )

    # ===================================================================
    # TAB: Receipts (all inflows)
    # ===================================================================

    @rt("/module/production/{production_id}/tab/receipts")
    def tab_receipts(production_id: str, session):
        rows = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT t.created_at, t.territory,
                           COALESCE(src.name, 'Unknown') AS distributor,
                           t.amount, t.reference, t.status
                    FROM ahcam.transactions t
                    JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                    LEFT JOIN ahcam.stakeholders src ON src.stakeholder_id = t.source_stakeholder_id
                    WHERE a.production_id = :pid
                      AND t.transaction_type = 'inflow'
                    ORDER BY t.created_at DESC
                """), {"pid": production_id}).fetchall()
        except Exception:
            pass

        if not rows:
            return Div(
                H4("Receipts"),
                Div("No inflow transactions recorded yet.", cls="empty-state"),
            )

        trs = []
        for r in rows:
            trs.append(Tr(
                Td(str(r[0])[:10] if r[0] else "\u2014"),
                Td(r[1] or "\u2014"),
                Td(r[2]),
                Td(f"${float(r[3]):,.2f}"),
                Td(r[4] or "\u2014"),
                Td(r[5].title() if r[5] else "\u2014"),
            ))

        return Div(
            H4("Receipts"),
            Table(
                Thead(Tr(Th("Date"), Th("Territory"), Th("Distributor"), Th("Amount"), Th("Reference"), Th("Status"))),
                Tbody(*trs),
                cls="module-table",
            ),
        )

    # ===================================================================
    # TAB: Outstanding
    # ===================================================================

    @rt("/module/production/{production_id}/tab/outstanding")
    def tab_outstanding(production_id: str, session):
        rows = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                # Try recoupment_positions first
                rows = s.execute(text("""
                    SELECT COALESCE(s.name, 'Unknown') AS stakeholder,
                           rp.total_owed, rp.total_received, rp.outstanding
                    FROM ahcam.recoupment_positions rp
                    LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = rp.stakeholder_id
                    WHERE rp.production_id = :pid
                    ORDER BY rp.outstanding DESC
                """), {"pid": production_id}).fetchall()
        except Exception:
            pass

        # If no recoupment positions, attempt to derive from waterfall rules
        if not rows:
            try:
                pool = get_pool()
                with pool.get_session() as s:
                    rules = s.execute(text("""
                        SELECT COALESCE(s.name, r.recipient_label, 'Rule #' || r.priority) AS stakeholder,
                               r.percentage, r.cap,
                               COALESCE(
                                   (SELECT SUM(d.amount) FROM ahcam.disbursements d
                                    WHERE d.production_id = :pid AND d.waterfall_rule_id = r.rule_id
                                      AND d.status = 'completed'), 0
                               ) AS received
                        FROM ahcam.waterfall_rules r
                        LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = r.recipient_stakeholder_id
                        WHERE r.production_id = :pid AND r.active = TRUE
                        ORDER BY r.priority
                    """), {"pid": production_id}).fetchall()
                derived = []
                for ru in rules:
                    owed = float(ru[2]) if ru[2] else 0  # use cap as total owed estimate
                    received = float(ru[3])
                    outstanding = max(owed - received, 0)
                    derived.append((ru[0], owed, received, outstanding))
                rows = derived
            except Exception:
                pass

        if not rows:
            return Div(
                H4("Outstanding Positions"),
                Div("No outstanding position data available.", cls="empty-state"),
            )

        trs = []
        for r in rows:
            owed = float(r[1]) if r[1] else 0
            received = float(r[2]) if r[2] else 0
            outstanding = float(r[3]) if r[3] else 0
            trs.append(Tr(
                Td(r[0]),
                Td(f"${owed:,.2f}"),
                Td(f"${received:,.2f}"),
                Td(f"${outstanding:,.2f}", style="font-weight:600;" if outstanding > 0 else ""),
            ))

        return Div(
            H4("Outstanding Positions"),
            Table(
                Thead(Tr(Th("Stakeholder"), Th("Total Owed"), Th("Received"), Th("Outstanding"))),
                Tbody(*trs),
                cls="module-table",
            ),
        )

    # ===================================================================
    # TAB: DAs (Distribution Agreements)
    # ===================================================================

    @rt("/module/production/{production_id}/tab/das")
    def tab_das(production_id: str, session):
        rows = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT da.territory, COALESCE(s.name, 'Unknown') AS distributor,
                           da.signature_date, da.term_years, da.start_date, da.expiry_date,
                           da.mg_amount, da.mg_paid, da.financial_status
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = da.distributor_stakeholder_id
                    WHERE da.production_id = :pid
                    ORDER BY da.territory
                """), {"pid": production_id}).fetchall()
        except Exception:
            rows = []

        if not rows:
            return Div(
                H4("Distribution Agreements"),
                Div("No distribution agreements recorded yet.", cls="empty-state"),
            )

        trs = []
        for r in rows:
            mg_amount = float(r[6]) if r[6] else 0
            mg_paid = float(r[7]) if r[7] else 0
            pct = (mg_paid / mg_amount * 100) if mg_amount > 0 else 0
            bar_color = "#22c55e" if pct >= 100 else "#f59e0b" if pct >= 50 else "#ef4444"
            progress = Div(
                Div(style=f"width:{min(pct, 100):.0f}%;height:100%;background:{bar_color};border-radius:4px;"),
                style="width:80px;height:8px;background:#1e293b;border-radius:4px;display:inline-block;vertical-align:middle;margin-right:6px;",
            )
            status_cls = "badge-green" if r[8] == "active" else "badge-amber" if r[8] == "pending" else "badge-blue"
            trs.append(Tr(
                Td(r[0] or "\u2014"),
                Td(r[1]),
                Td(str(r[2])[:10] if r[2] else "\u2014"),
                Td(r[3] or "\u2014"),
                Td(str(r[4])[:10] if r[4] else "\u2014"),
                Td(str(r[5])[:10] if r[5] else "\u2014"),
                Td(f"${mg_amount:,.2f}"),
                Td(Span(progress, f"${mg_paid:,.2f}")),
                Td(Span(r[8].title() if r[8] else "\u2014", cls=status_cls)),
            ))

        return Div(
            H4("Distribution Agreements"),
            Table(
                Thead(Tr(Th("Territory"), Th("Distributor"), Th("Signed"), Th("Term"),
                         Th("Start"), Th("Expiry"), Th("MG Amount"), Th("MG Paid"), Th("Status"))),
                Tbody(*trs),
                cls="module-table",
            ),
        )

    # ===================================================================
    # TAB: Waterfall
    # ===================================================================

    @rt("/module/production/{production_id}/tab/waterfall")
    def tab_waterfall(production_id: str, session):
        rules = []
        balance = 0
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rules = s.execute(text("""
                    SELECT r.rule_id, r.priority, r.recipient_label, r.rule_type,
                           r.percentage, r.cap, r.description, s.name
                    FROM ahcam.waterfall_rules r
                    LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = r.recipient_stakeholder_id
                    WHERE r.production_id = :pid AND r.active = TRUE
                    ORDER BY r.priority
                """), {"pid": production_id}).fetchall()
                bal_row = s.execute(text("""
                    SELECT COALESCE(SUM(balance), 0) FROM ahcam.collection_accounts
                    WHERE production_id = :pid AND status = 'active'
                """), {"pid": production_id}).fetchone()
                if bal_row:
                    balance = float(bal_row[0])
        except Exception:
            pass

        rule_rows = []
        for r in rules:
            name = r[7] or r[2] or "\u2014"
            cap = f"${r[5]:,.0f}" if r[5] else "\u2014"
            pct = f"{r[4]}%" if r[4] else "\u2014"
            rule_rows.append(Tr(Td(str(r[1])), Td(name), Td(r[3].title()), Td(pct), Td(cap), Td(r[6] or "\u2014")))

        return Div(
            H4("Waterfall Rules"),
            Div(f"Account Balance: ${balance:,.2f}", cls="stat-highlight", style="margin-bottom:1rem;"),
            Table(
                Thead(Tr(Th("Priority"), Th("Recipient"), Th("Type"), Th("%"), Th("Cap"), Th("Description"))),
                Tbody(*rule_rows) if rule_rows else Tbody(Tr(Td("No waterfall rules defined.", colspan="6"))),
                cls="module-table",
            ),
            Div(
                Button("Run Waterfall",
                       hx_post=f"/module/waterfall/run/{production_id}",
                       hx_target="#tab-waterfall-result",
                       hx_swap="innerHTML",
                       cls="module-action-btn"),
                style="margin-top:1rem;",
            ),
            Div(id="tab-waterfall-result"),
        )

    # ===================================================================
    # TAB: Disbursements
    # ===================================================================

    @rt("/module/production/{production_id}/tab/disbursements")
    def tab_disbursements(production_id: str, session):
        rows = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT COALESCE(s.name, 'Unknown') AS stakeholder,
                           d.amount, r.recipient_label, d.status, d.created_at
                    FROM ahcam.disbursements d
                    LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = d.stakeholder_id
                    LEFT JOIN ahcam.waterfall_rules r ON r.rule_id = d.waterfall_rule_id
                    WHERE d.production_id = :pid
                    ORDER BY d.created_at DESC
                """), {"pid": production_id}).fetchall()
        except Exception:
            pass

        if not rows:
            return Div(
                H4("Disbursements"),
                Div("No disbursements processed yet.", cls="empty-state"),
            )

        trs = []
        for r in rows:
            status_cls = "badge-green" if r[3] == "completed" else "badge-amber" if r[3] == "approved" else "badge-blue"
            trs.append(Tr(
                Td(r[0]),
                Td(f"${float(r[1]):,.2f}"),
                Td(r[2] or "\u2014"),
                Td(Span(r[3].title() if r[3] else "\u2014", cls=status_cls)),
                Td(str(r[4])[:10] if r[4] else "\u2014"),
            ))

        return Div(
            H4("Disbursements"),
            Table(
                Thead(Tr(Th("Stakeholder"), Th("Amount"), Th("Rule"), Th("Status"), Th("Date"))),
                Tbody(*trs),
                cls="module-table",
            ),
        )

    # ===================================================================
    # TAB: Statements
    # ===================================================================

    @rt("/module/production/{production_id}/tab/statements")
    def tab_statements(production_id: str, session):
        rows = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT statement_name, period, issued_date, payment_date, status
                    FROM ahcam.collection_statements
                    WHERE production_id = :pid
                    ORDER BY issued_date DESC
                """), {"pid": production_id}).fetchall()
        except Exception:
            rows = []

        if not rows:
            return Div(
                H4("Collection Statements"),
                Div("No statements generated yet.", cls="empty-state"),
            )

        trs = []
        for r in rows:
            status_cls = "badge-green" if r[4] == "issued" else "badge-amber" if r[4] == "draft" else "badge-blue"
            trs.append(Tr(
                Td(r[0] or "\u2014"),
                Td(r[1] or "\u2014"),
                Td(str(r[2])[:10] if r[2] else "\u2014"),
                Td(str(r[3])[:10] if r[3] else "\u2014"),
                Td(Span(r[4].title() if r[4] else "\u2014", cls=status_cls)),
            ))

        return Div(
            H4("Collection Statements"),
            Table(
                Thead(Tr(Th("Statement Name"), Th("Period"), Th("Issued Date"), Th("Payment Date"), Th("Status"))),
                Tbody(*trs),
                cls="module-table",
            ),
        )

    # ===================================================================
    # TAB: Bank Details
    # ===================================================================

    @rt("/module/production/{production_id}/tab/bank-details")
    def tab_bank_details(production_id: str, session):
        rows = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT ba.beneficiary_name, ba.bank_name, ba.currency,
                           ba.account_number, ba.status
                    FROM ahcam.beneficiary_bank_accounts ba
                    WHERE ba.production_id = :pid
                    ORDER BY ba.beneficiary_name
                """), {"pid": production_id}).fetchall()
        except Exception:
            rows = []

        if not rows:
            return Div(
                H4("Beneficiary Bank Details"),
                Div("No bank account details recorded yet.", cls="empty-state"),
            )

        trs = []
        for r in rows:
            # Mask account number: show only last 4 digits
            acct = r[3] or ""
            masked = "****" + acct[-4:] if len(acct) >= 4 else "****"
            status_cls = "badge-green" if r[4] == "verified" else "badge-amber" if r[4] == "pending" else "badge-blue"
            trs.append(Tr(
                Td(r[0] or "\u2014"),
                Td(r[1] or "\u2014"),
                Td(r[2] or "\u2014"),
                Td(masked),
                Td(Span(r[4].title() if r[4] else "\u2014", cls=status_cls)),
            ))

        return Div(
            H4("Beneficiary Bank Details"),
            Table(
                Thead(Tr(Th("Beneficiary"), Th("Bank"), Th("Currency"), Th("Account"), Th("Status"))),
                Tbody(*trs),
                cls="module-table",
            ),
        )

    # ===================================================================
    # TAB: Comments
    # ===================================================================

    @rt("/module/production/{production_id}/tab/comments")
    def tab_comments(production_id: str, session):
        comments = []
        try:
            pool = get_pool()
            with pool.get_session() as s:
                comments = s.execute(text("""
                    SELECT c.comment_id, c.content, c.created_at,
                           COALESCE(u.display_name, u.email, 'Unknown') AS author,
                           c.parent_comment_id
                    FROM ahcam.production_comments c
                    LEFT JOIN ahcam.users u ON u.user_id = c.user_id
                    WHERE c.production_id = :pid
                    ORDER BY c.created_at ASC
                """), {"pid": production_id}).fetchall()
        except Exception:
            comments = []

        comment_items = []
        for c in comments:
            indent = "margin-left:1.5rem;" if c[4] else ""
            comment_items.append(
                Div(
                    Div(
                        Span(c[3], style="font-weight:600;color:#e2e8f0;"),
                        Span(f" \u00b7 {str(c[2])[:16]}" if c[2] else "", style="color:#64748b;font-size:0.8rem;"),
                        style="margin-bottom:4px;",
                    ),
                    Div(c[1] or "", style="color:#cbd5e1;white-space:pre-wrap;"),
                    style=f"background:#0f172a;border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.5rem;{indent}",
                )
            )

        if not comment_items:
            comment_items = [Div("No comments yet.", style="color:#64748b;margin-bottom:1rem;")]

        # Comment form
        form = Form(
            Textarea(name="content", placeholder="Add a comment...", rows="3",
                     style="width:100%;background:#0f172a;border:1px solid #334155;border-radius:6px;color:#e2e8f0;padding:0.5rem;resize:vertical;"),
            Button("Post Comment", type="submit", cls="module-action-btn", style="margin-top:0.5rem;"),
            hx_post=f"/module/production/{production_id}/tab/comments/add",
            hx_target="#cama-tab-content",
            hx_swap="innerHTML",
        )

        return Div(
            H4("Comments"),
            *comment_items,
            Hr(style="border-color:#1e293b;margin:1rem 0;"),
            form,
        )

    @rt("/module/production/{production_id}/tab/comments/add", methods=["POST"])
    def tab_comments_add(production_id: str, session, content: str = ""):
        if content.strip():
            try:
                pool = get_pool()
                with pool.get_session() as s:
                    s.execute(text("""
                        INSERT INTO ahcam.production_comments (production_id, user_id, content)
                        VALUES (:pid, :uid, :content)
                    """), {
                        "pid": production_id,
                        "uid": session.get("user_id"),
                        "content": content.strip(),
                    })
            except Exception:
                pass
        return tab_comments(production_id, session)
