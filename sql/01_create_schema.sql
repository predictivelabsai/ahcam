-- AHCAM schema and users table
CREATE SCHEMA IF NOT EXISTS ahcam;

CREATE TABLE IF NOT EXISTS ahcam.users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'manager',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
