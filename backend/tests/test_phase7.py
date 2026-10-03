import sys
import os
from fastapi.testclient import TestClient

# Ensure root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app
from backend.app.services.code_runner_service import execute_code_safely

client = TestClient(app)

def clean(text) -> str:
    if not text:
        return ""
    return str(text).encode('ascii', 'replace').decode('ascii')

def get_auth_token():
    email = "phase7_tester@example.com"
    pwd = "password123"
    client.post("/api/v1/auth/signup", json={"name": "P7 Tester", "email": email, "password": pwd})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login_res.json()["access_token"]

def test_code_execution_sandbox():
    print("==================================================================")
    print("      Running Phase 7 Sandbox & Multi-Subject Test Suite          ")
    print("==================================================================")

    print("\n[Test 1] Testing Code Runner Sandbox on Valid Python Code...")
    code = """
def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

primes = [x for x in range(2, 25) if is_prime(x)]
print("Primes:", primes)
"""
    res = execute_code_safely(code, language="python")
    print(f"  [OK] Sandbox Status: {res['status']}")
    print(f"  [OK] Execution Duration: {res['execution_time_ms']} ms")
    print(f"  [OK] Terminal Stdout: {clean(res['output']).strip()}")
    assert res["status"] == "success"
    assert "Primes: [2, 3, 5, 7, 11, 13, 17, 19, 23]" in res["output"]

    print("\n[Test 2] Testing Timeout Protection against Infinite Loops...")
    infinite_loop_code = """
while True:
    pass
"""
    res_timeout = execute_code_safely(infinite_loop_code, language="python")
    print(f"  [OK] Sandbox Status: {res_timeout['status']}")
    print(f"  [OK] Error Guard: {res_timeout['error']}")
    assert res_timeout["status"] == "timeout"
    assert "timed out" in res_timeout["error"].lower()

    print("\n[Test 3] Testing Runtime Error Capture...")
    err_code = """
print("Starting calculation...")
x = 10 / 0
print("Finished")
"""
    res_err = execute_code_safely(err_code, language="python")
    print(f"  [OK] Sandbox Status: {res_err['status']}")
    print(f"  [OK] Captured Stderr: {clean(res_err['error']).strip()}")
    assert res_err["status"] == "runtime_error"
    assert "ZeroDivisionError" in res_err["error"]

def test_code_runner_api_endpoint():
    print("\n[Test 4] Testing /api/v1/session/run-code HTTP Endpoint...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "code_content": "def add(a, b): return a + b\nprint('Result:', add(40, 2))",
        "code_language": "python"
    }
    res = client.post("/api/v1/session/run-code", headers=headers, json=payload)
    assert res.status_code == 200, f"run-code endpoint failed: {res.text}"
    body = res.json()

    print(f"  [OK] HTTP Status: {res.status_code}")
    print(f"  [OK] Endpoint Output: {clean(body['output']).strip()}")
    print(f"  [OK] Measured Latency: {body['execution_time_ms']} ms")
    assert body["status"] == "success"
    assert "Result: 42" in body["output"]

def test_multi_subject_combined_session():
    print("\n[Test 5] Testing Multi-Subject Combined Interview Session (DSA + OS + DBMS)...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    multi_start = client.post("/api/v1/session/start", json={
        "mode": "SUBJECT",
        "subject_ids": ["dsa", "os", "dbms"],
        "max_turns": 3
    }, headers=headers)

    assert multi_start.status_code == 200, f"Start multi-subject failed: {multi_start.text}"
    s_data = multi_start.json()
    session_id = s_data["id"]
    current_q = s_data["current_question"]

    print(f"  [OK] Multi-subject session created: {session_id}")
    print(f"  [OK] Subjects combined: {s_data['subject_ids']}")
    print(f"  [OK] First Question Topic: '{clean(current_q['topic_id'])}'")
    print(f"  [OK] Question Type: '{current_q['question_type']}'")
    print(f"  [OK] First Question Text: '{clean(current_q['question_text'])}'")
    assert len(s_data["subject_ids"]) == 3

    print("\n==================================================================")
    print("      ALL PHASE 7 SANDBOX & MULTI-SUBJECT TESTS PASSED 100%!      ")
    print("==================================================================")

if __name__ == "__main__":
    test_code_execution_sandbox()
    test_code_runner_api_endpoint()
    test_multi_subject_combined_session()
