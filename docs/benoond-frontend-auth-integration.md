# Benoond frontend authentication integration

Benoond's existing Streamlit frontend (PR #4, branch `feature/dashboard_Member5`) calls `POST /api/auth/login` and expects a JSON `token` property. The internal owner authentication API now returns both `access_token` (standard naming) and `token` (frontend compatibility) with the same opaque bearer token.

## Integration steps (not yet live)
1. Preserve Benoond's frontend contribution and attribution; reconcile PR #4's merge conflicts in a dedicated integration branch rather than overwriting its source branch.
2. Configure `BACKEND_API_URL` for the internal backend; never point the frontend at the lightweight public preview until authentication is explicitly deployed.
3. Change Streamlit logout to call `POST /api/auth/logout` with the bearer token before clearing local session state. The existing logout only clears Streamlit state and leaves the server token valid.
4. Validate the token on rerun using `GET /api/auth/me`, rather than trusting the presence of `st.session_state["token"]` alone.
5. Do not expose documents or conversations until both endpoints enforce authenticated, active business membership; these endpoints are not implemented as owner-scoped APIs yet.
6. Apply migrations only to a reviewed non-production environment first. Verify rate limiting, TLS, trusted proxy behavior, and token handling before exposing login publicly.

## Status
Only the login response contract is updated here. This PR does **not** merge PR #4, deploy a Streamlit app, or establish complete frontend login/logout.
