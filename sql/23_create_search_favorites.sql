-- User favorites: bookmark any entity
CREATE TABLE IF NOT EXISTS ahcam.user_favorites (
    user_id UUID REFERENCES ahcam.users(user_id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, entity_type, entity_id)
);

-- User recent views: track recently accessed entities
CREATE TABLE IF NOT EXISTS ahcam.user_recent_views (
    view_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES ahcam.users(user_id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_title VARCHAR(500),
    viewed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recent_views_user ON ahcam.user_recent_views(user_id, viewed_at DESC);
