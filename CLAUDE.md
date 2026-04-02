# AHCAM — Ashland Hill Collection Account Management

AI-powered Collection Account Management platform for film & entertainment finance. Competes with Freeway Entertainment and Fintage House — differentiated by AI contract parsing, predictive revenue forecasting, anomaly detection, and natural-language stakeholder queries.

## Stack

- **Python 3.13**, virtualenv at `.venv/`
- **FastHTML** 3-pane agentic UI (`app.py`, port 5011)
- **LangGraph** + XAI Grok-3 for AI chat agents
- **PostgreSQL** (`ahcam` schema on finespresso_db)
- **HTMX + WebSocket** for real-time streaming
- **Pandas + NumPy** for waterfall calculations & financial processing

## Architecture (Cloned from AHMF Pattern)

- **3-pane layout**: Left sidebar (260px nav) | Center (chat + module views) | Right (380px detail/trace canvas)
- **Command interceptor**: Colon-syntax routed to handlers, free-form to LangGraph AI
- **WebSocket streaming**: LangGraph astream_events(v2) for real-time AI responses
- **HTMX module views**: Product pages swapped into center pane via hx-get/hx-swap
- **Module pattern**: Each module exports `register_routes(rt)` + AI tool functions + UI components

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `modules/` | Product module routes (productions, stakeholders, collections, waterfall, transactions, disbursements, contracts, reports, forecasting, anomaly) |
| `agents/` | LangGraph agents and tool definitions |
| `agents/tools/` | Structured tool functions for agents |
| `utils/` | Core utilities (db, auth, ledger, pdf extraction, encryption) |
| `utils/agui/` | AG-UI chat engine (vendored from AHMF) |
| `sql/` | Database migrations |
| `config/` | App settings, waterfall templates, constants |
| `tests/` | Test suite |
| `static/` | CSS, screenshots, guide assets |
| `docs/` | Roadmap, presentations |

## Products / Modules

1. **Productions** — CRUD for film/TV productions (title, type, genre, budget, status, key personnel)
2. **Stakeholders** — Manage all parties: Producers, Financiers, Sales Agents, Distributors, Profit Participants, Guilds
3. **Collection Accounts** — Core CAM: segregated accounts per production, balance tracking, bank integration status
4. **Waterfall Engine** — Define & execute recoupment waterfalls (priority-based rules, caps, corridors, cross-collateralization)
5. **Transactions** — Immutable ledger: all inflows (distributor payments) and outflows (disbursements) with SHA-256 chain
6. **Disbursements** — Automated payout processing based on waterfall rules, approval workflows, payment status tracking
7. **Contracts** — AI-powered contract parsing: upload CAMA PDFs → auto-extract waterfall rules, parties, terms
8. **Reports** — Stakeholder-specific collection reports, waterfall position statements, PDF exports, scheduled delivery
9. **Revenue Forecasting** — AI-predicted future sales/royalties from historical data, territory analysis, comp-based projections
10. **Anomaly Detection** — AI flags unusual payments, rule violations, timing irregularities, duplicate transactions

## Chat Commands

```
production:list              List all productions
production:PROD_ID           View production details
stakeholder:search NAME      Search stakeholders
account:list                 List collection accounts
account:ACCOUNT_ID           View account details & balance
waterfall:PROD_ID            View waterfall rules for a production
waterfall:run PROD_ID        Execute waterfall calculation
transaction:list             View transaction ledger
transaction:ACCOUNT_ID       Transactions for specific account
disbursement:list            Pending & completed disbursements
disbursement:run PROD_ID     Process disbursements for production
contract:upload              Upload contract for AI parsing
report:generate PROD_ID      Generate collection account report
forecast:PROD_ID             Revenue forecast for production
anomaly:scan                 Run anomaly detection scan
help                         Show available commands
```

## Data Models (PostgreSQL — `ahcam` schema)

### Core Tables

- **productions** — production_id (UUID PK), title, project_type, genre, status, budget, currency, producer, director, synopsis, territory, created_by, timestamps
- **stakeholders** — stakeholder_id (UUID PK), name, role (enum: producer/financier/sales_agent/distributor/profit_participant/guild/talent), company, email, phone, bank_details_encrypted, notes JSONB, created_by, timestamps
- **collection_accounts** — account_id (UUID PK), production_id FK, account_name, bank_name, account_number_encrypted, routing_encrypted, balance, currency, status (active/frozen/closed), created_by, timestamps
- **production_stakeholders** — Junction: production_id FK, stakeholder_id FK, role_in_production, participation_percentage

### Waterfall & Recoupment

- **waterfall_rules** — rule_id (UUID PK), production_id FK, priority (int), recipient_stakeholder_id FK, rule_type (percentage/fixed/corridor/residual), percentage, cap, floor, corridor_start, corridor_end, recoupment_basis, cross_collateral_group, description, active (bool), timestamps
- **recoupment_positions** — position_id (UUID PK), production_id FK, stakeholder_id FK, total_owed, total_received, outstanding, last_calculated, timestamps

