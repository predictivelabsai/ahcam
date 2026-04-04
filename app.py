"""
AHCAM — Ashland Hill Collection Account Management

3-pane agentic UI for film & entertainment collection account management.

Left pane:  Navigation sidebar (10 modules, auth, settings)
Center:     Chat (WebSocket streaming) + module content views
Right:      AI thinking trace / detail canvas (toggled)

Launch:  python app.py          # port 5011
         uvicorn app:app --port 5011 --reload
"""

import os
import sys
import uuid as _uuid
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fasthtml.common import *

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LangGraph Agent
# ---------------------------------------------------------------------------

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = (
    "You are AHCAM, an AI assistant for Ashland Hill Collection Account Management — "
    "a platform that manages collection accounts for film & entertainment finance. "
    "You help collection account managers, producers, financiers, and distributors with: "
    "collection account management, waterfall/recoupment calculations, transaction tracking, "
    "disbursement processing, contract parsing, revenue forecasting, and anomaly detection. "
    "Be concise and use markdown formatting with tables where appropriate. "
    "When users ask about productions, use production tools. "
    "When users ask about stakeholders, use stakeholder tools. "
    "When users ask about accounts or balances, use account tools. "
    "When users ask about waterfall rules or recoupment, use waterfall tools. "
    "Users can also type structured commands: production:list, account:list, waterfall:run PROD_ID, help."
)

llm = ChatOpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
    model="grok-3-mini",
    streaming=True,
)


# ---------------------------------------------------------------------------
# Agent Tools (imported from modules)
# ---------------------------------------------------------------------------

from modules.productions import search_productions, get_production_detail
from modules.stakeholders import search_stakeholders
from modules.collections import search_accounts, get_account_balance
from modules.waterfall import get_waterfall_rules, run_waterfall
from modules.transactions import search_transactions
from modules.disbursements import get_disbursement_status, run_disbursements
from modules.contracts import parse_contract_tool
from modules.reports import generate_report, get_recoupment_position
from modules.forecasting import generate_forecast
from modules.anomaly import run_anomaly_scan
from modules.crm import search_crm_deals, search_crm_contacts
from modules.documents import search_documents

TOOLS = [
    search_productions, get_production_detail,
    search_stakeholders,
    search_accounts, get_account_balance,
    get_waterfall_rules, run_waterfall,
    search_transactions,
    get_disbursement_status, run_disbursements,
    parse_contract_tool,
    generate_report, get_recoupment_position,
    generate_forecast,
    run_anomaly_scan,
    search_crm_deals, search_crm_contacts,
    search_documents,
]

langgraph_agent = create_react_agent(model=llm, tools=TOOLS, prompt=SYSTEM_PROMPT)


# ---------------------------------------------------------------------------
# Google OAuth (optional — gracefully skip if no creds)
# ---------------------------------------------------------------------------

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
_oauth_enabled = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

_authlib_oauth = None
if _oauth_enabled:
    from authlib.integrations.starlette_client import OAuth as AuthlibOAuth
    _authlib_oauth = AuthlibOAuth()
    _authlib_oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

_GOOGLE_SVG = """<svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
<path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
<path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
<path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9s.38 1.572.957 3.042l3.007-2.332z" fill="#FBBC05"/>
<path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
</svg>"""


def _google_btn(label: str):
    return A(NotStr(_GOOGLE_SVG), label, href="/oauth/google", cls="google-btn")


# ---------------------------------------------------------------------------
# Command Interceptor
# ---------------------------------------------------------------------------

async def _command_interceptor(msg: str, session) -> str | None:
    """Route structured commands before sending to AI agent."""
    cmd = msg.strip().lower()
    parts = cmd.split(maxsplit=1)
    first = parts[0] if parts else ""
    rest = parts[1] if len(parts) > 1 else ""

    if cmd == "help":
        return (
            "## AHCAM Commands\n\n"
            "| Command | Description |\n"
            "|---------|-------------|\n"
            "| `production:list` | List all productions |\n"
            "| `production:PROD_ID` | View production details |\n"
            "| `stakeholder:search NAME` | Search stakeholders |\n"
            "| `account:list` | List collection accounts |\n"
            "| `account:ACCOUNT_ID` | View account balance |\n"
            "| `waterfall:list` | List productions with waterfall rules |\n"
            "| `waterfall:PROD_ID` | View waterfall rules |\n"
            "| `waterfall:run PROD_ID` | Run waterfall calculation |\n"
            "| `transaction:list` | View transaction ledger |\n"
            "| `disbursement:list` | View disbursements |\n"
            "| `disbursement:run PROD_ID` | Process disbursements |\n"
            "| `contract:upload` | Parse a contract with AI |\n"
            "| `report:PROD_ID` | Generate collection report |\n"
            "| `forecast:PROD_ID` | Revenue forecast |\n"
            "| `anomaly:scan` | Run anomaly detection |\n"
            "| `help` | Show this help |\n"
        )

    if first == "production:list" or cmd == "productions":
        return search_productions(rest)
    if first.startswith("production:") and len(first) > 11:
        return get_production_detail(first[11:])

    if first == "stakeholder:search":
        return search_stakeholders(rest) if rest else "Usage: `stakeholder:search NAME`"

    if first == "account:list" or cmd == "accounts":
        return search_accounts(rest)
    if first.startswith("account:") and first != "account:list" and len(first) > 8:
        return get_account_balance(first[8:])

    if first == "waterfall:list":
        return get_waterfall_rules("") if not rest else get_waterfall_rules(rest)
    if first == "waterfall:run":
        return run_waterfall(rest) if rest else "Usage: `waterfall:run PRODUCTION_ID`"
    if first.startswith("waterfall:") and first != "waterfall:list" and first != "waterfall:run" and len(first) > 10:
        return get_waterfall_rules(first[10:])

    if first == "transaction:list" or cmd == "transactions":
        return search_transactions(rest)

    if first == "disbursement:list" or cmd == "disbursements":
        return get_disbursement_status(rest)
    if first == "disbursement:run":
        return run_disbursements(rest) if rest else "Usage: `disbursement:run PRODUCTION_ID`"

    if first == "contract:upload":
        return (
            "Navigate to **Contracts** in the sidebar to upload and parse a contract.\n\n"
            "Or paste contract text directly in chat and ask me to extract waterfall rules."
        )

    if first.startswith("report:") and len(first) > 7:
        return generate_report(first[7:])
    if first == "report:list" or cmd == "reports":
        return "Navigate to **Reports** in the sidebar to generate collection account reports."

    if first.startswith("forecast:") and len(first) > 9:
        return generate_forecast(first[9:])
    if first == "forecast:list" or cmd == "forecasts":
        return "Navigate to **Forecasting** in the sidebar to generate revenue forecasts."

    if first == "anomaly:scan" or cmd == "anomalies":
        return run_anomaly_scan(rest)

    return None


