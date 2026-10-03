import os
import glob
import logging
from typing import List, Dict, Any
from pypdf import PdfReader
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.all_models import PDFChunk, Subject, Topic
from backend.app.services.embedding_service import _local_semantic_embedding, EMBEDDING_DIM

logger = logging.getLogger("uvicorn.error")

def extract_text_from_file(file_path: str) -> str:
    """Reads raw text from either PDF, TXT, or Markdown documents."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            pages_text = []
            for i, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt:
                    pages_text.append(txt)
            return "\n\n".join(pages_text)
        except Exception as e:
            logger.error(f"Failed to extract PDF {file_path}: {e}")
            return ""
    else:
        # Standard text or markdown file
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return ""

def chunk_text(text: str, chunk_words: int = 350, overlap_words: int = 50) -> List[str]:
    """Splits a body of text into overlapping semantic word chunks (300-500 tokens)."""
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_words, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 30:  # Avoid empty fragments
            chunks.append(chunk)
        if end >= len(words):
            break
        start += (chunk_words - overlap_words)

    return chunks

def auto_assign_topic(chunk_text: str, subject_id: str, available_topics: List[Topic]) -> str:
    """Assigns the closest topic_id in the subject based on keyword matching."""
    lower_text = chunk_text.lower()
    best_topic = available_topics[0].id if available_topics else f"{subject_id}_general"
    max_matches = 0

    for topic in available_topics:
        # Check topic name keywords
        keywords = topic.name.lower().split()
        matches = sum(1 for kw in keywords if len(kw) > 3 and kw in lower_text)
        if matches > max_matches:
            max_matches = matches
            best_topic = topic.id

    return best_topic

def run_pdf_ingestion(db: Session, force_reload: bool = False) -> Dict[str, Any]:
    """
    Ingests all subject documents found in data/subject_pdfs/<subject_name>/,
    chunks them, embeds them, and inserts into pdf_chunks.
    """
    base_dir = settings.SUBJECT_PDFS_DIR
    if not os.path.exists(base_dir):
        logger.warning(f"Subject PDFs directory {base_dir} does not exist.")
        return {"total_files": 0, "total_chunks": 0, "status": "Directory not found"}

    subjects = db.query(Subject).all()
    subject_map = {s.id: s for s in subjects}

    total_files_processed = 0
    total_chunks_created = 0
    results_per_subject = {}

    for subject_folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, subject_folder)
        if not os.path.isdir(folder_path):
            continue

        subject_id = subject_folder.lower()
        topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()

        # Find all documents in this subject folder
        files = glob.glob(os.path.join(folder_path, "*.*"))
        subject_chunks_count = 0

        for file_path in files:
            file_name = os.path.basename(file_path)
            if file_name.lower().endswith((".pdf", ".txt", ".md")):
                # Check if already ingested
                existing_count = db.query(PDFChunk).filter(
                    PDFChunk.subject_id == subject_id,
                    PDFChunk.source_filename == file_name
                ).count()

                if existing_count > 0 and not force_reload:
                    subject_chunks_count += existing_count
                    continue

                if force_reload and existing_count > 0:
                    db.query(PDFChunk).filter(
                        PDFChunk.subject_id == subject_id,
                        PDFChunk.source_filename == file_name
                    ).delete()
                    db.commit()

                raw_text = extract_text_from_file(file_path)
                if not raw_text.strip():
                    continue

                chunks = chunk_text(raw_text, chunk_words=350, overlap_words=50)
                for chunk in chunks:
                    matched_topic_id = auto_assign_topic(chunk, subject_id, topics)
                    embedding = _local_semantic_embedding(chunk, EMBEDDING_DIM)

                    chunk_record = PDFChunk(
                        subject_id=subject_id,
                        topic_id=matched_topic_id,
                        source_filename=file_name,
                        chunk_text=chunk,
                        embedding=embedding
                    )
                    db.add(chunk_record)
                    subject_chunks_count += 1
                    total_chunks_created += 1

                db.commit()
                total_files_processed += 1

        results_per_subject[subject_id] = subject_chunks_count

    logger.info(f"Ingestion complete: {total_files_processed} files processed, {total_chunks_created} new chunks created.")
    return {
        "status": "success",
        "total_files_processed": total_files_processed,
        "total_chunks_created": total_chunks_created,
        "breakdown": results_per_subject
    }
