"""
Search module — Cross-module search and user favorites.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def global_search(query: str) -> str:
    """Search across productions, stakeholders, and distribution agreements. Returns markdown."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            productions = session.execute(text("""
                SELECT production_id, title, genre, status
                FROM ahcam.productions
                WHERE title ILIKE :q
                ORDER BY title LIMIT 5
            """), {"q": f"%{query}%"}).fetchall()

            stakeholders = session.execute(text("""
                SELECT stakeholder_id, name, company, role
                FROM ahcam.stakeholders
                WHERE name ILIKE :q OR company ILIKE :q
                ORDER BY name LIMIT 5
            """), {"q": f"%{query}%"}).fetchall()

            agreements = session.execute(text("""
                SELECT da.agreement_id, da.territory, da.distributor_name, p.title
                FROM ahcam.distribution_agreements da
                LEFT JOIN ahcam.productions p ON p.production_id = da.production_id
                WHERE da.territory ILIKE :q OR da.distributor_name ILIKE :q
                ORDER BY da.territory LIMIT 5
            """), {"q": f"%{query}%"}).fetchall()

        lines = [f"## Search Results for \"{query}\"\n"]
        if productions:
            lines.append("### Productions")
            for r in productions:
                lines.append(f"- **{r[1]}** ({r[2] or '\u2014'}) \u2014 {r[3]}")
        if stakeholders:
            lines.append("\n### Stakeholders")
            for r in stakeholders:
                lines.append(f"- **{r[1]}** ({r[3]}) \u2014 {r[2] or '\u2014'}")
        if agreements:
            lines.append("\n### Distribution Agreements")
            for r in agreements:
                lines.append(f"- **{r[1]}** \u2014 {r[2]} ({r[3] or '\u2014'})")
        if not (productions or stakeholders or agreements):
            lines.append("No results found.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/search")
    def search_results(session, q: str = ""):
        if not q or len(q.strip()) < 2:
            return Div(
                Div("Enter at least 2 characters to search.", cls="empty-state",
                    style="padding:1rem;"),
            )

        query = q.strip()
        productions = []
        stakeholders = []
        agreements = []

        try:
            pool = get_pool()
            with pool.get_session() as s:
                productions = s.execute(text("""
                    SELECT production_id, title, genre, status
                    FROM ahcam.productions
                    WHERE title ILIKE :q
                    ORDER BY title LIMIT 5
                """), {"q": f"%{query}%"}).fetchall()
        except Exception:
            pass

        try:
            pool = get_pool()
            with pool.get_session() as s:
                stakeholders = s.execute(text("""
                    SELECT stakeholder_id, name, company, role
                    FROM ahcam.stakeholders
                    WHERE name ILIKE :q OR company ILIKE :q
                    ORDER BY name LIMIT 5
                """), {"q": f"%{query}%"}).fetchall()
        except Exception:
            pass

        try:
            pool = get_pool()
            with pool.get_session() as s:
                agreements = s.execute(text("""
                    SELECT da.agreement_id, da.territory, da.distributor_name, p.title
                    FROM ahcam.distribution_agreements da
                    LEFT JOIN ahcam.productions p ON p.production_id = da.production_id
                    WHERE da.territory ILIKE :q OR da.distributor_name ILIKE :q
                    ORDER BY da.territory LIMIT 5
                """), {"q": f"%{query}%"}).fetchall()
        except Exception:
            pass

        sections = []

        # Productions
        if productions:
            items = []
            for r in productions:
                status_cls = "badge-green" if r[3] in ("released", "completed") else "badge-amber" if r[3] == "production" else "badge-blue"
                items.append(Div(
                    Div(
                        Span(r[1], style="font-weight:500;color:#e2e8f0;"),
                        Span(r[3].replace("_", " ").title() if r[3] else "", cls=status_cls),
                        style="display:flex;justify-content:space-between;align-items:center;",
                    ),
                    Div(r[2] or "", cls="deal-card-meta"),
                    cls="deal-card",
                    hx_get=f"/module/production/{r[0]}",
                    hx_target="#center-content",
                    hx_swap="innerHTML",
                    style="cursor:pointer;",
                ))
            sections.append(Div(
                H4("Productions", style="color:#94a3b8;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;"),
                *items,
            ))

        # Stakeholders
        if stakeholders:
            items = []
            for r in stakeholders:
                items.append(Div(
                    Div(
                        Span(r[1], style="font-weight:500;color:#e2e8f0;"),
                        Span(r[3].replace("_", " ").title() if r[3] else "", cls="badge-blue"),
                        style="display:flex;justify-content:space-between;align-items:center;",
                    ),
                    Div(r[2] or "", cls="deal-card-meta"),
                    cls="deal-card",
                    hx_get=f"/module/stakeholder/{r[0]}",
                    hx_target="#center-content",
                    hx_swap="innerHTML",
                    style="cursor:pointer;",
                ))
            sections.append(Div(
                H4("Stakeholders", style="color:#94a3b8;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;margin-top:12px;"),
                *items,
            ))

        # Distribution Agreements
        if agreements:
            items = []
            for r in agreements:
                items.append(Div(
                    Div(
                        Span(f"{r[1]} \u2014 {r[2]}", style="font-weight:500;color:#e2e8f0;"),
                        style="display:flex;justify-content:space-between;align-items:center;",
                    ),
                    Div(r[3] or "", cls="deal-card-meta"),
                    cls="deal-card",
                    hx_get=f"/module/distribution-agreement/{r[0]}",
                    hx_target="#center-content",
                    hx_swap="innerHTML",
                    style="cursor:pointer;",
                ))
            sections.append(Div(
                H4("Distribution Agreements", style="color:#94a3b8;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;margin-top:12px;"),
                *items,
            ))

        if not sections:
            return Div(
                Div(f"No results found for \"{query}\".", cls="empty-state",
                    style="padding:1rem;"),
            )

        return Div(*sections)

    @rt("/module/favorites")
    def module_favorites(session):
        user_id = session.get("user_id")
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT f.favorite_id, f.entity_type, f.entity_id, f.label,
                           f.created_at
                    FROM ahcam.favorites f
                    WHERE f.user_id = :uid
                    ORDER BY f.created_at DESC
                    LIMIT 50
                """), {"uid": user_id}).fetchall()
        except Exception:
            rows = []

        if not rows:
            return Div(
                H3("Favorites"),
                Div("No favorites yet. Star items from other modules to see them here.", cls="empty-state"),
                cls="module-content",
            )

        fav_items = []
        for r in rows:
            fav_id = r[0]
            entity_type = r[1]
            entity_id = r[2]
            label = r[3] or entity_type.replace("_", " ").title()
            created = str(r[4])[:10] if r[4] else ""

            # Determine link based on entity type
            if entity_type == "production":
                link = f"/module/production/{entity_id}"
            elif entity_type == "stakeholder":
                link = f"/module/stakeholder/{entity_id}"
            elif entity_type == "agreement":
                link = f"/module/distribution-agreement/{entity_id}"
            elif entity_type == "account":
                link = f"/module/account/{entity_id}"
            else:
                link = "#"

            type_cls = "badge-blue" if entity_type == "production" else "badge-green" if entity_type == "stakeholder" else "badge-amber"

            fav_items.append(Div(
                Div(
                    Div(
                        Span(label, style="font-weight:500;color:#e2e8f0;"),
                        Span(entity_type.replace("_", " ").title(), cls=type_cls),
                        style="display:flex;justify-content:space-between;align-items:center;",
                    ),
                    Div(created, cls="deal-card-meta"),
                    style="flex:1;",
                ),
                Button("\u2716",
                       hx_post=f"/favorite/toggle?entity_type={entity_type}&entity_id={entity_id}&label={label}",
                       hx_target="#center-content",
                       hx_swap="innerHTML",
                       style="background:none;border:none;color:#ef4444;cursor:pointer;font-size:1rem;padding:4px 8px;",
                       title="Remove from favorites"),
                cls="deal-card",
                style="display:flex;align-items:center;cursor:pointer;",
                hx_get=link,
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        return Div(
            Div(
                Div(Div(str(len(rows)), cls="stat-value"), Div("Favorites", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                H3("Favorites"),
                *fav_items,
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/favorite/toggle", methods=["POST"])
    def favorite_toggle(session, entity_type: str, entity_id: str, label: str = ""):
        user_id = session.get("user_id")
        if not user_id:
            return Div("Not authenticated.", cls="module-error")

        try:
            pool = get_pool()
            with pool.get_session() as s:
                # Check if favorite exists
                existing = s.execute(text("""
                    SELECT favorite_id FROM ahcam.favorites
                    WHERE user_id = :uid AND entity_type = :etype AND entity_id = :eid
                """), {"uid": user_id, "etype": entity_type, "eid": entity_id}).fetchone()

                if existing:
                    # Remove favorite
                    s.execute(text("""
                        DELETE FROM ahcam.favorites
                        WHERE favorite_id = :fid
                    """), {"fid": str(existing[0])})
                    return Div(
                        Span("\u2606 Removed from favorites", style="color:#94a3b8;font-size:0.85rem;"),
                        id="favorite-status",
                    )
                else:
                    # Add favorite
                    s.execute(text("""
                        INSERT INTO ahcam.favorites (user_id, entity_type, entity_id, label)
                        VALUES (:uid, :etype, :eid, :label)
                    """), {"uid": user_id, "etype": entity_type, "eid": entity_id, "label": label or None})
                    return Div(
                        Span("\u2605 Added to favorites", style="color:#f59e0b;font-size:0.85rem;"),
                        id="favorite-status",
                    )
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
