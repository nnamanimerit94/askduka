# WhatsApp single-business pilot — activation gates

**Status: NOT APPROVED FOR LIVE ACTIVATION.** This checklist is a deployment gate, not an instruction to deploy.

## Prerequisites

- [ ] Confirm pilot business owner consent, test participants, permitted customer data and retention.
- [ ] Confirm deployed runtime is the intended WhatsApp/owner API (the public preview demo is not the owner API).
- [ ] Confirm isolated staging PostgreSQL backup and tested rollback; review and explicitly approve migrations 001–006 in dependency order.
- [ ] Confirm dedicated Meta WhatsApp test number, app secret, verification token, outbound token, configured phone number ID, and business UUID; never commit secrets.
- [ ] Verify webhook HMAC signature enforcement, configured-number filtering, and invalid payload rejection on staging.
- [ ] Verify the owner can upload a .txt catalog and that opted-in 384-dimensional embeddings are actually stored and retrieved for the correct business.
- [ ] Verify outbound sends fail closed on missing credentials, and only authorized test recipients receive replies.
- [ ] Review durability limitations: processing receipts can become stuck, and a crash after outbound acceptance but before marking sent can create ambiguous delivery. No automatic stale reclaim.
- [ ] Define an operator to inspect stale receipts, evidence sources, escalation path and manual disposition audit log.
- [ ] Exercise failure injection: database unavailable, Meta send timeout, concurrent duplicate webhook, restart during processing, retry after confirmed failure.
- [ ] Confirm logs avoid exposing secrets or full customer message bodies; establish limited access and retention.
- [ ] Set explicit pilot stop conditions and a rollback plan. Keep ASKDUKA_USE_DURABLE_RECEIPTS off until all conditions are met.

## Activation decision

Record who approved activation, the exact commit, deployment target, migration versions, configuration flags, monitoring owner, test number, start time, and rollback contact. **Do not apply migrations, set flags, or deploy without explicit user authorization.**

## Rollback

Stop accepting pilot traffic or disable the webhook at the provider, preserve receipts and logs for investigation, and return to the previous verified deployment. Do not blindly drop receipt tables or resend ambiguous messages. Validate state with the operator before reactivation.
