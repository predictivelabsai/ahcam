"""
Doc Sharing module — Secure document sharing linked to productions.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_shared_documents(query: str = "") -> str:
    """Search shared documents. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT sd.document_id, sd.document_name, sd.comment, sd.upload_date,
                           STRING_AGG(p.title, ', ' ORDER BY p.title) AS titles
                    FROM ahcam.shared_documents sd
                    LEFT JOIN ahcam.shared_document_titles sdt ON sdt.document_id = sd.document_id
                    LEFT JOIN ahcam.productions p ON p.production_id = sdt.production_id
                    WHERE sd.document_name ILIKE :q OR sd.comment ILIKE :q
                    GROUP BY sd.document_id, sd.document_name, sd.comment, sd.upload_date
                    ORDER BY sd.upload_date DESC LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT sd.document_id, sd.document_name, sd.comment, sd.upload_date,
                           STRING_AGG(p.title, ', ' ORDER BY p.title) AS titles
                    FROM ahcam.shared_documents sd
                    LEFT JOIN ahcam.shared_document_titles sdt ON sdt.document_id = sd.document_id
                    LEFT JOIN ahcam.productions p ON p.production_id = sdt.production_id
                    GROUP BY sd.document_id, sd.document_name, sd.comment, sd.upload_date
                    ORDER BY sd.upload_date DESC LIMIT 20
                """)).fetchall()
        if not rows:
            return "No shared documents found."
        header = "| Document | Related Titles | Comment | Uploaded |\n|----------|----------------|---------|----------|\n"
        lines = []
        for r in rows:
            lines.append(f"| {r[1]} | {r[4] or '\u2014'} | {r[2] or '\u2014'} | {str(r[3])[:10] if r[3] else '\u2014'} |")
        return f"## Shared Documents\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/doc-sharing")
    def module_doc_sharing(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT sd.document_id, sd.document_name, sd.comment, sd.upload_date,
                           sd.file_path,
                           STRING_AGG(p.title, ', ' ORDER BY p.title) AS titles,
                           COUNT(sdt.production_id) AS title_count
                    FROM ahcam.shared_documents sd
                    LEFT JOIN ahcam.shared_document_titles sdt ON sdt.document_id = sd.document_id
                    LEFT JOIN ahcam.productions p ON p.production_id = sdt.production_id
                    GROUP BY sd.document_id, sd.document_name, sd.comment, sd.upload_date, sd.file_path
                    ORDER BY sd.upload_date DESC NULLS LAST, sd.created_at DESC
                    LIMIT 50
                """)).fetchall()

                totals = s.execute(text("""
                    SELECT COUNT(*) FROM ahcam.shared_documents
                """)).fetchone()
        except Exception:
            rows = []
            totals = (0,)

        # Stat cards
        stat_grid = Div(
            Div(Div(str(totals[0]), cls="stat-value"), Div("Total Documents", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        # Table rows
        table_rows = []
        for r in rows:
            doc_id = r[0]
            doc_name = r[1]
            comment = r[2] or "\u2014"
            upload_date = str(r[3])[:10] if r[3] else "\u2014"
            titles = r[5] or "\u2014"

            table_rows.append(Tr(
                Td(Span(doc_name, style="font-weight:500;")),
                Td(titles, style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;",
                   title=titles),
                Td(comment, style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"),
                Td(upload_date),
            ))

        content_table = Table(
            Thead(Tr(
                Th("Document Name"), Th("Related Titles"), Th("Comment"), Th("Upload Date"),
            )),
            Tbody(*table_rows) if table_rows else Tbody(Tr(Td("No shared documents found.", colspan="4", style="text-align:center;"))),
            cls="module-table",
        )

        return Div(
            stat_grid,
            Div(
                Div(
                    H3("Secure Documents"),
                    Button("+ Add Secure Document",
                           hx_get="/module/doc-sharing/new",
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

    @rt("/module/doc-sharing/new")
    def doc_sharing_new_form(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                prods = s.execute(text("""
                    SELECT production_id, title FROM ahcam.productions ORDER BY title
                """)).fetchall()
        except Exception:
            prods = []

        # Build checkbox list for productions
        checkboxes = []
        for p in prods:
            checkboxes.append(Div(
                Label(
                    Input(type="checkbox", name="production_ids", value=str(p[0])),
                    f" {p[1]}",
                    style="display:flex;align-items:center;gap:6px;color:#e2e8f0;font-size:0.9rem;cursor:pointer;",
                ),
                style="padding:4px 0;",
            ))

        return Div(
            H3("Add Secure Document"),
            Form(
                Div(
                    Div(Input(type="text", name="document_name", placeholder="Document Name", required=True), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(
                        Input(type="file", name="file", accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt",
                              style="color:#e2e8f0;"),
                        cls="form-group",
                    ),
                    cls="form-row",
                ),
                Div(
                    Div(
                        Div("Related Productions", style="font-size:0.85rem;color:#94a3b8;margin-bottom:6px;font-weight:500;"),
                        Div(
                            *checkboxes if checkboxes else [Span("No productions available.", style="color:#6b7280;font-size:0.85rem;")],
                            style="max-height:200px;overflow-y:auto;padding:8px;background:#0f172a;border-radius:6px;border:1px solid #334155;",
                        ),
                        cls="form-group",
                    ),
                    cls="form-row",
                ),
                Div(
                    Div(Textarea(name="comment", placeholder="Comment...", rows="3"), cls="form-group"),
                    cls="form-row",
                ),
                Button("Upload Document", type="submit", cls="module-action-btn"),
                hx_post="/module/doc-sharing/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                hx_encoding="multipart/form-data",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/doc-sharing/create", methods=["POST"])
    async def doc_sharing_create(session, document_name: str, comment: str = "",
                                  production_ids=None):
        if production_ids is None:
            production_ids = []
        if isinstance(production_ids, str):
            production_ids = [production_ids]

        # File handling would go here in production
        # For now, just store the metadata
        file_path = None  # Placeholder for actual file storage

        try:
            pool = get_pool()
            with pool.get_session() as s:
                result = s.execute(text("""
                    INSERT INTO ahcam.shared_documents
                        (document_name, file_path, comment, upload_date, created_by)
                    VALUES (:name, :fpath, :comment, NOW(), :uid)
                    RETURNING document_id
                """), {
                    "name": document_name,
                    "fpath": file_path,
                    "comment": comment or None,
                    "uid": session.get("user_id"),
                })
                doc_id = result.fetchone()[0]

                for pid in production_ids:
                    if pid:
                        s.execute(text("""
                            INSERT INTO ahcam.shared_document_titles (document_id, production_id)
                            VALUES (:did, :pid)
                        """), {"did": str(doc_id), "pid": pid})
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
        return module_doc_sharing(session)
