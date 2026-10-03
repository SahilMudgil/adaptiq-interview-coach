from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.all_models import Subject, Topic
from backend.app.schemas.all_schemas import SubjectOut, TopicOut

router = APIRouter()

@router.get("", response_model=List[SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    """Returns all available core subjects and their topic hierarchies."""
    subjects = db.query(Subject).all()
    return subjects

@router.get("/{subject_id}/topics", response_model=List[TopicOut])
def list_subject_topics(subject_id: str, db: Session = Depends(get_db)):
    """Returns all topics for a specific subject."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()
    return topics
