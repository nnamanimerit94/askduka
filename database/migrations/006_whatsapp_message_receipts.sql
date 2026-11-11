-- Staging-only until reviewed; apply after migrations 001-005.
-- One receipt per business and provider message ID.
-- A receipt is not proof of successful WhatsApp delivery.
CREATE TABLE IF NOT EXISTS whatsapp_message_receipts (
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    message_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'sent', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (business_id, message_id)
);
CREATE INDEX IF NOT EXISTS ix_whatsapp_message_receipts_status_updated
    ON whatsapp_message_receipts(status, updated_at);
