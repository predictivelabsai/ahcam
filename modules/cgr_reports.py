"""
CGR Reports module — Collection Gross Receipts reports with territory/distributor filters.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from config.settings import TERRITORY_LIST


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def generate_cgr_report(territory: str = "", distributor: str = "") -> str:
    """Generate a Collection Gross Receipts report. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            where_clauses = []
            params = {}
            if territory:
                where_clauses.append("da.territory = :territory")
                params["territory"] = territory
            if distributor:
                where_clauses.append("da.distributor_name ILIKE :dist")
                params["dist"] = f"%{distributor}%"
            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            rows = session.execute(text(f"""
                SELECT da.territory, da.distributor_name,
                       COALESCE(SUM(t.amount) FILTER (WHERE t.transaction_type = 'inflow'), 0) AS gross_receipts
                FROM ahcam.distribution_agreements da
                LEFT JOIN ahcam.collection_accounts ca ON ca.production_id = da.production_id
                LEFT JOIN ahcam.transactions t ON t.account_id = ca.account_id
                {where_sql}
                GROUP BY da.territory, da.distributor_name
                ORDER BY gross_receipts DESC
            """), params).fetchall()
        if not rows:
            return "No CGR data found."
        header = "| Territory | Distributor | Gross Receipts | WHT (5%) | Net Receipts |\n|-----------|-------------|---------------|----------|---------------|\n"
        lines = []
        for r in rows:
            gross = float(r[2])
            wht = gross * 0.05
            net = gross - wht
            lines.append(f"| {r[0]} | {r[1]} | ${gross:,.2f} | ${wht:,.2f} | ${net:,.2f} |")
        return f"## CGR Report\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/cgr-reports")
    def module_cgr_reports(session, territory: str = "", distributor: str = ""):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                where_clauses = []
                params = {}
                if territory:
                    where_clauses.append("da.territory = :territory")
                    params["territory"] = territory
                if distributor:
                    where_clauses.append("da.distributor_name ILIKE :dist")
                    params["dist"] = f"%{distributor}%"
                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

                rows = s.execute(text(f"""
                    SELECT da.territory, da.distributor_name,
                           COALESCE(SUM(t.amount) FILTER (WHERE t.transaction_type = 'inflow'), 0) AS gross_receipts
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.collection_accounts ca ON ca.production_id = da.production_id
                    LEFT JOIN ahcam.transactions t ON t.account_id = ca.account_id
                    {where_sql}
                    GROUP BY da.territory, da.distributor_name
                    ORDER BY gross_receipts DESC
                    LIMIT 100
                """), params).fetchall()

                # Totals
                totals_row = s.execute(text(f"""
                    SELECT COALESCE(SUM(t.amount) FILTER (WHERE t.transaction_type = 'inflow'), 0) AS total_gross
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.collection_accounts ca ON ca.production_id = da.production_id
                    LEFT JOIN ahcam.transactions t ON t.account_id = ca.account_id
                    {where_sql}
                """), params).fetchone()
                total_gross = float(totals_row[0]) if totals_row else 0
        except Exception:
            rows = []
            total_gross = 0

        total_wht = total_gross * 0.05
        total_deductions = 0  # Placeholder for future deductions
        total_net = total_gross - total_wht - total_deductions

        # Stat cards
        stat_grid = Div(
            Div(Div(f"${total_gross:,.2f}", cls="stat-value"), Div("Gross Receipts", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${total_wht:,.2f}", cls="stat-value negative"), Div("WHT (5%)", cls="stat-label"), cls="stat-card"),
            Div(Div(f"${total_net:,.2f}", cls="stat-value positive"), Div("Net Receipts", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        # Filter bar
        filter_form = Form(
            Div(
                Div(Select(
                    Option("All Territories", value=""),
                    *[Option(t, value=t, selected=(t == territory)) for t in TERRITORY_LIST],
                    name="territory",
                ), cls="form-group"),
                Div(Input(type="text", name="distributor", placeholder="Search distributor...",
                          value=distributor), cls="form-group"),
                Div(Button("Run Report", type="submit", cls="module-action-btn",
                           style="font-size:0.85rem;padding:6px 16px;"), cls="form-group"),
                cls="form-row",
            ),
            hx_get="/module/cgr-reports",
            hx_target="#center-content",
            hx_swap="innerHTML",
            style="margin-bottom:1rem;",
        )

        # Table rows
        table_rows = []
        for r in rows:
            gross = float(r[2])
            wht = gross * 0.05
            deductions = 0.0
            net = gross - wht - deductions

            table_rows.append(Tr(
                Td(r[0]),
                Td(r[1]),
                Td(f"${gross:,.2f}", style="text-align:right;"),
                Td(f"${wht:,.2f}", style="text-align:right;color:#f59e0b;"),
                Td(f"${deductions:,.2f}", style="text-align:right;"),
                Td(f"${net:,.2f}", style="text-align:right;font-weight:500;"),
            ))

        content_table = Table(
            Thead(Tr(
                Th("Territory"), Th("Distributor"), Th("Gross Receipts"),
                Th("WHT (5%)"), Th("Deductions"), Th("Net Receipts"),
            )),
            Tbody(*table_rows) if table_rows else Tbody(Tr(Td("No CGR data. Run a report with filters.", colspan="6", style="text-align:center;"))),
            cls="module-table",
        )

        # Export buttons
        export_bar = Div(
            Button("Export Excel",
                   hx_get=f"/export/cgr-report?fmt=excel&territory={territory}&distributor={distributor}",
                   hx_swap="none",
                   cls="module-action-btn",
                   style="font-size:0.8rem;padding:4px 12px;margin-right:8px;"),
            Button("Export PDF",
                   hx_get=f"/export/cgr-report?fmt=pdf&territory={territory}&distributor={distributor}",
                   hx_swap="none",
                   cls="module-action-btn",
                   style="font-size:0.8rem;padding:4px 12px;background:#6b7280;"),
            style="display:flex;gap:8px;",
        )

        return Div(
            stat_grid,
            filter_form,
            Div(
                Div(
                    H3("CGR Report"),
                    export_bar,
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                content_table,
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/export/cgr-report")
    def export_cgr_report(session, fmt: str = "excel", territory: str = "", distributor: str = ""):
        """Export CGR report data."""
        from starlette.responses import Response
        try:
            from utils.export import export_table_to_excel, export_html_to_pdf
        except ImportError:
            return Response("Export not available", status_code=500)

        try:
            pool = get_pool()
            with pool.get_session() as s:
                where_clauses = []
                params = {}
                if territory:
                    where_clauses.append("da.territory = :territory")
                    params["territory"] = territory
                if distributor:
                    where_clauses.append("da.distributor_name ILIKE :dist")
                    params["dist"] = f"%{distributor}%"
                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

                rows = s.execute(text(f"""
                    SELECT da.territory, da.distributor_name,
                           COALESCE(SUM(t.amount) FILTER (WHERE t.transaction_type = 'inflow'), 0) AS gross_receipts
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.collection_accounts ca ON ca.production_id = da.production_id
                    LEFT JOIN ahcam.transactions t ON t.account_id = ca.account_id
                    {where_sql}
                    GROUP BY da.territory, da.distributor_name
                    ORDER BY gross_receipts DESC
                """), params).fetchall()
        except Exception:
            rows = []

        headers = ["Territory", "Distributor", "Gross Receipts", "WHT (5%)", "Deductions", "Net Receipts"]
        data = []
        for r in rows:
            gross = float(r[2])
            wht = gross * 0.05
            net = gross - wht
            data.append([r[0], r[1], gross, wht, 0.0, net])

        if fmt == "pdf":
            html = "<html><head><style>body{font-family:Arial;font-size:12px;}table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ccc;padding:6px 8px;text-align:left;}th{background:#2C3E50;color:#fff;}</style></head><body>"
            html += "<h2>CGR Report \u2014 Ashland Hill CAM</h2><table><tr>"
            for h in headers:
                html += f"<th>{h}</th>"
            html += "</tr>"
            for row in data:
                html += "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>"
            html += "</table></body></html>"
            pdf_bytes = export_html_to_pdf(html)
            return Response(pdf_bytes, media_type="application/pdf",
                          headers={"Content-Disposition": "attachment; filename=cgr_report.pdf"})
        else:
            xlsx_bytes = export_table_to_excel(headers, data, "CGR Report")
            return Response(xlsx_bytes,
                          media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          headers={"Content-Disposition": "attachment; filename=cgr_report.xlsx"})
