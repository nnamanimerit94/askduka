# Durable WhatsApp message processing — implementation contract

This migration adds a **schema only**. It does not yet change webhook behavior, prevent duplicates, or enable a retry worker.

## Proposed processing protocol

1. Verify Meta signature, configured phone number and business UUID.
2. Require a nonempty provider message ID for any reply-producing text event.
3. Atomically claim a receipt keyed by (business_id, message_id). Use a database transaction and conditional update or row lock so only one worker can own a claim at a time.
4. Treat `sent` as terminal for inbound duplicate suppression. A fresh `processing` receipt must not be claimed by a second worker. Define a bounded lease and recovery procedure for abandoned claims.
5. On confirmed successful WhatsApp API response, persist `sent`. On definite failure, persist `failed` and return a retryable error. Never store access tokens or raw message bodies in receipts.
6. Explicitly test two workers racing for the same message, a failed send followed by retry, a crash after claim, and redelivery after process restart.

## Important limitation

A crash after Meta accepts an outbound send but before the database marks the receipt `sent` can cause a duplicate outbound reply on retry. Database receipts alone cannot guarantee exactly-once external delivery. An outbox and reconciliation strategy may reduce this risk but cannot eliminate the external acknowledgement gap without provider-side idempotency.

## Deployment gate

Do not run migration 006 on live Neon or enable receipt processing without staging review and a tested rollout. The current webhook still uses in-memory deduplication.
