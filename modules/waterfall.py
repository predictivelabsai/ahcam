"""
Waterfall Engine module — Define & execute recoupment waterfalls.
"""

import pandas as pd
from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from config.settings import RULE_TYPES


# ---------------------------------------------------------------------------
# Waterfall Engine (Core Logic)
# ---------------------------------------------------------------------------

def apply_waterfall(incoming_amount: float, rules: list[dict]) -> dict:
    """Apply priority-ordered recoupment rules to incoming revenue.

    Returns dict of {recipient_label: payout_amount}.
    """
    if not rules:
        return {"Unallocated": incoming_amount}

    df = pd.DataFrame(rules).sort_values("priority")
    remaining = incoming_amount
    payouts = {}

    for _, rule in df.iterrows():
        if remaining <= 0:
            break

        recipient = rule.get("recipient_label") or f"Rule #{int(rule['priority'])}"
        rule_type = rule.get("rule_type", "percentage")
        pct = float(rule.get("percentage", 0) or 0)
        cap = float(rule.get("cap") or float("inf"))
        floor_val = float(rule.get("floor") or 0)

        if rule_type == "percentage":
            share = remaining * (pct / 100)
        elif rule_type == "fixed":
            share = min(remaining, cap)
        elif rule_type == "corridor":
            corridor_start = float(rule.get("corridor_start") or 0)
            corridor_end = float(rule.get("corridor_end") or float("inf"))
            if incoming_amount < corridor_start:
                share = 0
            elif incoming_amount > corridor_end:
                share = (corridor_end - corridor_start) * (pct / 100)
            else:
                share = (incoming_amount - corridor_start) * (pct / 100)
        elif rule_type == "residual":
            share = remaining
        else:
            share = 0

        share = min(share, cap)
        share = max(share, floor_val)
        share = min(share, remaining)

        payouts[recipient] = payouts.get(recipient, 0) + share
        remaining -= share

    if remaining > 0:
        payouts["Residual/Unallocated"] = remaining

    return payouts


# ---------------------------------------------------------------------------
# AI Agent Tools
# ---------------------------------------------------------------------------

