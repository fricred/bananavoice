"""Cost monitoring utility for BananaVoice voice services."""

import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CostBreakdown:
    """Cost breakdown for voice services."""

    daily_audio: float = 0.00099  # Daily.co audio-only per minute
    stt_cost: float = 0.003  # GPT-4o Mini STT per minute
    llm_cost: float = (
        0.0005  # GPT-4.1 mini ($0.40/$1.60 per 1M tokens - 83% cheaper than GPT-4o)
    )
    tts_cost: float = 0.012  # OpenAI TTS per minute (estimated)

    @property
    def total_per_minute(self) -> float:
        """Calculate total cost per minute."""
        return self.daily_audio + self.stt_cost + self.llm_cost + self.tts_cost

    @property
    def total_per_hour(self) -> float:
        """Calculate total cost per hour."""
        return self.total_per_minute * 60

    def format_breakdown(self) -> str:
        """Format cost breakdown as string."""
        return f"""
🍌 BananaVoice Cost Breakdown (2025) - PREMIUM OPTIMIZED
=====================================
Daily.co (audio):      ${self.daily_audio:.5f}/min
GPT-4o Mini STT:        ${self.stt_cost:.5f}/min  (50% savings vs Whisper)
GPT-4.1 Mini LLM:       ${self.llm_cost:.5f}/min  (83% cheaper than GPT-4o!)
OpenAI TTS:             ${self.tts_cost:.5f}/min
=====================================
TOTAL:                  ${self.total_per_minute:.5f}/min
TOTAL:                  ${self.total_per_hour:.3f}/hour
"""


class CostTracker:
    """Track costs during voice conversations."""

    def __init__(self) -> None:
        self.costs = CostBreakdown()
        self.start_time: Optional[float] = None
        self.participants: int = 0

    def start_session(self, participants: int = 1) -> None:
        """Start tracking a voice session."""
        self.start_time = time.time()
        self.participants = participants

    def get_current_cost(self) -> Dict[str, float]:
        """Get current accumulated cost."""
        if not self.start_time:
            return {"error": "No active session"}

        elapsed_minutes = (time.time() - self.start_time) / 60
        total_cost = self.costs.total_per_minute * elapsed_minutes * self.participants

        return {
            "elapsed_minutes": elapsed_minutes,
            "participants": self.participants,
            "cost_per_minute": self.costs.total_per_minute,
            "total_cost": total_cost,
            "daily_savings_vs_old_model": (0.006 - 0.003)
            * elapsed_minutes
            * self.participants,
        }

    def print_current_cost(self) -> None:
        """Print current cost status."""
        cost_data = self.get_current_cost()
        if "error" in cost_data:
            return


    def stop_session(self) -> None:
        """Stop tracking and show final cost."""
        if not self.start_time:
            return

        self.get_current_cost()
        self.start_time = None


# Utility function for quick cost calculation
def calculate_monthly_cost(
    daily_minutes: int, participants: int = 1,
) -> Dict[str, float]:
    """Calculate estimated monthly costs."""
    costs = CostBreakdown()
    daily_cost = costs.total_per_minute * daily_minutes * participants
    monthly_cost = daily_cost * 30

    # Old model cost (with Whisper)
    old_stt_cost = 0.006
    old_total_per_minute = (
        costs.daily_audio + old_stt_cost + costs.llm_cost + costs.tts_cost
    )
    old_monthly_cost = old_total_per_minute * daily_minutes * participants * 30

    return {
        "daily_minutes": daily_minutes,
        "participants": participants,
        "new_daily_cost": daily_cost,
        "new_monthly_cost": monthly_cost,
        "old_monthly_cost": old_monthly_cost,
        "monthly_savings": old_monthly_cost - monthly_cost,
        "savings_percentage": ((old_monthly_cost - monthly_cost) / old_monthly_cost)
        * 100,
    }


if __name__ == "__main__":
    # Example usage
    tracker = CostTracker()


    # Show current pricing
    costs = CostBreakdown()

    # Example calculation
    monthly_projection = calculate_monthly_cost(daily_minutes=60, participants=10)
