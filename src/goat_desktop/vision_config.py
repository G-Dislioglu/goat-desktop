from __future__ import annotations

import json
import os
from pathlib import Path

from goat_desktop.vision_hint import ReasoningLevel, VisionProvider


DEFAULT_PROVIDER = VisionProvider.GEMINI_FLASH_LITE.value
DEFAULT_REASONING = ReasoningLevel.MINIMAL.value


def get_config_path() -> Path:
    explicit = os.environ.get("GOAT_VISION_CONFIG_PATH")
    if explicit:
        return Path(explicit)
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "GoatDesktop" / "vision_config.json"
    return Path.home() / "AppData" / "Roaming" / "GoatDesktop" / "vision_config.json"


def load_vision_config() -> dict[str, str]:
    path = get_config_path()
    if not path.exists():
        return {"provider": DEFAULT_PROVIDER, "reasoning_level": DEFAULT_REASONING}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"provider": DEFAULT_PROVIDER, "reasoning_level": DEFAULT_REASONING}
    provider = _valid_provider(payload.get("provider"))
    reasoning = _valid_reasoning(payload.get("reasoning_level"))
    return {"provider": provider, "reasoning_level": reasoning}


def save_vision_config(provider: str, level: str) -> dict[str, str]:
    payload = {
        "provider": _valid_provider(provider),
        "reasoning_level": _valid_reasoning(level),
    }
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _valid_provider(value: object) -> str:
    try:
        return VisionProvider(str(value)).value
    except ValueError:
        return DEFAULT_PROVIDER


def _valid_reasoning(value: object) -> str:
    normalized = "minimal" if value == "none" else str(value)
    try:
        return ReasoningLevel(normalized).value
    except ValueError:
        return DEFAULT_REASONING
