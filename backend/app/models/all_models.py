import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    weak_profiles = relationship("WeakTopicProfile", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)  # List of floats
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    sessions = relationship("InterviewSession", back_populates="resume")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)  # List of floats
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="job_descriptions")
    sessions = relationship("InterviewSession", back_populates="job_description")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(50), primary_key=True)  # e.g., 'dsa', 'os', 'dbms'
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
    pdf_chunks = relationship("PDFChunk", back_populates="subject", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(String(100), primary_key=True)  # e.g., 'dsa_arrays', 'os_deadlocks'
    subject_id = Column(String(50), ForeignKey("subjects.id"), nullable=False)
    name = Column(String(150), nullable=False)
    parent_topic_id = Column(String(100), ForeignKey("topics.id"), nullable=True)
    difficulty_range = Column(String(20), default="1-5")

    subject = relationship("Subject", back_populates="topics")
    question_bank_items = relationship("QuestionBank", back_populates="topic")
    questions = relationship("Question", back_populates="topic")


class QuestionBank(Base):
    __tablename__ = "question_bank"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    topic_id = Column(String(100), ForeignKey("topics.id"), nullable=False)
    difficulty = Column(Integer, default=1)  # 1 to 5
    question_type = Column(String(20), default="conceptual")  # conceptual | coding
    question_text = Column(Text, nullable=False)
    source = Column(String(100), default="seed")
    embedding = Column(JSON, nullable=True)

    topic = relationship("Topic", back_populates="question_bank_items")


class PDFChunk(Base):
    __tablename__ = "pdf_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(50), ForeignKey("subjects.id"), nullable=False)
    topic_id = Column(String(100), ForeignKey("topics.id"), nullable=True)
    source_filename = Column(String(255), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="pdf_chunks")


class InterviewSession(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    mode = Column(String(20), nullable=False)  # "JD" | "SUBJECT"
    resume_id = Column(String(36), ForeignKey("resumes.id"), nullable=True)
    jd_id = Column(String(36), ForeignKey("job_descriptions.id"), nullable=True)
    subject_ids = Column(JSON, default=list)  # list of subject string IDs
    session_state = Column(JSON, default=dict)  # Complete persistent agent state object
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # "active" | "completed" | "abandoned"

    user = relationship("User", back_populates="sessions")
    resume = relationship("Resume", back_populates="sessions")
    job_description = relationship("JobDescription", back_populates="sessions")
    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")
    report = relationship("SessionReport", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    topic_id = Column(String(100), ForeignKey("topics.id"), nullable=True)
    difficulty = Column(Integer, default=1)
    question_type = Column(String(20), default="conceptual")  # conceptual | coding
    question_text = Column(Text, nullable=False)
    source_mix = Column(String(50), default="pure_llm")  # "pdf_grounded" | "bank_grounded" | "pure_llm"
    audio_url = Column(String(500), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="questions")
    topic = relationship("Topic", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False, cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("questions.id"), nullable=False)
    transcript_text = Column(Text, nullable=True)
    code_submission = Column(Text, nullable=True)
    code_language = Column(String(30), nullable=True)  # python, java, cpp, javascript, c
    answer_mode = Column(String(20), default="full_code")  # full_code | pseudocode
    audio_url = Column(String(500), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="answer")
    evaluation = relationship("Evaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    answer_id = Column(String(36), ForeignKey("answers.id"), nullable=False)
    score = Column(Float, nullable=False)  # 0.0 to 10.0 or 1.0 to 5.0
    sub_scores_json = Column(JSON, default=dict)  # correctness, clarity, completeness, etc.
    feedback_text = Column(Text, nullable=False)
    evaluator_model_version = Column(String(100), default="base-llm-api")

    answer = relationship("Answer", back_populates="evaluation")


class WeakTopicProfile(Base):
    __tablename__ = "weak_topic_profile"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    topic_id = Column(String(100), ForeignKey("topics.id"), nullable=False)
    running_score = Column(Float, default=0.0)
    attempts_count = Column(Integer, default=1)
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="weak_profiles")


class SessionReport(Base):
    __tablename__ = "session_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    summary_text = Column(Text, nullable=False)
    overall_score = Column(Float, default=0.0)
    strengths_json = Column(JSON, default=list)
    weaknesses_json = Column(JSON, default=list)
    topic_breakdown_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="report")
