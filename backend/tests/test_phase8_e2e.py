import sys
import os
import io
import wave
import math
import asyncio
from fastapi.testclient import TestClient

# Ensure root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.all_models import (
    User, Resume, JobDescription, InterviewSession, Question, Answer, Evaluation, SessionReport, WeakTopicProfile
)

client = TestClient(app)

def clean(text) -> str:
    if not text:
        return ""
    return str(text).encode('ascii', 'replace').decode('ascii')

def generate_test_audio() -> bytes:
    """Generates synthetic 16-bit PCM WAV audio."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        num_samples = int(1.0 * 16000)
        frames = bytearray()
        for i in range(num_samples):
            val = int(math.sin(2 * math.pi * 440.0 * (i / 16000)) * 16384)
            frames += val.to_bytes(2, byteorder='little', signed=True)
        wf.writeframes(frames)
    buf.seek(0)
    return buf.read()

def get_auth_token():
    email = "e2e_candidate@interviewcoach.ai"
    pwd = "SecurePassword123!"
    client.post("/api/v1/auth/signup", json={"name": "Alex Candidate", "email": email, "password": pwd})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login_res.json()["access_token"]

def test_complete_e2e_system():
    print("==================================================================")
    print("      AI-POWERED ADAPTIVE INTERVIEW COACH — MASTER E2E TEST       ")
    print("==================================================================")

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    print("  [OK] Step 1: Candidate authenticated with JWT.")

    # -------------------------------------------------------------
    # JOURNEY 1: Mode A (Targeted Resume + JD Gap Analysis)
    # -------------------------------------------------------------
    print("\n------------------------------------------------------------------")
    print("  JOURNEY 1: Mode A — Targeted JD + Resume Gap Analysis Flow      ")
    print("------------------------------------------------------------------")

    # 1.1 Upload Resume
    resume_text = (
        "Experienced Backend Developer with 3 years in Python, FastAPI, and PostgreSQL. "
        "Built microservices and REST APIs. Basic knowledge of Docker and Git. "
        "Looking for Backend Engineer role."
    )
    resume_file = io.BytesIO(resume_text.encode('utf-8'))
    files = {"file": ("resume.txt", resume_file, "text/plain")}
    res_upload = client.post("/api/v1/resume/upload", headers=headers, files=files)
    assert res_upload.status_code == 200, f"Resume upload failed: {res_upload.text}"
    resume_id = res_upload.json()["id"]
    print(f"  [OK] Resume uploaded and parsed. Resume ID: {resume_id}")

    # 1.2 Submit JD
    jd_text = (
        "Seeking Senior Backend Engineer. Requirements: Expert in Python and Distributed Systems. "
        "Strong knowledge of Database Indexing, B-Trees, Normalization, and Redis caching. "
        "Experience with Docker, Kubernetes, and Microservices design patterns."
    )
    jd_res = client.post("/api/v1/jd/submit", headers=headers, json={"raw_text": jd_text})
    assert jd_res.status_code == 200, f"JD submit failed: {jd_res.text}"
    jd_id = jd_res.json()["id"]
    print(f"  [OK] Job Description parsed. JD ID: {jd_id}")

    # 1.3 Run Gap Analysis
    gap_res = client.post("/api/v1/jd/gap-analysis", headers=headers, json={
        "resume_id": resume_id,
        "jd_id": jd_id
    })
    assert gap_res.status_code == 200, f"Gap analysis failed: {gap_res.text}"
    gap_data = gap_res.json()
    match_score = gap_data.get("match_score", 70)
    gaps = gap_data.get("missing_skills", [])
    print(f"  [OK] Gap Analysis Complete! Match Score: {match_score}% | Identified Gaps: {gaps[:3]}")

    # 1.4 Start Mode A Targeted Interview Session
    mode_a_res = client.post("/api/v1/session/start", headers=headers, json={
        "mode": "JD",
        "resume_id": resume_id,
        "jd_id": jd_id,
        "max_turns": 2
    })
    assert mode_a_res.status_code == 200
    session_a = mode_a_res.json()
    session_a_id = session_a["id"]
    question_a = session_a["current_question"]
    print(f"  [OK] Mode A Session started: {session_a_id}")
    print(f"       Targeted Question: '{clean(question_a['question_text'])}'")

    # 1.5 Spoken Answer via Whisper STT & Evaluator Scoring
    wav_bytes = generate_test_audio()
    stt_res = client.post(
        "/api/v1/voice/transcribe",
        headers=headers,
        files={"audio_file": ("answer.wav", wav_bytes, "audio/wav")}
    )
    assert stt_res.status_code == 200
    print(f"  [OK] Voice STT latency: {stt_res.json().get('latency_ms')} ms")

    answer_a_text = (
        "In distributed architectures, caching with Redis reduces database query load by storing frequently "
        "read keys in memory with TTL expiration. Database indexing uses B-Trees to provide O(log n) lookup times."
    )
    turn_a_res = client.post(f"/api/v1/session/{session_a_id}/answer", headers=headers, json={
        "transcript_text": answer_a_text,
        "answer_mode": "spoken"
    })
    assert turn_a_res.status_code == 200
    eval_a = turn_a_res.json()["evaluation"]
    print(f"  [OK] Mode A Evaluator Score: {eval_a['score']}/10.0")
    print(f"       Feedback: {clean(eval_a['feedback_text'])}")

    # -------------------------------------------------------------
    # JOURNEY 2: Mode B (Multi-Subject with Coding Sandbox)
    # -------------------------------------------------------------
    print("\n------------------------------------------------------------------")
    print("  JOURNEY 2: Mode B — Multi-Subject & Monaco Sandbox Flow         ")
    print("------------------------------------------------------------------")

    # 2.1 Start Combined DSA + DBMS Session
    mode_b_res = client.post("/api/v1/session/start", headers=headers, json={
        "mode": "SUBJECT",
        "subject_ids": ["dsa", "dbms"],
        "max_turns": 2
    })
    assert mode_b_res.status_code == 200
    session_b = mode_b_res.json()
    session_b_id = session_b["id"]
    question_b = session_b["current_question"]
    print(f"  [OK] Mode B Session started: {session_b_id}")
    print(f"       Combined Subjects: {session_b['subject_ids']}")
    print(f"       Question Type: {question_b['question_type']} | Topic: {question_b['topic_id']}")

    # 2.2 Test Candidate Code Execution in Sandbox
    code_candidate = """
