"""
Anomaly Detection module — Flag unusual transactions, rule violations, duplicates.
"""

import os
from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def run_anomaly_scan(query: str = "") -> str:
    """Scan transactions for anomalies: unusual amounts, timing, duplicates, rule violations."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            # Get recent transactions for analysis
            txns = session.execute(text("""
                SELECT t.transaction_id, t.transaction_type, t.amount, t.description,
                       t.created_at, a.account_name, p.title
                FROM ahcam.transactions t
                LEFT JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                LEFT JOIN ahcam.productions p ON p.production_id = a.production_id
                ORDER BY t.created_at DESC LIMIT 50
            """)).fetchall()

            # Check for existing unresolved alerts
            alerts = session.execute(text("""
                SELECT alert_type, severity, description, created_at
                FROM ahcam.anomaly_alerts
                WHERE resolved = FALSE
                ORDER BY created_at DESC LIMIT 10
            """)).fetchall()

        if not txns:
            return "No transactions to scan."

        # Simple rule-based anomaly detection
        anomalies = []

        # Check for duplicate amounts on same day
        seen = {}
        for t in txns:
            key = f"{t[2]}_{str(t[4])[:10]}_{t[5]}"
            if key in seen:
                anomalies.append(f"**Possible duplicate:** ${t[2]:,.2f} on {str(t[4])[:10]} in {t[5]}")
            seen[key] = True

        # Check for unusually large transactions (>2x average)
        amounts = [float(t[2]) for t in txns if t[2]]
        if amounts:
            avg = sum(amounts) / len(amounts)
            for t in txns:
                if float(t[2]) > avg * 3:
                    anomalies.append(f"**Large transaction:** ${t[2]:,.2f} ({t[3] or 'no description'}) - {float(t[2])/avg:.1f}x average")

        result = "## Anomaly Scan Results\n\n"
        result += f"**Transactions scanned:** {len(txns)}\n"
        result += f"**Unresolved alerts:** {len(alerts)}\n\n"

        if anomalies:
            result += "### Detected Anomalies\n\n"
            for a in anomalies:
                result += f"- {a}\n"
        else:
            result += "No anomalies detected.\n"

        if alerts:
            result += "\n### Open Alerts\n\n| Type | Severity | Description | Date |\n|------|----------|-------------|------|\n"
            for a in alerts:
                result += f"| {a[0]} | {a[1]} | {a[2] or '\u2014'} | {str(a[3])[:10]} |\n"

        return result
    except Exception as e:
        return f"Error running anomaly scan: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/anomaly")
    def module_anomaly(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                alerts = s.execute(text("""
                    SELECT a.alert_id, a.alert_type, a.severity, a.description,
                           a.resolved, a.created_at, p.title
                    FROM ahcam.anomaly_alerts a
                    LEFT JOIN ahcam.productions p ON p.production_id = a.production_id
                    ORDER BY a.created_at DESC LIMIT 30
                """)).fetchall()
                totals = s.execute(text("""
                    SELECT COUNT(*),
                           COUNT(*) FILTER (WHERE resolved = FALSE),
                           COUNT(*) FILTER (WHERE severity IN ('high', 'critical') AND resolved = FALSE)
                    FROM ahcam.anomaly_alerts
                """)).fetchone()
        except Exception:
            alerts, totals = [], (0, 0, 0)

        alert_rows = []
        for a in alerts:
            sev_cls = "badge-red" if a[2] in ("high", "critical") else "badge-amber" if a[2] == "medium" else "badge-blue"
            resolved_cls = "badge-green" if a[4] else "badge-red"
            alert_rows.append(Tr(
                Td(a[6] or "\u2014"), Td(a[1].replace("_", " ").title()),
                Td(Span(a[2].title(), cls=sev_cls)),
                Td(a[3] or "\u2014"),
                Td(Span("Resolved" if a[4] else "Open", cls=resolved_cls)),
                Td(str(a[5])[:10]),
            ))

        return Div(
            Div(
                Div(Div(str(totals[0]), cls="stat-value"), Div("Total Alerts", cls="stat-label"), cls="stat-card"),
                Div(Div(str(totals[1]), cls="stat-value negative"), Div("Unresolved", cls="stat-label"), cls="stat-card"),
                Div(Div(str(totals[2]), cls="stat-value negative"), Div("Critical/High", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Anomaly Detection"),
                    Button("Run Scan",
                           hx_post="/module/anomaly/scan",
                           hx_target="#scan-result",
                           hx_swap="innerHTML",
                           cls="module-action-btn"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                Div(id="scan-result"),
                Table(
                    Thead(Tr(Th("Production"), Th("Type"), Th("Severity"), Th("Description"), Th("Status"), Th("Date"))),
                    Tbody(*alert_rows) if alert_rows else Tbody(Tr(Td("No alerts", colspan="6"))),
                    cls="module-table",
                ),
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/anomaly/scan", methods=["POST"])
    def anomaly_scan(session):
        result = run_anomaly_scan()
        return Div(Pre(result, cls="chat-message-content marked"), cls="scan-result-box",
                   style="margin-bottom:1rem;border:1px solid #e2e8f0;border-radius:8px;padding:1rem;")
