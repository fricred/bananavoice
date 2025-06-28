"""Voice service for basic TTS processing."""

import io
import wave

import numpy as np


class VoiceService:
    """Service for processing voice with basic TTS functionality."""

    def __init__(self) -> None:
        """Initialize the voice service."""

    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech using a basic TTS pipeline.

        :param text: Text to convert to speech.
        :return: Audio bytes in WAV format.
        """
        try:
            # Simple implementation: generate a sine wave based on text length
            sample_rate = 16000
            duration = max(1.0, len(text) * 0.1)  # Minimum 1 second
            samples = int(sample_rate * duration)

            # Generate simple sine wave
            frequency = 440  # A4 note
            t = np.linspace(0, duration, samples, False)
            audio_data = np.sin(2 * np.pi * frequency * t) * 0.3

            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)

            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())

            wav_buffer.seek(0)
            return wav_buffer.read()

        except Exception:
            # Fallback: return minimal WAV file
            return self._create_silence_wav(1.0)

    async def setup_basic_pipeline(self) -> None:
        """Set up a basic Pipecat pipeline for voice processing."""
        # This could be expanded to use actual Pipecat pipelines
        # For now, we use direct processing in the methods above

    async def process_audio(self, audio_data: bytes) -> str:
        """
        Process audio data and return transcribed text.

        :param audio_data: Raw audio bytes.
        :return: Transcribed text.
        """
        # Placeholder: In a real implementation, you'd use an STT service
        # For the POC, return a simple response based on audio size
        if len(audio_data) > 1000:
            return (
                f"Processed audio of {len(audio_data)} bytes - Hello from BananaVoice!"
            )
        return "Audio too short to process"

    def _create_silence_wav(self, duration: float) -> bytes:
        """Create a WAV file with silence."""
        sample_rate = 16000
        samples = int(sample_rate * duration)
        silence = np.zeros(samples, dtype=np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.read()

    async def cleanup(self) -> None:
        """Clean up resources."""
