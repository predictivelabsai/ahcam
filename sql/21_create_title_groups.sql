-- Title groups: group productions for cross-collateralization or reporting
CREATE TABLE IF NOT EXISTS ahcam.title_groups (
    group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_name VARCHAR(500) NOT NULL,
    comment TEXT,
    created_by UUID REFERENCES ahcam.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Junction table linking productions to title groups
CREATE TABLE IF NOT EXISTS ahcam.title_group_members (
    group_id UUID REFERENCES ahcam.title_groups(group_id) ON DELETE CASCADE,
    production_id UUID REFERENCES ahcam.productions(production_id) ON DELETE CASCADE,
    PRIMARY KEY (group_id, production_id)
);
