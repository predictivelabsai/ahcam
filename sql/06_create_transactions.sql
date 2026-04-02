-- Immutable transaction ledger with hash chain
CREATE TABLE IF NOT EXISTS ahcam.transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES ahcam.collection_accounts(account_id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    source_stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    destination_stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    reference VARCHAR(255),
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    previous_hash VARCHAR(64),
    hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_account ON ahcam.transactions(account_id, created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON ahcam.transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON ahcam.transactions(status);
