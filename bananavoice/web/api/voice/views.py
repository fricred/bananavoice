"""Voice API endpoints for TTS and STT functionality."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from bananavoice.services.voice import VoiceService, get_voice_service
from bananavoice.services.voice.webrtc_bot import get_webrtc_voice_agent

router = APIRouter()


class TTSRequest(BaseModel):
    """Request model for text-to-speech."""

    text: str
    voice: str = "default"


class STTResponse(BaseModel):
    """Response model for speech-to-text."""

    text: str
    confidence: float = 0.0


class VoiceRoomRequest(BaseModel):
    """Request model for creating a voice room."""

    daily_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    cartesia_api_key: Optional[str] = None


class VoiceRoomResponse(BaseModel):
    """Response model for voice room creation."""

    room_url: str
    room_name: str
    bot_token: Optional[str] = None


class WebRTCOfferRequest(BaseModel):
    """Request model for WebRTC offer."""

    sdp: str
    type: str
    pc_id: Optional[str] = None


class WebRTCOfferResponse(BaseModel):
    """Response model for WebRTC offer."""

    sdp: str
    type: str
    pc_id: str


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


@router.get("/demo/realtime")
async def realtime_voice_demo() -> FileResponse:
    """
    Serve the real-time voice demo page.

    :return: HTML demo page.
    """
    demo_path = (
        Path(__file__).parent
        / ".."
        / ".."
        / ".."
        / "static"
        / "realtime_voice_demo.html"
    )
    return FileResponse(demo_path, media_type="text/html")


@router.post("/room/create", response_model=VoiceRoomResponse)
async def create_voice_room(request: VoiceRoomRequest) -> VoiceRoomResponse:
    """
    Create a Daily room for voice communication and launch the bot.

    :param request: Voice room creation request.
    :return: Room details and bot information.
    """
    try:
        # Create Daily room
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.daily.co/v1/rooms",
                headers={
                    "Authorization": f"Bearer {request.daily_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "properties": {
                        "max_participants": 10,
                        "enable_chat": False,
                        "enable_knocking": False,
                        "start_audio_off": False,
                        "start_video_off": True,
                        "enable_screenshare": False,
                    },
                },
            )
            response.raise_for_status()
            room_data = response.json()

        room_url = room_data["url"]
        room_name = room_data["name"]

        # Launch bot in background process
        bot_script = (
            Path(__file__).parent / ".." / ".." / ".." / "services" / "voice" / "bot.py"
        )

        # Get API keys from request or settings
        from bananavoice.settings import settings

        daily_key = request.daily_api_key or settings.daily_api_key
        openai_key = request.openai_api_key or settings.openai_api_key
        cartesia_key = request.cartesia_api_key or settings.cartesia_api_key

        if not daily_key:
            raise HTTPException(
                status_code=400,
                detail="Daily API key required (provide in request or set BANANAVOICE_DAILY_API_KEY env var)",
            )
        if not openai_key:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key required (provide in request or set BANANAVOICE_OPENAI_API_KEY env var)",
            )

        # Pass API keys to bot process via environment
        env = {**dict(os.environ)}
        env.update(
            {
                "BANANAVOICE_DAILY_API_KEY": daily_key,
                "BANANAVOICE_OPENAI_API_KEY": openai_key,
            },
        )
        if cartesia_key:
            env["BANANAVOICE_CARTESIA_API_KEY"] = cartesia_key

        # Start bot process
        subprocess.Popen(
            [
                sys.executable,
                str(bot_script),
                room_url,
            ],
            env=env,
        )

        return VoiceRoomResponse(
            room_url=room_url,
            room_name=room_name,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create voice room: {e!s}",
        ) from e


@router.get("/rooms")
async def list_rooms(daily_api_key: str) -> dict:
    """
    List available Daily rooms.

    :param daily_api_key: Daily API key.
    :return: List of rooms.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.daily.co/v1/rooms",
                headers={"Authorization": f"Bearer {daily_api_key}"},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list rooms: {e!s}",
        ) from e


@router.post("/webrtc/offer", response_model=WebRTCOfferResponse)
async def webrtc_offer(
    request: WebRTCOfferRequest,
    background_tasks: BackgroundTasks,
) -> WebRTCOfferResponse:
    """
    Handle WebRTC offer for voice agent connection.

    :param request: WebRTC offer request.
    :param background_tasks: Background tasks for async processing.
    :return: WebRTC answer response.
    """
    try:
        agent = get_webrtc_voice_agent()

        # Check if this is a renegotiation
        if request.pc_id:
            answer = await agent.renegotiate_connection(
                request.pc_id,
                request.sdp,
                request.type,
            )
            if answer:
                return WebRTCOfferResponse(**answer)

        # Create new connection
        answer = await agent.create_connection(request.sdp, request.type)
        return WebRTCOfferResponse(**answer)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"WebRTC offer failed: {e!s}",
        ) from e


@router.get("/webrtc/demo")
async def webrtc_demo() -> FileResponse:
    """
    Serve the WebRTC voice agent demo page.

    :return: HTML demo page.
    """
    demo_path = (
        Path(__file__).parent
        / ".."
        / ".."
        / ".."
        / "static"
        / "webrtc_voice_agent.html"
    )
    return FileResponse(demo_path, media_type="text/html")
