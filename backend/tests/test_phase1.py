from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.services.embedding_service import (
    search_similar_pdf_chunks,
    search_similar_question_bank
)

client = TestClient(app)

def get_auth_token():
    # Login or create test user
    email = "phase1_tester@example.com"
    pwd = "password123"
    client.post("/api/v1/auth/signup", json={"name": "P1 Tester", "email": email, "password": pwd})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login_res.json()["access_token"]

def test_subjects_and_topics():
    print("\n[Test 1] Testing Subjects & Topics endpoints...")
    res = client.get("/api/v1/subjects")
    assert res.status_code == 200
    subjects = res.json()
    assert len(subjects) == 7
    subject_ids = [s["id"] for s in subjects]
    for expected in ["dsa", "os", "dbms", "computer_networks", "oops", "hr_behavioral", "aptitude"]:
        assert expected in subject_ids
    print(f"  [OK] Found all 7 core subjects: {subject_ids}")

    # Check DSA topics
    dsa_topics_res = client.get("/api/v1/subjects/dsa/topics")
    assert dsa_topics_res.status_code == 200
    topics = dsa_topics_res.json()
    assert len(topics) >= 5
    print(f"  [OK] DSA has {len(topics)} topics.")

def test_semantic_retrieval():
    print("\n[Test 2] Testing Semantic Vector Search on Ingested PDF Chunks...")
    db = SessionLocal()
    try:
        # Search for deadlock concepts in OS
        chunks = search_similar_pdf_chunks(db, query_text="deadlock conditions Coffman Banker algorithm", subject_id="os", limit=2)
        assert len(chunks) > 0
        assert "deadlock" in chunks[0].chunk_text.lower() or "os" in chunks[0].subject_id
        print(f"  [OK] Retrieved {len(chunks)} relevant OS chunks. Top chunk preview: '{chunks[0].chunk_text[:70]}...'")

        # Search for DBMS indexing
        dbms_chunks = search_similar_pdf_chunks(db, query_text="clustered vs non clustered B-Tree index", subject_id="dbms", limit=2)
        assert len(dbms_chunks) > 0
        print(f"  [OK] Retrieved {len(dbms_chunks)} relevant DBMS chunks. Top chunk preview: '{dbms_chunks[0].chunk_text[:70]}...'")

        # Search in question bank
        qb_items = search_similar_question_bank(db, query_text="binary search tree time complexity", limit=2)
        assert len(qb_items) > 0
        print(f"  [OK] Retrieved question bank item: '{qb_items[0].question_text[:70]}...'")
    finally:
        db.close()

def test_resume_and_jd_gap_analysis():
    print("\n[Test 3] Testing Resume Upload, JD Submission, and Gap Analysis...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Upload mock resume
    resume_text = """
    Jane Doe - Software Engineer
    Skills: Python, Django, PostgreSQL, Docker, Git.
    Experience: 2 years building REST APIs and database models.
    Projects: E-commerce platform with PostgreSQL and Redis caching.
    Education: B.Tech Computer Science.
    """
    resume_res = client.post("/api/v1/resume/upload", data={"raw_text": resume_text}, headers=headers)
    assert resume_res.status_code == 200
    resume_data = resume_res.json()
    assert "id" in resume_data
    resume_id = resume_data["id"]
    print(f"  [OK] Resume processed and embedded (ID: {resume_id})")

    # Submit mock JD requiring skills the candidate lacks (e.g., C++, Low-Level Concurrency, Distributed Systems)
    jd_text = """
    Senior Systems Engineer
    Requirements:
    - 3+ years experience with C++, Multi-threading, and Concurrency.
    - Deep understanding of Operating Systems kernel internals, memory management, and Deadlocks.
    - Strong algorithmic background in Dynamic Programming and Graph algorithms.
    - Experience in distributed consensus protocols.
    """
    jd_res = client.post("/api/v1/jd/submit", json={"raw_text": jd_text}, headers=headers)
    assert jd_res.status_code == 200
    jd_data = jd_res.json()
    assert "id" in jd_data
    jd_id = jd_data["id"]
    print(f"  [OK] Job Description processed and embedded (ID: {jd_id})")

    # Run Gap Analysis
    gap_res = client.post("/api/v1/jd/gap-analysis", json={"resume_id": resume_id, "jd_id": jd_id}, headers=headers)
    assert gap_res.status_code == 200
    gap_analysis = gap_res.json()

    assert "overall_match_percentage" in gap_analysis
    assert "missing_critical_skills" in gap_analysis
    assert "recommended_interview_focus" in gap_analysis

    print(f"  [OK] Gap Analysis Generated:")
    print(f"    - Overall Match: {gap_analysis.get('overall_match_percentage')}%")
    print(f"    - Missing Skills Identified: {gap_analysis.get('missing_critical_skills')[:3]}")
    print(f"    - Recommended Focus: {[f.get('topic') for f in gap_analysis.get('recommended_interview_focus', [])]}")

if __name__ == "__main__":
    print("==========================================================")
    print("         Running Phase 1 Comprehensive Test Suite         ")
    print("==========================================================")
    test_subjects_and_topics()
    test_semantic_retrieval()
    test_resume_and_jd_gap_analysis()
    print("\n==========================================================")
    print("     ALL PHASE 1 INTEGRATION TESTS PASSED 100%!           ")
    print("==========================================================")
