# AHCAM Business Overview

Ashland Hill Collection Account Management (AHCAM) is an AI-powered platform for managing collection accounts in film and entertainment finance. It competes with incumbents like Freeway Entertainment and Fintage House, differentiated by AI contract parsing, predictive revenue forecasting, anomaly detection, and a natural-language query interface.

## What Is a Collection Account?

In film finance, a **Collection Account Management Agreement (CAMA)** is a legal arrangement where an independent third party manages the flow of revenues from a film or TV production. Distributors pay into a segregated bank account (the "collection account"), and funds are disbursed to stakeholders according to a contractually defined priority order called a **waterfall**.

This ensures:
- **Transparency** — all parties can see what has been collected and disbursed
- **Fairness** — recoupment follows the agreed priority, preventing disputes
- **Audit trail** — every payment is recorded immutably for compliance and audit

## Business Functions

### 1. Production Registry

Tracks film and TV projects through their lifecycle.

| Field | Description |
|-------|-------------|
| Title & type | Feature film, documentary, series, short, animation |
| Status | Development, pre-production, production, post-production, completed, released |
| Financials | Budget, currency, territory |
| Personnel | Producer, director, cast summary |

Each production has one or more collection accounts and a set of waterfall rules governing how revenue is distributed.

### 2. Stakeholder Management

Centralised directory of all parties involved across productions.

| Role | Description | Example |
|------|-------------|---------|
| Financier | Senior lender or equity investor providing production capital | Apex Film Finance, Eagle Point Investors |
| Distributor | Acquires distribution rights for specific territories | Lionsgate International, Pathe Distribution, Toho International |
| Sales Agent | Sells international distribution rights on behalf of the producer | Horizon Sales Agency |
| Producer | Develops and oversees the production | Sarah Chen, Jean-Luc Moreau |
| Guild | Industry union collecting residual payments | WGA, SAG-AFTRA |
| Completion Guarantor | Insures the production will be delivered on budget | Northstar Completion Guarantors |
| Talent | Above-the-line creative participants with profit participation | Directors, lead actors |

Stakeholders are linked to productions with specific roles and participation percentages. Bank details are stored encrypted (Fernet) for payment processing.

### 3. Collection Accounts

Segregated bank accounts, one per production, where all distribution revenues are deposited.

- **Balance tracking** — real-time balance updated on every transaction
- **Multi-currency** — USD, EUR, GBP, CAD, AUD, JPY, CNY
- **Status management** — active, frozen, or closed
- **Bank details** — name, account number (encrypted), routing (encrypted)

### 4. Waterfall Engine

The core of the platform. Executes priority-ordered recoupment rules to determine how collected revenue is split among stakeholders.

#### Rule Types

| Type | Behaviour | Example |
|------|-----------|---------|
| **Percentage** | Recipient gets X% of remaining balance | "Financier recoups 100% until $28M cap" |
| **Fixed** | Recipient gets a flat amount (up to cap) | "Completion bond fee: $840K" |
| **Corridor** | Percentage applies only within a revenue band | "Producer gets 50% of revenue between $8M–$12M" |
| **Residual** | Recipient gets everything remaining | "Net profits split per interparty agreement" |

#### Execution Flow

```
Incoming Revenue ($4.25M)
  |
  |--> Priority 1: Financier (100%, cap $28M)     -> $4,250,000
  |--> Priority 2: Completion Bond (fixed $840K)   -> $0 (remaining exhausted)
  |--> Priority 3: Sales Agent (15%)               -> $0
  |--> Priority 4: Producer (10%)                  -> $0
  |--> Priority 5: Profit Participants (residual)  -> $0
```

Each rule can have:
- **Cap** — maximum payout (e.g., senior lender stops recouping at $28M)
- **Floor** — minimum guaranteed payout
- **Corridor** — percentage applies only within a defined revenue range
- **Cross-collateralisation group** — pools revenues across multiple productions

