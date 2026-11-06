-- Owner identity foundation. Apply only after reviewing target database.
-- No existing business is automatically assigned an owner.
CREATE TABLE IF NOT EXISTS owner_accounts (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS business_memberships (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES owner_accounts(id) ON DELETE CASCADE,
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'owner' CHECK (role IN ('owner')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_business_membership UNIQUE (user_id, business_id)
);
