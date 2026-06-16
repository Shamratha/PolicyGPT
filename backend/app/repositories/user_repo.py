from sqlalchemy.orm import Session
from typing import Optional
from app.repositories.base_repo import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_clerk_id(self, db: Session, clerk_id: str) -> Optional[User]:
        return db.query(self.model).filter(self.model.clerk_id == clerk_id).first()

user_repository = UserRepository()
