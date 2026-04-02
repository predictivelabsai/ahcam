-- Stakeholders table
CREATE TABLE IF NOT EXISTS ahcam.stakeholders (
    stakeholder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    role VARCHAR(50) DEFAULT 'distributor',
    company VARCHAR(500),
    email VARCHAR(255),
    phone VARCHAR(50),
    bank_details_encrypted TEXT,
    notes JSONB DEFAULT '{}',
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Junction table: production <-> stakeholder
CREATE TABLE IF NOT EXISTS ahcam.production_stakeholders (
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id) ON DELETE CASCADE,
    role_in_production VARCHAR(100),
    participation_percentage NUMERIC(8, 4),
    PRIMARY KEY (production_id, stakeholder_id)
);

CREATE INDEX IF NOT EXISTS idx_stakeholders_role ON ahcam.stakeholders(role);
CREATE INDEX IF NOT EXISTS idx_stakeholders_name ON ahcam.stakeholders(name);
