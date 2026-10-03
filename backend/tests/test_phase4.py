import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Ensure root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.services.code_evaluator import evaluate_code_submission
from backend.app.core.database import SessionLocal
from backend.app.models.all_models import Answer, Evaluation

client = TestClient(app)

def clean(text) -> str:
    if not text:
        return ""
    return str(text).encode('ascii', 'replace').decode('ascii')

def get_auth_token():
    email = "phase4_coder@example.com"
    pwd = "password123"
    client.post("/api/v1/auth/signup", json={"name": "P4 Coder", "email": email, "password": pwd})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login_res.json()["access_token"]

def test_code_evaluator_unit():
    print("==================================================================")
    print("       Running Phase 4 Coding Questions Test Suite                ")
    print("==================================================================")

    print("\n[Test 1] Testing Code Evaluator on Optimal O(n) Two-Sum in Python...")
    optimal_code = """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""
    res_optimal = asyncio.run(evaluate_code_submission(
        question_text="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        topic_name="Arrays and Strings",
        difficulty=2,
        code_submission=optimal_code,
        code_language="python",
        answer_mode="full_code",
        spoken_narration="I use a hash map to look up complements in O(1) time."
    ))

    print(f"  [OK] Optimal Code Score: {res_optimal['score']} / 10.0")
    print(f"  [OK] Detected Time Complexity: {res_optimal.get('time_complexity_detected')}")
    print(f"  [OK] Detected Space Complexity: {res_optimal.get('space_complexity_detected')}")
    print(f"  [OK] Code Feedback: {clean(res_optimal['feedback'])}")
    assert res_optimal["score"] >= 8.0, "Expected >= 8.0 for optimal O(n) solution"

    print("\n[Test 2] Testing Code Evaluator on Sub-optimal O(n^2) Brute Force...")
    brute_force_code = """
def two_sum(nums, target):
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
    res_brute = asyncio.run(evaluate_code_submission(
        question_text="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        topic_name="Arrays and Strings",
        difficulty=2,
        code_submission=brute_force_code,
        code_language="python",
        answer_mode="full_code"
    ))

    print(f"  [OK] Brute-Force Code Score: {res_brute['score']} / 10.0")
    print(f"  [OK] Detected Time Complexity: {res_brute.get('time_complexity_detected')}")
    print(f"  [OK] Code Feedback: {clean(res_brute['feedback'])}")
    assert res_brute["score"] < res_optimal["score"], "Optimal score must exceed brute force score"

    print("\n[Test 3] Testing Pseudocode Mode...")
    pseudocode = """
initialize empty hash_table
for each index i and element x in array:
    diff = target - x
    if diff exists in hash_table:
        return (hash_table[diff], i)
    hash_table[x] = i
return null
"""
    res_pseudo = asyncio.run(evaluate_code_submission(
        question_text="Two Sum problem in pseudocode",
        topic_name="Arrays and Strings",
        difficulty=2,
        code_submission=pseudocode,
        code_language="python",
        answer_mode="pseudocode"
    ))

    print(f"  [OK] Pseudocode Score: {res_pseudo['score']} / 10.0")
    assert res_pseudo["score"] >= 7.5, "Expected high score for logically complete pseudocode"

def test_code_interview_turn_integration():
    print("\n[Test 4] Testing Live Agent Turn with Monaco Code Submission...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Start session on DSA
    start_res = client.post("/api/v1/session/start", json={
        "mode": "SUBJECT",
        "subject_ids": ["dsa"],
        "max_turns": 2
    }, headers=headers)

    assert start_res.status_code == 200
    s_data = start_res.json()
    session_id = s_data["id"]
    current_q = s_data["current_question"]
    print(f"  [OK] Session started with question_type: '{current_q['question_type']}' on topic '{current_q['topic_id']}'")

    # Submit Code Answer
    code_submission = """
def solve(nums):
    if not nums:
        return 0
    # Two pointer reverse
    left, right = 0, len(nums) - 1
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1
    return nums
"""
    answer_res = client.post(f"/api/v1/session/{session_id}/answer", json={
        "code_submission": code_submission,
        "code_language": "python",
        "answer_mode": "full_code",
        "transcript_text": "I used a two-pointer technique to reverse in O(n) time and O(1) space."
    }, headers=headers)

    assert answer_res.status_code == 200
    turn_data = answer_res.json()
    evaluation = turn_data["evaluation"]

    print(f"  [OK] Code Evaluated Score: {evaluation['score']}/10.0")
    print(f"  [OK] Evaluator Model Version: {evaluation['evaluator_model_version']}")
    print(f"  [OK] Code Feedback: {clean(evaluation['feedback_text'])}")

    # Verify DB persistence of code fields
    db = SessionLocal()
    try:
        ans = db.query(Answer).filter(Answer.code_submission != None).order_by(Answer.submitted_at.desc()).first()
        assert ans is not None
        assert ans.code_language == "python"
        assert ans.answer_mode == "full_code"
        assert "two pointer" in ans.code_submission.lower()
        print("  [OK] Verified code_submission, code_language, and answer_mode stored in DB answers table.")
    finally:
        db.close()

    print("\n==================================================================")
    print("      ALL PHASE 4 CODING QUESTION TESTS PASSED 100%!             ")
    print("==================================================================")

if __name__ == "__main__":
    test_code_evaluator_unit()
    test_code_interview_turn_integration()
