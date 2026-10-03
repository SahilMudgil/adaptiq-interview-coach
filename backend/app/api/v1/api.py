from fastapi import APIRouter
from backend.app.api.v1.endpoints import auth, subjects, resume, jd, admin, session, voice, analytics

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(subjects.router, prefix="/subjects", tags=["Subjects & Topics"])
api_router.include_router(resume.router, prefix="/resume", tags=["Resume"])
api_router.include_router(jd.router, prefix="/jd", tags=["Job Description"])
api_router.include_router(session.router, prefix="/session", tags=["Interview Session"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice Layer"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Dashboard"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Pipeline"])


