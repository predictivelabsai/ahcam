-- Beneficiary bank accounts for stakeholder payouts
CREATE TABLE IF NOT EXISTS ahcam.beneficiary_bank_accounts (
    bank_account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    beneficiary_name VARCHAR(500),
    bank_name VARCHAR(500),
    bank_address TEXT,
    aba_routing_encrypted TEXT,
    account_number_encrypted TEXT,
    iban_encrypted TEXT,
    swift_bic VARCHAR(20),
    beneficiary_address TEXT,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bank_accounts_production ON ahcam.beneficiary_bank_accounts(production_id);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_stakeholder ON ahcam.beneficiary_bank_accounts(stakeholder_id);
