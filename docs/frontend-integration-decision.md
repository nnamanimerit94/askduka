# AskDuka frontend integration decision

## Decision (2026-11-05)

Keep the lightweight HTML admin dashboard as a **local/internal development tool**.
Preserve Benoond's Streamlit frontend (PR #4) as a **candidate business-owner UI**,
but do not merge it until its API contracts and authorization are implemented and
verified. Do not deploy the shared admin API key to a public customer-facing UI.

## Existing work

- Member 2 PR #2: PostgreSQL schema, ingestion, vector retrieval (merged).
- Member 3 PR #5: retrieval fix and lazy-loaded embedding model (merged).
- Benoond PR #4: Streamlit login, documents, conversations, settings (open).
- Internal dashboard PRs #10 and #15: admin catalog editing and question testing (merged).

## API contract gaps

| Streamlit feature | Current client expectation | Required next step |
| --- | --- | --- |
| Login | POST /api/auth/login | Implement owner identity and secure session/token issuance. |
| Document upload | POST /api/documents | Implement authenticated per-business upload, parsing, and ingestion. |
| Conversations | GET /api/conversations | Define persistence and business-scoped conversation listing. |
| Settings | No real persistence | Add authenticated business settings API. |

The current /admin endpoints use a single administrator API key and are
**not** substitutes for business-owner authentication.

## Delivery sequence

1. Design owner and business membership models, authorization checks, and tests.
2. Implement and test login and owner-scoped business access.
3. Implement file upload and retrieval with ownership checks and size/type limits.
4. Persist conversation history and add business-scoped read API.
5. Update Benoond's Streamlit API client to verified backend contracts.
6. Rebase or selectively port PR #4, resolve conflicts, test all user journeys.
7. Deploy the customer frontend separately from the admin preview.

## Release gates

- No public owner dashboard without proper owner auth and tenant isolation.
- No secrets in browser code, repo, or logs.
- Real PostgreSQL-backed HTTP integration tests must run, not merely skip.
- Confirmed login, upload, conversation, and question-answering journeys.
- Existing public preview remains isolated from admin routes.
