import sys
import os
from fastapi.testclient import TestClient

# Ensure root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.all_models import Topic, QuestionBank, InterviewSession, User
from backend.app.services.analytics_service import get_user_dashboard_analytics, generate_session_text_export

client = TestClient(app)

def clean(text) -> str:
    if not text:
        return ""
    return str(text).encode('ascii', 'replace').decode('ascii')

def get_auth_token():
    email = "phase6_analytics@example.com"
    pwd = "password123"
    client.post("/api/v1/auth/signup", json={"name": "P6 Analyst", "email": email, "password": pwd})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login_res.json()["access_token"]

def test_basic_math_logic_question_bank():
    print("==================================================================")
    print("      Running Phase 6 Analytics & Question Bank Test Suite        ")
    print("==================================================================")

    print("\n[Test 1] Verifying Seeded Foundational Math & Number Logic Questions...")
    db = SessionLocal()
    try:
        topic = db.query(Topic).filter(Topic.id == "dsa_basic_math_logic").first()
        assert topic is not None, "Topic dsa_basic_math_logic must exist in database"
        assert topic.subject_id == "dsa"
        print(f"  [OK] Verified Topic '{topic.name}' under subject '{topic.subject_id}'")

        questions = db.query(QuestionBank).filter(QuestionBank.topic_id == "dsa_basic_math_logic").all()
        assert len(questions) >= 20, f"Expected >= 20 seeded math/logic questions, got {len(questions)}"
        print(f"  [OK] Found {len(questions)} seeded questions under dsa_basic_math_logic:")

        sample_keywords = ["prime", "factorial", "fibonacci", "reverse", "palindrome", "armstrong", "gcd", "lcm", "swap"]
        for kw in sample_keywords:
            matched = any(kw in q.question_text.lower() for q in questions)
            assert matched, f"Expected question containing '{kw}' in question bank"
            print(f"       + Confirmed problem: {kw.capitalize()}")

    finally:
        db.close()

def test_analytics_service_unit():
    print("\n[Test 2] Testing Analytics Aggregation Service Unit Logic...")
    db = SessionLocal()
    try:
        user = db.query(User).first()
        assert user is not None

        analytics = get_user_dashboard_analytics(user.id, db)
        assert "summary" in analytics
        assert "rubric_radar" in analytics
        assert "subject_mastery" in analytics
        assert "weak_topic_heatmap" in analytics
        assert "recent_sessions" in analytics

        # Check radar rubrics
        radar = analytics["rubric_radar"]
        for key in ["technical_accuracy", "clarity", "completeness", "depth"]:
            assert key in radar
            assert 0.0 <= radar[key] <= 10.0
        print(f"  [OK] Radar Averages: Accuracy={radar['technical_accuracy']}, Clarity={radar['clarity']}, Completeness={radar['completeness']}, Depth={radar['depth']}")

        # Check subject mastery for 7 subjects
        subjects = analytics["subject_mastery"]
        assert len(subjects) == 7, f"Expected 7 subjects in mastery list, got {len(subjects)}"
        subject_names = [s["name"] for s in subjects]
        print(f"  [OK] 7 Subjects Tracked in Mastery Grid: {subject_names[:3]}... ({len(subjects)} total)")

    finally:
        db.close()

def test_analytics_api_endpoints():
    print("\n[Test 3] Testing /api/v1/analytics/dashboard HTTP Endpoint...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert res.status_code == 200, f"Dashboard endpoint failed: {res.text}"
    body = res.json()

    print(f"  [OK] HTTP Status: {res.status_code}")
    print(f"  [OK] Dashboard Summary: {body['summary']}")
    assert body["summary"]["tier_badge"] is not None

    print("\n[Test 4] Testing /api/v1/analytics/sessions HTTP Endpoint...")
    sessions_res = client.get("/api/v1/analytics/sessions", headers=headers)
    assert sessions_res.status_code == 200
    s_body = sessions_res.json()
    assert "sessions" in s_body
    print(f"  [OK] Successfully retrieved past sessions list ({len(s_body['sessions'])} sessions found)")

def test_session_report_export():
    print("\n[Test 5] Testing Session Performance Summary Export...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Start a quick session to test export
    start_res = client.post("/api/v1/session/start", json={
        "mode": "SUBJECT",
        "subject_ids": ["dsa"],
        "max_turns": 1
    }, headers=headers)
    assert start_res.status_code == 200
    session_id = start_res.json()["id"]

    export_res = client.get(f"/api/v1/analytics/session/{session_id}/export", headers=headers)
    assert export_res.status_code == 200
    text = export_res.text

    assert "PERFORMANCE REPORT" in text
    assert session_id in text
    print(f"  [OK] Export text successfully generated ({len(text)} characters):")
    print("------------------------------------------------------------------")
    for line in text.splitlines()[:10]:
        print("  " + clean(line))
    print("------------------------------------------------------------------")

    print("\n==================================================================")
    print("      ALL PHASE 6 ANALYTICS & DASHBOARD TESTS PASSED 100%!        ")
    print("==================================================================")

if __name__ == "__main__":
    test_basic_math_logic_question_bank()
    test_analytics_service_unit()
    test_analytics_api_endpoints()
    test_session_report_export()
