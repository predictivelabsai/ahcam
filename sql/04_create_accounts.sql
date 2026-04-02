-- Collection accounts table
CREATE TABLE IF NOT EXISTS ahcam.collection_accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    account_name VARCHAR(500) NOT NULL,
    bank_name VARCHAR(255),
    account_number_encrypted TEXT,
    routing_encrypted TEXT,
    balance NUMERIC(15, 2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'active',
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_accounts_production ON ahcam.collection_accounts(production_id);
CREATE INDEX IF NOT EXISTS idx_accounts_status ON ahcam.collection_accounts(status);
