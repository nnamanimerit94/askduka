# Run AskDuka owner dashboard privately (development only)

This is a **local-only** setup. It does not change Render or Neon. Use a disposable PostgreSQL database with pgvector and apply migrations **001–003** only to that test database. Never point the migration command at a live database without a reviewed backup and approval.

From the repository root, in a Python environment with the backend dependencies installed:

1. Set `DATABASE_URL` to the **isolated** PostgreSQL test database. Ensure all schema migrations are present.
2. Set `ASKDUKA_ENABLE_OWNER_SIGNUP=true` only for the duration of this local test.
3. Start the **owner-only** API (not `admin_app`): `uvicorn backend.app.owner_app:app --host 127.0.0.1 --port 8001`.
4. In a second terminal, run `python scripts/check_private_owner_api.py` to verify the app identity, admin-route exclusion and unauthenticated denial.
5. In a third terminal, install `dashboard/requirements.txt`, set `BACKEND_API_URL=http://127.0.0.1:8001` and `ASKDUKA_SHOW_OWNER_SIGNUP=true`, then run `streamlit run dashboard/app.py --server.address 127.0.0.1`.
6. Register a test owner, sign in, navigate to Documents, select the new business, upload a short UTF-8 `.txt` file, verify it is listed, and sign out.
7. Stop both servers and unset both signup flags.

The owner API is **not** a production-ready public service. Its bearer tokens are held in Streamlit session state and signup lacks email verification and distributed rate limiting. This test does not validate AI responses or WhatsApp messaging.
