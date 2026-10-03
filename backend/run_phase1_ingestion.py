import sys
import os

# Ensure workspace root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.services.seeder import seed_database
from backend.app.services.pdf_ingest_service import run_pdf_ingestion
from backend.app.models.all_models import Subject, Topic, QuestionBank, PDFChunk

def main():
    print("==========================================================")
    print("      Starting Phase 1: Context Builders & Ingestion     ")
    print("==========================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Step 1: Seed Subjects, Topics, and Initial Question Bank
        print("\n[1/2] Seeding 7 CS Subjects, Topic Trees, and Question Bank...")
        seed_database(db)

        subject_count = db.query(Subject).count()
        topic_count = db.query(Topic).count()
        qb_count = db.query(QuestionBank).count()
        print(f"  -> Total Subjects in DB: {subject_count}")
        print(f"  -> Total Topics in DB: {topic_count}")
        print(f"  -> Total Question Bank Items in DB: {qb_count}")

        # Step 2: Run PDF Ingestion Pipeline
        print("\n[2/2] Running Document Ingestion Pipeline on all 7 subject folders...")
        ingest_stats = run_pdf_ingestion(db, force_reload=True)
        print(f"  -> Status: {ingest_stats.get('status')}")
        print(f"  -> Total files processed: {ingest_stats.get('total_files_processed')}")
        print(f"  -> Total PDF/document chunks embedded: {ingest_stats.get('total_chunks_created')}")

        total_pdf_chunks = db.query(PDFChunk).count()
        print(f"  -> Total chunks stored in `pdf_chunks` table: {total_pdf_chunks}")

        print("\nBreakdown per Subject:")
        for subj, count in ingest_stats.get("breakdown", {}).items():
            print(f"    - {subj.upper()}: {count} chunks embedded")

        print("\n==========================================================")
        print("  Phase 1 Data Seeding & PDF Ingestion Succeeded 100%!   ")
        print("==========================================================")

    finally:
        db.close()

if __name__ == "__main__":
    main()
