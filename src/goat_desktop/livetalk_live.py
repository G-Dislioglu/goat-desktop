from __future__ import annotations

import base64
import json
import os
import socket
import wave
import winreg
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse, urlunparse


@dataclass(frozen=True)
class GeminiLiveConfig:
    builder_url: str | None
    builder_token: str | None
    timeout_seconds: float
    model: str
    voice: str
    instructions: str


@dataclass(frozen=True)
class GeminiLiveResult:
    status: str
    transcript: str
    response_text: str
    audio_path: str | None
    time_ms: float
    raw_evidence: dict
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def load_gemini_live_config() -> GeminiLiveConfig:
    timeout = float(_get_env("GOAT_VOICE_TIMEOUT_SECONDS", "20.0") or "20.0")
    return GeminiLiveConfig(
        builder_url=_get_env("GOAT_BUILDER_URL"),
        builder_token=_get_env("GOAT_BUILDER_TOKEN"),
        timeout_seconds=max(1.0, timeout),
        model=_get_env("GOAT_VOICE_MODEL", "gemini-3.1-flash-live-preview") or "gemini-3.1-flash-live-preview",
        voice=_get_env("GOAT_VOICE_VOICE", "Kore") or "Kore",
        instructions=_get_env(
            "GOAT_VOICE_INSTRUCTIONS",
            "Du bist Maya im GOAT Desktop. Antworte kurz, hilfreich und deutsch. Fuehre keine Desktop-Aktionen aus.",
        )
        or "Du bist Maya im GOAT Desktop. Antworte kurz, hilfreich und deutsch. Fuehre keine Desktop-Aktionen aus.",
    )


def request_gemini_live_turn(
    audio_path: Path,
    output_path: Path,
    config: GeminiLiveConfig | None = None,
) -> GeminiLiveResult:
    active_config = config or load_gemini_live_config()
    started = perf_counter()
    if not active_config.builder_url or not active_config.builder_token:
        return _uncertain_result("GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required", active_config, started)
    if not audio_path.exists() or audio_path.stat().st_size <= 44:
        return _uncertain_result("audio file is empty", active_config, started)

    uri = build_goat_voice_ws_url(active_config.builder_url)
    headers = {"Authorization": f"Bearer {active_config.builder_token}"}
    output_audio_chunks: list[bytes] = []
    transcript_parts: list[str] = []
    response_text_parts: list[str] = []
    message_count = 0

    try:
        import websockets.sync.client

        with _temporary_resolve_override(active_config.builder_url):
            with websockets.sync.client.connect(
                uri,
                additional_headers=headers,
                open_timeout=min(8.0, active_config.timeout_seconds),
                close_timeout=2.0,
            ) as websocket:
                websocket.send(
                    json.dumps(
                        {
                            "type": "session.update",
                            "session": {
                                "model": active_config.model,
                                "voice": active_config.voice,
                                "instructions": active_config.instructions,
                            },
                        }
                    )
                )
                for chunk in iter_wav_pcm_chunks(audio_path):
                    websocket.send(chunk)
                websocket.send(json.dumps({"type": "audio.end"}))

                while (perf_counter() - started) < active_config.timeout_seconds:
                    try:
                        raw_message = websocket.recv(timeout=0.75)
                    except TimeoutError:
                        if output_audio_chunks or response_text_parts:
                            break
                        continue
                    message_count += 1
                    if isinstance(raw_message, bytes):
                        output_audio_chunks.append(raw_message)
                        continue
                    parsed = _parse_json_object(raw_message)
                    if parsed is None:
                        continue
                    input_text = _nested_text(parsed, ["serverContent", "inputTranscription", "text"])
                    output_text = _nested_text(parsed, ["serverContent", "outputTranscription", "text"])
                    if input_text:
                        transcript_parts.append(input_text)
                    if output_text:
                        response_text_parts.append(output_text)
                    for audio_bytes in _extract_inline_audio(parsed):
                        output_audio_chunks.append(audio_bytes)
                    if _nested_bool(parsed, ["serverContent", "turnComplete"]):
                        break
    except Exception as exc:  # noqa: BLE001 - fail closed into explicit Live result
        return _uncertain_result(type(exc).__name__, active_config, started)

    final_audio_path: str | None = None
    if output_audio_chunks:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_pcm_wav(output_path, b"".join(output_audio_chunks))
        final_audio_path = str(output_path)

    return GeminiLiveResult(
        status="ok" if final_audio_path or response_text_parts else "uncertain",
        transcript=" ".join(part.strip() for part in transcript_parts if part.strip()).strip(),
        response_text=" ".join(part.strip() for part in response_text_parts if part.strip()).strip()
        or ("Gemini Live hat Audio geliefert." if final_audio_path else "Gemini Live hat keine Antwort geliefert."),
        audio_path=final_audio_path,
        time_ms=round((perf_counter() - started) * 1000, 2),
        error=None if final_audio_path or response_text_parts else "empty live response",
        raw_evidence={
            "mode": "gemini_live",
            "model": active_config.model,
            "voice": active_config.voice,
            "messages": message_count,
            "audio_chunks": len(output_audio_chunks),
        },
    )


