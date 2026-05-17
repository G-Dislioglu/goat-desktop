from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from time import perf_counter


@dataclass(frozen=True)
class LiveTalkResult:
    provider: str
    mode: str
    transcript: str
    response_text: str
    time_ms: float
    audio_recorded: bool
    audio_played: bool

    def to_dict(self) -> dict:
        return asdict(self)


class LiveTalkSession:
    """Half-duplex LiveTalk shell.

    Run F code-ready deliberately supports a deterministic mock path only. Real
    STT/TTS providers must be measured before Run F can be marked completed.
    """

    def __init__(self) -> None:
        self.provider = os.environ.get("GOAT_LIVETALK_PROVIDER", "mock").strip().lower() or "mock"
        self.state = "idle"
        self.last_result: LiveTalkResult | None = None

    def run_once(self) -> LiveTalkResult:
        if self.provider != "mock":
            raise RuntimeError("real LiveTalk provider is not implemented yet")

        started = perf_counter()
        self.state = "listening"
        transcript = "zeig mir das Suchfeld"
        self.state = "thinking"
        response_text = "Ich zeige das Suchfeld nur nach Freigabe."
        self.state = "speaking"
        result = LiveTalkResult(
            provider="mock",
            mode="half_duplex",
            transcript=transcript,
            response_text=response_text,
            time_ms=round((perf_counter() - started) * 1000, 2),
            audio_recorded=False,
            audio_played=False,
        )
        self.last_result = result
        self.state = "idle"
        return result
