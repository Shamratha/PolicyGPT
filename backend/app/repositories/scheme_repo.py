from sqlalchemy.orm import Session
from typing import Optional, List
from app.repositories.base_repo import BaseRepository
from app.models.scheme import Scheme, SavedScheme, SearchHistory

class SchemeRepository(BaseRepository[Scheme]):
    def __init__(self):
        super().__init__(Scheme)

    def get_by_name(self, db: Session, name: str) -> Optional[Scheme]:
        return db.query(self.model).filter(self.model.name == name).first()

    def get_saved_schemes(self, db: Session, user_id: str) -> List[SavedScheme]:
        return db.query(SavedScheme).filter(SavedScheme.user_id == user_id).all()

    def is_scheme_saved(self, db: Session, user_id: str, scheme_id: str) -> bool:
        return db.query(SavedScheme).filter(
            SavedScheme.user_id == user_id,
            SavedScheme.scheme_id == scheme_id
        ).first() is not None

    def save_scheme(self, db: Session, user_id: str, scheme_id: str) -> SavedScheme:
        db_obj = SavedScheme(user_id=user_id, scheme_id=scheme_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def unsave_scheme(self, db: Session, user_id: str, scheme_id: str) -> bool:
        db_obj = db.query(SavedScheme).filter(
            SavedScheme.user_id == user_id,
            SavedScheme.scheme_id == scheme_id
        ).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False

    def add_search_history(self, db: Session, user_id: str, query: str) -> SearchHistory:
        db_obj = SearchHistory(user_id=user_id, query=query)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_search_history(self, db: Session, user_id: str, limit: int = 10) -> List[SearchHistory]:
        return db.query(SearchHistory).filter(
            SearchHistory.user_id == user_id
        ).order_by(SearchHistory.created_at.desc()).limit(limit).all()

scheme_repository = SchemeRepository()
