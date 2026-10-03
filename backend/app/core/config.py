import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AdaptIQ: AI-Powered Voice-First Adaptive Interview Coach"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "adaptive-interview-coach-super-secret-key-change-in-prod-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    # Standard PostgreSQL default, with automatic graceful fallback if PostgreSQL is inaccessible
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/interview_coach"
    FALLBACK_SQLITE_URL: str = "sqlite:///./interview_coach.db"
    
    # LLM & Model API Keys
    GROQ_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # Judge0 (optional stretch)
    JUDGE0_API_URL: str = "https://judge0-ce.p.rapidapi.com"
    JUDGE0_API_KEY: Optional[str] = None
    
    # Data directories
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(os.path.dirname(BASE_DIR), "data")
    SUBJECT_PDFS_DIR: str = os.path.join(DATA_DIR, "subject_pdfs")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()