### Transactions & Disbursements

- **transactions** — transaction_id (UUID PK), account_id FK, transaction_type (inflow/outflow/adjustment), amount, currency, source_stakeholder_id FK, destination_stakeholder_id FK, reference, description, status (pending/confirmed/reversed), previous_hash, hash (SHA-256), metadata JSONB, created_by, timestamps
- **disbursements** — disbursement_id (UUID PK), production_id FK, transaction_id FK, stakeholder_id FK, amount, waterfall_rule_id FK, status (calculated/approved/processing/completed/failed), approved_by, approved_at, payment_reference, timestamps

### Contracts & AI

- **contracts** — contract_id (UUID PK), production_id FK, contract_type (cama/distribution/sales/finance), file_path, file_hash, parsed_rules JSONB, parsed_parties JSONB, parsed_terms JSONB, parsing_status (pending/processing/completed/failed/needs_review), parsed_at, created_by, timestamps
- **revenue_forecasts** — forecast_id (UUID PK), production_id FK, territory, forecast_period, predicted_amount, confidence_interval JSONB, model_used, input_data JSONB, created_by, timestamps
- **anomaly_alerts** — alert_id (UUID PK), production_id FK, transaction_id FK, alert_type (unusual_amount/timing/duplicate/rule_violation), severity (low/medium/high/critical), description, resolved (bool), resolved_by, resolved_at, timestamps

### System

- **users** — user_id (UUID PK), email (unique), password_hash, display_name, role (admin/manager/viewer/stakeholder), timestamps
- **audit_log** — log_id (UUID PK), user_id FK, action, entity_type, entity_id, old_values JSONB, new_values JSONB, ip_address, timestamps
- **chat_conversations** — thread_id (UUID PK), user_id FK, title, timestamps
- **chat_messages** — message_id (UUID PK), thread_id FK, role, content, metadata JSONB, timestamps

## Waterfall Engine (Core Logic)

The waterfall engine is the heart of CAM. Key behaviors:

```python
# Simplified flow
def apply_waterfall(incoming_amount: float, rules: list[dict]) -> dict:
    """Apply priority-ordered recoupment rules to incoming revenue."""
    df = pd.DataFrame(rules).sort_values("priority")
    remaining = incoming_amount
    payouts = {}
    for _, rule in df.iterrows():
        if rule["rule_type"] == "percentage":
            share = remaining * (rule["percentage"] / 100)
        elif rule["rule_type"] == "fixed":
            share = min(remaining, rule["cap"])
        elif rule["rule_type"] == "corridor":
            share = remaining * (rule["percentage"] / 100)
        share = min(share, rule.get("cap", float("inf")))
        share = min(share, remaining)
        payouts[rule["recipient"]] = share
        remaining -= share
        if remaining <= 0:
            break
    return payouts
```

Rule types: percentage, fixed, corridor (% within a revenue band), residual (everything left).
Supports: caps, floors, cross-collateralization groups, cumulative recoupment tracking.

## Transaction Ledger (Immutable)

Every transaction is hash-chained for audit integrity:
- `hash = SHA-256(transaction_id + amount + timestamp + previous_hash)`
- Append-only: no updates or deletes on transaction records
- Reversals create new offsetting transactions

## Security & Compliance

- **Encryption**: Bank details encrypted at rest (Fernet via `cryptography` library)
- **Audit trail**: Every action logged with user, timestamp, old/new values
- **Row-Level Security**: All tables scoped by `created_by` / user role
- **Auth**: bcrypt password hashing + JWT (7-day expiry) + role-based access
- **Data isolation**: Stakeholder portal shows only their positions and reports

## Secrets Policy

**NEVER copy, persist, log, or document actual secret values.** API keys, tokens, passwords, and connection strings from `.env` must only be used transiently during runtime.

## Required Environment Variables (.env)

```
DB_URL=...                    # PostgreSQL connection string
XAI_API_KEY=...               # XAI Grok LLM
ENCRYPTION_KEY=...            # Fernet encryption key for bank details
JWT_SECRET=...                # JWT signing secret
TAVILY_API_KEY=...            # Tavily web search (optional)
```

## AI Agent Tools

```
search_productions            Search/list productions
get_production_detail         Get production details
search_stakeholders           Search stakeholders by name/role
get_account_balance           Get collection account balance
get_waterfall_rules           View waterfall rules for production
run_waterfall                 Execute waterfall calculation
search_transactions           Search transaction ledger
get_disbursement_status       Check disbursement status
parse_contract                AI-parse uploaded contract PDF
generate_forecast             Revenue forecast for production
run_anomaly_scan              Detect anomalies in transactions
generate_report               Generate stakeholder report
get_recoupment_position       Stakeholder's recoupment position
```

## Running

