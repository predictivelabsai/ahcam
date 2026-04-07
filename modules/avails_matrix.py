"""
Avails Matrix module — Territory availability tracking with mosaic and list views.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from config.settings import TERRITORIES


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def get_avails(query: str = "") -> str:
    """Get territory availability for productions. Returns markdown."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            rows = session.execute(text("""
                SELECT p.title, da.territory
                FROM ahcam.productions p
                LEFT JOIN ahcam.distribution_agreements da ON da.production_id = p.production_id
                ORDER BY p.title, da.territory
            """)).fetchall()
        if not rows:
            return "No productions found."
        # Build per-title sold territories
        title_sold = {}
        for r in rows:
            title_sold.setdefault(r[0], set())
            if r[1]:
                title_sold[r[0]].add(r[1])
        lines = ["## Avails Matrix\n"]
        for title, sold in title_sold.items():
            avail = [t for t in TERRITORIES if t not in sold]
            lines.append(f"**{title}** — {len(avail)} available, {len(sold)} sold")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/avails")
    def module_avails(session, view: str = "mosaic"):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                productions = s.execute(text("""
                    SELECT p.production_id, p.title, p.genre, p.director, p.budget
                    FROM ahcam.productions p
                    ORDER BY p.title
                """)).fetchall()

                agreements = s.execute(text("""
                    SELECT production_id, territory
                    FROM ahcam.distribution_agreements
                """)).fetchall()
        except Exception:
            productions, agreements = [], []

        # Build sold territory map: production_id -> set of territories
        sold_map = {}
        for a in agreements:
            sold_map.setdefault(str(a[0]), set()).add(a[1])

        # Use a subset of key territories for display
        display_territories = TERRITORIES

        # View toggle
        view_toggle = Div(
            Button("Mosaic",
                   hx_get="/module/avails?view=mosaic",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="module-action-btn" if view != "mosaic" else "module-action-btn",
                   style=f"font-size:0.8rem;padding:4px 12px;{'background:#3b82f6;' if view == 'mosaic' else 'background:#374151;'}"),
            Button("List",
                   hx_get="/module/avails?view=list",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="module-action-btn",
                   style=f"font-size:0.8rem;padding:4px 12px;{'background:#3b82f6;' if view == 'list' else 'background:#374151;'}"),
            style="display:flex;gap:4px;margin-bottom:1rem;",
        )

        if not productions:
            return Div(
                H3("Avails Matrix"),
                view_toggle,
                Div("No productions found.", cls="empty-state"),
                cls="module-content",
            )

        if view == "mosaic":
            content = _build_mosaic_view(productions, sold_map, display_territories)
        else:
            content = _build_list_view(productions, sold_map, display_territories)

        # Stats
        total_prods = len(productions)
        total_sold = sum(len(s) for s in sold_map.values())
        total_possible = total_prods * len(display_territories)
        total_avail = total_possible - total_sold

        stat_grid = Div(
            Div(Div(str(total_prods), cls="stat-value"), Div("Productions", cls="stat-label"), cls="stat-card"),
            Div(Div(str(total_avail), cls="stat-value positive"), Div("Available Slots", cls="stat-label"), cls="stat-card"),
            Div(Div(str(total_sold), cls="stat-value"), Div("Sold Slots", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        return Div(
            stat_grid,
            Div(
                Div(
                    H3("Avails Matrix"),
                    view_toggle,
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;",
                ),
                content,
                cls="module-list",
            ),
            cls="module-content",
        )


def _build_mosaic_view(productions, sold_map, territories):
    """Card grid: one card per production with territory badges."""
    cards = []
    for p in productions:
        prod_id = str(p[0])
        title = p[1]
        genre = p[2] or "\u2014"
        director = p[3] or "\u2014"
        budget = f"${p[4]:,.0f}" if p[4] else "\u2014"
        sold = sold_map.get(prod_id, set())

        territory_badges = []
        for t in territories:
            if t in sold:
                territory_badges.append(Span(
                    t, cls="badge-red",
                    style="font-size:0.65rem;padding:1px 6px;margin:1px;display:inline-block;background:#ef4444;color:#fff;border-radius:3px;",
                    title=f"{t}: Sold",
                ))
            else:
                territory_badges.append(Span(
                    t, cls="badge-green",
                    style="font-size:0.65rem;padding:1px 6px;margin:1px;display:inline-block;background:#22c55e;color:#fff;border-radius:3px;",
                    title=f"{t}: Available",
                ))

        cards.append(Div(
            Div(
                Span(title, cls="deal-card-title"),
                style="margin-bottom:4px;",
            ),
            Div(f"{genre} | {director} | {budget}", cls="deal-card-meta",
                style="margin-bottom:6px;"),
            Div(
                *territory_badges,
                style="display:flex;flex-wrap:wrap;gap:2px;",
            ),
            cls="deal-card",
            style="padding:12px;",
            hx_get=f"/module/production/{prod_id}",
            hx_target="#center-content",
            hx_swap="innerHTML",
        ))

    return Div(*cards, style="display:flex;flex-direction:column;gap:8px;")


def _build_list_view(productions, sold_map, territories):
    """Table view: Title, Genre, Budget, then territory columns."""
    header_cells = [Th("Title"), Th("Genre"), Th("Budget")]
    for t in territories:
        header_cells.append(Th(
            t,
            style="font-size:0.7rem;writing-mode:vertical-rl;text-orientation:mixed;min-width:30px;max-width:35px;white-space:nowrap;",
            title=t,
        ))

    table_rows = []
    for p in productions:
        prod_id = str(p[0])
        title = p[1]
        genre = p[2] or "\u2014"
        budget = f"${p[4]:,.0f}" if p[4] else "\u2014"
        sold = sold_map.get(prod_id, set())

        cells = [
            Td(A(title, href="#",
                 onclick=f"loadModule(this,'/module/production/{prod_id}', '{title}'); return false;",
                 style="color:#60a5fa;text-decoration:none;font-weight:500;")),
            Td(genre),
            Td(budget, style="text-align:right;"),
        ]
        for t in territories:
            if t in sold:
                cells.append(Td(
                    "\u2716",
                    style="text-align:center;background:rgba(239,68,68,0.15);color:#ef4444;font-size:0.8rem;",
                    title=f"{t}: Sold",
                ))
            else:
                cells.append(Td(
                    "\u2714",
                    style="text-align:center;background:rgba(34,197,94,0.1);color:#22c55e;font-size:0.8rem;",
                    title=f"{t}: Available",
                ))
        table_rows.append(Tr(*cells))

    return Div(
        Table(
            Thead(Tr(*header_cells)),
            Tbody(*table_rows),
            cls="module-table",
            style="min-width:100%;",
        ),
        style="overflow-x:auto;max-height:70vh;overflow-y:auto;",
    )
