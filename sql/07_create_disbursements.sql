-- Disbursements table
CREATE TABLE IF NOT EXISTS ahcam.disbursements (
    disbursement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    transaction_id UUID REFERENCES ahcam.transactions(transaction_id),
    stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    amount NUMERIC(15, 2) NOT NULL,
    waterfall_rule_id UUID REFERENCES ahcam.waterfall_rules(rule_id),
    status VARCHAR(20) DEFAULT 'calculated',
    approved_by UUID REFERENCES ahcam.users(user_id),
    approved_at TIMESTAMP,
    payment_reference VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_disbursements_production ON ahcam.disbursements(production_id);
CREATE INDEX IF NOT EXISTS idx_disbursements_status ON ahcam.disbursements(status);
