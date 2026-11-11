-- Apply only after migration 004 and after verifying existing duplicates.
-- A duplicate pair intentionally causes this migration to fail rather than delete data.
ALTER TABLE conversations
ADD CONSTRAINT uq_conversations_business_customer UNIQUE (business_id, customer_phone);
