# AHCAM Architecture

## System Overview

```mermaid
graph TB
    subgraph Client["Browser"]
        UI["FastHTML 3-Pane UI"]
        WS["WebSocket Client"]
        HTMX["HTMX Partials"]
    end

    subgraph App["app.py — FastHTML Server (port 5011)"]
        Router["Route Handler"]
        Auth["Auth Module<br/>bcrypt + JWT"]
        Interceptor["Command Interceptor<br/>15 colon-syntax commands"]
        AGUI["AG-UI Engine<br/>WebSocket streaming"]
    end

    subgraph Agent["LangGraph Agent"]
        LLM["XAI Grok-3<br/>ChatOpenAI"]
        React["create_react_agent"]
        Tools["15 Agent Tools"]
    end

    subgraph Modules["10 Product Modules"]
        M1["Productions"]
        M2["Stakeholders"]
        M3["Collection Accounts"]
        M4["Waterfall Engine"]
        M5["Transactions"]
        M6["Disbursements"]
        M7["Contract Parser"]
        M8["Reports"]
        M9["Forecasting"]
        M10["Anomaly Detection"]
    end

    subgraph Data["PostgreSQL (ahcam schema)"]
        DB[(15 Tables<br/>UUID PKs, JSONB)]
        Ledger["Hash-Chained<br/>Transaction Ledger"]
    end

    UI -->|HTTP GET/POST| Router
    WS -->|WebSocket msg| AGUI
    HTMX -->|hx-get/hx-post| Modules

    Router --> Auth
    AGUI --> Interceptor
    Interceptor -->|structured cmd| Tools
    Interceptor -->|free-form| React
    React --> LLM
    React --> Tools

    Tools --> Modules
    Modules --> DB
    M5 --> Ledger
    M4 -->|Pandas| M6
```

## 3-Pane Layout

```mermaid
graph LR
    subgraph Layout["Browser Viewport (100vh)"]
        subgraph Left["Left Pane (260px)"]
            Logo["AH Logo"]
            NewChat["+ New Chat"]
            Nav["Module Navigation<br/>• Productions<br/>• Stakeholders<br/>• Accounts<br/>• Waterfall<br/>• Transactions<br/>• Disbursements<br/>• Contracts<br/>• Reports<br/>• Forecasting<br/>• Anomaly"]
            Help["Command Expanders"]
            History["Chat History"]
            UserBtn["User / Logout"]
        end

        subgraph Center["Center Pane (flex)"]
            Header["Header Bar + Inspector Toggle"]
            Chat["AI Chat<br/>WebSocket streaming<br/>welcome screen + messages"]
            Content["Module Content<br/>HTMX partials<br/>stat cards, tables, forms"]
        end

        subgraph Right["Right Pane (380px, toggled)"]
            Tabs["Trace | Detail"]
            Trace["Tool execution log<br/>on_tool_start / on_tool_end"]
            Detail["Entity detail canvas"]
        end
    end

    Nav -->|"loadModule(path, title)"| Content
    Nav -->|"showChat()"| Chat
    Help -->|"fillChat(cmd)"| Chat
```

## Chat Message Flow

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant WS as WebSocket /agui/ws/{thread_id}
    participant CI as Command Interceptor
    participant AG as LangGraph Agent
    participant LLM as XAI Grok-3
    participant T as Tool Function
    participant DB as PostgreSQL

    U->>WS: Send message via form
    WS->>WS: AGUIThread._handle_message()
    WS->>WS: Remove welcome screen
    WS->>WS: Disable input, show "Thinking..."

    alt Structured Command (e.g. "account:list")
        WS->>CI: _command_interceptor(msg)
        CI->>T: Direct tool call (search_accounts)
        T->>DB: SQL query
        DB-->>T: Result rows
        T-->>CI: Markdown table
        CI-->>WS: Return result string
        WS->>U: Render user bubble + assistant bubble (marked)
        WS->>U: renderMarkdown() via JS
    else Free-form Query
        WS->>CI: _command_interceptor(msg)
        CI-->>WS: None (not a command)
        WS->>AG: _handle_ai_run(msg)
        WS->>U: Create streaming bubble + trace entry

        loop astream_events(v2)
            AG->>LLM: Messages + tool definitions
            LLM-->>AG: Token stream / tool_call

            alt on_chat_model_stream
                AG-->>WS: Token chunk
                WS->>U: Append token (hx_swap_oob beforeend)
            else on_tool_start
                AG->>T: Call tool function
                WS->>U: "Running {tool_name}..." bubble + trace entry
            else on_tool_end
                T-->>AG: Tool result
                WS->>U: Update trace: "Tool complete"
            end
        end

        WS->>U: Remove streaming cursor
        WS->>U: renderMarkdown() + re-enable input
    end

    WS->>DB: save_message(thread_id, role, content)
    WS->>U: Set follow-up suggestion buttons
