-- Prompt versioning system
CREATE TABLE IF NOT EXISTS ahcam.prompt_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES ahcam.prompt_templates(template_id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    prompt TEXT NOT NULL,
    change_summary VARCHAR(500),
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_versions_template ON ahcam.prompt_versions(template_id, version DESC);

-- Add source_file column to track which prompts/ file a template originated from
ALTER TABLE ahcam.prompt_templates ADD COLUMN IF NOT EXISTS source_file VARCHAR(255);
