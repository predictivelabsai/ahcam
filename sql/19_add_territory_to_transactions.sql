-- Add territory and payment fields to transactions
ALTER TABLE ahcam.transactions ADD COLUMN IF NOT EXISTS territory VARCHAR(100);
ALTER TABLE ahcam.transactions ADD COLUMN IF NOT EXISTS payment_date DATE;
ALTER TABLE ahcam.transactions ADD COLUMN IF NOT EXISTS reported BOOLEAN DEFAULT FALSE;
ALTER TABLE ahcam.transactions ADD COLUMN IF NOT EXISTS distributor_name VARCHAR(500);

-- Production comments with threaded replies
CREATE TABLE IF NOT EXISTS ahcam.production_comments (
    comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    user_id UUID REFERENCES ahcam.users(user_id),
    content TEXT NOT NULL,
    parent_comment_id UUID REFERENCES ahcam.production_comments(comment_id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comments_production ON ahcam.production_comments(production_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON ahcam.production_comments(parent_comment_id);
