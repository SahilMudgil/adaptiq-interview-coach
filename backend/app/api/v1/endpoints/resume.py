import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pypdf import PdfReader
from backend.app.core.database import get_db
from backend.app.models.all_models import Resume, User
from backend.app.schemas.all_schemas import ResumeOut
from backend.app.api.deps import get_current_user
from backend.app.services.context_builder_service import parse_resume_to_json
from backend.app.services.embedding_service import _local_semantic_embedding, EMBEDDING_DIM

router = APIRouter()

@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
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
                raise HTTPException(status_code=400, detail=f"Failed to parse PDF file: {e}")
        else:
            extracted_text = content.decode("utf-8", errors="ignore")
    elif raw_text:
        extracted_text = raw_text.strip()
    else:
        raise HTTPException(status_code=400, detail="Please upload a PDF file or provide resume text.")

    if len(extracted_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Resume content is too short to parse.")

    # 1. Parse into structured technical competencies via LLM
    parsed_json = await parse_resume_to_json(extracted_text)

    # 2. Compute embedding
    embedding = _local_semantic_embedding(extracted_text, EMBEDDING_DIM)

    # 3. Save to database
    resume_record = Resume(
        user_id=current_user.id,
        raw_text=extracted_text,
        parsed_json=parsed_json,
        embedding=embedding
    )
    db.add(resume_record)
    db.commit()
    db.refresh(resume_record)

    return resume_record
