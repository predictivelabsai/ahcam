"""
Sales Matrix module — Territory x Title grid showing distributor deals and MG amounts.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def get_sales_matrix(query: str = "") -> str:
    """Get sales matrix: territories vs productions with distributor/MG info. Returns markdown."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            rows = session.execute(text("""
                SELECT p.title, da.territory, da.distributor_name, da.mg_amount
                FROM ahcam.distribution_agreements da
                JOIN ahcam.productions p ON p.production_id = da.production_id
                ORDER BY da.territory, p.title
            """)).fetchall()
        if not rows:
            return "No sales data found."
        lines = ["## Sales Matrix\n"]
        for r in rows:
            mg = f"${r[3]:,.0f}" if r[3] else "\u2014"
            lines.append(f"- **{r[0]}** | {r[1]} | {r[2]} | MG: {mg}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/sales-matrix")
    def module_sales_matrix(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                # Get all productions that have at least one agreement
                productions = s.execute(text("""
                    SELECT DISTINCT p.production_id, p.title
                    FROM ahcam.productions p
                    JOIN ahcam.distribution_agreements da ON da.production_id = p.production_id
                    ORDER BY p.title
                """)).fetchall()

                # Get territories that have agreements
                territories = s.execute(text("""
                    SELECT DISTINCT territory
                    FROM ahcam.distribution_agreements
                    ORDER BY territory
                """)).fetchall()

                # Get all agreements
                agreements = s.execute(text("""
                    SELECT da.production_id, da.territory, da.distributor_name, da.mg_amount
                    FROM ahcam.distribution_agreements da
                """)).fetchall()
        except Exception:
            productions, territories, agreements = [], [], []

        if not productions or not territories:
            return Div(
                H3("Sales Matrix"),
                Div("No distribution agreements found. Create agreements to populate the sales matrix.", cls="empty-state"),
                cls="module-content",
            )

        # Build lookup: (production_id, territory) -> (distributor, mg)
        agreement_map = {}
        for a in agreements:
            key = (str(a[0]), a[1])
            agreement_map[key] = (a[2], a[3])

        territory_list = [t[0] for t in territories]
        prod_list = [(str(p[0]), p[1]) for p in productions]

        # Build header row
        header_cells = [Th("Territory", style="position:sticky;left:0;z-index:2;background:#1e293b;min-width:180px;")]
        for _, title in prod_list:
            header_cells.append(Th(
                title,
                style="min-width:160px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;",
                title=title,
            ))

        # Build data rows
        table_rows = []
        for terr in territory_list:
            cells = [Td(
                terr,
                style="position:sticky;left:0;z-index:1;background:#1e293b;font-weight:500;white-space:nowrap;",
            )]
            for prod_id, _ in prod_list:
                info = agreement_map.get((prod_id, terr))
                if info:
                    dist_name, mg = info
                    mg_str = f"${mg:,.0f}" if mg else "\u2014"
                    cells.append(Td(
                        Div(
                            Div(dist_name, style="font-size:0.8rem;font-weight:500;"),
                            Div(mg_str, style="font-size:0.75rem;color:#94a3b8;"),
                        ),
                        style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);",
                    ))
                else:
                    cells.append(Td(
                        "\u2014",
                        style="background:rgba(107,114,128,0.1);color:#6b7280;text-align:center;",
                    ))
            table_rows.append(Tr(*cells))

        content_table = Div(
            Table(
                Thead(Tr(*header_cells)),
                Tbody(*table_rows),
                cls="module-table",
                style="min-width:100%;",
            ),
            style="overflow-x:auto;max-height:70vh;overflow-y:auto;",
        )

        # Stats
        total_deals = len(agreements)
        total_territories = len(territory_list)
        total_titles = len(prod_list)
        coverage = (total_deals / (total_territories * total_titles) * 100) if (total_territories * total_titles) > 0 else 0

        stat_grid = Div(
            Div(Div(str(total_titles), cls="stat-value"), Div("Titles", cls="stat-label"), cls="stat-card"),
            Div(Div(str(total_territories), cls="stat-value"), Div("Territories", cls="stat-label"), cls="stat-card"),
            Div(Div(str(total_deals), cls="stat-value"), Div("Deals", cls="stat-label"), cls="stat-card"),
            Div(Div(f"{coverage:.0f}%", cls="stat-value"), Div("Coverage", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        return Div(
            stat_grid,
            Div(
                H3("Sales Matrix"),
                content_table,
                cls="module-list",
            ),
            cls="module-content",
        )