def get_waterfall_rules(production_id: str) -> str:
    """Get the waterfall rules for a production. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            rows = session.execute(text("""
                SELECT r.priority, r.recipient_label, r.rule_type, r.percentage,
                       r.cap, r.description,
                       s.name AS stakeholder_name
                FROM ahcam.waterfall_rules r
                LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = r.recipient_stakeholder_id
                WHERE r.production_id = :pid AND r.active = TRUE
                ORDER BY r.priority
            """), {"pid": production_id}).fetchall()
        if not rows:
            return f"No waterfall rules found for production `{production_id}`."
        header = "| Priority | Recipient | Type | % | Cap | Description |\n|----------|-----------|------|---|-----|-------------|\n"
        lines = []
        for r in rows:
            name = r[6] or r[1] or "\u2014"
            cap = f"${r[4]:,.0f}" if r[4] else "\u2014"
            pct = f"{r[3]}%" if r[3] else "\u2014"
            lines.append(f"| {r[0]} | {name} | {r[2]} | {pct} | {cap} | {r[5] or '\u2014'} |")
        return f"## Waterfall Rules\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def run_waterfall(production_id: str, amount: float = None) -> str:
    """Execute waterfall calculation for a production. Uses account balance if no amount specified."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            if amount is None:
                bal_row = session.execute(text("""
                    SELECT COALESCE(SUM(balance), 0) FROM ahcam.collection_accounts
                    WHERE production_id = :pid AND status = 'active'
                """), {"pid": production_id}).fetchone()
                amount = float(bal_row[0]) if bal_row else 0

            rows = session.execute(text("""
                SELECT priority, recipient_label, rule_type, percentage,
                       cap, floor, corridor_start, corridor_end
                FROM ahcam.waterfall_rules
                WHERE production_id = :pid AND active = TRUE
                ORDER BY priority
            """), {"pid": production_id}).fetchall()

        if not rows:
            return f"No waterfall rules defined for this production."

        rules = [
            {
                "priority": r[0], "recipient_label": r[1], "rule_type": r[2],
                "percentage": r[3], "cap": r[4], "floor": r[5],
                "corridor_start": r[6], "corridor_end": r[7],
            }
            for r in rows
        ]

        payouts = apply_waterfall(amount, rules)

        header = "| Recipient | Amount | % of Total |\n|-----------|--------|------------|\n"
        lines = []
        for recipient, payout in payouts.items():
            pct = (payout / amount * 100) if amount > 0 else 0
            lines.append(f"| {recipient} | ${payout:,.2f} | {pct:.1f}% |")

        return (
            f"## Waterfall Results\n\n"
            f"**Input Amount:** ${amount:,.2f}\n\n"
            f"{header}" + "\n".join(lines)
        )
    except Exception as e:
        return f"Error running waterfall: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/waterfall")
    def module_waterfall(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                prods_with_rules = s.execute(text("""
                    SELECT p.production_id, p.title, COUNT(r.rule_id) as rule_count,
                           COALESCE(SUM(a.balance), 0) as total_balance
                    FROM ahcam.productions p
                    LEFT JOIN ahcam.waterfall_rules r ON r.production_id = p.production_id AND r.active = TRUE
                    LEFT JOIN ahcam.collection_accounts a ON a.production_id = p.production_id
                    GROUP BY p.production_id, p.title
                    HAVING COUNT(r.rule_id) > 0
                    ORDER BY p.title
                """)).fetchall()
                total_rules = s.execute(text("""
                    SELECT COUNT(*) FROM ahcam.waterfall_rules WHERE active = TRUE
                """)).fetchone()
        except Exception:
            prods_with_rules, total_rules = [], (0,)

        cards = []
        for r in prods_with_rules:
            cards.append(Div(
                Div(
                    Span(r[1], cls="deal-card-title"),
                    Span(f"{r[2]} rules", cls="badge-blue"),
                    style="display:flex;justify-content:space-between;align-items:center;",
                ),
                Div(f"Balance: ${r[3]:,.2f}", cls="deal-card-meta"),
                cls="deal-card",
                hx_get=f"/module/waterfall/{r[0]}",
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        return Div(
            Div(
                Div(Div(str(total_rules[0]), cls="stat-value"), Div("Active Rules", cls="stat-label"), cls="stat-card"),
                Div(Div(str(len(prods_with_rules)), cls="stat-value"), Div("Productions with Rules", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Waterfall Engine"),
                    Button("+ Add Rules",
                           hx_get="/module/waterfall/new",
                           hx_target="#center-content",
                           hx_swap="innerHTML",
                           cls="module-action-btn"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                *cards if cards else [Div("No waterfall rules defined yet. Add rules to a production to get started.", cls="empty-state")],
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/waterfall/new")
    def waterfall_new_form(session):
        pool = get_pool()
        with pool.get_session() as s:
            prods = s.execute(text("SELECT production_id, title FROM ahcam.productions ORDER BY title")).fetchall()
            stakeholders = s.execute(text("SELECT stakeholder_id, name FROM ahcam.stakeholders ORDER BY name")).fetchall()
        return Div(
            H3("Add Waterfall Rule"),
            Form(
                Div(
                    Div(Select(Option("Select Production", value=""), *[Option(p[1], value=str(p[0])) for p in prods], name="production_id", required=True), cls="form-group"),
                    Div(Input(type="number", name="priority", placeholder="Priority (1=first)", required=True, min="1"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Select(Option("Select Stakeholder (optional)", value=""), *[Option(s[1], value=str(s[0])) for s in stakeholders], name="recipient_stakeholder_id"), cls="form-group"),
                    Div(Input(type="text", name="recipient_label", placeholder="Recipient Label"), cls="form-group"),
                    cls="form-row",
                ),
                Div(
                    Div(Select(*[Option(t.title(), value=t) for t in RULE_TYPES], name="rule_type"), cls="form-group"),
                    Div(Input(type="number", name="percentage", placeholder="Percentage", step="0.01"), cls="form-group"),
                    Div(Input(type="number", name="cap", placeholder="Cap ($)", step="0.01"), cls="form-group"),
                    cls="form-row",
                ),
                Div(Input(type="text", name="description", placeholder="Description"), cls="form-group"),
                Button("Add Rule", type="submit", cls="module-action-btn"),
                hx_post="/module/waterfall/create",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/waterfall/create", methods=["POST"])
    def waterfall_create(session, production_id: str, priority: int,
                         recipient_stakeholder_id: str = "", recipient_label: str = "",
                         rule_type: str = "percentage", percentage: float = None,
                         cap: float = None, description: str = ""):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.waterfall_rules
                        (production_id, priority, recipient_stakeholder_id, recipient_label,
                         rule_type, percentage, cap, description)
                    VALUES (:pid, :pri, :rsid, :rlabel, :rtype, :pct, :cap, :desc)
                """), {
                    "pid": production_id, "pri": priority,
                    "rsid": recipient_stakeholder_id or None,
                    "rlabel": recipient_label or None,
                    "rtype": rule_type, "pct": percentage, "cap": cap,
                    "desc": description or None,
                })
        except Exception as e:
            return Div(f"Error: {e}", cls="module-error")
        return module_waterfall(session)

    @rt("/module/waterfall/{production_id}")
    def waterfall_detail(production_id: str, session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                prod = s.execute(text("SELECT title FROM ahcam.productions WHERE production_id = :pid"),
                                 {"pid": production_id}).fetchone()
                rules = s.execute(text("""
                    SELECT r.rule_id, r.priority, r.recipient_label, r.rule_type,
                           r.percentage, r.cap, r.description, s.name
                    FROM ahcam.waterfall_rules r
                    LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = r.recipient_stakeholder_id
                    WHERE r.production_id = :pid AND r.active = TRUE
                    ORDER BY r.priority
                """), {"pid": production_id}).fetchall()
                balance = s.execute(text("""
                    SELECT COALESCE(SUM(balance), 0) FROM ahcam.collection_accounts
                    WHERE production_id = :pid AND status = 'active'
                """), {"pid": production_id}).fetchone()
        except Exception:
            prod, rules, balance = None, [], (0,)
        if not prod:
            return Div("Production not found.", cls="module-error")

        rule_rows = []
        for r in rules:
            name = r[7] or r[2] or "\u2014"
            cap = f"${r[5]:,.0f}" if r[5] else "\u2014"
            pct = f"{r[4]}%" if r[4] else "\u2014"
            rule_rows.append(Tr(Td(str(r[1])), Td(name), Td(r[3].title()), Td(pct), Td(cap), Td(r[6] or "\u2014")))

        return Div(
            H3(f"Waterfall: {prod[0]}"),
            Div(f"Account Balance: ${float(balance[0]):,.2f}", cls="stat-highlight"),
            Table(
                Thead(Tr(Th("Priority"), Th("Recipient"), Th("Type"), Th("%"), Th("Cap"), Th("Description"))),
                Tbody(*rule_rows) if rule_rows else Tbody(Tr(Td("No rules", colspan="6"))),
                cls="module-table",
            ),
            Div(
                Button("Run Waterfall",
                       hx_post=f"/module/waterfall/run/{production_id}",
                       hx_target="#waterfall-result",
                       hx_swap="innerHTML",
                       cls="module-action-btn"),
                style="margin-top:1rem;",
            ),
            Div(id="waterfall-result"),
            Button("\u2190 Back",
                   hx_get="/module/waterfall",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="back-btn"),
            cls="module-content",
        )

    @rt("/module/waterfall/run/{production_id}", methods=["POST"])
    def waterfall_run(production_id: str, session):
        result = run_waterfall(production_id)
        return Div(Pre(result, cls="waterfall-result-pre"), cls="waterfall-result-box")
