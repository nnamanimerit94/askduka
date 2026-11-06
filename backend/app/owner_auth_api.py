"""Internal-only owner login and logout HTTP endpoints.

Do not mount this router in the public preview until rate limiting,
HTTPS, cookie/token security, migrations and integration tests are complete.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.owner_session_service import current_owner_id, login_owner, logout_owner
from backend.app.login_rate_limit import login_limiter

router = APIRouter(prefix="/api/auth", tags=["owner-auth"])


def db_session():
    from backend.app.db.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:].strip()
    if not token or " " in token:
        raise HTTPException(status_code=401, detail="Authentication required")
    return token


@router.post("/login")
def login(request: LoginRequest, http_request: Request, db: Session = Depends(db_session)):
    client_ip = http_request.client.host if http_request.client else "unknown"
    # Apply per-client limit before credential verification; never trust
    # caller-controlled forwarding headers for client identity.
    if not login_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Too many login attempts")
    token = login_owner(db, request.email, request.password)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer", "expires_in": 43200}


@router.get("/me")
def me(token: str = Depends(bearer_token), db: Session = Depends(db_session)):
    owner_id = current_owner_id(db, token)
    if owner_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return {"owner_id": str(owner_id)}


@router.post("/logout")
def logout(token: str = Depends(bearer_token), db: Session = Depends(db_session)):
    owner_id = current_owner_id(db, token)
    if owner_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    logout_owner(db, token)
    return {"logged_out": True}
