CREATE TABLE IF NOT EXISTS conversation (
    conversation_id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL REFERENCES users(id),
    user2_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user1_id, user2_id),
    CHECK (user1_id < user2_id)
);

CREATE TABLE IF NOT EXISTS message (
    message_id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversation(conversation_id),
    sender_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS message_read_receipt (
    message_id INTEGER NOT NULL REFERENCES message(message_id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    read_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (message_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_message_conversation ON message(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_user1 ON conversation(user1_id);
CREATE INDEX IF NOT EXISTS idx_conversation_user2 ON conversation(user2_id);
