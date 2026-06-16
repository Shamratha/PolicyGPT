import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth_utils import get_current_user_claims
from app.repositories.user_repo import user_repository
from app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/sync-user", response_model=UserResponse)
def sync_user(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    """
    Called by the frontend after authentication to synchronize the Clerk session.
    Registers user in local PostgreSQL database if they don't already exist.
    """
    clerk_id = claims.get("sub")
    
    # Extract email from various possible Clerk claim structures
    email = (
        claims.get("email") or 
        claims.get("email_address") or 
        claims.get("primary_email_address") or 
        ""
    )

    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=400, detail="Invalid token details: missing subject identifier.")

    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        try:
            user = user_repository.create(db, {"clerk_id": clerk_id, "email": email})
            logger.info(f"Registered new local user profile for Clerk ID: {clerk_id}")
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise HTTPException(status_code=500, detail="Failed to sync user session.")
            
    return user
