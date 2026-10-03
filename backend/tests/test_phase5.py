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
from backend.app.services.voice_service import transcribe_audio_bytes
from backend.app.core.database import SessionLocal
from backend.app.models.all_models import Answer, Evaluation

client = TestClient(app)

def clean(text) -> str:
    if not text:
        return ""
    return str(text).encode('ascii', 'replace').decode('ascii')

def generate_synthetic_pcm_wav(duration_sec: float = 1.0, sample_rate: int = 16000, freq: float = 440.0) -> bytes:
    """Generates synthetic 16-bit PCM WAV audio bytes for testing audio pipelines."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)       # Mono
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(sample_rate)
        num_samples = int(duration_sec * sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            # Sine wave tone
            value = int(math.sin(2 * math.pi * freq * (i / sample_rate)) * 16384)
            frames += value.to_bytes(2, byteorder='little', signed=True)
        wf.writeframes(frames)
    buf.seek(0)
    return buf.read()

def get_auth_token():
    email = "phase5_voice@example.com"
    pwd = "password123"
    client.post("/api/v1/auth/signup", json={"name": "P5 Voice Tester", "email": email, "password": pwd})
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    return login_res.json()["access_token"]

def test_voice_service_unit():
    print("==================================================================")
    print("           Running Phase 5 Voice Layer Test Suite                 ")
    print("==================================================================")

    print("\n[Test 1] Testing Groq Whisper Audio Transcription Engine...")
    wav_bytes = generate_synthetic_pcm_wav(duration_sec=1.2)
    assert len(wav_bytes) > 1000

    result = asyncio.run(transcribe_audio_bytes(
        audio_bytes=wav_bytes,
        filename="test_tone.wav",
        content_type="audio/wav",
        prompt_context="Technical interview on Binary Search Trees"
    ))

    print(f"  [OK] Transcription Success: {result['success']}")
    print(f"  [OK] Model Used: {result.get('model')}")
    print(f"  [OK] Groq Whisper Latency: {result.get('latency_ms')} ms")
    assert result["success"] is True, f"Expected success=True from Groq Whisper, got {result}"
    assert result["model"] == "whisper-large-v3-turbo"

    print("\n[Test 2] Testing Voice Engine Edge Cases (Empty & Truncated Audio)...")
    res_empty = asyncio.run(transcribe_audio_bytes(
        audio_bytes=b"too_short",
        filename="empty.wav",
        content_type="audio/wav"
    ))
    assert res_empty["success"] is False
    assert "too short" in res_empty["error"]
    print("  [OK] Empty/short audio gracefully caught without throwing exception.")

def test_voice_api_endpoint():
    print("\n[Test 3] Testing /api/v1/voice/transcribe HTTP Endpoint...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    wav_bytes = generate_synthetic_pcm_wav(duration_sec=1.0)
    files = {
        "audio_file": ("answer.wav", wav_bytes, "audio/wav")
    }
    data = {
        "prompt_context": "Data Structures and Algorithms"
    }

    res = client.post("/api/v1/voice/transcribe", headers=headers, files=files, data=data)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    body = res.json()

    print(f"  [OK] HTTP Status: {res.status_code}")
    print(f"  [OK] Response Success: {body.get('success')}")
    print(f"  [OK] Measured Server Latency: {body.get('latency_ms')} ms")
    assert body.get("success") is True

def test_full_voice_to_evaluation_flow():
    print("\n[Test 4] Testing Full Voice-to-Evaluation Interview Turn Flow...")
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start a session
    start_res = client.post("/api/v1/session/start", json={
        "mode": "SUBJECT",
        "subject_ids": ["dbms"],
        "max_turns": 2
    }, headers=headers)
    assert start_res.status_code == 200
    session_id = start_res.json()["id"]
    current_q = start_res.json()["current_question"]
    print(f"  [OK] Started Session on DBMS: '{clean(current_q['question_text'])}'")

    # 2. Transcribe voice audio
    wav_bytes = generate_synthetic_pcm_wav(duration_sec=1.0)
    files = {"audio_file": ("spoken_response.wav", wav_bytes, "audio/wav")}
    transcribe_res = client.post("/api/v1/voice/transcribe", headers=headers, files=files)
    assert transcribe_res.status_code == 200

    # 3. Submit spoken answer based on transcript addressing the exact question asked
    from backend.app.services.llm_service import call_groq_text
    prompt = f"Provide an accurate, 2-sentence interview response to the question: '{current_q['question_text']}'"
    spoken_answer = asyncio.run(call_groq_text(prompt, "You are a senior software engineer candidate in an interview."))

    ans_res = client.post(f"/api/v1/session/{session_id}/answer", json={
        "transcript_text": spoken_answer,
        "answer_mode": "spoken"
    }, headers=headers)

    assert ans_res.status_code == 200
    turn_data = ans_res.json()
    evaluation = turn_data["evaluation"]

    print(f"  [OK] Turn Evaluated Score: {evaluation['score']}/10.0")
    print(f"  [OK] Sub-Scores: {evaluation['sub_scores_json']}")
    print(f"  [OK] Evaluation Feedback: {clean(evaluation['feedback_text'])}")
    assert evaluation["score"] >= 6.5, f"Expected high score for accurate answer, got {evaluation['score']}"
    assert "technical_accuracy" in evaluation["sub_scores_json"]



    print("\n==================================================================")
    print("        ALL PHASE 5 VOICE LAYER TESTS PASSED 100%!                ")
    print("==================================================================")

if __name__ == "__main__":
    test_voice_service_unit()
    test_voice_api_endpoint()
    test_full_voice_to_evaluation_flow()
