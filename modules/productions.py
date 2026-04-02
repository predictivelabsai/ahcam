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
        return Div(
            Div(
                H3(row[1]),
                Span(row[4].replace("_", " ").title(), cls=f"status-pill status-{row[4]}"),
                style="display:flex;gap:1rem;align-items:center;margin-bottom:1rem;",
            ),
            Div(
                Div(Div("Type", cls="detail-label"), Div(row[2].replace("_", " ").title(), cls="detail-value"), cls="detail-item"),
                Div(Div("Genre", cls="detail-label"), Div(row[3] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Budget", cls="detail-label"), Div(budget, cls="detail-value"), cls="detail-item"),
                Div(Div("Producer", cls="detail-label"), Div(row[7] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Director", cls="detail-label"), Div(row[8] or "\u2014", cls="detail-value"), cls="detail-item"),
                Div(Div("Territory", cls="detail-label"), Div(row[11] or "\u2014", cls="detail-value"), cls="detail-item"),
                cls="detail-grid",
            ),
            Div(
                H4("Synopsis"),
                P(row[10] or "No synopsis provided."),
                cls="detail-section",
            ),
            Button("\u2190 Back to Productions",
                   hx_get="/module/productions",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="back-btn"),
            cls="module-content",
        )
