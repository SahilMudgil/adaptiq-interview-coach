import io
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pypdf import PdfReader
from backend.app.core.database import get_db
from backend.app.models.all_models import JobDescription, Resume, User
from backend.app.schemas.all_schemas import JobDescriptionCreate, JobDescriptionOut
from backend.app.api.deps import get_current_user
from backend.app.services.context_builder_service import parse_jd_to_json, perform_gap_analysis
from backend.app.services.embedding_service import _local_semantic_embedding, EMBEDDING_DIM

router = APIRouter()

class GapAnalysisRequest(BaseModel):
    resume_id: str
    jd_id: str

@router.post("/upload", response_model=JobDescriptionOut)
async def upload_job_description(
    file: UploadFile = File(None),
    raw_text: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    extracted_text = ""
    if file:
        content = await file.read()
        if file.filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(content))
                pages = [p.extract_text() for p in reader.pages if p.extract_text()]
                extracted_text = "\n\n".join(pages)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to parse JD PDF file: {e}")
        else:
            extracted_text = content.decode("utf-8", errors="ignore")
    elif raw_text:
        extracted_text = raw_text.strip()
    else:
        raise HTTPException(status_code=400, detail="Please upload a JD PDF/text file or provide JD text.")

    if len(extracted_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Job description content is too short to parse.")

    # 1. Parse structured role expectations via LLM
    parsed_json = await parse_jd_to_json(extracted_text)

    # 2. Compute embedding
    embedding = _local_semantic_embedding(extracted_text, EMBEDDING_DIM)

    # 3. Save to database
    jd_record = JobDescription(
        user_id=current_user.id,
        raw_text=extracted_text,
        parsed_json=parsed_json,
        embedding=embedding
    )
    db.add(jd_record)
    db.commit()
    db.refresh(jd_record)

    return jd_record

@router.post("/submit", response_model=JobDescriptionOut)
async def submit_job_description(
    jd_in: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Parse structured role expectations via LLM
    parsed_json = await parse_jd_to_json(jd_in.raw_text)

    # 2. Compute embedding
    embedding = _local_semantic_embedding(jd_in.raw_text, EMBEDDING_DIM)

    # 3. Save to database
    jd_record = JobDescription(
        user_id=current_user.id,
        raw_text=jd_in.raw_text,
        parsed_json=parsed_json,
        embedding=embedding
    )
    db.add(jd_record)
    db.commit()
    db.refresh(jd_record)

    return jd_record

@router.post("/gap-analysis")
async def run_gap_analysis(
    req: GapAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    resume = db.query(Resume).filter(Resume.id == req.resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    jd = db.query(JobDescription).filter(JobDescription.id == req.jd_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    analysis = await perform_gap_analysis(
        resume_json=resume.parsed_json or {},
        jd_json=jd.parsed_json or {},
        resume_embedding=resume.embedding or [],
        jd_embedding=jd.embedding or []
    )
    return analysis
