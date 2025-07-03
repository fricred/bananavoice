"""Standalone voice bot using Pipecat for real-time voice communication."""

import asyncio
import logging
import os
from typing import Optional

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.transports.services.daily import DailyParams, DailyTransport

# Optional imports
try:
    from pipecat.services.cartesia.tts import CartesiaTTSService
except (ImportError, Exception):
    CartesiaTTSService = None

logger = logging.getLogger(__name__)


class VoiceBot:
    """Voice bot that handles real-time conversation using Pipecat."""

    def __init__(
        self,
        room_url: str,
        token: str,
        daily_api_key: str,
        openai_api_key: str,
        cartesia_api_key: Optional[str] = None,
    ) -> None:
        """Initialize the voice bot."""
        self.room_url = room_url
        self.token = token
        self.daily_api_key = daily_api_key
        self.openai_api_key = openai_api_key
        self.cartesia_api_key = cartesia_api_key
        self.pipeline: Optional[Pipeline] = None
        self.runner: Optional[PipelineRunner] = None
        self.task: Optional[PipelineTask] = None
        self.transport: Optional[DailyTransport] = None

    async def setup_pipeline(self) -> None:
        """Set up the Pipecat pipeline for voice processing."""
        # Daily transport for WebRTC (following the instant-voice example)
        self.transport = DailyTransport(
            self.room_url,
            self.token,
            "BananaVoice Bot",
            DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
        )

        # STT service - Using GPT-4o Mini for 50% cost reduction ($0.003/min vs $0.006/min)
        stt = OpenAISTTService(
            api_key=self.openai_api_key,
            model="gpt-4o-mini-transcribe",
        )

        # LLM service - Using GPT-4.1 mini for optimal balance of cost and performance
        llm = OpenAILLMService(
            api_key=self.openai_api_key,
            model="gpt-4.1-mini-2025-04-14",
        )

        # TTS service - using OpenAI TTS for reliability
        from pipecat.services.openai.tts import OpenAITTSService

        tts = OpenAITTSService(
            api_key=self.openai_api_key,
            voice="nova",
        )

        # TODO: Add Cartesia support once voice ID is configured properly
        # if self.cartesia_api_key and CartesiaTTSService is not None:
        #     tts = CartesiaTTSService(
        #         api_key=self.cartesia_api_key,
        #         voice_id="a0e99841-438c-4a64-b679-ae501e7d6091",  # Sonic
        #     )

        # Context management (following instant-voice example)
        context = OpenAILLMContext()
        context_aggregator = llm.create_context_aggregator(context)

        # Build the pipeline with STT
        self.pipeline = Pipeline(
            [
                self.transport.input(),  # Audio input from Daily
                stt,  # Speech-to-Text
                context_aggregator.user(),  # User context aggregation
                llm,  # LLM processing
                tts,  # Text-to-Speech
                self.transport.output(),  # Audio output to Daily
                context_aggregator.assistant(),  # Assistant context aggregation
            ],
        )

        # Set up event handlers
        @self.transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant) -> None:
            logger.info(f"First participant joined: {participant['id']}")
            # Send initial context to start conversation
            initial_messages = [
                {
                    "role": "system",
                    "content": "You are BananaVoice, a friendly AI assistant. Keep responses brief and conversational.",
                },
                {
                    "role": "assistant",
                    "content": "Hello! I'm BananaVoice, your AI assistant. How can I help you today?",
                },
            ]
            context.set_messages(initial_messages)
            await self.task.queue_frames(
                [context_aggregator.user().get_context_frame()],
            )

        @self.transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason) -> None:
            logger.info(f"Participant left: {participant}")
            if self.task:
                await self.task.cancel()

    async def run(self) -> None:
        """Run the voice bot pipeline."""
        if not self.pipeline:
            await self.setup_pipeline()

        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized")

        self.task = PipelineTask(
            self.pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )

        self.runner = PipelineRunner(handle_sigint=False)
        await self.runner.run(self.task)

    async def stop(self) -> None:
        """Stop the voice bot."""
        if self.runner:
            # await self.runner.stop()  # API may vary
            pass


async def run_bot(
    room_url: str,
    token: str = "",
    daily_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    cartesia_api_key: Optional[str] = None,
) -> None:
    """Run the voice bot with the given configuration."""
    # Get API keys from environment if not provided (BananaVoice format)
    daily_key = (
        daily_api_key
        or os.getenv("BANANAVOICE_DAILY_API_KEY")
        or os.getenv("DAILY_API_KEY")
    )
    openai_key = (
        openai_api_key
        or os.getenv("BANANAVOICE_OPENAI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    cartesia_key = (
        cartesia_api_key
        or os.getenv("BANANAVOICE_CARTESIA_API_KEY")
        or os.getenv("CARTESIA_API_KEY")
    )

    if not daily_key:
        raise ValueError("Daily API key is required")
    if not openai_key:
        raise ValueError("OpenAI API key is required")

    bot = VoiceBot(
        room_url=room_url,
        token=token,
        daily_api_key=daily_key,
        openai_api_key=openai_key,
        cartesia_api_key=cartesia_key,
    )

    try:
        logger.info(f"Starting voice bot for room: {room_url}")
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise
    finally:
        await bot.stop()
        logger.info("Bot stopped")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        msg = "Usage: python bot.py <room_url> [token]"
        logger.error(msg)
        sys.exit(1)

    room_url = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 else ""

    asyncio.run(run_bot(room_url, token))
