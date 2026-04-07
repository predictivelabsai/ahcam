-- Territory avails: track rights availability per production/territory
CREATE TABLE IF NOT EXISTS ahcam.territory_avails (
    avail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    territory VARCHAR(100) NOT NULL,
    rights_type VARCHAR(100) DEFAULT 'all_rights',
    available BOOLEAN DEFAULT TRUE,
    reserved_by UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    agreement_id UUID REFERENCES ahcam.distribution_agreements(agreement_id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(production_id, territory, rights_type)
);

CREATE INDEX IF NOT EXISTS idx_avails_production ON ahcam.territory_avails(production_id);
CREATE INDEX IF NOT EXISTS idx_avails_territory ON ahcam.territory_avails(territory);
CREATE INDEX IF NOT EXISTS idx_avails_agreement ON ahcam.territory_avails(agreement_id);
