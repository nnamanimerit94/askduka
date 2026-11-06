CREATE TABLE IF NOT EXISTS owner_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES owner_accounts(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_owner_sessions_user_id ON owner_sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_owner_sessions_expires_at ON owner_sessions(expires_at);