### 5. Immutable Transaction Ledger

Every financial transaction is recorded in a tamper-proof, append-only ledger using SHA-256 hash chaining.

```
Transaction #1:  hash = SHA-256(txn_id | amount | timestamp | "GENESIS")
Transaction #2:  hash = SHA-256(txn_id | amount | timestamp | hash_of_#1)
Transaction #3:  hash = SHA-256(txn_id | amount | timestamp | hash_of_#2)
```

**Properties:**
- **Append-only** — no updates or deletes on transaction records
- **Reversals** — create a new offsetting transaction, preserving full history
- **Chain verification** — `verify_chain()` detects any tampering by validating the hash sequence
- **Auto-balance** — account balance updated atomically on each transaction

Transaction types:
- **Inflow** — distributor payment into collection account (increases balance)
- **Outflow** — disbursement to stakeholder (decreases balance)
- **Adjustment** — correction entry (auditor-initiated)

### 6. Disbursement Processing

Automates payout calculations based on waterfall rules.

**Flow:**
1. Waterfall engine calculates each stakeholder's share of available funds
2. For each non-zero payout, an outflow transaction is recorded in the ledger
3. A disbursement record links the transaction to the waterfall rule and stakeholder
4. Status tracks the payment lifecycle: calculated → approved → processing → completed

### 7. AI Contract Parser

Upload a CAMA or distribution agreement and the AI extracts structured data.

**Extracts:**
- **Parties** — all signatories with their roles
- **Waterfall rules** — priority, recipient, type, percentage, cap
- **Key terms** — dates, territories, conditions, minimum guarantees

The parsed output can be reviewed and approved before auto-creating waterfall rules in the system.

### 8. Collection Reports

Generates stakeholder-specific financial statements showing:

| Section | Content |
|---------|---------|
| Account summary | Account names, balances, currencies, statuses |
| Transaction summary | Count and total by type (inflow/outflow) |
| Disbursement detail | Per-stakeholder amounts and status |
| Recoupment position | Total owed vs. received vs. outstanding per stakeholder |

Reports can be generated per production or per stakeholder across all their productions.

### 9. Revenue Forecasting

AI-generated predictions based on production metadata and historical transaction patterns.

**Outputs:**
- 12-month revenue projection by quarter (Q1–Q4)
- Territory breakdown (top 5 markets)
- Revenue by source (theatrical, home video, streaming, TV sales)
- Confidence level and key assumptions

### 10. Anomaly Detection

Scans the transaction ledger for irregularities.

| Alert Type | Detection Method |
|-----------|-----------------|
| Duplicate transaction | Same amount + date + account |
| Unusual amount | Transaction >3x the account average |
| Timing irregularity | Payments outside expected windows |
| Rule violation | Disbursement inconsistent with waterfall rules |

Alerts are classified by severity (low, medium, high, critical) and tracked through resolution.

## Data Model

### Entity Relationship Summary

```
Productions ──< Collection Accounts ──< Transactions
     |                                       |
     ├──< Waterfall Rules                    └── hash chain (SHA-256)
     |         |
     ├──< Disbursements ──> Transactions
     |
     ├──< Contracts (AI-parsed)
     ├──< Revenue Forecasts
     ├──< Anomaly Alerts
     └──< Reports

Productions >──< Stakeholders  (via production_stakeholders junction)
                    |
                    └── bank_details_encrypted (Fernet)

Users ──< audit_log (every mutation recorded)
```

### Table Summary

