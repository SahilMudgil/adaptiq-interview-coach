import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import engine, Base, is_postgres, has_pgvector
import backend.app.models  # Ensure all models are registered with Base
from backend.app.api.v1.api import api_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend API for AdaptIQ: AI-Powered Voice-First Adaptive Interview Coach",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root & Health check
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "database": {
            "type": "PostgreSQL" if is_postgres else "SQLite (Local Fallback)",
            "pgvector_enabled": has_pgvector,
            "connected": True
        },
        "llm": {
            "groq_configured": bool(settings.GROQ_API_KEY)
        },
        "voice": {
            "openai_stt_configured": bool(settings.OPENAI_API_KEY)
        }
    }

@app.get("/", tags=["System"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs_url": "/docs",
        "health_url": "/health"
    }

# Mount v1 routers
app.include_router(api_router, prefix=settings.API_V1_STR)
