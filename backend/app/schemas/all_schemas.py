from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# --- Auth Schemas ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None


# --- Subject & Topic Schemas ---
class TopicOut(BaseModel):
    id: str
    subject_id: str
    name: str
    difficulty_range: str

    class Config:
        from_attributes = True

class SubjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    topics: List[TopicOut] = []

    class Config:
        from_attributes = True


# --- Resume & JD Schemas ---
class ResumeOut(BaseModel):
    id: str
    user_id: str
    parsed_json: Optional[Dict[str, Any]] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

class JobDescriptionCreate(BaseModel):
    raw_text: str = Field(..., min_length=10)

class JobDescriptionOut(BaseModel):
    id: str
    user_id: str
    parsed_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Interview Session Schemas ---
class SessionCreate(BaseModel):
    mode: str = Field(..., description="'JD' or 'SUBJECT'")
    resume_id: Optional[str] = None
    jd_id: Optional[str] = None
    subject_ids: Optional[List[str]] = []

class QuestionOut(BaseModel):
    id: str
    session_id: str
    topic_id: Optional[str] = None
    difficulty: int
    question_type: str  # "conceptual" | "coding"
    question_text: str
    source_mix: str
    audio_url: Optional[str] = None

    class Config:
        from_attributes = True

class SessionOut(BaseModel):
    id: str
    user_id: str
    mode: str
    subject_ids: List[str] = []
    status: str
    started_at: datetime
    current_question: Optional[QuestionOut] = None

    class Config:
        from_attributes = True


# --- Answer & Evaluation Schemas ---
class AnswerSubmit(BaseModel):
    transcript_text: Optional[str] = None
    code_submission: Optional[str] = None
    code_language: Optional[str] = "python"
    answer_mode: Optional[str] = "full_code"  # full_code | pseudocode
    audio_url: Optional[str] = None

class EvaluationOut(BaseModel):
    score: float
    feedback_text: str
    sub_scores_json: Dict[str, Any] = {}
    evaluator_model_version: str

class TurnResponse(BaseModel):
    evaluation: EvaluationOut
    next_question: Optional[QuestionOut] = None
    is_completed: bool = False
    session_id: str


# --- Report & Dashboard Schemas ---
class SessionReportOut(BaseModel):
    session_id: str
    summary_text: str
    overall_score: float
    strengths_json: List[str] = []
    weaknesses_json: List[str] = []
    topic_breakdown_json: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardAnalyticsOut(BaseModel):
    total_interviews: int
    average_score: float
    score_trends: List[Dict[str, Any]] = []
    weak_topic_heatmap: List[Dict[str, Any]] = []
    recent_sessions: List[Dict[str, Any]] = []
