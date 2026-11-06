# Controlled owner-dashboard test plan (not public launch)

## Current deployment boundary
- Public Render preview runs `backend.app.preview:app` and exposes a **keyword demo only**. It does not serve owner login, registration or document APIs.
- The owner API is mounted in `backend.app.admin_app:app`, intended for internal use. Do not point the public dashboard at the keyword preview URL.
- Streamlit dashboard is in `dashboard/app.py`; it has not been deployed as a public customer service.
- New registration requires both `ASKDUKA_ENABLE_OWNER_SIGNUP=true` on the internal API and `ASKDUKA_SHOW_OWNER_SIGNUP=true` on Streamlit. Keep both unset for normal deployments.

## Safer owner API separation
- The internal admin app includes catalog administration endpoints protected by an admin key. Never expose that whole app as the customer API.
- A separate owner-only FastAPI application can mount only authentication, business and document routers. Keep it on localhost/private network during testing.
- Restrict cross-origin requests to the dashboard origin if a browser-facing deployment is later approved. Avoid wildcard CORS with credentials.

## Prerequisites for an authorized isolated test
1. Use a disposable PostgreSQL database with pgvector available. Back up any existing data; do not run schema changes against live Neon without explicit authorization.
2. Apply migrations 001, 002 and 003 to that isolated database and verify the `schema_migrations` table.
3. Run the internal FastAPI app with `DATABASE_URL` pointing at the isolated database and bind to localhost or a private network only. Never expose the internal admin API or its key on a public URL.
4. Run Streamlit dashboard privately, configure `BACKEND_API_URL` to the private internal API, and enable both signup flags only for the controlled test.
5. Test: register a unique owner and business, log in, select that business, upload a small UTF-8 `.txt` file, verify it appears in the list, then log out and confirm access is denied.
6. Confirm another owner cannot list or upload documents for that business. Check invalid/oversized files, duplicate email and wrong passwords.
7. Disable both signup flags when testing ends. Delete disposable credentials/data using an approved cleanup procedure.

## Blockers before public deployment
- Public owner authentication architecture and token storage review; HTTPS and CSRF/session handling as applicable.
- Shared, persistent signup/login abuse protection, email verification and account recovery.
- Secure separation of internal admin key and customer-facing owner APIs; deployment CORS/network restrictions.
- Production migration review and rollback/backup plan.
- Retrieval/indexing readiness: uploading chunks alone does not prove embeddings or AI answers work.
- Conversations API and real WhatsApp integration are not completed.
- Deployment-specific dependency/configuration verification and full browser end-to-end tests.

**Do not describe the existing Render preview as the full AskDuka product.**