def two_sum(nums, target):
    lookup = {}
    for i, n in enumerate(nums):
        diff = target - n
        if diff in lookup:
            return [lookup[diff], i]
        lookup[n] = i
    return []

print("Result:", two_sum([2, 7, 11, 15], 9))
"""
    run_res = client.post("/api/v1/session/run-code", headers=headers, json={
        "code_content": code_candidate,
        "code_language": "python"
    })
    assert run_res.status_code == 200
    run_data = run_res.json()
    print(f"  [OK] Sandbox Code Executed! Status: {run_data['status']} | Output: {clean(run_data['output']).strip()} ({run_data['execution_time_ms']}ms)")
    assert run_data["status"] == "success"

    # 2.3 Submit Code Solution & Spoken Narration
    turn_b_res = client.post(f"/api/v1/session/{session_b_id}/answer", headers=headers, json={
        "code_submission": code_candidate,
        "code_language": "python",
        "answer_mode": "full_code",
        "transcript_text": "I used a hash map to achieve O(n) time and O(n) space complexity."
    })
    assert turn_b_res.status_code == 200
    turn_b_data = turn_b_res.json()
    eval_b = turn_b_data["evaluation"]
    print(f"  [OK] Mode B Code Evaluated Score: {eval_b['score']}/10.0")

    # Complete the second turn to trigger report generation
    next_q = turn_b_data["next_question"]
    if next_q:
        client.post(f"/api/v1/session/{session_b_id}/answer", headers=headers, json={
            "transcript_text": "BCNF eliminates all transitive and partial functional dependencies.",
            "answer_mode": "spoken"
        })

    # 2.4 Verify Final Executive Report
    report_res = client.get(f"/api/v1/session/{session_b_id}/report", headers=headers)
    assert report_res.status_code == 200
    report = report_res.json()
    print(f"  [OK] Final Executive Report Score: {report['overall_score']}/10.0")
    print(f"       Executive Summary: {clean(report['summary_text'])}")

    # -------------------------------------------------------------
    # JOURNEY 3: Candidate Dashboard & Performance Analytics
    # -------------------------------------------------------------
    print("\n------------------------------------------------------------------")
    print("  JOURNEY 3: Candidate Dashboard & Analytics Verification         ")
    print("------------------------------------------------------------------")

    dash_res = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()

    print(f"  [OK] Dashboard Total Interviews: {dash_data['summary']['total_interviews']}")
    print(f"  [OK] Average Score: {dash_data['summary']['average_score']}/10.0 ({dash_data['summary']['tier_badge']})")
    print(f"  [OK] 4-Rubric Balance: {dash_data['rubric_radar']}")
    print(f"  [OK] Core CS Subjects Mastery Count: {len(dash_data['subject_mastery'])}")
    print(f"  [OK] Tracked Weak-Topic Profile Entries: {len(dash_data['weak_topic_heatmap'])}")

    # Export report check
    export_res = client.get(f"/api/v1/analytics/session/{session_b_id}/export", headers=headers)
    assert export_res.status_code == 200
    assert "PERFORMANCE REPORT" in export_res.text
    print("  [OK] Downloadable Performance Summary Export verified.")

    print("\n==================================================================")
    print("     ALL MASTER E2E SYSTEM TESTS PASSED CLEANLY (100%)!           ")
    print("==================================================================")

if __name__ == "__main__":
    test_complete_e2e_system()
