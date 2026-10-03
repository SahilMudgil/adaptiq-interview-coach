import io
import time
import logging
from typing import Dict, Any, Optional
from backend.app.services.llm_service import get_groq_client

logger = logging.getLogger("uvicorn.error")

TECHNICAL_VOCAB_HINT = (
    "Computer Science technical interview: Data Structures, Algorithms, Two-Pointer, Hash Map, "
    "Binary Search Tree, AVL, Heap, Trie, Graph BFS DFS, Dijkstra, Dynamic Programming, "
    "Time Complexity O(n), O(log n), O(1), Space Complexity, ACID transactions, B-Tree indexing, "
    "Normalization 1NF 2NF 3NF, Sharding, Replication, PostgreSQL, Redis, TCP/IP, UDP, Three-Way Handshake, "
    "DNS, HTTP/2, Deadlock, Virtual Memory, Paging, Mutex, Semaphore, OOP, Polymorphism, Encapsulation, "
    "Inheritance, Abstraction, Python, Java, C++, TypeScript, JavaScript, Microservices, REST API."
)

async def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    content_type: str = "audio/webm",
    prompt_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribes audio bytes using Groq Whisper (whisper-large-v3-turbo)
    with technical vocabulary conditioning and latency measurement.
    """
    start_time = time.time()
    client = get_groq_client()
    if not client:
        return {
            "success": False,
            "error": "Groq client is not configured with GROQ_API_KEY",
            "transcript": "",
            "duration_ms": 0
        }

    if not audio_bytes or len(audio_bytes) < 100:
        return {
            "success": False,
            "error": "Audio payload is empty or too short.",
            "transcript": "",
            "duration_ms": 0
        }

    # Combine technical domain vocab hint with contextual prompt if provided
    combined_prompt = TECHNICAL_VOCAB_HINT
    if prompt_context:
        combined_prompt = f"{prompt_context.strip()}. {TECHNICAL_VOCAB_HINT}"

    # Ensure suitable filename extension for Groq whisper audio recognition
    ext = "webm"
    if "wav" in content_type.lower() or filename.lower().endswith(".wav"):
        ext = "wav"
    elif "mp3" in content_type.lower() or filename.lower().endswith(".mp3"):
        ext = "mp3"
    elif "ogg" in content_type.lower() or filename.lower().endswith(".ogg"):
        ext = "ogg"
    elif "m4a" in content_type.lower() or filename.lower().endswith(".m4a"):
        ext = "m4a"

    audio_file_tuple = (f"candidate_voice.{ext}", audio_bytes, content_type)

    try:
        response = client.audio.transcriptions.create(
            file=audio_file_tuple,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            language="en",
            temperature=0.0,
            prompt=combined_prompt
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        transcript_text = getattr(response, "text", "") or ""
        transcript_text = transcript_text.strip()

        # Sanitize common Whisper artifacts when completely silent
        unwanted_noise_tokens = ["[blank_audio]", "[applause]", "[laughter]", "[music]", "..."]
        clean_text = transcript_text
        if clean_text.lower() in unwanted_noise_tokens:
            clean_text = ""

        duration = getattr(response, "duration", None)
        language = getattr(response, "language", "en")

        return {
            "success": True,
            "transcript": clean_text,
            "raw_text": transcript_text,
            "duration_seconds": duration,
            "latency_ms": elapsed_ms,
            "model": "whisper-large-v3-turbo",
            "language": language
        }
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": str(e),
            "transcript": "",
            "latency_ms": elapsed_ms,
            "model": "whisper-large-v3-turbo"
        }
