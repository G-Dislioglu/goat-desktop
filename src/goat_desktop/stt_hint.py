from __future__ import annotations

import base64
import json
import os
import socket
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class SttMode(StrEnum):
    DISABLED = "disabled"
    BUILDER_PROXY = "builder_proxy"


@dataclass(frozen=True)
class SttConfig:
    mode: SttMode
    builder_url: str | None
    builder_token: str | None
    provider: str
    timeout_seconds: float


@dataclass(frozen=True)
class SttResult:
    status: str
    transcript: str
    confidence: float
    provider: str
    time_ms: float
    raw_evidence: dict[str, Any]
    http_status: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_stt_config() -> SttConfig:
    mode = _parse_mode(os.environ.get("GOAT_STT_MODE"), SttMode.DISABLED)
    timeout = float(os.environ.get("GOAT_STT_TIMEOUT_SECONDS", "8.0"))
    return SttConfig(
        mode=mode,
        builder_url=os.environ.get("GOAT_BUILDER_URL"),
        builder_token=os.environ.get("GOAT_BUILDER_TOKEN"),
        provider=os.environ.get("GOAT_STT_PROVIDER", "builder_default"),
        timeout_seconds=max(0.5, timeout),
    )


def transcribe_audio(audio_path: Path, config: SttConfig | None = None) -> SttResult:
    active_config = config or load_stt_config()
    started = time.perf_counter()
    if active_config.mode != SttMode.BUILDER_PROXY:
        return _uncertain_result("STT mode disabled", active_config.provider, started)
    if not active_config.builder_url or not active_config.builder_token:
        return _uncertain_result("GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required", active_config.provider, started)
    if not audio_path.exists():
        return _uncertain_result("audio file does not exist", active_config.provider, started)

    body = {
        "audio_base64": base64.b64encode(audio_path.read_bytes()).decode("ascii"),
        "mime_type": "audio/wav",
        "provider": active_config.provider,
    }
    request = urllib.request.Request(
        active_config.builder_url.rstrip("/") + "/api/goat/stt",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {active_config.builder_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with _temporary_resolve_override(active_config.builder_url):
            response_context = urllib.request.urlopen(request, timeout=active_config.timeout_seconds)
        with response_context as response:
            payload = json.loads(response.read().decode("utf-8"))
            http_status = int(response.status)
    except urllib.error.HTTPError as exc:
        return _uncertain_result(f"http_{exc.code}", active_config.provider, started, http_status=exc.code)
    except Exception as exc:  # noqa: BLE001 - fail closed into uncertain STT
        return _uncertain_result(type(exc).__name__, active_config.provider, started)

    transcript = str(payload.get("transcript") or "").strip()
    if not transcript:
        return _uncertain_result("empty transcript", active_config.provider, started, http_status=http_status)

    return SttResult(
        status="ok",
        transcript=transcript,
        confidence=float(payload.get("confidence") or 0.0),
        provider=str(payload.get("source") or active_config.provider),
        time_ms=float(payload.get("latency_ms") or round((time.perf_counter() - started) * 1000, 2)),
        http_status=http_status,
        raw_evidence={
            "mode": SttMode.BUILDER_PROXY.value,
            "provider": active_config.provider,
            "http_status": http_status,
            "audio_bytes": audio_path.stat().st_size,
        },
    )


def _parse_mode(value: str | None, default: SttMode) -> SttMode:
    if value is None:
        return default
    try:
        return SttMode(value.strip().lower())
    except ValueError:
        return default


def _uncertain_result(
    error: str,
    provider: str,
    started: float,
    http_status: int | None = None,
) -> SttResult:
    return SttResult(
        status="uncertain",
        transcript="",
        confidence=0.0,
        provider=provider,
        time_ms=round((time.perf_counter() - started) * 1000, 2),
        http_status=http_status,
        error=error,
        raw_evidence={
            "error": error,
            "http_status": http_status,
            "fallback": "uncertain_stt",
        },
    )


@contextmanager
def _temporary_resolve_override(url: str | None):
    override_ip = os.environ.get("GOAT_BUILDER_RESOLVE_IP")
    if not url or not override_ip:
        yield
        return

    hostname = urlparse(url).hostname
    if not hostname:
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
