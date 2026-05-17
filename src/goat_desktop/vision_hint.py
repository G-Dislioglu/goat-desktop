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
from urllib.parse import urlparse
from typing import Any


class VisionMode(StrEnum):
    DISABLED = "disabled"
    MOCK = "mock"
    OPENAI_COMPATIBLE = "openai_compatible"
    BUILDER_PROXY = "builder_proxy"


class VisionProvider(StrEnum):
    GEMINI_FLASH_LITE = "gemini_flash_lite"
    GROK_4_3 = "grok_4_3"
    GEMINI_FLASH = "gemini_flash"


class ReasoningLevel(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class VisionHintConfig:
    mode: VisionMode
    provider: VisionProvider
    reasoning_level: ReasoningLevel
    builder_url: str | None
    builder_token: str | None
    timeout_seconds: float


@dataclass(frozen=True)
class VisionHint:
    provider: str
    label: str
    rough_position: str
    confidence: float
    time_ms: float
    raw_evidence: dict[str, Any]
    status: str = "ok"
    reasoning_level: str = "minimal"
    http_status: int | None = None
    error: str | None = None

    @property
    def source(self) -> str:
        return self.provider

    @property
    def semantic_label(self) -> str:
        return self.label

    @property
    def approximate_position(self) -> str:
        return self.rough_position

    @property
    def latency_ms(self) -> float:
        return self.time_ms

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source"] = self.source
        data["semantic_label"] = self.semantic_label
        data["approximate_position"] = self.approximate_position
        data["latency_ms"] = self.latency_ms
        data["reasoning_level_used"] = self.reasoning_level
        return data


def load_vision_hint_config() -> VisionHintConfig:
    persisted = _load_persisted_user_choice()
    mode_value = os.environ.get("GOAT_VISION_MODE")
    legacy_provider_value = os.environ.get("GOAT_VISION_PROVIDER")
    if mode_value is None and legacy_provider_value in {mode.value for mode in VisionMode}:
        mode_value = legacy_provider_value
    mode = _parse_enum(VisionMode, mode_value, VisionMode.DISABLED)
    provider_value = os.environ.get("GOAT_VISION_PROVIDER") or persisted.get("provider")
    reasoning_value = os.environ.get("GOAT_VISION_REASONING") or persisted.get("reasoning_level")
    provider = _parse_enum(VisionProvider, provider_value, VisionProvider.GEMINI_FLASH_LITE)
    reasoning = _parse_enum(ReasoningLevel, reasoning_value, ReasoningLevel.MINIMAL)
    timeout = _timeout_for_reasoning(reasoning)
    timeout_override = os.environ.get("GOAT_VISION_TIMEOUT_SECONDS")
    if timeout_override:
        timeout = max(0.1, float(timeout_override))
    return VisionHintConfig(
        mode=mode,
        provider=provider,
        reasoning_level=reasoning,
        builder_url=os.environ.get("GOAT_BUILDER_URL"),
        builder_token=os.environ.get("GOAT_BUILDER_TOKEN"),
        timeout_seconds=timeout,
    )


def get_configured_provider() -> str:
    return load_vision_hint_config().provider.value


def get_vision_hint(
    image_path: Path,
    prompt: str,
    config: VisionHintConfig | None = None,
) -> VisionHint:
    active_config = config or load_vision_hint_config()
    if active_config.mode == VisionMode.MOCK:
        return _mock_hint(prompt, active_config)
    if active_config.mode == VisionMode.OPENAI_COMPATIBLE:
        return _openai_compatible_hint(image_path, prompt, active_config)
    if active_config.mode == VisionMode.BUILDER_PROXY:
        return _builder_proxy_hint(image_path, prompt, active_config)
    return _uncertain_hint(
        provider=active_config.provider.value,
        reasoning_level=active_config.reasoning_level.value,
        error="vision mode disabled",
        started=time.perf_counter(),
    )


def _parse_enum(enum_type, value: str | None, default):
    if value is None:
        return default
    try:
        return enum_type(value.strip().lower())
    except ValueError:
        return default


def _load_persisted_user_choice() -> dict[str, str]:
    try:
        from goat_desktop.vision_config import load_vision_config

        return load_vision_config()
    except Exception:
        return {"provider": VisionProvider.GEMINI_FLASH_LITE.value, "reasoning_level": ReasoningLevel.MINIMAL.value}


def _timeout_for_reasoning(reasoning: ReasoningLevel) -> float:
    if reasoning == ReasoningLevel.HIGH:
        return 8.0
    if reasoning == ReasoningLevel.MEDIUM:
        return 5.0
    if reasoning == ReasoningLevel.LOW:
        return 3.0
    return 2.0


def _mock_hint(prompt: str, config: VisionHintConfig) -> VisionHint:
    started = time.perf_counter()
    return VisionHint(
        provider=config.provider.value,
        label="primary action area",
        rough_position="center",
        confidence=0.65,
        time_ms=round((time.perf_counter() - started) * 1000, 2),
        reasoning_level=config.reasoning_level.value,
        raw_evidence={
            "prompt": prompt,
            "mode": "deterministic mock for wiring only",
            "authority": "semantic_hint_only",
        },
    )


def _builder_proxy_hint(image_path: Path, prompt: str, config: VisionHintConfig) -> VisionHint:
    started = time.perf_counter()
    if not config.builder_url or not config.builder_token:
        return _uncertain_hint(
            provider=config.provider.value,
            reasoning_level=config.reasoning_level.value,
            error="GOAT_BUILDER_URL and GOAT_BUILDER_TOKEN are required",
            started=started,
        )

    body = {
        "screenshot_base64": base64.b64encode(image_path.read_bytes()).decode("ascii"),
        "prompt": prompt,
        "provider": config.provider.value,
        "reasoning_level": config.reasoning_level.value,
        "max_tokens": 300,
    }
    request = urllib.request.Request(
        config.builder_url.rstrip("/") + "/api/goat/vision-hint",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.builder_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with _temporary_resolve_override(config.builder_url):
            response_context = urllib.request.urlopen(request, timeout=config.timeout_seconds)
        with response_context as response:
            payload = json.loads(response.read().decode("utf-8"))
            http_status = int(response.status)
    except urllib.error.HTTPError as exc:
        return _uncertain_hint(
            provider=config.provider.value,
            reasoning_level=config.reasoning_level.value,
            error=f"http_{exc.code}",
            started=started,
            http_status=exc.code,
        )
    except Exception as exc:  # noqa: BLE001 - fail closed into uncertain hint
        return _uncertain_hint(
            provider=config.provider.value,
            reasoning_level=config.reasoning_level.value,
            error=type(exc).__name__,
            started=started,
        )

    return VisionHint(
        provider=str(payload.get("source") or config.provider.value),
        label=str(payload.get("semantic_label") or ""),
        rough_position=str(payload.get("approximate_position") or ""),
        confidence=float(payload.get("confidence") or 0.0),
        time_ms=float(payload.get("latency_ms") or round((time.perf_counter() - started) * 1000, 2)),
        reasoning_level=str(payload.get("reasoning_level_used") or config.reasoning_level.value),
        http_status=http_status,
        raw_evidence={
            "mode": VisionMode.BUILDER_PROXY.value,
            "provider": config.provider.value,
            "reasoning_level": config.reasoning_level.value,
            "http_status": http_status,
            "authority": "semantic_hint_only",
        },
    )


def _openai_compatible_hint(image_path: Path, prompt: str, config: VisionHintConfig) -> VisionHint:
    api_key = os.environ.get("GOAT_VISION_API_KEY")
    base_url = os.environ.get("GOAT_VISION_BASE_URL")
    model = os.environ.get("GOAT_VISION_MODEL")
    started = time.perf_counter()
    if not api_key or not base_url or not model:
        return _uncertain_hint(
            provider=config.provider.value,
            reasoning_level=config.reasoning_level.value,
            error="GOAT_VISION_API_KEY, GOAT_VISION_BASE_URL, and GOAT_VISION_MODEL are required",
            started=started,
        )

    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            prompt
                            + "\nReturn compact JSON only with keys: label, rough_position, confidence. "
                            + "Do not return pixel coordinates."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encoded}"},
                    },
                ],
            }
        ],
        "temperature": 0,
    }
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
            http_status = int(response.status)
        parsed = json.loads(payload["choices"][0]["message"]["content"])
    except Exception as exc:  # noqa: BLE001 - fail closed into uncertain hint
        return _uncertain_hint(
            provider=config.provider.value,
            reasoning_level=config.reasoning_level.value,
            error=type(exc).__name__,
            started=started,
        )
    return VisionHint(
        provider=config.provider.value,
        label=str(parsed.get("label", "")),
        rough_position=str(parsed.get("rough_position", "")),
        confidence=float(parsed.get("confidence", 0.0)),
        time_ms=round((time.perf_counter() - started) * 1000, 2),
        reasoning_level=config.reasoning_level.value,
        http_status=http_status,
        raw_evidence={
            "model": model,
            "response_shape": list(parsed.keys()),
            "authority": "semantic_hint_only",
        },
    )


def _uncertain_hint(
    provider: str,
    reasoning_level: str,
    error: str,
    started: float,
    http_status: int | None = None,
) -> VisionHint:
    return VisionHint(
        provider=provider,
        label="",
        rough_position="",
        confidence=0.0,
        time_ms=round((time.perf_counter() - started) * 1000, 2),
        reasoning_level=reasoning_level,
        http_status=http_status,
        error=error,
        status="uncertain",
        raw_evidence={
            "error": error,
            "http_status": http_status,
            "authority": "semantic_hint_only",
            "fallback": "uncertain_hint",
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
