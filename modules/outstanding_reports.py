"""
Outstanding Reports module — Cross-production outstanding amounts per stakeholder.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def get_outstanding_report(query: str = "") -> str:
    """Get outstanding amounts across productions and stakeholders. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            rows = session.execute(text("""
                SELECT p.title, s.name, rp.total_owed, rp.total_received,
                       rp.outstanding, rp.last_calculated
                FROM ahcam.recoupment_positions rp
                JOIN ahcam.productions p ON p.production_id = rp.production_id
                JOIN ahcam.stakeholders s ON s.stakeholder_id = rp.stakeholder_id
                ORDER BY rp.outstanding DESC NULLS LAST
                LIMIT 50
            """)).fetchall()
        if not rows:
            return "No outstanding positions found."
        header = "| Production | Stakeholder | Total Owed | Total Received | Outstanding |\n|------------|-------------|------------|----------------|-------------|\n"
        lines = []
        for r in rows:
            owed = f"${r[2]:,.2f}" if r[2] else "$0.00"
            received = f"${r[3]:,.2f}" if r[3] else "$0.00"
            outstanding = f"${r[4]:,.2f}" if r[4] else "$0.00"
            lines.append(f"| {r[0]} | {r[1]} | {owed} | {received} | {outstanding} |")
        return f"## Outstanding Report\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/outstanding-reports")
    def module_outstanding_reports(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT p.title, p.production_id, s.name, s.stakeholder_id,
                           rp.total_owed, rp.total_received, rp.outstanding,
                           rp.last_calculated
                    FROM ahcam.recoupment_positions rp
                    JOIN ahcam.productions p ON p.production_id = rp.production_id
                    JOIN ahcam.stakeholders s ON s.stakeholder_id = rp.stakeholder_id
                    ORDER BY rp.outstanding DESC NULLS LAST
                    LIMIT 100
                """)).fetchall()

                totals = s.execute(text("""
                    SELECT COALESCE(SUM(total_owed), 0),
                           COALESCE(SUM(total_received), 0),
                           COALESCE(SUM(outstanding), 0),
                           COUNT(*)
                    FROM ahcam.recoupment_positions
                """)).fetchone()
        except Exception:
            rows = []
            totals = (0, 0, 0, 0)

        total_owed = float(totals[0])
        total_received = float(totals[1])
        total_outstanding = float(totals[2])
        total_positions = int(totals[3])

        # Stat cards
        stat_grid = Div(
            Div(Div(str(total_positions), cls="stat-value"), Div("Positions", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${total_owed:,.2f}", cls="stat-value"), Div("Total Owed", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${total_received:,.2f}", cls="stat-value positive"), Div("Total Received", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${total_outstanding:,.2f}", cls="stat-value negative"), Div("Total Outstanding", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        # Table rows
        table_rows = []
        for r in rows:
            title = r[0]
            prod_id = r[1]
            stakeholder = r[2]
            owed = float(r[4]) if r[4] else 0
            received = float(r[5]) if r[5] else 0
            outstanding = float(r[6]) if r[6] else 0
            last_calc = str(r[7])[:10] if r[7] else "\u2014"

            # Color code outstanding
            if outstanding > 0:
                out_style = "color:#ef4444;font-weight:500;"
            elif outstanding == 0 and owed > 0:
                out_style = "color:#22c55e;font-weight:500;"
            else:
                out_style = ""

            table_rows.append(Tr(
                Td(A(title, href="#",
                     onclick=f"loadModule(this,'/module/production/{prod_id}', '{title}'); return false;",
                     style="color:#60a5fa;text-decoration:none;font-weight:500;")),
                Td(stakeholder),
                Td(f"${owed:,.2f}", style="text-align:right;"),
                Td(f"${received:,.2f}", style="text-align:right;"),
                Td(f"${outstanding:,.2f}", style=f"text-align:right;{out_style}"),
                Td(last_calc),
            ))

        content_table = Table(
            Thead(Tr(
                Th("Production"), Th("Stakeholder"), Th("Total Owed"),
                Th("Total Received"), Th("Outstanding"), Th("Last Calculated"),
            )),
            Tbody(*table_rows) if table_rows else Tbody(Tr(Td("No outstanding positions found.", colspan="6", style="text-align:center;"))),
            cls="module-table",
        )

        # Export buttons
        export_bar = Div(
            Button("Export Excel",
                   hx_get="/export/outstanding-report?fmt=excel",
                   hx_swap="none",
                   cls="module-action-btn",
                   style="font-size:0.8rem;padding:4px 12px;margin-right:8px;"),
            Button("Export PDF",
                   hx_get="/export/outstanding-report?fmt=pdf",
                   hx_swap="none",
                   cls="module-action-btn",
                   style="font-size:0.8rem;padding:4px 12px;background:#6b7280;"),
            style="display:flex;gap:8px;",
        )

        return Div(
            stat_grid,
            Div(
                Div(
                    H3("Outstanding Report"),
                    export_bar,
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                content_table,
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/export/outstanding-report")
    def export_outstanding_report(session, fmt: str = "excel"):
        """Export outstanding report data."""
        from starlette.responses import Response
        try:
            from utils.export import export_table_to_excel, export_html_to_pdf
        except ImportError:
            return Response("Export not available", status_code=500)

        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT p.title, s.name, rp.total_owed, rp.total_received,
                           rp.outstanding, rp.last_calculated
                    FROM ahcam.recoupment_positions rp
                    JOIN ahcam.productions p ON p.production_id = rp.production_id
                    JOIN ahcam.stakeholders s ON s.stakeholder_id = rp.stakeholder_id
                    ORDER BY rp.outstanding DESC NULLS LAST
                """)).fetchall()
        except Exception:
            rows = []

        headers = ["Production", "Stakeholder", "Total Owed", "Total Received", "Outstanding", "Last Calculated"]
        data = []
        for r in rows:
            data.append([
                r[0], r[1],
                float(r[2]) if r[2] else 0,
                float(r[3]) if r[3] else 0,
                float(r[4]) if r[4] else 0,
                str(r[5])[:10] if r[5] else "",
            ])

        if fmt == "pdf":
            html = "<html><head><style>body{font-family:Arial;font-size:12px;}table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ccc;padding:6px 8px;text-align:left;}th{background:#2C3E50;color:#fff;}</style></head><body>"
            html += "<h2>Outstanding Report \u2014 Ashland Hill CAM</h2><table><tr>"
            for h in headers:
                html += f"<th>{h}</th>"
            html += "</tr>"
            for row in data:
                html += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>"
            html += "</table></body></html>"
            pdf_bytes = export_html_to_pdf(html)
            return Response(pdf_bytes, media_type="application/pdf",
                          headers={"Content-Disposition": "attachment; filename=outstanding_report.pdf"})
        else:
            xlsx_bytes = export_table_to_excel(headers, data, "Outstanding Report")
            return Response(xlsx_bytes,
                          media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          headers={"Content-Disposition": "attachment; filename=outstanding_report.xlsx"})
