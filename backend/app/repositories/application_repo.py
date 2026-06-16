from sqlalchemy.orm import Session
from typing import Optional, List
from app.repositories.base_repo import BaseRepository
from app.models.application import Application

class ApplicationRepository(BaseRepository[Application]):
    def __init__(self):
        super().__init__(Application)

    def get_by_user_and_scheme(self, db: Session, user_id: str, scheme_id: str) -> Optional[Application]:
        return db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.scheme_id == scheme_id
        ).first()

    def get_user_applications(self, db: Session, user_id: str) -> List[Application]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()

application_repository = ApplicationRepository()