```

## Agent Tool Architecture

```mermaid
graph TD
    subgraph Agent["LangGraph React Agent"]
        LLM["XAI Grok-3-mini<br/>streaming=True"]
    end

    subgraph CoreTools["Core CAM Tools"]
        T1["search_productions<br/>query → markdown table"]
        T2["get_production_detail<br/>production_id → detail view"]
        T3["search_stakeholders<br/>query → markdown table"]
        T4["search_accounts<br/>query → markdown table"]
        T5["get_account_balance<br/>account_id → balance detail"]
        T6["get_waterfall_rules<br/>production_id → rules table"]
        T7["run_waterfall<br/>production_id → payout breakdown"]
        T8["search_transactions<br/>query → ledger table"]
        T9["get_disbursement_status<br/>query → disbursement table"]
        T10["run_disbursements<br/>production_id → process payouts"]
    end

    subgraph AITools["AI-Powered Tools"]
        T11["parse_contract_tool<br/>text → parties, rules, terms"]
        T12["generate_report<br/>production_id → collection statement"]
        T13["get_recoupment_position<br/>stakeholder → position across productions"]
        T14["generate_forecast<br/>production_id → 12-month projection"]
        T15["run_anomaly_scan<br/>query → anomaly report"]
    end

    Agent --> CoreTools
    Agent --> AITools

    T7 -->|"Pandas DataFrame"| WF["apply_waterfall()"]
    T10 -->|"waterfall + ledger"| WF
    T10 -->|"record_transaction()"| Ledger["Hash-Chained Ledger"]
    T8 --> Ledger
    T11 -->|"LLM call"| LLM2["Grok-3 (separate)"]
    T14 -->|"LLM call"| LLM2
```

## Waterfall Engine Flow

```mermaid
flowchart TD
    Start["Incoming Revenue<br/>$4,250,000"] --> Sort["Sort rules by priority"]
    Sort --> R1{"Rule 1: Percentage<br/>Financier 100%<br/>cap $28M"}
    R1 -->|"$4,250,000"| Payout1["Financier: $4,250,000"]
    R1 -->|"remaining: $0"| R2{"Rule 2: Fixed<br/>Completion Bond<br/>$840K"}
    R2 -->|"$0 (exhausted)"| R3{"Rule 3: Percentage<br/>Sales Agent 15%"}
    R3 -->|"$0"| R4{"Rule 4: Percentage<br/>Producer 10%"}
    R4 -->|"$0"| R5{"Rule 5: Residual<br/>Profit Participants"}
    R5 -->|"$0"| Done["Disbursement Complete"]

    style Payout1 fill:#dcfce7,stroke:#166534
    style Done fill:#f1f5f9,stroke:#64748b
```

## Transaction Ledger Hash Chain

```mermaid
graph LR
    G["GENESIS"] -->|previous_hash| T1["Transaction #1<br/>Inflow $1.5M<br/>hash = SHA-256(<br/>txn_id|amt|ts|GENESIS)"]
    T1 -->|previous_hash| T2["Transaction #2<br/>Inflow $850K<br/>hash = SHA-256(<br/>txn_id|amt|ts|hash₁)"]
    T2 -->|previous_hash| T3["Transaction #3<br/>Inflow $1.2M<br/>hash = SHA-256(<br/>txn_id|amt|ts|hash₂)"]
    T3 -->|previous_hash| T4["Transaction #4<br/>Outflow $500K<br/>hash = SHA-256(<br/>txn_id|amt|ts|hash₃)"]
    T4 -->|previous_hash| TN["..."]

    T1 -.->|"balance += $1.5M"| Bal["Account Balance<br/>auto-updated"]
    T2 -.->|"balance += $850K"| Bal
    T4 -.->|"balance -= $500K"| Bal

    style G fill:#f1f5f9,stroke:#94a3b8
    style Bal fill:#dbeafe,stroke:#1e40af
