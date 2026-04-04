-- CRM: Deals, Contacts, Sales/Collections consolidated
CREATE TABLE IF NOT EXISTS ahcam.crm_contacts (
    contact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    contact_type VARCHAR(50) DEFAULT 'distributor',
    company VARCHAR(500),
    email VARCHAR(255),
    phone VARCHAR(50),
    territory VARCHAR(100),
    notes JSONB DEFAULT '{}',
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ahcam.crm_deals (
    deal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    production_id UUID REFERENCES ahcam.productions(production_id),
    contact_id UUID REFERENCES ahcam.crm_contacts(contact_id),
    deal_type VARCHAR(50) DEFAULT 'distribution',
    status VARCHAR(50) DEFAULT 'pipeline',
    stage VARCHAR(50) DEFAULT 'lead',
    amount NUMERIC(15, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    territory VARCHAR(100),
    close_date DATE,
    notes JSONB DEFAULT '{}',
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ahcam.crm_activities (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id UUID REFERENCES ahcam.crm_deals(deal_id) ON DELETE CASCADE,
    contact_id UUID REFERENCES ahcam.crm_contacts(contact_id),
    activity_type VARCHAR(50) DEFAULT 'note',
    description TEXT,
    due_date DATE,
    completed BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crm_deals_status ON ahcam.crm_deals(status);
CREATE INDEX IF NOT EXISTS idx_crm_deals_stage ON ahcam.crm_deals(stage);
CREATE INDEX IF NOT EXISTS idx_crm_deals_production ON ahcam.crm_deals(production_id);
CREATE INDEX IF NOT EXISTS idx_crm_contacts_type ON ahcam.crm_contacts(contact_type);
