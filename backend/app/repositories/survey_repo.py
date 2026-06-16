from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Dict, Any
from app.repositories.base_repo import BaseRepository
from app.models.survey import Survey
from app.models.profile import Profile
from app.models.scheme import Scheme

class SurveyRepository(BaseRepository[Survey]):
    def __init__(self):
        super().__init__(Survey)

    def get_user_surveys(self, db: Session, user_id: str) -> List[Survey]:
        return db.query(self.model).filter(self.model.user_id == user_id).all()

    def get_analytics_stats(self, db: Session) -> Dict[str, Any]:
        total = db.query(func.count(self.model.id)).scalar() or 0
        if total == 0:
            return {
                "total_submissions": 0,
                "awareness_rate": 0.0,
                "application_rate": 0.0,
                "average_difficulty": 0.0,
                "bottlenecks": {},
                "status_distribution": {},
                "state_awareness": [],
                "underserved_demographics": []
            }

        # Calculate awareness and application rates
        aware_count = db.query(func.count(self.model.id)).filter(self.model.aware_of_scheme == True).scalar() or 0
        applied_count = db.query(func.count(self.model.id)).filter(self.model.applied_for_scheme == True).scalar() or 0
        
        awareness_rate = (aware_count / total) * 100.0
        application_rate = (applied_count / total) * 100.0

        # Calculate average difficulty
        avg_difficulty = db.query(func.avg(self.model.difficulty_rating)).filter(self.model.difficulty_rating != None).scalar()
        avg_difficulty = float(avg_difficulty) if avg_difficulty is not None else 0.0

        # Bottlenecks distribution
        bottleneck_query = db.query(
            self.model.bottleneck_reason, 
            func.count(self.model.id)
        ).filter(self.model.bottleneck_reason != None).group_by(self.model.bottleneck_reason).all()
        bottlenecks = {reason: count for reason, count in bottleneck_query if reason}

        # Status distribution
        status_query = db.query(
            self.model.application_status,
            func.count(self.model.id)
        ).filter(self.model.application_status != None).group_by(self.model.application_status).all()
        status_dist = {status: count for status, count in status_query if status}

        # State-wise awareness (joins surveys -> user -> profiles to check state and awareness)
        # Note: If profile is missing state, we skip or mark as "Unknown"
        state_query = db.query(
            func.coalesce(Profile.state, 'Unknown').label('state'),
            func.count(Survey.id).label('total_sub'),
            func.sum(case((Survey.aware_of_scheme == True, 1), else_=0)).label('aware_sub')
        ).select_from(Survey).join(Profile, Survey.user_id == Profile.user_id, isouter=True).group_by(
            func.coalesce(Profile.state, 'Unknown')
        ).all()

        state_awareness = []
        for row in state_query:
            state_name = row[0] or "Unknown"
            sub_count = row[1] or 0
            aw_count = row[2] or 0
            rate = (aw_count / sub_count * 100.0) if sub_count > 0 else 0.0
            state_awareness.append({
                "state": state_name,
                "awareness_rate": round(rate, 2),
                "submissions_count": sub_count
            })

        # Underserved demographics: Group by gender and education/occupation to check who has the lowest match rate
        # For simplicity, we analyze success rates or match volumes by demographic groups
        demographic_query = db.query(
            func.coalesce(Profile.gender, 'Unspecified').label('gender'),
            func.coalesce(Profile.occupation, 'Unspecified').label('occupation'),
            func.count(Survey.id).label('total_sub'),
            func.sum(case((Survey.application_status == 'Approved', 1), else_=0)).label('approved_sub')
        ).select_from(Survey).join(Profile, Survey.user_id == Profile.user_id, isouter=True).group_by(
            func.coalesce(Profile.gender, 'Unspecified'),
            func.coalesce(Profile.occupation, 'Unspecified')
        ).all()

        underserved = []
        for row in demographic_query:
            gender = row[0]
            occupation = row[1]
            sub_count = row[2]
            app_count = row[3]
            rate = (app_count / sub_count * 100.0) if sub_count > 0 else 0.0
            underserved.append({
                "demographic": f"{gender} - {occupation}",
                "match_rate": round(rate, 2),
                "volume": sub_count
            })

        return {
            "total_submissions": total,
            "awareness_rate": round(awareness_rate, 2),
            "application_rate": round(application_rate, 2),
            "average_difficulty": round(avg_difficulty, 2),
            "bottlenecks": bottlenecks,
            "status_distribution": status_dist,
            "state_awareness": state_awareness,
            "underserved_demographics": underserved
        }

survey_repository = SurveyRepository()
