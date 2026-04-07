-- Shared documents with per-stakeholder permissions
CREATE TABLE IF NOT EXISTS ahcam.shared_documents (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_name VARCHAR(500),
    file_path TEXT,
    file_hash VARCHAR(64),
    comment TEXT,
    uploaded_by UUID REFERENCES ahcam.users(user_id),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Link shared documents to productions
CREATE TABLE IF NOT EXISTS ahcam.shared_document_titles (
    doc_id UUID REFERENCES ahcam.shared_documents(doc_id) ON DELETE CASCADE,
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    PRIMARY KEY (doc_id, production_id)
);

-- Per-stakeholder document permissions
CREATE TABLE IF NOT EXISTS ahcam.shared_document_permissions (
    doc_id UUID REFERENCES ahcam.shared_documents(doc_id) ON DELETE CASCADE,
    stakeholder_id UUID REFERENCES ahcam.stakeholders(stakeholder_id) ON DELETE CASCADE,
    permission VARCHAR(20) DEFAULT 'view',
    PRIMARY KEY (doc_id, stakeholder_id)
);

-- Collection statements: periodic account statements per production
CREATE TABLE IF NOT EXISTS ahcam.collection_statements (
    statement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    statement_name VARCHAR(500),
    period_start DATE,
    period_end DATE,
    issued_date DATE,
    payment_date DATE,
    next_due_date DATE,
    content JSONB DEFAULT '{}',
    pdf_path TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    account_manager VARCHAR(500),
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_statements_production ON ahcam.collection_statements(production_id);
