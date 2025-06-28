"""Voice API endpoints for TTS and STT functionality."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from bananavoice.services.voice import VoiceService, get_voice_service

router = APIRouter()


class TTSRequest(BaseModel):
    """Request model for text-to-speech."""

    text: str
    voice: str = "default"


class STTResponse(BaseModel):
    """Response model for speech-to-text."""

    text: str
    confidence: float = 0.0


@router.post("/tts", response_class=Response)
async def text_to_speech(
    request: TTSRequest,
    voice_service: VoiceService = Depends(get_voice_service),
) -> Response:
    """
    Convert text to speech.

    :param request: TTS request with text and voice parameters.
    :param voice_service: Voice service instance.
    :return: Audio data as response.
    """
    try:
        audio_data = await voice_service.text_to_speech(request.text)

        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS processing failed: {e!s}",
        ) from e


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(...),
    voice_service: VoiceService = Depends(get_voice_service),
) -> STTResponse:
    """
    Convert speech to text.

    :param audio: Audio file upload.
    :param voice_service: Voice service instance.
    :return: Transcribed text with confidence score.
    """
    try:
        if not audio.content_type or not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid audio file format")

        audio_data = await audio.read()
        text = await voice_service.process_audio(audio_data)

        return STTResponse(text=text, confidence=0.95)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"STT processing failed: {e!s}",
        ) from e


@router.get("/health")
async def voice_health() -> dict[str, str]:
    """
    Health check for voice services.

    :return: Health status.
    """
    return {"status": "healthy", "service": "voice"}


@router.get("/demo")
async def voice_demo() -> FileResponse:
    """
    Serve the voice demo page.

    :return: HTML demo page.
    """
    demo_path = (
        Path(__file__).parent / ".." / ".." / ".." / "static" / "voice_demo.html"
    )
    return FileResponse(demo_path, media_type="text/html")
