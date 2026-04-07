"""
Title Groups module — Group productions for cross-collateralization or packaging.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_title_groups(query: str = "") -> str:
    """Search title groups. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if query:
                rows = session.execute(text("""
                    SELECT tg.group_id, tg.group_name, tg.comment,
                           STRING_AGG(p.title, ', ' ORDER BY p.title) AS titles
                    FROM ahcam.title_groups tg
                    LEFT JOIN ahcam.title_group_members tgm ON tgm.group_id = tg.group_id
                    LEFT JOIN ahcam.productions p ON p.production_id = tgm.production_id
                    WHERE tg.group_name ILIKE :q OR tg.comment ILIKE :q
                    GROUP BY tg.group_id, tg.group_name, tg.comment
                    ORDER BY tg.group_name LIMIT 20
                """), {"q": f"%{query}%"}).fetchall()
            else:
                rows = session.execute(text("""
                    SELECT tg.group_id, tg.group_name, tg.comment,
                           STRING_AGG(p.title, ', ' ORDER BY p.title) AS titles
                    FROM ahcam.title_groups tg
                    LEFT JOIN ahcam.title_group_members tgm ON tgm.group_id = tg.group_id
                    LEFT JOIN ahcam.productions p ON p.production_id = tgm.production_id
                    GROUP BY tg.group_id, tg.group_name, tg.comment
                    ORDER BY tg.group_name LIMIT 20
                """)).fetchall()
        if not rows:
            return "No title groups found."
        header = "| Group Name | Titles | Comment |\n|------------|--------|---------|\n"
        lines = []
        for r in rows:
            lines.append(f"| {r[1]} | {r[3] or '\u2014'} | {r[2] or '\u2014'} |")
        return f"## Title Groups\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/title-groups")
    def module_title_groups(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT tg.group_id, tg.group_name, tg.comment,
                           STRING_AGG(p.title, ', ' ORDER BY p.title) AS titles,
                           COUNT(tgm.production_id) AS title_count
                    FROM ahcam.title_groups tg
                    LEFT JOIN ahcam.title_group_members tgm ON tgm.group_id = tg.group_id
                    LEFT JOIN ahcam.productions p ON p.production_id = tgm.production_id
                    GROUP BY tg.group_id, tg.group_name, tg.comment
                    ORDER BY tg.group_name
                    LIMIT 50
                """)).fetchall()

                totals = s.execute(text("""
                    SELECT COUNT(*) FROM ahcam.title_groups
                """)).fetchone()
        except Exception:
            rows = []
            totals = (0,)

        # Stat cards
        stat_grid = Div(
            Div(Div(str(totals[0]), cls="stat-value"), Div("Total Groups", cls="stat-label"), cls="stat-card"),
            cls="stat-grid",
        )

        # Table rows
        table_rows = []
        for r in rows:
            group_id = r[0]
            group_name = r[1]
            comment = r[2] or "\u2014"
            titles = r[3] or "\u2014"
            title_count = r[4]

            table_rows.append(Tr(
                Td(Span(group_name, style="font-weight:500;")),
                Td(Span(str(title_count), cls="badge-blue")),
                Td(titles, style="max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;",
                   title=titles),
                Td(comment, style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"),
            ))

        content_table = Table(
            Thead(Tr(
                Th("Group Name"), Th("# Titles"), Th("Titles"), Th("Comment"),
            )),
            Tbody(*table_rows) if table_rows else Tbody(Tr(Td("No title groups found.", colspan="4", style="text-align:center;"))),
            cls="module-table",
        )

        return Div(
            stat_grid,
            Div(
                Div(
                    H3("Title Groups"),
                    Button("+ New Group",
                           hx_get="/module/title-group/new",
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

    @rt("/module/title-group/new")
    def title_group_new_form(session):
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
            H3("New Title Group"),
            Form(
                Div(
                    Div(Input(type="text", name="group_name", placeholder="Group Name", required=True), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(
                        Div("Select Titles", style="font-size:0.85rem;color:#94a3b8;margin-bottom:6px;font-weight:500;"),
                        Div(
                            *checkboxes if checkboxes else [Span("No productions available.", style="color:#6b7280;font-size:0.85rem;")],
                            style="max-height:250px;overflow-y:auto;padding:8px;background:#0f172a;border-radius:6px;border:1px solid #334155;",
                        ),
                        cls="form-group",
                    ),
                    cls="form-row",
                ),
                Div(
                    Div(Textarea(name="comment", placeholder="Comment / description...", rows="3"), cls="form-group"),
                    cls="form-row",
                ),
                Button("Create Group", type="submit", cls="module-action-btn"),
                hx_post="/module/title-group/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/title-group/create", methods=["POST"])
    def title_group_create(session, group_name: str, comment: str = "", production_ids: list = None):
        if production_ids is None:
            production_ids = []
        # Ensure it's always a list
        if isinstance(production_ids, str):
            production_ids = [production_ids]

        try:
            pool = get_pool()
            with pool.get_session() as s:
                # Insert group
                result = s.execute(text("""
                    INSERT INTO ahcam.title_groups (group_name, comment, created_by)
                    VALUES (:name, :comment, :uid)
                    RETURNING group_id
                """), {
                    "name": group_name,
                    "comment": comment or None,
                    "uid": session.get("user_id"),
                })
                group_id = result.fetchone()[0]

                # Insert members
                for pid in production_ids:
                    if pid:
                        s.execute(text("""
                            INSERT INTO ahcam.title_group_members (group_id, production_id)
                            VALUES (:gid, :pid)
                        """), {"gid": str(group_id), "pid": pid})
        except Exception as e:
            return Div(f"Error creating group: {e}", cls="module-error")
        return module_title_groups(session)
