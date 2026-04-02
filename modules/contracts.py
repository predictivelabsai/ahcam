"""
Contracts module — AI-powered contract parsing.
Upload CAMA PDFs, extract waterfall rules, parties, and terms.
"""

from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def parse_contract_tool(contract_text: str) -> str:
    """AI-parse contract text to extract waterfall rules, parties, and key terms.
    Takes the text content of a contract and returns structured extraction."""
    import os
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
        model="grok-3-mini",
    )

    prompt = f"""Analyze this Collection Account Management Agreement (CAMA) or entertainment finance contract.
Extract the following in structured format:

1. **Parties**: List all parties with their roles (producer, financier, distributor, sales agent, etc.)
2. **Waterfall Rules**: Extract the recoupment waterfall as a priority-ordered list with:
   - Priority number
   - Recipient
   - Rule type (percentage, fixed, corridor, residual)
   - Percentage or fixed amount
   - Cap (if any)
   - Description
3. **Key Terms**: Important dates, conditions, territories, minimums

Contract text:
{contract_text[:8000]}

Return as structured markdown with tables."""

    response = llm.invoke(prompt)
    return response.content


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/contracts")
    def module_contracts(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                rows = s.execute(text("""
                    SELECT c.contract_id, c.contract_type, c.parsing_status, c.created_at,
                           p.title AS production
                    FROM ahcam.contracts c
                    LEFT JOIN ahcam.productions p ON p.production_id = c.production_id
                    ORDER BY c.created_at DESC LIMIT 20
                """)).fetchall()
                totals = s.execute(text("""
                    SELECT COUNT(*),
                           COUNT(*) FILTER (WHERE parsing_status = 'completed'),
                           COUNT(*) FILTER (WHERE parsing_status = 'pending')
                    FROM ahcam.contracts
                """)).fetchone()
        except Exception:
            rows, totals = [], (0, 0, 0)

        cards = []
        for r in rows:
            status_cls = "badge-green" if r[2] == "completed" else "badge-amber" if r[2] == "processing" else "badge-blue"
            cards.append(Div(
                Div(
                    Span(r[4] or "Unlinked", cls="deal-card-title"),
                    Span(r[2].title(), cls=status_cls),
                    style="display:flex;justify-content:space-between;align-items:center;",
                ),
                Div(f"{r[1].upper()} | {str(r[3])[:10]}", cls="deal-card-meta"),
                cls="deal-card",
                hx_get=f"/module/contract/{r[0]}",
                hx_target="#center-content",
                hx_swap="innerHTML",
            ))

        return Div(
            Div(
                Div(Div(str(totals[0]), cls="stat-value"), Div("Total Contracts", cls="stat-label"), cls="stat-card"),
                Div(Div(str(totals[1]), cls="stat-value"), Div("Parsed", cls="stat-label"), cls="stat-card"),
                Div(Div(str(totals[2]), cls="stat-value"), Div("Pending", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Contract Parser"),
                    Button("+ Parse Contract",
                           hx_get="/module/contract/new",
                           hx_target="#center-content",
                           hx_swap="innerHTML",
                           cls="module-action-btn"),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                *cards if cards else [Div("No contracts uploaded yet. Upload a CAMA or distribution agreement to get started.", cls="empty-state")],
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/contract/new")
    def contract_new_form(session):
        pool = get_pool()
        with pool.get_session() as s:
            prods = s.execute(text("SELECT production_id, title FROM ahcam.productions ORDER BY title")).fetchall()
        return Div(
            H3("Parse Contract"),
            P("Paste the contract text below for AI-powered extraction of waterfall rules, parties, and key terms.",
              style="color:#64748b;font-size:0.85rem;margin-bottom:1rem;"),
            Form(
                Div(
                    Div(Select(Option("Select Production (optional)", value=""),
                               *[Option(p[1], value=str(p[0])) for p in prods],
                               name="production_id"), cls="form-group"),
                    Div(Select(Option("CAMA", value="cama"), Option("Distribution", value="distribution"),
                               Option("Sales", value="sales"), Option("Finance", value="finance"),
                               name="contract_type"), cls="form-group"),
                    cls="form-row",
                ),
                Div(Textarea(name="contract_text", placeholder="Paste contract text here...", rows="12", required=True), cls="form-group"),
                Button("Parse with AI", type="submit", cls="module-action-btn"),
                hx_post="/module/contract/parse",
                hx_target="#center-content",
                hx_swap="innerHTML",
                cls="module-form",
            ),
            cls="module-content",
        )

    @rt("/module/contract/parse", methods=["POST"])
    def contract_parse(session, contract_text: str, production_id: str = "",
                       contract_type: str = "cama"):
        import hashlib
        try:
            # Parse with AI
            result = parse_contract_tool(contract_text)

            # Store in DB
            file_hash = hashlib.sha256(contract_text.encode()).hexdigest()
            pool = get_pool()
            with pool.get_session() as s:
                s.execute(text("""
                    INSERT INTO ahcam.contracts
                        (production_id, contract_type, file_hash, parsed_rules, parsing_status, parsed_at, created_by)
                    VALUES (:pid, :ctype, :fhash, :rules::jsonb, 'completed', NOW(), :uid)
                """), {
                    "pid": production_id or None,
                    "ctype": contract_type,
                    "fhash": file_hash,
                    "rules": f'{{"raw_extraction": {repr(result[:2000])}}}',
                    "uid": session.get("user_id"),
                })
        except Exception as e:
            return Div(f"Error parsing contract: {e}", cls="module-error")

        return Div(
            H3("Contract Parsed Successfully"),
            Div(Pre(result, cls="chat-message-content marked"), cls="contract-result"),
            Button("\u2190 Back to Contracts",
                   hx_get="/module/contracts",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="back-btn"),
            cls="module-content",
        )

    @rt("/module/contract/{contract_id}")
    def contract_detail(contract_id: str, session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                row = s.execute(text("""
                    SELECT c.contract_id, c.contract_type, c.parsing_status, c.parsed_rules,
                           c.created_at, p.title
                    FROM ahcam.contracts c
                    LEFT JOIN ahcam.productions p ON p.production_id = c.production_id
                    WHERE c.contract_id = :cid
                """), {"cid": contract_id}).fetchone()
        except Exception:
            row = None
        if not row:
            return Div("Contract not found.", cls="module-error")
        return Div(
            H3(f"Contract: {row[5] or 'Unlinked'} ({row[1].upper()})"),
            Div(
                Div(Div("Status", cls="detail-label"), Div(row[2].title(), cls="detail-value"), cls="detail-item"),
                Div(Div("Created", cls="detail-label"), Div(str(row[4])[:10], cls="detail-value"), cls="detail-item"),
                cls="detail-grid",
            ),
            Div(
                H4("Parsed Results"),
                Pre(str(row[3]) if row[3] else "No results", cls="contract-result-pre"),
                cls="detail-section",
            ),
            Button("\u2190 Back",
                   hx_get="/module/contracts",
                   hx_target="#center-content",
                   hx_swap="innerHTML",
                   cls="back-btn"),
            cls="module-content",
        )
