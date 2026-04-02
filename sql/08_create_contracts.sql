-- Contracts table (for AI-parsed documents)
CREATE TABLE IF NOT EXISTS ahcam.contracts (
    contract_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    contract_type VARCHAR(50) DEFAULT 'cama',
    file_path TEXT,
    file_hash VARCHAR(64),
    parsed_rules JSONB DEFAULT '[]',
    parsed_parties JSONB DEFAULT '[]',
    parsed_terms JSONB DEFAULT '{}',
    parsing_status VARCHAR(20) DEFAULT 'pending',
    parsed_at TIMESTAMP,
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contracts_production ON ahcam.contracts(production_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON ahcam.contracts(parsing_status);
