-- Waterfall rules and recoupment positions
CREATE TABLE IF NOT EXISTS ahcam.waterfall_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    priority INTEGER NOT NULL,
    recipient_stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    recipient_label VARCHAR(255),
    rule_type VARCHAR(20) DEFAULT 'percentage',
    percentage NUMERIC(8, 4),
    cap NUMERIC(15, 2),
    floor NUMERIC(15, 2),
    corridor_start NUMERIC(15, 2),
    corridor_end NUMERIC(15, 2),
    recoupment_basis VARCHAR(100),
    cross_collateral_group VARCHAR(100),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ahcam.recoupment_positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    total_owed NUMERIC(15, 2) DEFAULT 0.00,
    total_received NUMERIC(15, 2) DEFAULT 0.00,
    outstanding NUMERIC(15, 2) DEFAULT 0.00,
    last_calculated TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_waterfall_production ON ahcam.waterfall_rules(production_id, priority);
CREATE INDEX IF NOT EXISTS idx_recoupment_production ON ahcam.recoupment_positions(production_id);
