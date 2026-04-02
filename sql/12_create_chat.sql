-- Chat conversations and messages
CREATE TABLE IF NOT EXISTS ahcam.chat_conversations (
    thread_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES ahcam.users(user_id),
    title VARCHAR(500) DEFAULT 'New chat',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ahcam.chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID REFERENCES ahcam.chat_conversations(thread_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_thread ON ahcam.chat_messages(thread_id, created_at);
