-- Reports and audit log
CREATE TABLE IF NOT EXISTS ahcam.reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    report_type VARCHAR(50) DEFAULT 'collection_statement',
    stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id),
    content JSONB DEFAULT '{}',
    file_path TEXT,
    period_start DATE,
    period_end DATE,
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ahcam.audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES ahcam.users(user_id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_entity ON ahcam.audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON ahcam.audit_log(user_id);
