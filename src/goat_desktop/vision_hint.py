from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VisionHint:
    provider: str
    label: str
    rough_position: str
    confidence: float
    time_ms: float
    raw_evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_configured_provider() -> str:
    return os.environ.get("GOAT_VISION_PROVIDER", "disabled").strip().lower() or "disabled"


def get_vision_hint(image_path: Path, prompt: str) -> VisionHint:
    provider = get_configured_provider()
    if provider == "mock":
        return _mock_hint(prompt)
    if provider == "openai_compatible":
        return _openai_compatible_hint(image_path, prompt)
    raise RuntimeError("no vision provider configured; set GOAT_VISION_PROVIDER=mock or openai_compatible")


def _mock_hint(prompt: str) -> VisionHint:
    started = time.perf_counter()
    return VisionHint(
        provider="mock",
        label="primary action area",
        rough_position="center",
        confidence=0.65,
        time_ms=round((time.perf_counter() - started) * 1000, 2),
        raw_evidence={
            "prompt": prompt,
            "mode": "deterministic mock for Run E wiring only",
            "authority": "semantic_hint_only",
        },
    )


def _openai_compatible_hint(image_path: Path, prompt: str) -> VisionHint:
    api_key = os.environ.get("GOAT_VISION_API_KEY")
    base_url = os.environ.get("GOAT_VISION_BASE_URL")
    model = os.environ.get("GOAT_VISION_MODEL")
    if not api_key or not base_url or not model:
        raise RuntimeError("GOAT_VISION_API_KEY, GOAT_VISION_BASE_URL, and GOAT_VISION_MODEL are required")

    started = time.perf_counter()
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
    with urllib.request.urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return VisionHint(
        provider="openai_compatible",
        label=str(parsed.get("label", "")),
        rough_position=str(parsed.get("rough_position", "")),
        confidence=float(parsed.get("confidence", 0.0)),
        time_ms=round((time.perf_counter() - started) * 1000, 2),
        raw_evidence={
            "model": model,
            "response_shape": list(parsed.keys()),
            "authority": "semantic_hint_only",
        },
    )
