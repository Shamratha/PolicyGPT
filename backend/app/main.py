import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

# Import models to register them with metadata
from app.models.user import User
from app.models.profile import Profile
from app.models.scheme import Scheme, EligibilityRule, SavedScheme, SearchHistory
from app.models.application import Application
from app.models.survey import Survey
from app.models.analytics import AnalyticsEvent

# Import routers
from app.routers.auth import router as auth_router
from app.routers.profiles import router as profiles_router
from app.routers.schemes import router as schemes_router
from app.routers.chat import router as chat_router
from app.routers.surveys import router as surveys_router
from app.routers.dashboard import router as dashboard_router
from app.routers.analytics import router as analytics_router

# Setup logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables automatically on launch
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Successfully synchronized database tables with models.")
    
    # Automatically seed default schemas, metrics and ChromaDB guidelines
    from app.utils.seed_data import seed_database
    seed_database()
except Exception as e:
    logger.error(f"Failed to synchronize or seed database on launch: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS for frontend interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow development ports, adjust for production domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix="/api")
app.include_router(profiles_router, prefix="/api")
app.include_router(schemes_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(surveys_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "PolicyGPT API",
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
