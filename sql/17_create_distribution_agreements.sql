-- Distribution Agreements: territory-level deals with MG tracking
CREATE TABLE IF NOT EXISTS ahcam.distribution_agreements (
    agreement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    distributor_stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    territory VARCHAR(100) NOT NULL,
    distributor_name VARCHAR(500),
    agreement_type VARCHAR(100) DEFAULT 'distribution',
    signature_date DATE,
    term_years INTEGER,
    start_trigger VARCHAR(100),
    start_date DATE,
    expiry_date DATE,
    expired BOOLEAN DEFAULT FALSE,
    mg_amount NUMERIC(15,2),
    mg_currency VARCHAR(10) DEFAULT 'USD',
    mg_paid NUMERIC(15,2) DEFAULT 0.00,
    contract_available BOOLEAN DEFAULT FALSE,
    financial_status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_da_production ON ahcam.distribution_agreements(production_id);
CREATE INDEX IF NOT EXISTS idx_da_territory ON ahcam.distribution_agreements(territory);
CREATE INDEX IF NOT EXISTS idx_da_distributor ON ahcam.distribution_agreements(distributor_stakeholder_id);