```

## Database Schema

```mermaid
erDiagram
    users ||--o{ productions : created_by
    users ||--o{ stakeholders : created_by
    users ||--o{ audit_log : user_id
    users ||--o{ chat_conversations : user_id

    productions ||--o{ collection_accounts : production_id
    productions ||--o{ waterfall_rules : production_id
    productions ||--o{ disbursements : production_id
    productions ||--o{ contracts : production_id
    productions ||--o{ revenue_forecasts : production_id
    productions ||--o{ anomaly_alerts : production_id
    productions ||--o{ reports : production_id
    productions ||--o{ recoupment_positions : production_id

    productions }o--o{ stakeholders : production_stakeholders

    collection_accounts ||--o{ transactions : account_id

    stakeholders ||--o{ waterfall_rules : recipient_stakeholder_id
    stakeholders ||--o{ disbursements : stakeholder_id
    stakeholders ||--o{ recoupment_positions : stakeholder_id

    waterfall_rules ||--o{ disbursements : waterfall_rule_id
    transactions ||--o{ disbursements : transaction_id
    transactions ||--o{ anomaly_alerts : transaction_id

    chat_conversations ||--o{ chat_messages : thread_id

    users {
        uuid user_id PK
        varchar email UK
        varchar password_hash
        varchar display_name
        varchar role
    }

    productions {
        uuid production_id PK
        varchar title
        varchar project_type
        varchar genre
        varchar status
        numeric budget
        varchar currency
        uuid created_by FK
    }

    stakeholders {
        uuid stakeholder_id PK
        varchar name
        varchar role
        varchar company
        text bank_details_encrypted
        uuid created_by FK
    }

    collection_accounts {
        uuid account_id PK
        uuid production_id FK
        varchar account_name
        numeric balance
        varchar status
    }

    waterfall_rules {
        uuid rule_id PK
        uuid production_id FK
        integer priority
        uuid recipient_stakeholder_id FK
        varchar rule_type
        numeric percentage
        numeric cap
        boolean active
    }

    transactions {
        uuid transaction_id PK
        uuid account_id FK
        varchar transaction_type
        numeric amount
        varchar previous_hash
        varchar hash
        varchar status
    }

    disbursements {
        uuid disbursement_id PK
        uuid production_id FK
        uuid transaction_id FK
        uuid stakeholder_id FK
        numeric amount
        uuid waterfall_rule_id FK
        varchar status
    }

    contracts {
        uuid contract_id PK
        uuid production_id FK
        varchar contract_type
        jsonb parsed_rules
        varchar parsing_status
    }

    revenue_forecasts {
        uuid forecast_id PK
        uuid production_id FK
        varchar territory
        numeric predicted_amount
        jsonb confidence_interval
    }

    anomaly_alerts {
        uuid alert_id PK
        uuid production_id FK
        uuid transaction_id FK
        varchar alert_type
        varchar severity
        boolean resolved
    }
```

## Module Architecture Pattern

```mermaid
graph TD
    subgraph Module["Each Module (e.g. modules/waterfall.py)"]
        Tool["AI Tool Function<br/>get_waterfall_rules(production_id)<br/>→ markdown string"]
        Routes["register_routes(rt)<br/>• /module/waterfall (list)<br/>• /module/waterfall/new (form)<br/>• /module/waterfall/create (POST)<br/>• /module/waterfall/{id} (detail)"]
        UI["FastHTML Components<br/>Div, Table, Form, Button<br/>stat cards, deal cards"]
    end

    subgraph Integration
        Agent["LangGraph Agent"] -->|"calls"| Tool
        Interceptor["Command Interceptor"] -->|"calls"| Tool
        AppPy["app.py"] -->|"register_routes(rt)"| Routes
        Sidebar["Sidebar Nav"] -->|"loadModule()"| Routes
    end

    Routes -->|"HTMX swap"| Center["#center-content"]
    Tool -->|"return markdown"| Chat["Chat bubble"]

    style Module fill:#f8fafc,stroke:#e2e8f0
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant A as app.py
    participant Auth as utils/auth.py
    participant DB as PostgreSQL

    B->>A: GET /login
    A-->>B: Login form

    B->>A: POST /login (email, password)
    A->>Auth: authenticate(email, password)
    Auth->>DB: SELECT user by email
    DB-->>Auth: user row (with password_hash)
    Auth->>Auth: bcrypt.checkpw(password, hash)
    Auth-->>A: user dict (or None)

    alt Authentication Success
        A->>A: session["user_id"] = user_id
        A-->>B: Redirect → /
        B->>A: GET /
        A->>Auth: get_user_by_id(session.user_id)
        A-->>B: 3-pane layout + AG-UI chat
    else Authentication Failure
        A-->>B: Login form + "Invalid email or password"
    end
```

## Deployment

```mermaid
graph TB
    subgraph Cloud["Production (Coolify / Docker)"]
        Docker["Docker Container<br/>python app.py"]
        PG["PostgreSQL<br/>ahcam schema<br/>15 tables"]
        XAI["XAI API<br/>Grok-3"]
    end

    subgraph Build["CI/CD"]
        GH["GitHub<br/>push to main"]
        Coolify["Coolify<br/>auto-deploy"]
    end

    subgraph Config["Environment"]
        ENV["DB_URL<br/>XAI_API_KEY<br/>JWT_SECRET<br/>ENCRYPTION_KEY"]
    end

    GH -->|webhook| Coolify
    Coolify -->|docker build| Docker
    Docker -->|port 5011| LB["Load Balancer"]
    Docker --> PG
    Docker --> XAI
    ENV --> Docker

    LB -->|HTTPS| Users["Users"]
```

## File Structure

```
ahcam/
├── app.py                      # Main entry: layout, auth, agent, routes (~750 lines)
├── config/
│   └── settings.py             # Constants: statuses, roles, rule types, territories
├── modules/                    # 10 product modules (tool + routes + UI each)
│   ├── productions.py          # Production CRUD
│   ├── stakeholders.py         # Stakeholder management
│   ├── collections.py          # Collection account management
│   ├── waterfall.py            # Waterfall engine (Pandas) + rule builder
│   ├── transactions.py         # Immutable ledger UI
│   ├── disbursements.py        # Payout processing
│   ├── contracts.py            # AI contract parser (Grok LLM)
│   ├── reports.py              # Collection statements + recoupment positions
│   ├── forecasting.py          # AI revenue forecasting (Grok LLM)
│   └── anomaly.py              # Transaction anomaly detection
├── utils/
│   ├── db.py                   # SQLAlchemy singleton pool
│   ├── auth.py                 # bcrypt + JWT (7-day expiry)
│   ├── ledger.py               # SHA-256 hash chain + verify_chain()
│   └── agui/                   # WebSocket chat engine
│       ├── core.py             # AGUIThread, UI, streaming, command routing
│       ├── chat_store.py       # Chat persistence (PostgreSQL)
│       └── styles.py           # Chat CSS (light theme)
├── sql/                        # 12 migrations (01–12)
├── data/                       # 6 CSVs + load_seed_data.py
├── tests/
│   ├── test_suite.py           # Unit tests (DB, auth, waterfall, ledger, config)
│   ├── capture_guide.py        # Playwright screenshot capture
│   └── capture_video.py        # Playwright video/GIF generation
├── docs/
│   ├── business_overview.md    # Business logic and data model
│   ├── architecture_readme.md  # This file (Mermaid diagrams)
│   ├── demo_video.mp4          # 39-second product demo
│   └── demo_video.gif          # Animated demo for README
├── static/guide/               # 13 module screenshots
├── Dockerfile                  # Python 3.13-slim, port 5011
├── docker-compose.yml          # Single-service deployment
├── requirements.txt            # 14 dependencies
├── .env.sample                 # Template for environment variables
├── CLAUDE.md                   # AI assistant project context
└── README.md                   # Project readme with demo GIF
```
