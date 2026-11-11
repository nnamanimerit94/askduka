# AskDuka: controlled single-business pilot readiness

**Status: NOT ready for real customers.** GitHub CI verifies isolated behaviors, not production WhatsApp delivery, owner security, or AI quality.

## Architecture boundary

- The deployed `backend.app.preview:app` is a public **keyword-only demo**, not the owner API or WhatsApp service.
- `backend.app.owner_app:app` is a **private testing** API; do not expose publicly before session, signup-abuse, database-migration, and network-control review.
- The WhatsApp orchestrator currently uses a **single** `ASKDUKA_BUSINESS_ID`. Do not advertise multi-business WhatsApp routing.
- Owner document uploads are **not searchable by default**. `ASKDUKA_ENABLE_UPLOAD_EMBEDDINGS=true` enables synchronous model inference; confirm model installation, memory, request latency, pgvector availability, and rollback behavior in a private staging environment.
- `ASKDUKA_STORE_CONVERSATIONS=true` enables optional latest-inbound-message persistence, not a complete transcript. Initial-message concurrency and deduplication across workers still require hardening.

## Staging prerequisites (do not apply to production automatically)

1. Create a dedicated staging PostgreSQL database with pgvector. Verify migrations 001–004 and back up before applying any migration to an existing database.
2. Install application dependencies including `sentence-transformers`; ensure embedding model and query vectors are both 384 dimensions.
3. Provision a private owner API, confirm owner login/session/logout, business membership checks, and cross-business document isolation.
4. Provision owner Streamlit dashboard separately, point it to the private API, and verify signup (if intentionally enabled), login, upload, list, and conversation views.
5. Configure Meta WhatsApp Cloud API credentials and webhook verification/signature checks on the webhook deployment. Keep tokens out of Git and logs.
6. Set a **single** pilot business UUID and configure Anthropic credentials securely; never place API keys in frontend configuration.
7. Verify actual upload → embedding → vector retrieval → grounded answer → WhatsApp send, including unknown-product fallback, invalid credentials, and provider outage.
8. Test repeated webhook deliveries, concurrent first messages, worker restarts, and slow embedding/model requests. Do not assume in-memory deduplication is sufficient.
9. Validate owner consent, customer privacy, retention policy, and a clear escalation to the human business owner.
10. Restrict pilot to test numbers and approved users until security and delivery checks pass.

## Acceptance test

Upload a text catalog containing a uniquely identifiable product and price. Confirm the document status is `completed` and its chunks have non-null embeddings. From a permitted test WhatsApp number, ask its price. Confirm the correct price is returned, no unsupported prices are invented, and a question about an absent product triggers a safe fallback. Confirm a second business cannot retrieve the first business's catalog.

## Explicit launch blockers

- No verified live WhatsApp send/receive and provider-backed AI answer.
- Owner API and Streamlit dashboard are not confirmed publicly deployed with appropriate protections.
- Migrations 002–004 have not been verified on the live environment.
- Upload embeddings require staging enablement and operational verification.
- In-memory webhook deduplication and conversation first-write race are not multi-worker safe.
- Demo readiness endpoint describes only the keyword demo, not the pilot service.

**Go/no-go:** Do not call AskDuka production-ready until the acceptance test passes on an isolated staging deployment and security/operations review is complete.
