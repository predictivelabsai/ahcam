-- User prompt templates
CREATE TABLE IF NOT EXISTS ahcam.prompt_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES ahcam.users(user_id),
    name VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_templates_user ON ahcam.prompt_templates(user_id);
