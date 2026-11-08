-- Conversation summaries are scoped to a business. Do not run on production without review.
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY,
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    customer_phone TEXT NOT NULL,
    last_message TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_conversations_business_id ON conversations(business_id);
