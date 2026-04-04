-- Add Google OAuth support to users table
ALTER TABLE ahcam.users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255) UNIQUE;
CREATE INDEX IF NOT EXISTS idx_users_google_id ON ahcam.users(google_id);

-- Make password_hash nullable (Google-only users won't have one)
ALTER TABLE ahcam.users ALTER COLUMN password_hash DROP NOT NULL;
