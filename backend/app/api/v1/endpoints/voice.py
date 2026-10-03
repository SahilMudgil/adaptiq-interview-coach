import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from backend.app.api.deps import get_current_user
from backend.app.models.all_models import User
from backend.app.services.voice_service import transcribe_audio_bytes


logger = logging.getLogger("uvicorn.error")

router = APIRouter()

@router.post("/transcribe")
async def transcribe_voice(
    audio_file: UploadFile = File(...),
    prompt_context: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribes spoken interview audio using Groq Whisper (whisper-large-v3-turbo).
    Returns transcript, speech duration, and execution latency.
    """
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file uploaded."
        )

    try:
        audio_bytes = await audio_file.read()
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded audio file is empty."
            )

        result = await transcribe_audio_bytes(
            audio_bytes=audio_bytes,
            filename=audio_file.filename or "recording.webm",
            content_type=audio_file.content_type or "audio/webm",
            prompt_context=prompt_context
        )

        if not result.get("success"):
            logger.warning(f"Voice transcription warning: {result.get('error')}")
            # Still return 200 with error info so UI can degrade gracefully
            return {
                "success": False,
                "transcript": "",
                "error": result.get("error"),
                "latency_ms": result.get("latency_ms", 0)
            }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling voice transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription processing error: {str(e)}"
        )
