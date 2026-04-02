"""
Revenue Forecasting module — AI-predicted future sales/royalties.
"""

import os
from fasthtml.common import *
from sqlalchemy import text
from utils.db import get_pool


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def generate_forecast(production_id: str) -> str:
    """Generate AI revenue forecast for a production based on historical data and comparables."""
    try:
        pool = get_pool()
        with pool.get_session() as session:
            prod = session.execute(text("""
                SELECT title, genre, budget, territory, status
                FROM ahcam.productions WHERE production_id = :pid
            """), {"pid": production_id}).fetchone()

            if not prod:
                return f"Production `{production_id}` not found."

            # Get historical transaction data
            txn_data = session.execute(text("""
                SELECT t.transaction_type, t.amount, t.created_at
                FROM ahcam.transactions t
                JOIN ahcam.collection_accounts a ON a.account_id = t.account_id
                WHERE a.production_id = :pid AND t.transaction_type = 'inflow'
                ORDER BY t.created_at
            """), {"pid": production_id}).fetchall()

        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            api_key=os.getenv("XAI_API_KEY"),
            base_url="https://api.x.ai/v1",
            model="grok-3-mini",
        )

        historical = ""
        if txn_data:
            historical = "\n".join([f"- {str(t[2])[:10]}: ${t[1]:,.2f}" for t in txn_data[:20]])

        prompt = f"""You are a film finance analyst. Generate a revenue forecast for this production:

Title: {prod[0]}
Genre: {prod[1] or 'Unknown'}
Budget: ${prod[2]:,.0f} if {prod[2]} else 'Unknown'
Territory: {prod[3] or 'Global'}
Status: {prod[4]}

Historical inflows:
{historical or 'No historical data yet'}

Provide:
1. 12-month revenue projection by quarter (Q1-Q4)
2. Territory breakdown (top 5 territories)
3. Revenue sources (theatrical, home video, streaming, TV sales)
4. Confidence level (low/medium/high)
5. Key assumptions and risks

Format as structured markdown with tables."""

        response = llm.invoke(prompt)
        return response.content

    except Exception as e:
        return f"Error generating forecast: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/module/forecasting")
    def module_forecasting(session):
        try:
            pool = get_pool()
            with pool.get_session() as s:
                forecasts = s.execute(text("""
                    SELECT f.forecast_id, f.territory, f.predicted_amount, f.created_at,
                           p.title
                    FROM ahcam.revenue_forecasts f
                    LEFT JOIN ahcam.productions p ON p.production_id = f.production_id
                    ORDER BY f.created_at DESC LIMIT 20
                """)).fetchall()
                prods = s.execute(text("""
                    SELECT production_id, title FROM ahcam.productions ORDER BY title
                """)).fetchall()
        except Exception:
            forecasts, prods = [], []

        cards = []
        for f in forecasts:
            cards.append(Div(
                Div(
                    Span(f[4] or "\u2014", cls="deal-card-title"),
                    Span(f"${f[2]:,.0f}" if f[2] else "\u2014", cls="badge-green"),
                    style="display:flex;justify-content:space-between;align-items:center;",
                ),
                Div(f"{f[1] or 'Global'} | {str(f[3])[:10]}", cls="deal-card-meta"),
                cls="deal-card",
            ))

        gen_buttons = []
        for p in prods:
            gen_buttons.append(
                Button(f"Forecast: {p[1]}",
                       hx_post=f"/module/forecast/generate/{p[0]}",
                       hx_target="#forecast-result",
                       hx_swap="innerHTML",
                       cls="suggestion-btn",
                       style="margin:0.25rem;")
            )

        return Div(
            Div(H3("Revenue Forecasting"), cls="module-header"),
            Div(*gen_buttons, style="margin-bottom:1rem;") if gen_buttons else "",
            Div(id="forecast-result"),
            Div(
                *cards if cards else [Div("No forecasts generated yet. Select a production above.", cls="empty-state")],
                cls="module-list",
            ),
            cls="module-content",
        )

    @rt("/module/forecast/generate/{production_id}", methods=["POST"])
    def forecast_generate(production_id: str, session):
        result = generate_forecast(production_id)
        return Div(Pre(result, cls="chat-message-content marked"), cls="forecast-result-box",
                   style="margin-bottom:1rem;border:1px solid #e2e8f0;border-radius:8px;padding:1rem;")
