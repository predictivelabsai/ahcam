# AHCAM User Stories & Stakeholder Questionnaire

> **Purpose**: Validate assumptions, uncover gaps, and prioritize features for the Ashland Hill Collection Account Management platform.
> **How to use**: Review each user story, rate its priority (Must/Should/Could/Won't), and answer the follow-up questions. Add comments wherever your real-world workflow differs from what's described.

---

## 1. User Personas

| ID | Persona | Description |
|----|---------|-------------|
| P1 | Collection Account Manager | Day-to-day CAM operator: sets up productions, defines waterfalls, records transactions, runs disbursements, generates reports |
| P2 | Finance Administrator | System admin with oversight: manages users, reviews audit trails, batch-processes contracts |
| P3 | Financier / Equity Investor | Passive stakeholder viewing recoupment position, receives periodic statements |
| P4 | Sales Agent | Manages territory sales, distribution agreements, minimum guarantees |
| P5 | Distributor | Reports revenue, submits payments, tracks obligations |
| P6 | Producer / Profit Participant | Monitors profit participation, reviews waterfall position, receives residuals |
| P7 | Legal / Compliance Officer | Reviews contracts, ensures audit integrity, monitors anomalies |
| P8 | External Auditor | Read-only access to ledger, hash-chain verification, report exports |

### Questionnaire: Personas

- Q1.1: Which persona(s) best describe your role? Are there roles we're missing?
- Q1.2: How many people at your organization would use this platform, and in which roles?
- Q1.3: Do different team members need different levels of access to the same production? Describe.
- Q1.4: Do external parties (stakeholders, auditors) need direct platform access, or do they only receive reports?

---

## 2. Production Setup & Management

| ID | User Story | Persona |
|----|-----------|---------|
| US-01 | As a **Collection Account Manager**, I want to create a new production record with title, type, genre, budget, currency, key personnel, and territory so that all downstream CAM operations are linked to a single production. | P1 |
| US-02 | As a **Collection Account Manager**, I want to track production status (development, pre-production, production, post-production, completed, released) so that I can filter and prioritize active projects. | P1 |
| US-03 | As a **Finance Administrator**, I want to import multiple productions from a spreadsheet or CSV so that I can onboard a slate of titles quickly. | P2 |
| US-04 | As a **Producer**, I want to see all my productions in one dashboard with budget vs. collected revenue so I can track overall portfolio performance. | P6 |

### Questionnaire: Production Setup

- Q2.1: What information do you capture when setting up a new production? Is our field list (title, type, genre, budget, currency, producer, director, cast, synopsis, territory) sufficient?
- Q2.2: Do you manage productions individually or as slates/packages? If slates, how are they grouped?
- Q2.3: What production statuses do you use? Does our lifecycle (development -> pre-production -> production -> post-production -> completed -> released) match yours?
- Q2.4: Do you need to track production budgets at a line-item level, or is a single budget figure sufficient?
- Q2.5: How do you handle co-productions across multiple territories? Do they need separate collection accounts per territory?

---

## 3. Stakeholder Management

| ID | User Story | Persona |
|----|-----------|---------|
| US-05 | As a **Collection Account Manager**, I want to register stakeholders with their role (producer, financier, sales agent, distributor, profit participant, guild, talent, completion guarantor), company, contact info, and encrypted bank details so that disbursements can be processed accurately. | P1 |
| US-06 | As a **Collection Account Manager**, I want to link stakeholders to productions with a specific role and participation percentage so the waterfall engine knows who gets what. | P1 |
| US-07 | As a **Financier**, I want to view only my own productions, recoupment positions, and statements without seeing other stakeholders' details. | P3 |
| US-08 | As a **Legal Officer**, I want to verify that stakeholder bank details are encrypted at rest and that only authorized users can view them. | P7 |

### Questionnaire: Stakeholders

- Q3.1: What stakeholder roles do you work with? Are we missing any (e.g., completion guarantor, tax credit lender, gap financier, mezzanine financier)?
- Q3.2: How do you currently manage stakeholder bank details? What security/compliance requirements apply (e.g., PCI, SOC 2)?
- Q3.3: Do stakeholders change roles across productions (e.g., a distributor on one title is a co-financier on another)?
- Q3.4: How granular is participation? Is a single percentage per stakeholder per production sufficient, or do you need different percentages per revenue stream (theatrical, home video, streaming)?
- Q3.5: Do stakeholders currently have any self-service access to view their positions, or is everything communicated via periodic reports?

---

## 4. Collection Accounts

| ID | User Story | Persona |
|----|-----------|---------|
| US-09 | As a **Collection Account Manager**, I want to create segregated collection accounts per production with bank details, currency, and status (active/frozen/closed) so that revenue is properly ring-fenced. | P1 |
| US-10 | As a **Collection Account Manager**, I want to see real-time balances across all collection accounts in a single dashboard so I can spot issues quickly. | P1 |
| US-11 | As a **Finance Administrator**, I want to freeze or close a collection account and prevent further transactions against it. | P2 |
| US-12 | As a **Collection Account Manager**, I want to manage multi-currency accounts (USD, EUR, GBP, CAD, AUD, JPY, CNY) and see balances in both local and reporting currencies. | P1 |

### Questionnaire: Collection Accounts

- Q4.1: How many collection accounts does a typical production have? One per production, or multiple (e.g., per territory, per revenue stream)?
- Q4.2: Do you need automatic bank feed integration (receiving transaction data directly from the bank), or is manual entry sufficient for now?
- Q4.3: How do you handle currency conversion? Do you use a fixed contractual rate, spot rate at time of receipt, or something else?
- Q4.4: What does "freezing" an account mean in your workflow? What triggers it?
- Q4.5: Do you reconcile collection account balances against bank statements? How frequently?

---

## 5. Waterfall Engine

| ID | User Story | Persona |
|----|-----------|---------|
| US-13 | As a **Collection Account Manager**, I want to define priority-ordered waterfall rules (percentage, fixed, corridor, residual) with caps, floors, and cross-collateralization groups so that revenue is allocated per the contractual agreement. | P1 |
| US-14 | As a **Collection Account Manager**, I want to execute a waterfall calculation against incoming revenue and see a detailed breakdown of how each dollar was allocated across priorities. | P1 |
| US-15 | As a **Collection Account Manager**, I want to save waterfall templates so I can reuse standard structures across similar productions. | P1 |
| US-16 | As a **Legal Officer**, I want to compare the waterfall rules in the system against the original contract terms to verify accuracy. | P7 |
| US-17 | As a **Financier**, I want to see my cumulative recoupment position (total owed, total received, outstanding) updated after each waterfall execution. | P3 |
| US-18 | As a **Producer**, I want to model "what-if" scenarios by running the waterfall with hypothetical revenue amounts before actual collections arrive. | P6 |

### Questionnaire: Waterfall Engine

- Q5.1: How complex are your typical waterfall structures? How many priority tiers? Do you commonly use all four rule types (percentage, fixed, corridor, residual)?
- Q5.2: How do you handle **cross-collateralization** (offsetting losses on one title against profits on another)? Is this common in your deals?
- Q5.3: Do waterfall rules change over time (e.g., after a recoupment milestone is hit, percentages shift)? How do you handle versioning?
- Q5.4: Do you need to run waterfalls at different levels: per-transaction (each payment triggers a run), periodic (monthly/quarterly batch), or on-demand?
- Q5.5: How do you currently handle **corridor deals** (revenue bands where different splits apply)? Can you give an example?
- Q5.6: Do you need to track **cumulative recoupment** across multiple transactions, or is each waterfall run independent?
- Q5.7: Is "what-if" / scenario modeling a critical need, or a nice-to-have?
- Q5.8: Do you use waterfall templates across productions, or is every deal bespoke?

---

## 6. Transaction Ledger

| ID | User Story | Persona |
|----|-----------|---------|
| US-19 | As a **Collection Account Manager**, I want to record incoming payments (inflows) from distributors with amount, currency, source, reference, and description so that all revenue is tracked. | P1 |
| US-20 | As a **Collection Account Manager**, I want every transaction to be immutably hash-chained (SHA-256) so that the ledger cannot be tampered with. | P1 |
| US-21 | As a **Finance Administrator**, I want to reverse a transaction by creating an offsetting entry (not deleting the original) to maintain audit integrity. | P2 |
| US-22 | As an **External Auditor**, I want to verify the hash chain integrity of the entire transaction ledger to confirm no records have been altered. | P8 |
| US-23 | As a **Collection Account Manager**, I want to search and filter transactions by production, account, date range, type, and status. | P1 |

### Questionnaire: Transaction Ledger

- Q6.1: What information accompanies a typical incoming payment? Do you need to capture territory, media type, exploitation period, or other metadata?
- Q6.2: How important is an immutable audit trail? Is SHA-256 hash-chaining a requirement, or is standard database logging sufficient?
- Q6.3: How do you currently handle transaction reversals or corrections?
- Q6.4: What transaction statuses do you need (pending, confirmed, reversed)? Are there others (e.g., disputed, under review)?
- Q6.5: Do you receive payments in batches (e.g., monthly distributor reports with multiple line items), or individually?
- Q6.6: Do you need to reconcile transactions against distributor sales reports? How is that done today?

---

## 7. Disbursements

| ID | User Story | Persona |
|----|-----------|---------|
| US-24 | As a **Collection Account Manager**, I want to automatically generate disbursement records from waterfall execution so that payouts are calculated without manual work. | P1 |
| US-25 | As a **Finance Administrator**, I want to approve disbursements before they are processed to maintain control over outflows. | P2 |
| US-26 | As a **Collection Account Manager**, I want to track disbursement status (calculated, approved, processing, completed, failed) and see payment references. | P1 |
| US-27 | As a **Stakeholder**, I want to receive notification when a disbursement has been processed in my favor. | P3, P4, P5, P6 |

### Questionnaire: Disbursements

- Q7.1: What is your current disbursement approval workflow? How many approvals are needed, and by whom?
- Q7.2: Do you batch disbursements (e.g., monthly payouts) or process them as revenue arrives?
- Q7.3: How do you currently execute payments — manual bank transfers, payment APIs (Stripe, SEPA), or other?
- Q7.4: Do you need to hold back reserves (e.g., withholding tax, disputed amounts) before disbursing?
- Q7.5: How do you notify stakeholders of disbursements? Email, portal, PDF statement?
- Q7.6: Do you need multi-currency disbursement support (pay in the stakeholder's preferred currency)?

---

## 8. Contract Parsing (AI)

| ID | User Story | Persona |
|----|-----------|---------|
| US-28 | As a **Collection Account Manager**, I want to upload a CAMA (Collection Account Management Agreement) PDF and have AI extract the parties, waterfall rules, and key terms automatically. | P1 |
| US-29 | As a **Legal Officer**, I want to review and approve AI-extracted contract terms before they become active waterfall rules in the system. | P7 |
| US-30 | As a **Collection Account Manager**, I want to see a side-by-side view of the original contract text and the AI-extracted data so I can verify accuracy. | P1 |
| US-31 | As a **Finance Administrator**, I want to batch-upload multiple contracts and queue them for AI parsing. | P2 |

### Questionnaire: Contract Parsing

- Q8.1: What types of contracts do you need to parse (CAMA, distribution agreements, sales agency agreements, finance agreements, interparty agreements)?
- Q8.2: How standardized are your contracts? Are they mostly templated, or highly bespoke?
- Q8.3: What key data points do you need extracted from a contract? (parties, waterfall rules, territories, media rights, holdbacks, reporting periods, audit rights, etc.)
- Q8.4: What is your current process for translating contract terms into waterfall rules? How long does it take?
- Q8.5: Would you trust AI-extracted data with human review, or does every field need manual verification?
- Q8.6: Do you work with contracts in languages other than English?

---

## 9. Reports & Statements

| ID | User Story | Persona |
|----|-----------|---------|
| US-32 | As a **Collection Account Manager**, I want to generate collection account statements showing balances, transaction history, and waterfall positions per production. | P1 |
| US-33 | As a **Financier**, I want to receive quarterly recoupment statements showing my position (total owed, received, outstanding) across all my productions. | P3 |
| US-34 | As a **Sales Agent**, I want territory-level sales reports showing gross receipts, fees, and net amounts remitted. | P4 |
| US-35 | As a **Finance Administrator**, I want to schedule automatic report generation and email delivery on a recurring basis (monthly, quarterly). | P2 |
| US-36 | As an **External Auditor**, I want to export the full transaction ledger and waterfall execution history as CSV/PDF for offline review. | P8 |
| US-37 | As a **Collection Account Manager**, I want a financial overview dashboard with total collected, total disbursed, and pending amounts across all productions. | P1 |

### Questionnaire: Reports & Statements

- Q9.1: What reports do you produce today? Can you share samples or templates?
- Q9.2: How frequently are reports generated and distributed (monthly, quarterly, on-demand)?
- Q9.3: What format do stakeholders expect (PDF, Excel, online portal, email)?
- Q9.4: Do different stakeholders receive different views of the same data (e.g., a financier sees only their recoupment, not other parties)?
- Q9.5: Do you need a CGR (Certified Gross Receipts) report format? What fields does it require?
- Q9.6: Do you track outstanding/overdue amounts? How is aging calculated?
- Q9.7: What KPIs or summary metrics matter most on a dashboard?

---

## 10. Distribution Agreements & Territory Management

| ID | User Story | Persona |
|----|-----------|---------|
| US-38 | As a **Sales Agent**, I want to track distribution agreements by territory, media type, and deal terms (MG, advance, fee percentage) so I can manage my sales pipeline. | P4 |
| US-39 | As a **Collection Account Manager**, I want a sales matrix showing which territories are sold vs. available for each production. | P1 |
| US-40 | As a **Collection Account Manager**, I want an avails matrix showing which media rights (theatrical, home video, streaming, TV) are available by territory. | P1 |
| US-41 | As a **Sales Agent**, I want to track minimum guarantee payments and reconcile them against actual collections. | P4 |

### Questionnaire: Distribution & Territory

- Q10.1: How do you currently track which territories and media rights are sold vs. available?
- Q10.2: What deal terms do you track per distribution agreement (MG, advance, fee %, holdbacks, reporting periods, expiry dates)?
- Q10.3: Do you need to track sub-distribution (a distributor sub-licensing to another party)?
- Q10.4: How do you reconcile minimum guarantees against actual revenue? Is there an overage calculation?
- Q10.5: Do you deal with holdbacks (amounts withheld by distributors)? How are these tracked and released?

---

## 11. Revenue Forecasting (AI)

| ID | User Story | Persona |
|----|-----------|---------|
| US-42 | As a **Collection Account Manager**, I want AI-generated revenue forecasts for each production based on historical data, genre comparables, and territory analysis. | P1 |
| US-43 | As a **Financier**, I want to see projected recoupment timelines based on revenue forecasts so I can plan my cash flow. | P3 |
| US-44 | As a **Producer**, I want to compare actual collections against forecasts to understand production performance. | P6 |

### Questionnaire: Revenue Forecasting

- Q11.1: Do you currently forecast revenue? If so, what methodology (comps, historical trends, distributor estimates, internal models)?
- Q11.2: At what granularity do you forecast (total, by territory, by media type, by quarter)?
- Q11.3: How important are confidence intervals or ranges vs. point estimates?
- Q11.4: Would you use forecasts primarily for internal planning, or also to share with stakeholders?
- Q11.5: What data inputs would make forecasts most useful (box office comps, streaming viewership, festival performance, cast bankability)?

---

## 12. Anomaly Detection (AI)

| ID | User Story | Persona |
|----|-----------|---------|
| US-45 | As a **Finance Administrator**, I want the system to automatically flag duplicate transactions, unusual payment amounts, and timing irregularities. | P2 |
| US-46 | As a **Legal Officer**, I want to be alerted when a disbursement violates waterfall rules (e.g., paying more than the cap, skipping a priority). | P7 |
| US-47 | As a **Collection Account Manager**, I want to review, investigate, and resolve anomaly alerts with notes and status tracking. | P1 |

### Questionnaire: Anomaly Detection

- Q12.1: What types of anomalies or errors have you encountered in collection accounting? (duplicates, incorrect amounts, unauthorized payments, timing issues?)
- Q12.2: How do you currently catch and resolve errors?
- Q12.3: What severity levels make sense (low, medium, high, critical)? What constitutes "critical"?
- Q12.4: Do you need real-time alerting (email/notification when anomaly detected) or is periodic scanning sufficient?
- Q12.5: Who should be notified of anomalies, and through what channel?

---

## 13. CRM & Deal Pipeline

| ID | User Story | Persona |
|----|-----------|---------|
| US-48 | As a **Sales Agent**, I want to manage distribution deals through a pipeline (lead, negotiation, term sheet, due diligence, closing, closed won/lost) so I can track my sales process. | P4 |
| US-49 | As a **Collection Account Manager**, I want CRM contacts linked to stakeholder records so that deal contacts automatically become production stakeholders when a deal closes. | P1 |
| US-50 | As a **Sales Agent**, I want Kanban and list views of my deal pipeline filtered by territory, deal type, and stage. | P4 |

### Questionnaire: CRM & Deals

- Q13.1: Do you currently use a separate CRM system? If so, which one, and would you want integration or replacement?
- Q13.2: What deal stages do you track? Does our pipeline (lead -> negotiation -> term sheet -> due diligence -> closing -> closed) match yours?
- Q13.3: What information do you track per deal (parties, territory, media rights, MG, advance, fee %, deal memo, contract)?
- Q13.4: Do you need deal approval workflows (e.g., legal review before closing)?
- Q13.5: Would you want the CRM integrated into the main platform, or as a separate module?

---

## 14. AI Chat Assistant

| ID | User Story | Persona |
|----|-----------|---------|
| US-51 | As a **Collection Account Manager**, I want to ask natural-language questions ("What is the recoupment position for Midnight Horizon?") and get instant answers from the AI assistant. | P1 |
| US-52 | As a **Financier**, I want to ask the AI "How much have I recouped on Project X?" and get a clear, accurate answer without navigating multiple screens. | P3 |
| US-53 | As a **Collection Account Manager**, I want to execute commands via chat (e.g., "waterfall:run PROD_ID") as a power-user shortcut. | P1 |

### Questionnaire: AI Assistant

- Q14.1: What questions do you most frequently need to answer about collection accounts? (Imagine having an assistant you could ask anything.)
- Q14.2: Would you prefer structured commands (waterfall:run), natural language ("run the waterfall for Project X"), or both?
- Q14.3: How important is chat history / conversation memory?
- Q14.4: Should the AI assistant be able to take actions (create records, run calculations) or only answer questions?
- Q14.5: What level of trust would you place in AI-generated answers for financial data?

---

## 15. Security, Compliance & Audit

| ID | User Story | Persona |
|----|-----------|---------|
| US-54 | As a **Finance Administrator**, I want a complete audit log of every action (who did what, when, with before/after values) for compliance purposes. | P2 |
| US-55 | As a **Legal Officer**, I want role-based access control so that stakeholders can only see data related to their own productions and positions. | P7 |
| US-56 | As an **External Auditor**, I want to verify the integrity of the transaction ledger hash chain and export it for independent review. | P8 |
| US-57 | As a **Finance Administrator**, I want all sensitive data (bank details, SSNs) encrypted at rest with key rotation capability. | P2 |

### Questionnaire: Security & Compliance

- Q15.1: What compliance standards apply to your organization (SOC 2, GDPR, PCI DSS, local financial regulations)?
- Q15.2: What audit requirements do you face? How frequently are you audited?
- Q15.3: Do you need two-factor authentication (2FA) or single sign-on (SSO)?
- Q15.4: What data retention policies apply? How long must records be kept?
- Q15.5: Do you need IP-based access restrictions or VPN requirements?
- Q15.6: Are there specific regulatory bodies that oversee collection account management in your jurisdiction?

---

## 16. Integration & Workflow

| ID | User Story | Persona |
|----|-----------|---------|
| US-58 | As a **Finance Administrator**, I want to import transactions from bank statements (CSV/MT940) to reduce manual data entry. | P2 |
| US-59 | As a **Collection Account Manager**, I want email notifications when key events occur (payment received, disbursement approved, anomaly detected). | P1 |
| US-60 | As a **Finance Administrator**, I want to export data to accounting systems (Xero, QuickBooks, SAP) for general ledger reconciliation. | P2 |

### Questionnaire: Integration

- Q16.1: What systems does your collection accounting currently integrate with (banks, accounting software, ERPs, reporting tools)?
- Q16.2: How do you currently receive distributor payment data (email, portal, API, bank feed)?
- Q16.3: What file formats do you need for import/export (CSV, Excel, MT940, SWIFT, PDF)?
- Q16.4: Do you need real-time integrations or is batch (daily/weekly) sufficient?
- Q16.5: Do you use any industry-specific platforms (FilmChain, Rightsline, Cinando) that you'd want to integrate with?

---

## 17. General / Open-Ended

- Q17.1: What are the top 3 pain points in your current collection accounting workflow?
- Q17.2: What takes the most time in your day-to-day work that you wish were automated?
- Q17.3: What features would make you switch from your current system (or spreadsheets) to AHCAM?
- Q17.4: What's the biggest risk or fear you have about adopting a new platform?
- Q17.5: Is there anything about collection account management that we haven't covered in this questionnaire?
- Q17.6: How many productions do you typically manage simultaneously?
- Q17.7: What is the typical volume of transactions per month across all productions?
- Q17.8: Do you operate globally or in specific regions? Which territories are most important?

---

## Priority Rating Guide

For each user story, please rate using MoSCoW:

| Rating | Meaning |
|--------|---------|
| **Must** | Critical for launch — cannot operate without this |
| **Should** | Important — needed soon after launch |
| **Could** | Desirable — adds value but can wait |
| **Won't** | Not needed now — maybe in a future phase |

---

## How to Submit Feedback

1. Rate each user story (Must / Should / Could / Won't)
2. Answer questionnaire sections relevant to your role
3. Add comments or corrections inline
4. Note any missing user stories or workflows
5. Return to the AHCAM team for consolidation

**Contact**: [Your Name] — [email@ashlandhill.com]
