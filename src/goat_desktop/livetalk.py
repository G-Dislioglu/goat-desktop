from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from ctypes import create_unicode_buffer, windll
from dataclasses import asdict, dataclass
from pathlib import Path
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
    stt_provider: str = "none"
    tts_provider: str = "none"
    audio_path: str | None = None
    completion_ready: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class LiveTalkSession:
    """Half-duplex LiveTalk shell.

    The mock path is deterministic. The Windows SAPI path can record audio and
    play speech locally, but still needs a real STT provider before Run F can be
    marked completed.
    """

    def __init__(self) -> None:
        self.provider = os.environ.get("GOAT_LIVETALK_PROVIDER", "mock").strip().lower() or "mock"
        self.audio_dir = Path(os.environ.get("GOAT_LIVETALK_AUDIO_DIR", Path.home() / "AppData" / "Roaming" / "GoatDesktop"))
        self.state = "idle"
        self.last_result: LiveTalkResult | None = None

    def run_once(self) -> LiveTalkResult:
        started = perf_counter()
        if self.provider == "windows_sapi":
            result = self._run_windows_sapi(started)
            self.last_result = result
            self.state = "idle"
            return result

        if self.provider != "mock":
            raise RuntimeError(f"unsupported LiveTalk provider: {self.provider}")

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
            stt_provider="mock",
            tts_provider="mock",
            completion_ready=False,
        )
        self.last_result = result
        self.state = "idle"
        return result

    def _run_windows_sapi(self, started: float) -> LiveTalkResult:
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = self.audio_dir / "livetalk-last-recording.wav"
        record_seconds = float(os.environ.get("GOAT_LIVETALK_RECORD_SECONDS", "1.0"))
        manual_transcript = os.environ.get("GOAT_LIVETALK_MANUAL_TRANSCRIPT", "").strip()

        self.state = "listening"
        audio_recorded = record_windows_wav(audio_path, record_seconds)
        self.state = "thinking"
        transcript = manual_transcript
        if transcript:
            response_text = f"Gehoert: {transcript}. Ich handle nur nach Freigabe."
        else:
            response_text = "Audio wurde aufgenommen. STT ist noch nicht konfiguriert."
        self.state = "speaking"
        audio_played = speak_windows_sapi(response_text)
        return LiveTalkResult(
            provider="windows_sapi",
            mode="half_duplex",
            transcript=transcript,
            response_text=response_text,
            time_ms=round((perf_counter() - started) * 1000, 2),
            audio_recorded=audio_recorded,
            audio_played=audio_played,
            stt_provider="manual" if transcript else "none",
            tts_provider="windows_sapi",
            audio_path=str(audio_path),
            completion_ready=False,
        )


def record_windows_wav(output_path: Path, seconds: float = 1.0) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    temp_path = Path(tempfile.gettempdir()) / "goatlt.wav"
    if temp_path.exists():
        temp_path.unlink()
    _mci("open new type waveaudio alias goat_livetalk")
    try:
        _mci("record goat_livetalk")
        time.sleep(max(0.1, seconds))
        _mci("stop goat_livetalk")
        _mci(f'save goat_livetalk "{temp_path}"')
    finally:
        _mci("close goat_livetalk", raise_on_error=False)
    if temp_path.exists():
        shutil.copyfile(temp_path, output_path)
    return output_path.exists() and output_path.stat().st_size > 44


def speak_windows_sapi(text: str) -> bool:
    escaped = text.replace("'", "''")
    command = (
        "$voice = New-Object -ComObject SAPI.SpVoice; "
        f"$null = $voice.Speak('{escaped}', 0)"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return completed.returncode == 0


def _mci(command: str, raise_on_error: bool = True) -> str:
    error = windll.winmm.mciSendStringW(command, None, 0, None)
    if error == 0:
        return ""
    buffer = create_unicode_buffer(256)
    windll.winmm.mciGetErrorStringW(error, buffer, len(buffer))
    message = buffer.value or f"MCI error {error}"
    if raise_on_error:
        raise RuntimeError(message)
    return message
