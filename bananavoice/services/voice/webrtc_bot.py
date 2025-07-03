"""WebRTC Voice Agent using Pipecat for peer-to-peer communication."""

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.gemini_multimodal_live import GeminiMultimodalLiveLLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
from pipecat.transports.network.webrtc_connection import (
    IceServer,
    SmallWebRTCConnection,
)

logger = logging.getLogger(__name__)

# System instruction for the voice agent
SYSTEM_INSTRUCTION = """
You are BananaVoice, a friendly AI assistant specialized in voice interactions.

Your goal is to provide helpful, conversational responses while keeping them
brief and natural.

Your output will be converted to audio, so:
- Don't include special characters in your responses
- Keep responses concise (1-2 sentences maximum)
- Be conversational and engaging
- Ask follow-up questions to keep the conversation flowing

Respond naturally to what the user says and help them with their questions or tasks.
"""

# WebRTC configuration
ICE_SERVERS = [
    IceServer(urls="stun:stun.l.google.com:19302"),
]


class WebRTCVoiceAgent:
    """WebRTC Voice Agent for real-time voice communication."""

    def __init__(
        self,
        google_api_key: str,
        voice_id: str = "Puck",
        system_instruction: str = SYSTEM_INSTRUCTION,
    ) -> None:
        """Initialize the WebRTC Voice Agent."""
        self.google_api_key = google_api_key
        self.voice_id = voice_id
        self.system_instruction = system_instruction
        self.connections: Dict[str, SmallWebRTCConnection] = {}
        self._tasks: Dict[str, asyncio.Task[Any]] = {}

    async def create_connection(self, sdp: str, sdp_type: str) -> Dict[str, str]:
        """Create a new WebRTC connection."""
        connection = SmallWebRTCConnection(ICE_SERVERS)
        await connection.initialize(sdp=sdp, type=sdp_type)

        # Set up connection cleanup
        @connection.event_handler("closed")
        async def handle_disconnected(webrtc_connection: SmallWebRTCConnection) -> None:
            logger.info(f"Discarding connection for pc_id: {webrtc_connection.pc_id}")
            self.connections.pop(webrtc_connection.pc_id, None)
            # Cancel and clean up the associated task
            if webrtc_connection.pc_id in self._tasks:
                task = self._tasks.pop(webrtc_connection.pc_id)
                if not task.done():
                    task.cancel()

        # Store connection first to get the ID
        answer = connection.get_answer()
        pc_id = answer["pc_id"]
        self.connections[pc_id] = connection

        # Start the voice agent for this connection
        task = asyncio.create_task(self._run_voice_agent(connection))
        self._tasks[pc_id] = task

        return answer

    async def renegotiate_connection(
        self,
        pc_id: str,
        sdp: str,
        sdp_type: str,
    ) -> Optional[Dict[str, str]]:
        """Renegotiate an existing WebRTC connection."""
        if pc_id not in self.connections:
            return None

        connection = self.connections[pc_id]
        await connection.renegotiate(sdp=sdp, type=sdp_type)
        return connection.get_answer()

    async def _run_voice_agent(self, webrtc_connection: SmallWebRTCConnection) -> None:
        """Run the voice agent pipeline for a WebRTC connection."""
        # Create the Pipecat transport
        transport = SmallWebRTCTransport(
            webrtc_connection=webrtc_connection,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                audio_out_10ms_chunks=2,
            ),
        )

        # Create the LLM service
        llm = GeminiMultimodalLiveLLMService(
            api_key=self.google_api_key,
            voice_id=self.voice_id,
            transcribe_user_audio=True,
            transcribe_model_audio=True,
            system_instruction=self.system_instruction,
        )

        # Create context
        context = OpenAILLMContext(
            [
                {
                    "role": "user",
                    "content": "Start by greeting the user warmly and "
                    "introducing yourself.",
                },
            ],
        )
        context_aggregator = llm.create_context_aggregator(context)

        # Build pipeline
        pipeline = Pipeline(
            [
                transport.input(),
                context_aggregator.user(),
                llm,
                transport.output(),
                context_aggregator.assistant(),
            ],
        )

        # Create pipeline task
        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )

        # Event handlers
        @transport.event_handler("on_client_connected")
        async def on_client_connected(
            transport: SmallWebRTCTransport,
            client: str,
        ) -> None:
            logger.info("Voice agent client connected")
            await task.queue_frames([context_aggregator.user().get_context_frame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(
            transport: SmallWebRTCTransport,
            client: str,
        ) -> None:
            logger.info("Voice agent client disconnected")
            await task.cancel()

        # Run the pipeline
        runner = PipelineRunner(handle_sigint=False)
        try:
            await runner.run(task)
        except Exception as e:
            logger.error(f"Voice agent pipeline error: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up all connections."""
        # Cancel all running tasks
        for task in self._tasks.values():
            if not task.done():
                task.cancel()

        # Disconnect all connections
        cleanup_tasks = []
        for connection in self.connections.values():
            cleanup_tasks.append(connection.disconnect())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        self.connections.clear()
        self._tasks.clear()


class WebRTCVoiceAgentManager:
    """Manager for WebRTC Voice Agent instances."""

    def __init__(self) -> None:
        """Initialize the manager."""
        self._agent: Optional[WebRTCVoiceAgent] = None

    def get_agent(self) -> WebRTCVoiceAgent:
        """Get or create the voice agent instance."""
        if self._agent is None:
            google_api_key = os.getenv("BANANAVOICE_GOOGLE_API_KEY") or os.getenv(
                "GOOGLE_API_KEY",
            )
            if not google_api_key:
                raise ValueError("Google API key is required for WebRTC Voice Agent")

            self._agent = WebRTCVoiceAgent(
                google_api_key=google_api_key,
                voice_id="Puck",  # Available: Aoede, Charon, Fenrir, Kore, Puck
                system_instruction=SYSTEM_INSTRUCTION,
            )

        return self._agent

    async def cleanup(self) -> None:
        """Clean up the voice agent."""
        if self._agent:
            await self._agent.cleanup()
            self._agent = None


# Global manager instance
_manager = WebRTCVoiceAgentManager()


def get_webrtc_voice_agent() -> WebRTCVoiceAgent:
    """Get the WebRTC Voice Agent instance."""
    return _manager.get_agent()


async def cleanup_webrtc_voice_agent() -> None:
    """Clean up the WebRTC Voice Agent."""
    await _manager.cleanup()
