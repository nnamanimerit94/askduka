# Stale WhatsApp receipts — pilot operations

Durable receipts are opt-in and **must remain disabled** until migration 006, operational monitoring, and manual recovery are approved. A receipt stuck in `processing` may mean either (a) no WhatsApp reply was sent, or (b) WhatsApp accepted a reply but the worker crashed before recording `sent`. The database alone cannot distinguish them.

## Inspect (read only)

Use `list_stale_processing_receipts(session, older_than_minutes=15)` in a controlled internal maintenance session against the **authorized** database. This returns business ID, provider message ID, attempts and timestamps. It never changes a receipt or sends a message.

## Triage

1. Verify the affected business and provider message ID; review sanitized application logs and Meta delivery evidence, if available.
2. If delivery is confirmed, resolve the receipt to `sent` only after explicit operator approval and an audit record.
3. If non-delivery is confirmed, an operator may authorize a controlled retry, noting that external delivery can be ambiguous.
4. If uncertain, **do not automatically reclaim or resend**. Escalate for human review; avoid duplicate customer messages.

No automated stale-lease reclaim or state-changing administrative endpoint is implemented. The feature flag remains off by default. Never run schema migrations or change production receipts without explicit approval.