| Table | Records | Description |
|-------|---------|-------------|
| `users` | 1 | Platform users with role-based access |
| `productions` | 15 | Film/TV projects across 6 statuses |
| `stakeholders` | 20 | Financiers, distributors, producers, guilds, talent |
| `production_stakeholders` | 27 | Many-to-many with role and participation % |
| `collection_accounts` | 15 | One per production, $22.8M total balance |
| `waterfall_rules` | 26 | 6 productions with full recoupment chains |
| `transactions` | 33 | Hash-chained inflows totalling $22.8M |
| `disbursements` | — | Created when waterfall is executed |
| `contracts` | — | Created when contracts are parsed |
| `revenue_forecasts` | — | Created when forecasts are generated |
| `anomaly_alerts` | — | Created when anomaly scans run |
| `reports` | — | Created when reports are generated |
| `audit_log` | — | Every mutation tracked |
| `chat_conversations` | — | AI chat session headers |
| `chat_messages` | — | Individual chat messages |

## Seed Data Profile

### Productions (15)

| Category | Count | Budget Range |
|----------|-------|-------------|
| Feature films | 12 | $5.5M – $45M |
| Documentary | 1 | $3.2M |
| Series | 1 | $22M |
| Animation | 1 | $7M |

**Status breakdown:** 3 development, 2 pre-production, 3 production, 2 post-production, 2 completed, 3 released

**Territories:** US/Canada (7), Italy (2), France (1), UK (1), South Korea (1), Japan (1), Middle East (1), Australia/NZ (1), Eastern Europe (1), Spain (1)

### Stakeholders (20)

| Role | Count | Examples |
|------|-------|---------|
| Producer | 5 | Sarah Chen, Jean-Luc Moreau, Robert Kim, Ahmed Hassan, Marie Tremblay |
| Distributor | 5 | Global Screen, Lionsgate, Pathe, Toho, Pacific Rim |
| Financier | 3 | Apex Film Finance, Eagle Point Investors, Mediterranean Film Fund |
| Talent | 3 | David Park, Denis Villeneuve, Jordan Peele |
| Guild | 2 | WGA, SAG-AFTRA |
| Sales Agent | 1 | Horizon Sales Agency |
| Completion Guarantor | 1 | Northstar Completion Guarantors |

### Transaction Flow ($22.8M across 33 transactions)

| Source Distributor | Total Inflows | Transactions |
|-------------------|---------------|-------------|
| Lionsgate International | $8.8M | 9 |
| Global Screen Distribution | $6.8M | 9 |
| Pathe Distribution | $3.2M | 4 |
| Toho International | $3.0M | 5 |
| Pacific Rim Distributors | $2.1M | 5 |

### Waterfall Rules (26 rules across 6 productions)

| Production | Rules | Highest Cap | Key Positions |
|-----------|-------|-------------|---------------|
| The Last Horizon | 5 | $28M | Apex (senior debt), Northstar (bond), Horizon (15% commission) |
| Code Red | 5 | $22M | Apex (loan), Lionsgate ($8M MG), Horizon (12.5%) |
| Midnight in Marrakech | 4 | $8M | MFF (senior), Pathe (25% commission), corridor rule |
| Blood Orange | 4 | $7M | MFF (finance), Pathe (20%), Italian tax credit $2.2M |
| Broken Strings | 4 | $8.5M | Eagle Point (equity), WGA (3%), SAG (4%) |
| The Baker's Daughter | 4 | $3M | Apex (gap), Global Screen (20%), UK tax credit $1.1M |

## Competitive Positioning

| Capability | Freeway / Fintage | AHCAM |
|-----------|-------------------|-------|
| Waterfall execution | Manual / spreadsheet | Automated engine with 4 rule types |
| Transaction integrity | Standard DB | SHA-256 hash-chained immutable ledger |
| Contract setup | Manual legal review | AI-powered extraction from PDFs |
| Revenue forecasting | External consultants | Built-in AI predictions by territory |
| Anomaly detection | Periodic manual audit | Real-time automated scanning |
| Stakeholder queries | Email / portal login | Natural-language AI chat + structured commands |
| Reporting | Quarterly PDF statements | On-demand generation with stakeholder-specific views |
| Technology | Legacy enterprise software | Modern Python stack (FastHTML, LangGraph, PostgreSQL) |
