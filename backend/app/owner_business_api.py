"""Business-scoped owner access; deny access unless an active membership exists."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.owner_models import BusinessMembership
from backend.app.owner_auth_api import bearer_token, db_session
from backend.app.owner_session_service import current_owner_id


router = APIRouter(prefix="/api/businesses", tags=["owner-businesses"])


def require_owner(token: str = Depends(bearer_token), db: Session = Depends(db_session)) -> uuid.UUID:
    owner_id = current_owner_id(db, token)
    if owner_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return owner_id


def require_business_owner(
    business_id: uuid.UUID,
    owner_id: uuid.UUID = Depends(require_owner),
    db: Session = Depends(db_session),
) -> uuid.UUID:
    membership = db.scalar(
        select(BusinessMembership).where(
            BusinessMembership.user_id == owner_id,
            BusinessMembership.business_id == business_id,
            BusinessMembership.is_active.is_(True),
            BusinessMembership.role == "owner",
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return business_id


@router.get("")
def list_my_businesses(owner_id: uuid.UUID = Depends(require_owner), db: Session = Depends(db_session)):
    memberships = db.scalars(
        select(BusinessMembership).where(
            BusinessMembership.user_id == owner_id,
            BusinessMembership.is_active.is_(True),
            BusinessMembership.role == "owner",
        )
    ).all()
    return {"businesses": [{"business_id": str(item.business_id)} for item in memberships]}


@router.get("/{business_id}")
def get_my_business(business_id: uuid.UUID = Depends(require_business_owner)):
    return {"business_id": str(business_id)}
