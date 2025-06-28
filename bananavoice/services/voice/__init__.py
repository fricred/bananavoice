"""Voice service module."""

from bananavoice.services.voice.dependencies import get_voice_service
from bananavoice.services.voice.service import VoiceService

__all__ = ["VoiceService", "get_voice_service"]