def build_goat_voice_ws_url(builder_url: str) -> str:
    parsed = urlparse(builder_url.rstrip("/"))
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse((scheme, parsed.netloc, "/api/goat/voice", "", "", ""))


def iter_wav_pcm_chunks(audio_path: Path, chunk_frames: int = 2048):
    with wave.open(str(audio_path), "rb") as wav:
        while True:
            data = wav.readframes(chunk_frames)
            if not data:
                break
            yield data


def write_pcm_wav(output_path: Path, pcm_data: bytes, sample_rate: int | None = None) -> None:
    rate = int(_get_env("GOAT_VOICE_OUTPUT_SAMPLE_RATE", str(sample_rate or 24000)) or str(sample_rate or 24000))
    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm_data)


def _parse_json_object(raw: str) -> dict | None:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _nested_text(root: dict, path: list[str]) -> str:
    value = root
    for key in path:
        if not isinstance(value, dict):
            return ""
        value = value.get(key)
    return value.strip() if isinstance(value, str) else ""


def _nested_bool(root: dict, path: list[str]) -> bool:
    value = root
    for key in path:
        if not isinstance(value, dict):
            return False
        value = value.get(key)
    return bool(value)


def _extract_inline_audio(root: dict) -> list[bytes]:
    chunks: list[bytes] = []

    def visit(value) -> None:
        if isinstance(value, dict):
            inline = value.get("inlineData")
            if isinstance(inline, dict):
                data = inline.get("data")
                mime_type = str(inline.get("mimeType") or "")
                if isinstance(data, str) and mime_type.startswith("audio/"):
                    try:
                        chunks.append(base64.b64decode(data))
                    except Exception:
                        pass
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(root)
    return chunks


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _value_type = winreg.QueryValueEx(key, name)
    except OSError:
        return default
    return str(value) if value else default


def _uncertain_result(
    error: str,
    config: GeminiLiveConfig,
    started: float,
    http_status: int | None = None,
) -> GeminiLiveResult:
    return GeminiLiveResult(
        status="uncertain",
        transcript="",
        response_text=error,
        audio_path=None,
        time_ms=round((perf_counter() - started) * 1000, 2),
        error=error,
        raw_evidence={
            "error": error,
            "http_status": http_status,
            "mode": "gemini_live",
            "model": config.model,
        },
    )


@contextmanager
def _temporary_resolve_override(url: str | None):
    override_ip = _get_env("GOAT_BUILDER_RESOLVE_IP")
    if not url or not override_ip:
        yield
        return

    hostname = urlparse(url).hostname
    if not hostname or hostname in {"127.0.0.1", "localhost", "::1"}:
        yield
        return

    original_getaddrinfo = socket.getaddrinfo

    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == hostname:
            return original_getaddrinfo(override_ip, port, family, type, proto, flags)
        return original_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = patched_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = original_getaddrinfo
