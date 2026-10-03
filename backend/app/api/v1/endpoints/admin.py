from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.seeder import seed_database
from backend.app.services.pdf_ingest_service import run_pdf_ingestion

router = APIRouter()

@router.post("/seed")
def trigger_seed(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Populates subjects, topic trees, and baseline question bank items."""
    seed_database(db)
    return {"status": "Database successfully seeded with 7 CS subjects and question bank."}

@router.post("/pdf-ingest")
def trigger_pdf_ingest(force_reload: bool = False, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Runs the PDF/document ingestion pipeline across all subject folders."""
    res = run_pdf_ingestion(db=db, force_reload=force_reload)
    return res
