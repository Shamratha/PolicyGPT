import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth_utils import get_current_user_claims
from app.repositories.user_repo import user_repository
from app.repositories.profile_repo import profile_repository
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.get("/me", response_model=ProfileResponse)
def get_my_profile(db: Session = Depends(get_db), claims: dict = Depends(get_current_user_claims)):
    """
    Get user profile demographics.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not registered. Sync user first.")
        
    profile = profile_repository.get_by_user_id(db, str(user.id))
    if not profile:
        # Create a default profile to make it smooth
        profile = profile_repository.create(db, {"user_id": user.id})
        
    return profile

@router.post("/me", response_model=ProfileResponse)
def update_my_profile(
    profile_data: ProfileUpdate, 
    db: Session = Depends(get_db), 
    claims: dict = Depends(get_current_user_claims)
):
    """
    Create or update user profile details.
    """
    clerk_id = claims.get("sub")
    if not isinstance(clerk_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing.")
    user = user_repository.get_by_clerk_id(db, clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not registered. Sync user first.")

    profile = profile_repository.get_by_user_id(db, str(user.id))
    update_dict = profile_data.model_dump(exclude_unset=True)

    if not profile:
        update_dict["user_id"] = user.id
        profile = profile_repository.create(db, update_dict)
    else:
        profile = profile_repository.update(db, profile, update_dict)

    return profile