```bash
source .venv/bin/activate
pip install -r requirements.txt
for f in sql/*.sql; do psql $DB_URL -f "$f"; done
python app.py    # port 5011
```

## Testing

```bash
python tests/test_suite.py
# Results written to test-data/*.json
```

When the user says "run tests" or "run regression", execute `python tests/test_suite.py`.

## Deployment

```bash
docker build -t ahcam .
docker run --env-file .env -p 5011:5011 ahcam
```

---

## Implementation Plan

### Phase 1: Skeleton & Core Infrastructure (Week 1)

**Goal**: Running FastHTML app with 3-pane layout, auth, DB, and chat shell.

1. **Project setup**: `requirements.txt`, `.env.sample`, `Dockerfile`, `docker-compose.yml`
2. **Copy & adapt from AHMF**: `utils/db.py`, `utils/auth.py`, `utils/agui/` (chat engine), `config/settings.py`
3. **`app.py` scaffold**: 3-pane layout, sidebar with 10 module nav items, WebSocket chat, command interceptor shell
4. **SQL migrations**: `01_create_schema.sql` (users), `02_create_productions.sql`, `03_create_stakeholders.sql`
5. **Auth routes**: `/login`, `/register`, session management
6. **Basic modules**: `modules/productions.py` (CRUD), `modules/stakeholders.py` (CRUD)

### Phase 2: Core CAM Engine (Weeks 2-3)

**Goal**: Working waterfall engine, immutable ledger, collection accounts.

1. **SQL migrations**: `04_create_accounts.sql`, `05_create_waterfall.sql`, `06_create_transactions.sql`, `07_create_disbursements.sql`
2. **`modules/collections.py`**: Collection account CRUD, balance views, account status management
3. **`modules/waterfall.py`**: Waterfall rule builder UI (form-based), rule visualization, execution engine with Pandas
4. **`modules/transactions.py`**: Immutable ledger with hash chain, inflow/outflow recording, transaction search & filtering
5. **`modules/disbursements.py`**: Payout calculation from waterfall, approval workflow, status tracking
6. **`utils/ledger.py`**: Hash-chain logic, transaction validation, balance reconciliation helpers
7. **Chat commands**: `account:list`, `waterfall:PROD_ID`, `waterfall:run`, `transaction:list`, `disbursement:run`
8. **Agent tools**: Wire up 8+ tools to LangGraph agent

### Phase 3: AI Features — Differentiation (Weeks 4-5)

**Goal**: AI contract parsing, revenue forecasting, anomaly detection.

1. **SQL migrations**: `08_create_contracts.sql`, `09_create_forecasts.sql`, `10_create_anomalies.sql`
2. **`modules/contracts.py`**: PDF upload, AI parsing pipeline (extract waterfall rules, parties, terms from CAMA documents), review & approve parsed results, auto-create waterfall rules from parsed contracts
3. **`modules/forecasting.py`**: Historical revenue analysis, territory-level predictions, confidence intervals, comp-based projections
4. **`modules/anomaly.py`**: Transaction anomaly scanner (unusual amounts, timing, duplicates, rule violations), severity classification, alert dashboard, resolution workflow
5. **`utils/pdf_extractor.py`**: PDF text extraction (pdfplumber), structured parsing helpers
6. **Natural-language queries**: "What does Producer X's recoupment position look like?" → agent queries DB and responds

### Phase 4: Reporting & Stakeholder Views (Week 6)

**Goal**: Production-ready reports, stakeholder transparency.

1. **SQL migrations**: `11_create_reports.sql`, `12_create_audit_log.sql`
2. **`modules/reports.py`**: Collection account statements, waterfall position reports, stakeholder-specific views, PDF export (reportlab or weasyprint), scheduled report generation (Celery task)
3. **Stakeholder portal concept**: Role-based views — stakeholders see only their productions, positions, and reports
4. **Audit log**: Every mutation logged with before/after JSONB snapshots
5. **Dashboard**: Summary stats (total collected, disbursed, pending), charts (Plotly)

### Phase 5: Polish, Testing & Deployment (Week 7)

**Goal**: Production-ready, tested, documented.

1. **Test suite**: DB, auth, waterfall engine (property-based with Hypothesis), transaction integrity, AI tool functions, command interceptor, chat persistence
2. **User guide**: Playwright screenshot capture (same pattern as AHMF)
3. **Slide deck**: PowerPoint generator
4. **Docker + CI/CD**: GitHub Actions pipeline
5. **README**: Feature list, quick start, demo GIF

### Phase 6: Roadmap Beyond MVP

- **Month 3-6**: Multi-production dashboards, distributor auto-payment API (Stripe Connect / SEPA), cross-collateralization engine
- **Month 6-9**: Stakeholder self-service portal (login → see your positions), mobile-responsive UI, blockchain audit trail (optional)
- **Month 9+**: Escrow-as-a-service API, marketplace integration (FilmChain-style), SOC 2 compliance path
