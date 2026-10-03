import sys
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.all_models import WeakTopicProfile, SessionReport

client = TestClient(app)

def clean(text) -> str:
    """Sanitize strings for Windows cp1252 terminal printing."""
    if not text:
        return ""
    return str(text).encode('ascii', 'replace').decode('ascii')

def get_auth_token():
    email = "phase2_tester@example.com"
    pwd = "password123"
    client.post("/api/v1/auth/signup", json={"name": "P2 Candidate", "email": email, "password": pwd})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login_res.json()["access_token"]

def test_complete_phase2_agent_loop():
    print("==========================================================")
    print("        Running Phase 2 Core Agent Loop Test Suite        ")
    print("==========================================================")

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Start Mode B Session (3 turns max)
    print("\n[Step 1] Starting Mode B Subject Interview Session (DSA & OS)...")
    start_res = client.post("/api/v1/session/start", json={
        "mode": "SUBJECT",
        "subject_ids": ["dsa", "os"],
        "max_turns": 3
    }, headers=headers)

    assert start_res.status_code == 200, f"Session start failed: {start_res.text}"
    session_data = start_res.json()
    session_id = session_data["id"]
    current_q = session_data["current_question"]

    assert session_id is not None
    assert current_q is not None
    print(f"  [OK] Session started successfully! (ID: {clean(session_id)})")
    print(f"  [OK] Question 1 Topic: {clean(current_q['topic_id'])} | Difficulty: {current_q['difficulty']}/5 | Source Mix: {clean(current_q['source_mix'])}")
    print(f"  [OK] Question 1 Text: '{clean(current_q['question_text'])}'")

    # Step 2: Answer Question 1 dynamically based on its topic
    print("\n[Step 2] Generating on-topic high-scoring candidate answer for Question 1...")
    import asyncio
    from backend.app.services.llm_service import call_groq_text
    strong_answer = asyncio.run(call_groq_text(
        f"Answer this technical question clearly in 2-3 sentences as a top candidate: {current_q['question_text']}",
        "You are an expert software engineer interviewing at a top tech company."
    ))
    print(f"  Candidate Answer: '{clean(strong_answer)}'")

    turn1_res = client.post(f"/api/v1/session/{session_id}/answer", json={
        "transcript_text": strong_answer
    }, headers=headers)

    assert turn1_res.status_code == 200, f"Turn 1 failed: {turn1_res.text}"
    turn1_data = turn1_res.json()
    eval1 = turn1_data["evaluation"]
    next_q1 = turn1_data["next_question"]

    print(f"  [OK] Evaluator Score: {eval1['score']}/10.0")
    print(f"  [OK] Evaluator Feedback: {clean(eval1['feedback_text'])}")
    assert eval1["score"] >= 6.0, f"Expected a high score for relevant answer, got {eval1['score']}"
    assert turn1_data["is_completed"] is False
    assert next_q1 is not None
    print(f"  [OK] Next Question 2 generated | Topic: {clean(next_q1['topic_id'])} | Difficulty: {next_q1['difficulty']}/5 | Source: {clean(next_q1['source_mix'])}")
    print(f"  [OK] Question 2 Text: '{clean(next_q1['question_text'])}'")

    # Step 3: Answer Question 2 with an incomplete/weak answer
    print("\n[Step 3] Submitting weak answer for Question 2 to test critic & difficulty adjustment...")
    weak_answer = "I'm not entirely sure, I think it uses an array or list to do something fast."
    turn2_res = client.post(f"/api/v1/session/{session_id}/answer", json={
        "transcript_text": weak_answer
    }, headers=headers)

    assert turn2_res.status_code == 200, f"Turn 2 failed: {turn2_res.text}"
    turn2_data = turn2_res.json()
    eval2 = turn2_data["evaluation"]
    next_q2 = turn2_data["next_question"]

    print(f"  [OK] Evaluator/Critic Score: {eval2['score']}/10.0 (Sanity-checked by Critic)")
    print(f"  [OK] Evaluator Feedback: {clean(eval2['feedback_text'])}")
    assert eval2["score"] <= 5.5, f"Expected a lower score for weak answer, got {eval2['score']}"
    assert turn2_data["is_completed"] is False
    assert next_q2 is not None
    print(f"  [OK] Question 3 generated | Topic: {clean(next_q2['topic_id'])} | Difficulty: {next_q2['difficulty']}/5")

    # Step 4: Answer Question 3 (Final turn)
    print("\n[Step 4] Submitting answer for Question 3 (Final turn)...")
    final_answer = (
        "Operating systems use demand paging to bring pages from disk to RAM only when referenced. "
        "A page fault triggers the OS to allocate a free frame, read the block from disk, and update the page table."
    )
    turn3_res = client.post(f"/api/v1/session/{session_id}/answer", json={
        "transcript_text": final_answer
    }, headers=headers)

    assert turn3_res.status_code == 200, f"Turn 3 failed: {turn3_res.text}"
    turn3_data = turn3_res.json()
    assert turn3_data["is_completed"] is True
    assert turn3_data["next_question"] is None
    print("  [OK] Turn 3 completed! Session transitioned to status: 'completed'")

    # Step 5: Verify Final Session Report
    print("\n[Step 5] Fetching Final Session Report...")
    report_res = client.get(f"/api/v1/session/{session_id}/report", headers=headers)
    assert report_res.status_code == 200, f"Get report failed: {report_res.text}"
    report = report_res.json()

    print(f"  [OK] Overall Report Score: {report['overall_score']} / 10.0")
    print(f"  [OK] Executive Summary: {clean(report['summary_text'])}")
    print(f"  [OK] Identified Strengths: {[clean(s) for s in report['strengths_json']]}")
    print(f"  [OK] Identified Weaknesses: {[clean(w) for w in report['weaknesses_json']]}")
    print(f"  [OK] Topic Breakdown: {report['topic_breakdown_json']}")

    # Step 6: Verify Database Persistence
    print("\n[Step 6] Verifying Database Persistence & Weak Topic Profile...")
    db = SessionLocal()
    try:
        profiles = db.query(WeakTopicProfile).all()
        assert len(profiles) > 0
        print(f"  [OK] User has {len(profiles)} tracked topics in weak_topic_profile table.")
        for p in profiles[:3]:
            print(f"    - Topic: {clean(p.topic_id)} | Running Score: {p.running_score} | Attempts: {p.attempts_count}")
    finally:
        db.close()

    print("\n==========================================================")
    print("     ALL PHASE 2 AGENT LOOP TESTS PASSED 100%!           ")
    print("==========================================================")

if __name__ == "__main__":
    test_complete_phase2_agent_loop()
