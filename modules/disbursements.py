"""
Disbursements module — Automated payout processing based on waterfall rules.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool
from utils.ledger import record_transaction
from modules.waterfall import apply_waterfall


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def get_disbursement_status(query: str = "") -> str:
    """Get disbursement status. Returns markdown table."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            rows = session.execute(text("""
                SELECT d.disbursement_id, d.amount, d.status, d.created_at,
                       s.name AS stakeholder, p.title AS production
                FROM ahcam.disbursements d
                LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = d.stakeholder_id
                LEFT JOIN ahcam.productions p ON p.production_id = d.production_id
                ORDER BY d.created_at DESC LIMIT 20
            """)).fetchall()
        if not rows:
            return "No disbursements found."
        header = "| Production | Stakeholder | Amount | Status | Date |\n|-----------|-------------|--------|--------|------|\n"
        lines = [f"| {r[5] or '\u2014'} | {r[4] or '\u2014'} | ${r[1]:,.2f} | {r[2]} | {str(r[3])[:10]} |" for r in rows]
        return f"## Disbursements\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def run_disbursements(production_id: str) -> str:
    """Process disbursements for a production based on waterfall rules."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            # Get active account and balance
            account = session.execute(text("""
                SELECT account_id, balance FROM ahcam.collection_accounts
                WHERE production_id = :pid AND status = 'active'
                ORDER BY balance DESC LIMIT 1
            """), {"pid": production_id}).fetchone()

            if not account or float(account[1]) <= 0:
                return "No funds available for disbursement."

            balance = float(account[1])
            account_id = str(account[0])

            # Get waterfall rules
            rules = session.execute(text("""
                SELECT r.priority, r.recipient_label, r.rule_type, r.percentage,
                       r.cap, r.floor, r.corridor_start, r.corridor_end,
                       r.rule_id, r.recipient_stakeholder_id
                FROM ahcam.waterfall_rules r
                WHERE r.production_id = :pid AND r.active = TRUE
                ORDER BY r.priority
            """), {"pid": production_id}).fetchall()

        if not rules:
            return "No waterfall rules defined."

        rule_dicts = [
            {
                "priority": r[0], "recipient_label": r[1], "rule_type": r[2],
                "percentage": r[3], "cap": r[4], "floor": r[5],
                "corridor_start": r[6], "corridor_end": r[7],
            }
            for r in rules
        ]

        payouts = apply_waterfall(balance, rule_dicts)

        # Record disbursements
        results = []
        for i, rule in enumerate(rules):
            recipient = rule[1] or f"Rule #{rule[0]}"
            amount = payouts.get(recipient, 0)
            if amount <= 0:
                continue

            # Record outflow transaction
            txn = record_transaction(
                account_id=account_id,
                transaction_type="outflow",
                amount=amount,
                description=f"Waterfall disbursement: {recipient}",
                destination_stakeholder_id=str(rule[9]) if rule[9] else None,
            )

            # Record disbursement
            with pool.get_session() as session:
                session.execute(text("""
                    INSERT INTO ahcam.disbursements
                        (production_id, transaction_id, stakeholder_id, amount,
                         waterfall_rule_id, status)
                    VALUES (:pid, :tid, :sid, :amount, :rid, 'completed')
                """), {
                    "pid": production_id,
                    "tid": txn["transaction_id"],
                    "sid": str(rule[9]) if rule[9] else None,
                    "amount": amount,
                    "rid": str(rule[8]),
                })

            results.append(f"| {recipient} | ${amount:,.2f} | completed |")

        header = "| Recipient | Amount | Status |\n|-----------|--------|--------|\n"
        return f"## Disbursements Processed\n\n**Total Disbursed:** ${sum(payouts.values()):,.2f}\n\n{header}" + "\n".join(results)
    except Exception as e:
        return f"Error processing disbursements: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/disbursements")
    def module_disbursements(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT d.disbursement_id, d.amount, d.status, d.created_at,
                           s.name, p.title
                    FROM ahcam.disbursements d
                    LEFT JOIN ahcam.stakeholders s ON s.stakeholder_id = d.stakeholder_id
                    LEFT JOIN ahcam.productions p ON p.production_id = d.production_id
                    ORDER BY d.created_at DESC LIMIT 30
                """)).fetchall()
                totals = s.execute(text("""
                    SELECT COUNT(*),
                           COALESCE(SUM(amount), 0),
                           COUNT(*) FILTER (WHERE status = 'completed')
                    FROM ahcam.disbursements
                """)).fetchone()
        except Exception:
            rows, totals = [], (0, 0, 0)

        txn_rows = []
        for r in rows:
            status_cls = "badge-green" if r[2] == "completed" else "badge-amber" if r[2] == "approved" else "badge-blue"
            txn_rows.append(Tr(
                Td(r[5] or "\u2014"), Td(r[4] or "\u2014"),
                Td(f"${r[1]:,.2f}"), Td(Span(r[2].title(), cls=status_cls)),
                Td(str(r[3])[:10]),
            ))

        return Div(
            Div(
                Div(Div(str(totals[0]), cls="stat-value"), Div("Total Disbursements", cls="stat-label"), cls="stat-card"),
                Div(Div(f"${totals[1]:,.2f}", cls="stat-value"), Div("Amount Disbursed", cls="stat-label"), cls="stat-card"),
                Div(Div(str(totals[2]), cls="stat-value"), Div("Completed", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                H3("Disbursements"),
                Table(
                    Thead(Tr(Th("Production"), Th("Stakeholder"), Th("Amount"), Th("Status"), Th("Date"))),
                    Tbody(*txn_rows) if txn_rows else Tbody(Tr(Td("No disbursements yet", colspan="5"))),
                    cls="module-table",
                ),
                cls="module-list",
            ),
            cls="module-content",
        )
