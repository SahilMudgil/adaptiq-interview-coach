import json
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
from backend.app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def get_groq_client() -> Optional[Groq]:
    if not settings.GROQ_API_KEY:
        return None
    try:
        return Groq(api_key=settings.GROQ_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        return None

# Active high-speed models on Groq
PRIMARY_MODEL = "openai/gpt-oss-120b"
FAST_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODEL = "qwen/qwen3.8-27b"

async def call_groq_json(prompt: str, system_prompt: str = "You are an expert technical interviewer assistant. Return valid JSON only.", model: str = FAST_MODEL) -> Dict[str, Any]:
    client = get_groq_client()
    if not client:
        # Graceful fallback mock if Groq is temporarily unreachable
        return {"error": "Groq client not configured"}

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"{system_prompt} You must respond ONLY with a raw JSON object, without markdown formatting or code fences."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        logger.warning(f"Groq JSON call failed ({e}). Retrying with primary model {PRIMARY_MODEL}...")
        try:
            response = client.chat.completions.create(
                model=PRIMARY_MODEL,
                messages=[
                    {"role": "system", "content": f"{system_prompt} Return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content.strip())
        except Exception as err:
            logger.error(f"Groq call failed completely: {err}")
            return {"error": str(err)}

async def call_groq_text(prompt: str, system_prompt: str, model: str = FAST_MODEL) -> str:
    client = get_groq_client()
    if not client:
        return "I am ready for your answer."

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq text call failed: {e}")
        return f"Could you elaborate on your experience with this topic?"