# ---------------------------------------------------------------------------
# FastHTML App
# ---------------------------------------------------------------------------

app, rt = fast_app(
    exts="ws",
    secret_key=os.getenv("JWT_SECRET", "ahcam-dev-secret"),
    hdrs=(
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js"),
    ),
)

from utils.agui import setup_agui, get_chat_styles, StreamingCommand, list_conversations

agui = setup_agui(app, langgraph_agent, command_interceptor=_command_interceptor)


@rt("/api/health")
def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Layout CSS
# ---------------------------------------------------------------------------

APP_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { height: 100vh; overflow: hidden; }

/* === 3-Pane Grid === */
.app-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  height: 100vh;
  transition: grid-template-columns 0.3s ease;
}

.app-layout .right-pane { display: none; }

.app-layout.right-open {
  grid-template-columns: 260px 1fr 380px;
}

.app-layout.right-open .right-pane { display: flex; }

/* === Left Pane (Sidebar) === */
.left-pane {
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-logo {
  padding: 1.25rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sidebar-logo-icon {
  width: 36px; height: 36px;
  background: linear-gradient(135deg, #0066cc, #004d99);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: 0.9rem;
}

.sidebar-logo-text {
  font-size: 0.9rem; font-weight: 700; color: #1e293b;
}

.sidebar-logo-sub {
  font-size: 0.65rem; color: #64748b; margin-top: 0.1rem;
}

.sidebar-section {
  padding: 0.25rem 0;
}
.sidebar-section.collapsible { padding: 0; }

.sidebar-section-title {
  padding: 0 1rem 0.5rem;
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
}

.sidebar-item {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s;
  text-decoration: none;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
}

.sidebar-item:hover { background: #e2e8f0; color: #1e293b; }
.sidebar-item.active { background: #dbeafe; color: #0066cc; font-weight: 600; }

.sidebar-item-icon {
  width: 18px; height: 18px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.sidebar-badge {
  margin-left: auto;
  background: #0066cc;
  color: white;
  font-size: 0.6rem;
  padding: 0.1rem 0.4rem;
  border-radius: 1rem;
  font-weight: 600;
}

.sidebar-footer {
  padding: 0.5rem 0;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

/* === Center Pane === */
.center-pane {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  position: relative;
}

.center-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  background: #ffffff;
  min-height: 50px;
}

.center-header h2 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.center-chat { flex: 1; overflow: hidden; }

.header-btn {
  padding: 0.4rem 0.6rem;
  background: none; border: 1px solid #e2e8f0;
  border-radius: 6px; cursor: pointer; font-size: 0.75rem; color: #64748b;
  transition: all 0.15s;
}
.header-btn:hover { background: #f1f5f9; color: #1e293b; }

#center-content {
  display: none;
  overflow-y: auto;
  padding: 1.5rem;
  position: absolute;
  top: 50px;
  left: 0;
  right: 0;
  bottom: 0;
  background: #ffffff;
  z-index: 10;
}

/* === Right Pane (Canvas) === */
.right-pane {
  background: #f8fafc;
  border-left: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.right-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0;
}

.right-header h3 { font-size: 0.85rem; font-weight: 600; color: #1e293b; margin: 0; }

.right-tabs {
  display: flex; border-bottom: 1px solid #e2e8f0;
}

.right-tab {
  flex: 1; padding: 0.5rem; font-size: 0.75rem; text-align: center;
  background: none; border: none; cursor: pointer; color: #64748b;
  border-bottom: 2px solid transparent;
}
.right-tab.active { color: #0066cc; border-bottom-color: #0066cc; font-weight: 600; }

.right-content { flex: 1; overflow-y: auto; padding: 0.75rem; }

.trace-entry {
  padding: 0.4rem 0.6rem; margin-bottom: 0.25rem;
  border-radius: 0.375rem; font-size: 0.75rem;
}
.trace-label { font-weight: 600; }
.trace-detail { color: #64748b; margin-left: 0.5rem; }
.trace-run-start { background: #dbeafe; color: #1e40af; }
.trace-run-end { background: #dcfce7; color: #166534; }
.trace-tool-active { background: #fef3c7; color: #92400e; }
.trace-tool-done { background: #f1f5f9; color: #64748b; }

/* === Auth Pages === */
.auth-container {
  max-width: 400px; margin: 10vh auto; padding: 2rem;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
}
.auth-form { display: flex; flex-direction: column; gap: 0.75rem; }
.auth-form input {
  padding: 0.6rem 0.8rem; border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 0.85rem; width: 100%; box-sizing: border-box;
}
.auth-form input:focus { outline: none; border-color: #0066cc; box-shadow: 0 0 0 3px rgba(0,102,204,0.1); }
.auth-btn {
  padding: 0.6rem; background: #0066cc; color: white; border: none;
  border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.85rem;
}
.auth-btn:hover { background: #0052a3; }
.auth-link { text-align: center; font-size: 0.8rem; }
.auth-link a { color: #0066cc; }

/* === Module Content === */
.module-content { padding: 0.5rem 0; }

.stat-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem; margin-bottom: 1.5rem;
}
.stat-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 1rem; text-align: center;
}
.stat-value { font-size: 1.5rem; font-weight: 700; color: #1e293b; }
.stat-value.positive { color: #16a34a; }
.stat-value.negative { color: #dc2626; }
.stat-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }
.stat-highlight { background: #dbeafe; color: #1e40af; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600; margin-bottom: 1rem; }

.deal-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 0.75rem 1rem; margin-bottom: 0.5rem; cursor: pointer;
  transition: all 0.15s;
}
.deal-card:hover { border-color: #0066cc; box-shadow: 0 2px 8px rgba(0,102,204,0.08); }
.deal-card-title { font-weight: 600; font-size: 0.85rem; color: #1e293b; }
.deal-card-meta { font-size: 0.75rem; color: #64748b; margin-top: 0.25rem; }

.status-pill {
  display: inline-block; padding: 0.15rem 0.5rem; border-radius: 1rem;
  font-size: 0.7rem; font-weight: 500;
}
.status-development { background: #dbeafe; color: #1e40af; }
.status-pre_production { background: #fef3c7; color: #92400e; }
.status-production { background: #dcfce7; color: #166534; }
.status-post_production { background: #e0e7ff; color: #3730a3; }
.status-completed { background: #f1f5f9; color: #475569; }
.status-released { background: #dcfce7; color: #166534; }

.module-action-btn {
  padding: 0.45rem 0.9rem; background: #0066cc; color: white; border: none;
  border-radius: 8px; font-size: 0.8rem; font-weight: 500; cursor: pointer;
}
.module-action-btn:hover { background: #0052a3; }

.back-btn {
  margin-top: 1rem; padding: 0.4rem 0.8rem; background: none;
  border: 1px solid #e2e8f0; border-radius: 6px; font-size: 0.8rem;
  color: #64748b; cursor: pointer;
}
.back-btn:hover { background: #f1f5f9; }

.module-table {
  width: 100%; border-collapse: collapse; font-size: 0.8rem;
}
.module-table th {
  background: #f1f5f9; padding: 0.5rem 0.75rem; text-align: left;
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em;
  color: #64748b; border-bottom: 2px solid #e2e8f0;
}
.module-table td {
  padding: 0.5rem 0.75rem; border-bottom: 1px solid #f1f5f9; color: #1e293b;
}
.module-table tr:hover td { background: #f8fafc; }

.positive { color: #16a34a; }
.negative { color: #dc2626; }

.detail-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem; margin-bottom: 1rem;
}
.detail-item { padding: 0.5rem 0; }
.detail-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.detail-value { font-size: 0.9rem; font-weight: 500; color: #1e293b; margin-top: 0.15rem; }
.detail-section { margin-top: 1rem; }

.form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 0.75rem; }
.form-group { display: flex; flex-direction: column; }
.form-group input, .form-group select, .form-group textarea {
  padding: 0.5rem 0.75rem; border: 1px solid #e2e8f0; border-radius: 6px;
  font-size: 0.8rem; font-family: inherit;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus {
  outline: none; border-color: #0066cc; box-shadow: 0 0 0 3px rgba(0,102,204,0.1);
}
.module-form { margin-top: 1rem; }
.module-error { color: #dc2626; padding: 1rem; }
.empty-state { color: #94a3b8; text-align: center; padding: 2rem; font-size: 0.85rem; }

.waterfall-result-pre, .contract-result-pre {
  background: #f8fafc; padding: 1rem; border-radius: 8px;
  font-size: 0.8rem; white-space: pre-wrap; border: 1px solid #e2e8f0;
}

/* === Help Expanders === */
.help-section { padding: 0.5rem 0; }
.help-toggle {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.35rem 1rem; font-size: 0.75rem; color: #64748b;
  background: none; border: none; cursor: pointer; width: 100%;
  text-align: left; transition: color 0.15s;
}
.help-toggle:hover { color: #1e293b; }
.help-cnt { margin-left: auto; font-size: 0.65rem; background: #e2e8f0; padding: 0.1rem 0.35rem; border-radius: 0.75rem; }
.help-arrow { font-size: 0.6rem; transition: transform 0.2s; }
.help-toggle.open .help-arrow { transform: rotate(90deg); }
.help-list { display: none; padding: 0 0 0 1.5rem; }
.help-list.open { display: block; }
.help-item {
  display: block; padding: 0.25rem 0.5rem; font-size: 0.7rem;
  color: #0066cc; background: none; border: none; cursor: pointer;
  font-family: ui-monospace, monospace; text-align: left; width: 100%;
}
.help-item:hover { background: #dbeafe; border-radius: 4px; }

/* === New Chat Button === */
.new-chat-btn {
  width: calc(100% - 2rem); margin: 0.75rem 1rem 0.25rem;
  padding: 0.5rem; background: #0066cc; color: white; border: none;
  border-radius: 8px; font-size: 0.8rem; font-weight: 500; cursor: pointer;
}
.new-chat-btn:hover { background: #0052a3; }

/* === Conversation list === */
.conv-section { margin-top: 0.5rem; max-height: 200px; overflow-y: auto; }
.conv-item {
  display: block; padding: 0.35rem 1rem; font-size: 0.75rem;
  color: #475569; cursor: pointer; border: none; background: none;
  text-align: left; width: 100%; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; transition: background 0.15s;
}
.conv-item:hover { background: #e2e8f0; }

/* === Collapsible Sections === */
.section-toggle {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 1rem; font-size: 0.7rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: #94a3b8; background: none; border: none; cursor: pointer;
  width: 100%; text-align: left; transition: color 0.15s;
}
.section-toggle:hover { color: #64748b; }
.section-arrow { margin-left: auto; transition: transform 0.2s; }
.section-toggle.open .section-arrow { transform: rotate(180deg); }
.section-body { display: none; }
.section-body.open { display: block; }

/* === Kanban Board === */
.kanban-board { display: flex; gap: 0.75rem; overflow-x: auto; padding-bottom: 0.5rem; }
.kanban-col { min-width: 180px; flex: 1; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
.kanban-col-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.5rem 0.75rem; border-bottom: 1px solid #e2e8f0;
}
.kanban-col-title { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; color: #64748b; }
.kanban-col-count { font-size: 0.65rem; background: #e2e8f0; padding: 0.1rem 0.4rem; border-radius: 1rem; color: #475569; }
.kanban-col-body { padding: 0.5rem; display: flex; flex-direction: column; gap: 0.4rem; min-height: 60px; }
.kanban-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 6px;
  padding: 0.5rem 0.6rem; cursor: pointer; transition: all 0.15s;
}
.kanban-card:hover { border-color: #0066cc; box-shadow: 0 2px 6px rgba(0,102,204,0.1); }
.kanban-card-title { font-size: 0.75rem; font-weight: 600; color: #1e293b; }
.kanban-card-meta { font-size: 0.65rem; color: #64748b; margin-top: 0.15rem; }

/* === View Toggle === */
.view-toggle { display: flex; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; }
.view-toggle-btn {
  padding: 0.3rem 0.6rem; font-size: 0.7rem; border: none;
  background: #fff; color: #64748b; cursor: pointer;
}
.view-toggle-btn.active { background: #0066cc; color: #fff; }
.view-toggle-btn:not(.active):hover { background: #f1f5f9; }

/* === Google OAuth Button === */
.google-btn {
  display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  padding: 0.6rem; background: #4285f4; color: #fff; text-decoration: none;
  border-radius: 8px; font-weight: 600; font-size: 0.85rem; width: 100%;
  box-sizing: border-box;
}
.google-btn:hover { background: #3367d6; color: #fff; }
.google-btn svg { flex-shrink: 0; }
.divider {
  text-align: center; color: #94a3b8; font-size: 0.75rem;
  margin: 0.75rem 0; position: relative;
}
.divider::before, .divider::after {
  content: ''; position: absolute; top: 50%; width: 40%;
  height: 1px; background: #e2e8f0;
}
.divider::before { left: 0; }
.divider::after { right: 0; }

/* === Chat History Search === */
.conv-search-input {
  width: calc(100% - 2rem); margin: 0.25rem 1rem; padding: 0.3rem 0.6rem;
  border: 1px solid #e2e8f0; border-radius: 6px; font-size: 0.7rem;
  color: #475569; background: #fff;
}
.conv-search-input:focus { outline: none; border-color: #0066cc; }
.conv-item.hidden { display: none; }
.conv-more-btn {
  display: block; width: calc(100% - 2rem); margin: 0.25rem 1rem; padding: 0.3rem;
  font-size: 0.7rem; color: #0066cc; background: none; border: 1px solid #e2e8f0;
  border-radius: 6px; cursor: pointer; text-align: center;
}
.conv-more-btn:hover { background: #f1f5f9; }

/* === Profile Form === */
.profile-form { max-width: 400px; }
.profile-form .form-group { margin-bottom: 0.75rem; }
.profile-form label { font-size: 0.75rem; color: #64748b; font-weight: 600; display: block; margin-bottom: 0.25rem; }

/* === Document Viewer Pane === */
.doc-viewer-pane {
  position: fixed; top: 0; right: -50vw; width: 50vw; height: 100vh;
  background: #fff; border-left: 1px solid #e2e8f0;
  box-shadow: -4px 0 24px rgba(0,0,0,.08); z-index: 200;
  display: flex; flex-direction: column;
  transition: right 0.3s ease;
}
.doc-viewer-pane.open { right: 0; }
.doc-viewer-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; gap: 0.5rem;
}
.doc-viewer-iframe { flex: 1; width: 100%; border: none; }

/* === Responsive === */
@media (max-width: 768px) {
  .app-layout { grid-template-columns: 1fr !important; }
  .left-pane { display: none; }
  .right-pane { display: none; }
  .kanban-board { flex-direction: column; }
  .doc-viewer-pane { width: 100vw; right: -100vw; }
}
"""

LAYOUT_JS = """
function toggleRightPane() {
    var layout = document.querySelector('.app-layout');
    layout.classList.toggle('right-open');
}

function toggleGroup(catId) {
    var list = document.getElementById(catId);
    if (!list) return;
    list.classList.toggle('open');
    var btn = list.previousElementSibling;
    if (btn) btn.classList.toggle('open');
}

function toggleSection(sectionId) {
    var sec = document.getElementById(sectionId);
    if (!sec) return;
    sec.classList.toggle('open');
    var btn = sec.previousElementSibling;
    if (btn) btn.classList.toggle('open');
}

function fillChat(cmd) {
    if (window._aguiProcessing) return;
    showChat();
    setTimeout(function() {
        var ta = document.getElementById('chat-input');
        if (ta) { ta.value = cmd; ta.focus(); }
    }, 100);
}

function showTab(tabName) {
    document.querySelectorAll('.right-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('[data-tab]').forEach(function(c) { c.style.display = 'none'; });
    var tab = document.querySelector('[data-tab-btn="'+tabName+'"]');
    var content = document.querySelector('[data-tab="'+tabName+'"]');
    if (tab) tab.classList.add('active');
    if (content) content.style.display = 'block';
}

function loadModule(btn, path, title) {
    var container = document.getElementById('center-content');
    var chatContainer = document.getElementById('center-chat');
    if (container) { container.style.display = 'block'; container.style.flex = '1'; container.style.overflow = 'auto'; }
    if (chatContainer) chatContainer.style.display = 'none';
    htmx.ajax('GET', path, {target: '#center-content', swap: 'innerHTML'});
    var h = document.getElementById('center-title');
    if (h) h.textContent = title;
    document.querySelectorAll('.sidebar-item').forEach(function(i) { i.classList.remove('active'); });
    if (btn) btn.classList.add('active');
}

function showChat() {
    var container = document.getElementById('center-content');
    var chatContainer = document.getElementById('center-chat');
    if (container) container.style.display = 'none';
    if (chatContainer) chatContainer.style.display = 'block';
    var h = document.getElementById('center-title');
    if (h) h.textContent = 'AI Assistant';
    document.querySelectorAll('.sidebar-item').forEach(function(i) { i.classList.remove('active'); });
    var chatBtn = document.getElementById('nav-chat');
    if (chatBtn) chatBtn.classList.add('active');
}

function showMoreHistory() {
    var hidden = document.querySelectorAll('.conv-item.hidden');
    hidden.forEach(function(el) { el.classList.remove('hidden'); });
    var btn = document.getElementById('conv-more-btn');
    if (btn) btn.style.display = 'none';
    var search = document.getElementById('conv-search');
    if (search) search.style.display = 'block';
}

function filterHistory(q) {
    var items = document.querySelectorAll('.conv-item');
    q = q.toLowerCase();
    items.forEach(function(el) {
        if (!q || el.textContent.toLowerCase().indexOf(q) >= 0) {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });
}
"""


# ---------------------------------------------------------------------------
# Sidebar icons (SVG)
# ---------------------------------------------------------------------------

_ICONS = {
    "chat": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>',
    "productions": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/><line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="7" x2="22" y2="7"/><line x1="17" y1="17" x2="22" y2="17"/></svg>',
    "stakeholders": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
    "accounts": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
    "waterfall": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>',
    "transactions": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
    "disbursements": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/></svg>',
    "contracts": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "reports": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>',
    "forecasting": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "anomaly": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "crm": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>',
    "documents": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "guide": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>',
    "profile": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "templates": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>',
    "chevron": '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>',
    "logout": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
}


def _icon(name):
    return NotStr(_ICONS.get(name, ""))


# ---------------------------------------------------------------------------
# Layout Components
# ---------------------------------------------------------------------------

def _sidebar_item(icon_name, label, onclick="", item_id="", active=False):
    return Button(
        Span(_icon(icon_name), cls="sidebar-item-icon"),
        label,
        cls=f"sidebar-item {'active' if active else ''}",
        onclick=onclick,
        id=item_id,
    )


# ---------------------------------------------------------------------------
# Sidebar Help Commands
# ---------------------------------------------------------------------------

_HELP_CATEGORIES = [
    ("Account Operations", [
        ("account:list", "List collection accounts"),
        ("transaction:list", "Transaction ledger"),
        ("disbursement:list", "View disbursements"),
    ]),
    ("Waterfall & Rules", [
        ("waterfall:list", "List waterfall rules"),
        ("production:list", "List productions"),
        ("stakeholder:search", "Search stakeholders"),
    ]),
    ("AI Analysis", [
        ("contract:upload", "Parse contract with AI"),
        ("anomaly:scan", "Run anomaly detection"),
    ]),
]


def _help_expanders():
    groups = []
    for cat_name, items in _HELP_CATEGORIES:
        cat_id = f"help-{cat_name.lower().replace(' ', '-').replace('&', '')}"
        toggle_btn = Button(
            cat_name,
            Span(f"{len(items)}", cls="help-cnt"),
            Span(">", cls="help-arrow"),
            cls="help-toggle",
            onclick=f"toggleGroup('{cat_id}')",
        )
        tool_items = [
            Button(cmd, cls="help-item", onclick=f"fillChat({repr(cmd)})", title=desc)
            for cmd, desc in items
        ]
        tool_list = Div(*tool_items, cls="help-list", id=cat_id)
        groups.append(toggle_btn)
        groups.append(tool_list)
    return Div(*groups, cls="help-section")


def _section_toggle(label, section_id, icon_name=None):
    """Collapsible section header for sidebar."""
    return Button(
        Span(_icon(icon_name), cls="sidebar-item-icon") if icon_name else "",
        label,
        Span(_icon("chevron"), cls="section-arrow"),
        cls="section-toggle",
        onclick=f"toggleSection('{section_id}')",
    )


def _left_pane(user=None):
    return Div(
        Div(
            Div("AH", cls="sidebar-logo-icon"),
            Div(
                Div("Ashland Hill", cls="sidebar-logo-text"),
                Div("Collection Account Mgmt", cls="sidebar-logo-sub"),
            ),
            cls="sidebar-logo",
        ),
        # Scrollable middle section
        Div(
            # Chat controls
            Div(
                Button("+ New Chat", cls="new-chat-btn", onclick="window.location.href='/?new=1'"),
                _sidebar_item("chat", "AI Assistant", "showChat()", item_id="nav-chat", active=True),
                Div(
                    Div("Recent Chats", cls="sidebar-section-title"),
                    Div(id="conv-list", hx_get="/agui-conv/list", hx_trigger="load", hx_swap="innerHTML"),
                    cls="conv-section",
                ),
                cls="sidebar-section",
            ),
            # CRM + Documents (always visible)
            Div(
                _sidebar_item("crm", "CRM", "loadModule(this,'/module/crm', 'CRM')", item_id="nav-crm"),
                _sidebar_item("documents", "Documents", "loadModule(this,'/module/documents', 'Documents')", item_id="nav-documents"),
                cls="sidebar-section",
                style="padding-top:0;",
            ),
            # Financing OS (collapsed by default)
            Div(
                _section_toggle("Financing OS", "sec-financing"),
                Div(
                    _sidebar_item("productions", "Productions", "loadModule(this,'/module/productions', 'Productions')", item_id="nav-productions"),
                    _sidebar_item("stakeholders", "Stakeholders", "loadModule(this,'/module/stakeholders', 'Stakeholders')", item_id="nav-stakeholders"),
                    _sidebar_item("accounts", "Collection Accounts", "loadModule(this,'/module/accounts', 'Collection Accounts')", item_id="nav-accounts"),
                    _sidebar_item("waterfall", "Waterfall Engine", "loadModule(this,'/module/waterfall', 'Waterfall Engine')", item_id="nav-waterfall"),
                    _sidebar_item("transactions", "Transactions", "loadModule(this,'/module/transactions', 'Transactions')", item_id="nav-transactions"),
                    _sidebar_item("disbursements", "Disbursements", "loadModule(this,'/module/disbursements', 'Disbursements')", item_id="nav-disbursements"),
                    cls="section-body", id="sec-financing",
                ),
                cls="sidebar-section collapsible",
            ),
            # AI Tools (collapsed by default)
            Div(
                _section_toggle("AI Tools", "sec-ai-tools"),
                Div(
                    _sidebar_item("contracts", "Contract Parser", "loadModule(this,'/module/contracts', 'Contract Parser')", item_id="nav-contracts"),
                    _sidebar_item("reports", "Reports", "loadModule(this,'/module/reports', 'Reports')", item_id="nav-reports"),
                    _sidebar_item("forecasting", "Forecasting", "loadModule(this,'/module/forecasting', 'Revenue Forecasting')", item_id="nav-forecasting"),
                    _sidebar_item("anomaly", "Anomaly Detection", "loadModule(this,'/module/anomaly', 'Anomaly Detection')", item_id="nav-anomaly"),
                    cls="section-body", id="sec-ai-tools",
                ),
                cls="sidebar-section collapsible",
            ),
            # Shortcuts (collapsed by default)
            Div(
                _section_toggle("Shortcuts", "sec-shortcuts"),
                Div(_help_expanders(), cls="section-body", id="sec-shortcuts"),
                cls="sidebar-section collapsible",
            ),
            cls="sidebar-scroll",
        ),
        # Pinned footer: Guide + Profile + Templates + Logout
        Div(
            _sidebar_item("guide", "User Guide", "loadModule(this,'/module/guide', 'User Guide')", item_id="nav-guide"),
            _sidebar_item("profile", "Profile", "loadModule(this,'/module/profile', 'Profile')", item_id="nav-profile"),
            _sidebar_item("templates", "Templates", "loadModule(this,'/module/templates', 'Templates')", item_id="nav-templates"),
            _sidebar_item("logout", user.get("display_name", "User") if user else "Login",
                           "window.location.href='/logout'" if user else "window.location.href='/login'"),
            cls="sidebar-footer",
        ),
        cls="left-pane",
    )


def _right_pane():
    return Div(
        Div(
            H3("Canvas"),
            Button("X", cls="header-btn", onclick="toggleRightPane()"),
            cls="right-header",
        ),
        Div(
            Button("Trace", cls="right-tab active", onclick="showTab('trace')", **{"data-tab-btn": "trace"}),
            Button("Detail", cls="right-tab", onclick="showTab('detail')", **{"data-tab-btn": "detail"}),
            cls="right-tabs",
        ),
        Div(
            Div(id="trace-content", style="display:block", **{"data-tab": "trace"}),
            Div(id="detail-content", style="display:none", **{"data-tab": "detail"}),
            cls="right-content",
        ),
        cls="right-pane",
    )


# ---------------------------------------------------------------------------
# Auth Routes
# ---------------------------------------------------------------------------

def _auth_page(title, parts, error=None):
    """Shared auth page layout."""
    els = [H2(title, style="text-align:center; margin-bottom:1.5rem;")]
    if error:
        els.append(Div(error, style="color:#dc2626;text-align:center;font-size:0.8rem;margin-bottom:0.5rem;"))
    els.extend(parts)
    return Titled(f"AHCAM \u2014 {title}", Style(APP_CSS), Div(*els, cls="auth-container"))


def _session_login(session, user):
    session["user_id"] = user["user_id"]
    session["email"] = user.get("email", "")
    session["display_name"] = user.get("display_name", "")


@rt("/login", methods=["GET"])
def login_page(session):
    if session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    parts = []
    if _oauth_enabled:
        parts.append(_google_btn("Sign in with Google"))
        parts.append(Div("or", cls="divider"))
    parts.append(Form(
        Input(type="email", name="email", placeholder="Email", required=True),
        Input(type="password", name="password", placeholder="Password", required=True),
        Button("Sign In", type="submit", cls="auth-btn"),
        Div(A("Forgot password?", href="/forgot"), cls="auth-link"),
        Div(A("Create account", href="/register"), cls="auth-link"),
        cls="auth-form", method="post", action="/login",
    ))
    return _auth_page("Sign In", parts)


@rt("/login", methods=["POST"])
def login_submit(email: str, password: str, session):
    from utils.auth import authenticate
    user = authenticate(email, password)
    if not user:
        parts = []
        if _oauth_enabled:
            parts.append(_google_btn("Sign in with Google"))
            parts.append(Div("or", cls="divider"))
        parts.append(Form(
            Input(type="email", name="email", placeholder="Email", value=email, required=True),
            Input(type="password", name="password", placeholder="Password", required=True),
            Button("Sign In", type="submit", cls="auth-btn"),
            Div(A("Forgot password?", href="/forgot"), cls="auth-link"),
            Div(A("Create account", href="/register"), cls="auth-link"),
            cls="auth-form", method="post", action="/login",
        ))
        return _auth_page("Sign In", parts, error="Invalid email or password.")
    _session_login(session, user)
    return RedirectResponse("/", status_code=303)


@rt("/register", methods=["GET"])
def register_page(session):
    if session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    parts = []
    if _oauth_enabled:
        parts.append(_google_btn("Sign up with Google"))
        parts.append(Div("or", cls="divider"))
    parts.append(Form(
        Input(type="text", name="display_name", placeholder="Name", required=True),
        Input(type="email", name="email", placeholder="Email", required=True),
        Input(type="password", name="password", placeholder="Password", required=True, minlength="6"),
        Button("Create Account", type="submit", cls="auth-btn"),
        Div(A("Already have an account? Sign in", href="/login"), cls="auth-link"),
        cls="auth-form", method="post", action="/register",
    ))
    return _auth_page("Create Account", parts)


@rt("/register", methods=["POST"])
def register_submit(email: str, password: str, display_name: str, session):
    from utils.auth import create_user
    user = create_user(email, password, display_name=display_name)
    if not user:
        parts = []
        if _oauth_enabled:
            parts.append(_google_btn("Sign up with Google"))
            parts.append(Div("or", cls="divider"))
        parts.append(Form(
            Input(type="text", name="display_name", placeholder="Name", value=display_name, required=True),
            Input(type="email", name="email", placeholder="Email", value=email, required=True),
            Input(type="password", name="password", placeholder="Password", required=True, minlength="6"),
            Button("Create Account", type="submit", cls="auth-btn"),
            cls="auth-form", method="post", action="/register",
        ))
        return _auth_page("Create Account", parts, error="Email already registered.")
    _session_login(session, user)
    return RedirectResponse("/", status_code=303)


# --- Google OAuth routes ---
if _oauth_enabled:
    @rt("/oauth/google")
    async def oauth_google(request):
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host", request.url.netloc)
        redirect_uri = f"{scheme}://{host}/auth/callback"
        return await _authlib_oauth.google.authorize_redirect(request, redirect_uri)

    @rt("/auth/callback")
    async def auth_callback(request, session):
        from utils.auth import get_user_by_google_id, get_user_by_email, create_user, link_google_id
        try:
            token = await _authlib_oauth.google.authorize_access_token(request)
        except Exception as e:
            logger.error(f"OAuth token exchange failed: {e}")
            return RedirectResponse("/login", status_code=303)

        userinfo = token.get("userinfo", {})
        if not userinfo:
            userinfo = await _authlib_oauth.google.userinfo(token=token)

        google_id = userinfo.get("sub", "")
        email = userinfo.get("email", "")
        name = userinfo.get("name", "")

        if not email:
            return RedirectResponse("/login", status_code=303)

        user = get_user_by_google_id(google_id) if google_id else None
        if not user:
            user = get_user_by_email(email)
            if user and google_id:
                link_google_id(email, google_id)
            elif not user:
                user = create_user(email=email, google_id=google_id, display_name=name)

        if user:
            _session_login(session, user)
        return RedirectResponse("/", status_code=303)


@rt("/logout")
def logout(session):
    session.clear()
    return RedirectResponse("/login", status_code=303)


# ---------------------------------------------------------------------------
# Forgot / Reset Password
# ---------------------------------------------------------------------------

@rt("/forgot", methods=["GET"])
def forgot_page(session, msg: str = "", error: str = ""):
    parts = []
    if msg:
        parts.append(Div(msg, style="color:#16a34a;text-align:center;font-size:0.85rem;margin-bottom:0.5rem;"))
    if error:
        parts.append(Div(error, style="color:#dc2626;text-align:center;font-size:0.85rem;margin-bottom:0.5rem;"))
    parts.append(Form(
        Input(type="email", name="email", placeholder="Enter your email", required=True, autofocus=True),
        Button("Send Reset Link", type="submit", cls="auth-btn"),
        Div(A("Back to sign in", href="/login"), cls="auth-link"),
        cls="auth-form", method="post", action="/forgot",
    ))
    return _auth_page("Reset Password", parts)


@rt("/forgot", methods=["POST"])
def forgot_submit(request, email: str):
    from utils.auth import create_reset_token, send_reset_email
    token = create_reset_token(email)
    if token:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host", request.url.netloc)
        reset_url = f"{scheme}://{host}/reset?token={token}"
        send_reset_email(email, reset_url)
    # Always show success (don't leak whether email exists)
    return RedirectResponse("/forgot?msg=If+an+account+exists+with+that+email,+a+reset+link+has+been+sent.", status_code=303)


@rt("/reset", methods=["GET"])
def reset_page(token: str = "", error: str = ""):
    from utils.auth import verify_reset_token
    if not token:
        return RedirectResponse("/forgot?error=Invalid+or+expired+reset+link.", status_code=303)
    payload = verify_reset_token(token)
    if not payload:
        return RedirectResponse("/forgot?error=Invalid+or+expired+reset+link.", status_code=303)
    parts = []
    if error:
        parts.append(Div(error, style="color:#dc2626;text-align:center;font-size:0.85rem;margin-bottom:0.5rem;"))
    parts.append(Form(
        Hidden(name="token", value=token),
        Input(type="password", name="password", placeholder="New password", required=True, minlength="6", autofocus=True),
        Input(type="password", name="password_confirm", placeholder="Confirm new password", required=True, minlength="6"),
        Button("Reset Password", type="submit", cls="auth-btn"),
        cls="auth-form", method="post", action="/reset",
    ))
    return _auth_page("Set New Password", parts)


@rt("/reset", methods=["POST"])
def reset_submit(token: str, password: str, password_confirm: str):
    from utils.auth import verify_reset_token, update_password
    if password != password_confirm:
        return RedirectResponse(f"/reset?token={token}&error=Passwords+do+not+match.", status_code=303)
    if len(password) < 6:
        return RedirectResponse(f"/reset?token={token}&error=Password+must+be+at+least+6+characters.", status_code=303)
    payload = verify_reset_token(token)
    if not payload:
        return RedirectResponse("/forgot?error=Invalid+or+expired+reset+link.", status_code=303)
    update_password(payload["user_id"], password)
    return RedirectResponse("/login", status_code=303)


# ---------------------------------------------------------------------------
# Profile & Templates Routes
# ---------------------------------------------------------------------------

@rt("/module/profile")
def module_profile(session):
    from utils.auth import get_user_by_id
    user = get_user_by_id(session.get("user_id")) or {}
    return Div(
        H3("Profile"),
        Form(
            Div(
                Label("Display Name"),
                Input(type="text", name="display_name", value=user.get("display_name", ""), required=True),
                cls="form-group",
            ),
            Div(
                Label("Email"),
                Input(type="email", value=user.get("email", ""), disabled=True),
                cls="form-group",
            ),
            Div(
                Label("Role"),
                Input(type="text", value=user.get("role", ""), disabled=True),
                cls="form-group",
            ),
            Button("Save", type="submit", cls="module-action-btn"),
            hx_post="/module/profile/update", hx_target="#center-content", hx_swap="innerHTML",
            cls="profile-form module-form",
        ),
        cls="module-content",
    )


@rt("/module/profile/update", methods=["POST"])
def profile_update(session, display_name: str):
    from utils.auth import update_display_name
    uid = session.get("user_id")
    if uid and display_name:
        update_display_name(uid, display_name)
        session["display_name"] = display_name
    return Div(
        Div("Profile updated.", style="color:#16a34a;font-size:0.85rem;margin-bottom:1rem;"),
        module_profile(session),
    )


@rt("/module/templates")
def module_templates(session):
    from sqlalchemy import text
    from utils.db import get_pool
    uid = session.get("user_id")
    try:
        pool = get_pool()
        with pool.get_session() as s:
            rows = s.execute(text("""
                SELECT template_id, name, prompt, category FROM ahcam.prompt_templates
                WHERE user_id = :uid OR is_default = TRUE
                ORDER BY is_default DESC, name
            """), {"uid": uid}).fetchall()
    except Exception:
        rows = []

    cards = []
    for r in rows:
        cards.append(Div(
            Div(Span(r[1], cls="deal-card-title"), Span(r[3], cls="badge-blue"),
                style="display:flex;justify-content:space-between;align-items:center;"),
            Div(r[2][:80] + "..." if len(r[2]) > 80 else r[2], cls="deal-card-meta"),
            cls="deal-card",
            hx_get=f"/module/template/{r[0]}", hx_target="#center-content", hx_swap="innerHTML",
        ))

    return Div(
        Div(
            H3("Prompt Templates"),
            Button("+ New Template", hx_get="/module/template/new", hx_target="#center-content", hx_swap="innerHTML", cls="module-action-btn"),
            style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
        ),
        *cards if cards else [Div("No templates yet. Create your first prompt template.", cls="empty-state")],
        cls="module-content",
    )


@rt("/module/template/new")
def template_new(session):
    return Div(
        H3("New Template"),
        Form(
            Div(Input(type="text", name="name", placeholder="Template Name", required=True), cls="form-group"),
            Div(Select(Option("General", value="general"), Option("Waterfall", value="waterfall"),
                       Option("Report", value="report"), Option("Analysis", value="analysis"),
                       name="category"), cls="form-group"),
            Div(Textarea(name="prompt", placeholder="Enter your prompt template...", rows="6", required=True), cls="form-group"),
            Button("Save Template", type="submit", cls="module-action-btn"),
            hx_post="/module/template/create", hx_target="#center-content", hx_swap="innerHTML",
            cls="module-form",
        ),
        cls="module-content",
    )


@rt("/module/template/create", methods=["POST"])
def template_create(session, name: str, prompt: str, category: str = "general"):
    from sqlalchemy import text as sql_text
    from utils.db import get_pool
    try:
        pool = get_pool()
        with pool.get_session() as s:
            s.execute(sql_text("""
                INSERT INTO ahcam.prompt_templates (user_id, name, prompt, category)
                VALUES (:uid, :name, :prompt, :cat)
            """), {"uid": session.get("user_id"), "name": name, "prompt": prompt, "cat": category})
    except Exception as e:
        return Div(f"Error: {e}", cls="module-error")
    return module_templates(session)


@rt("/module/template/{template_id}")
def template_detail(template_id: str, session):
    from sqlalchemy import text as sql_text
    from utils.db import get_pool
    try:
        pool = get_pool()
        with pool.get_session() as s:
            row = s.execute(sql_text("""
                SELECT template_id, name, prompt, category FROM ahcam.prompt_templates WHERE template_id = :tid
            """), {"tid": template_id}).fetchone()
    except Exception:
        row = None
    if not row:
        return Div("Template not found.", cls="module-error")
    return Div(
        H3(row[1]),
        Div(Span(row[3].title(), cls="badge-blue"), style="margin-bottom:1rem;"),
        Div(
            Pre(row[2], style="white-space:pre-wrap;background:#f8fafc;padding:1rem;border-radius:8px;border:1px solid #e2e8f0;font-size:0.85rem;"),
            cls="detail-section",
        ),
        Div(
            Button("Use in Chat", cls="module-action-btn",
                   onclick=f"fillChat({repr(row[2][:200])})"),
            Button("\u2190 Back", hx_get="/module/templates", hx_target="#center-content", hx_swap="innerHTML", cls="back-btn", style="margin-left:0.5rem;"),
            style="margin-top:1rem;",
        ),
        cls="module-content",
    )


# --- Placeholder User Guide ---
@rt("/module/guide")
def module_guide(session):
    return Div(
        H3("User Guide"),
        P("Welcome to AHCAM. Use the sidebar to navigate modules, or type commands in the AI Assistant chat."),
        Div(
            H4("Quick Start"),
            Ul(
                Li("Type ", Code("help"), " in the chat to see all available commands"),
                Li("Click ", Strong("CRM"), " to manage deals, contacts, and sales"),
                Li("Expand ", Strong("Financing OS"), " for collection accounts, waterfall, and transactions"),
                Li("Expand ", Strong("AI Tools"), " for contract parsing, forecasting, and anomaly detection"),
            ),
            cls="detail-section",
        ),
        cls="module-content",
    )


# ---------------------------------------------------------------------------
# Module Route Registration
# ---------------------------------------------------------------------------

from modules.productions import register_routes as productions_routes
from modules.stakeholders import register_routes as stakeholders_routes
from modules.collections import register_routes as collections_routes
from modules.waterfall import register_routes as waterfall_routes
from modules.transactions import register_routes as transactions_routes
from modules.disbursements import register_routes as disbursements_routes
from modules.contracts import register_routes as contracts_routes
from modules.reports import register_routes as reports_routes
from modules.forecasting import register_routes as forecasting_routes
from modules.anomaly import register_routes as anomaly_routes
from modules.crm import register_routes as crm_routes
from modules.documents import register_routes as documents_routes

productions_routes(rt)
stakeholders_routes(rt)
collections_routes(rt)
waterfall_routes(rt)
transactions_routes(rt)
disbursements_routes(rt)
contracts_routes(rt)
reports_routes(rt)
forecasting_routes(rt)
anomaly_routes(rt)
crm_routes(rt)
documents_routes(rt)


# ---------------------------------------------------------------------------
# Conversation list (sidebar)
# ---------------------------------------------------------------------------

@rt("/agui-conv/list")
def conv_list(session):
    user_id = session.get("user_id")
    try:
        convs = list_conversations(user_id=user_id, limit=20)
    except Exception:
        convs = []
    if not convs:
        return Div(Span("No conversations yet", style="font-size:0.7rem;color:#94a3b8;padding:0.5rem 1rem;display:block;"))
    items = []
    for i, c in enumerate(convs):
        label = c.get("first_msg") or c.get("title") or "New chat"
        label = label[:40] + "..." if len(label) > 40 else label
        hidden = " hidden" if i >= 3 else ""
        items.append(Button(label, cls=f"conv-item{hidden}",
                            onclick=f"window.location.href='/?thread={c['thread_id']}'"))
    els = list(items)
    if len(convs) > 3:
        els.append(Button("More...", cls="conv-more-btn", id="conv-more-btn", onclick="showMoreHistory()"))
        els.append(Input(type="text", placeholder="Search chats...", cls="conv-search-input",
                         id="conv-search", style="display:none;", oninput="filterHistory(this.value)"))
    return Div(*els)


# ---------------------------------------------------------------------------
# Main Page (3-pane layout)
# ---------------------------------------------------------------------------

@rt("/")
def index(session, thread: str = None, new: str = None):
    if not session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    from utils.auth import get_user_by_id
    user = get_user_by_id(session["user_id"]) or {}

    if new:
        thread_id = str(_uuid.uuid4())
    elif thread:
        thread_id = thread
    elif not session.get("thread_id"):
        thread_id = str(_uuid.uuid4())
    else:
        thread_id = session["thread_id"]

    session["thread_id"] = thread_id

    return Titled(
        "AHCAM",
        Style(APP_CSS),
        Script(LAYOUT_JS),
        Div(
            _left_pane(user),
            Div(
                Div(
                    H2("AI Assistant", id="center-title"),
                    Div(
                        Button("Canvas", cls="header-btn", onclick="toggleRightPane()"),
                        style="display:flex;gap:0.5rem;",
                    ),
                    cls="center-header",
                ),
                Div(agui.chat(thread_id), cls="center-chat"),
                Div(id="center-content"),
                cls="center-pane",
            ),
            _right_pane(),
            cls="app-layout",
        ),
    )


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "5011"))
    print(f"Starting AHCAM on port {port}...")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
