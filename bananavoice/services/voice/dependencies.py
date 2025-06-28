"""Voice service dependencies."""

from typing import Generator

from bananavoice.services.voice.service import VoiceService


def get_voice_service() -> Generator[VoiceService, None, None]:
    """
    Get voice service instance.

    This creates a new instance of the voice service for each request.
    In a production environment, you might want to implement connection pooling
    or singleton patterns for better performance.

    :yields: VoiceService instance.
    """
    service = VoiceService()
    try:
        yield service
    finally:
        # Cleanup if needed (currently no cleanup required)
        pass
