"""Tests for voice functionality."""

import pytest
from fastapi.testclient import TestClient

from bananavoice.services.voice import VoiceService


@pytest.mark.asyncio
async def test_voice_service_tts() -> None:
    """Test that voice service can generate TTS audio."""
    service = VoiceService()

    # Test text to speech
    audio_data = await service.text_to_speech("Hello World")
    assert isinstance(audio_data, bytes)
    assert len(audio_data) > 0

    # Check that it's a valid WAV file (starts with RIFF)
    assert audio_data.startswith(b"RIFF")


@pytest.mark.asyncio
async def test_voice_service_stt() -> None:
    """Test that voice service can process audio."""
    service = VoiceService()

    # Test with dummy audio data
    dummy_audio = b"dummy_audio_data" * 100  # Make it > 1000 bytes
    result = await service.process_audio(dummy_audio)

    assert isinstance(result, str)
    assert "Hello from BananaVoice" in result


def test_voice_health_endpoint(client: TestClient) -> None:
    """Test voice health endpoint."""
    response = client.get("/api/voice/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_tts_endpoint(client: TestClient) -> None:
    """Test TTS endpoint."""
    response = client.post(
        "/api/voice/tts",
        json={"text": "Hello World", "voice": "default"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 0
