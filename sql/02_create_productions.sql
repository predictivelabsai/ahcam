-- Productions table
CREATE TABLE IF NOT EXISTS ahcam.productions (
    production_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    project_type VARCHAR(50) DEFAULT 'feature_film',
    genre VARCHAR(100),
    status VARCHAR(50) DEFAULT 'development',
    budget NUMERIC(15, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    producer VARCHAR(255),
    director VARCHAR(255),
    cast_summary TEXT,
    synopsis TEXT,
    territory VARCHAR(100),
    notes JSONB DEFAULT '{}',
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_productions_status ON ahcam.productions(status);
CREATE INDEX IF NOT EXISTS idx_productions_created_by ON ahcam.productions(created_by);
