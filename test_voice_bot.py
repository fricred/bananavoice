#!/usr/bin/env python3
"""Test script for the voice bot functionality."""

import asyncio
import os
from bananavoice.services.voice.bot import run_bot


async def main():
    """Test the voice bot with a demo room."""
    # You need to provide these API keys
    daily_api_key = os.getenv("DAILY_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    cartesia_api_key = os.getenv("CARTESIA_API_KEY")  # Optional

    if not daily_api_key:
        print("Please set DAILY_API_KEY environment variable")
        return

    if not openai_api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Create a test room URL (you can also create via Daily dashboard)
    room_url = "https://your-domain.daily.co/your-test-room"

    print(f"Starting voice bot for room: {room_url}")
    print("Make sure the room exists and you have the correct URL")
    print("Press Ctrl+C to stop the bot")

    try:
        await run_bot(
            room_url=room_url,
            daily_api_key=daily_api_key,
            openai_api_key=openai_api_key,
            cartesia_api_key=cartesia_api_key,
        )
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
