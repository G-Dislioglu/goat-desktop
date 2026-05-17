# Run E Completion Report - 2026-05-17

Scope: real Builder-proxy Vision-Hint smoke test against `/api/goat/vision-hint`. Vision remains semantic-only; final coordinates are still owned by local geometry and the Broker.

## Evidence

- Builder URL present in environment: `true`.
- Builder token present in environment: `true` (value not logged).
- Input screenshot: `docs/screenshots/run-e-vision-input.png`.
- Providers tested: `gemini_flash_lite`, `gemini_flash`, `grok_4_3`.
- Reasoning level: `minimal`.

## Results

- `gemini_flash_lite`: status `ok`, label `Manual Deploy button`, position `upper right quadrant`, confidence `0.95`, latency_ms `1617.0`, reasoning `minimal`.
- `gemini_flash`: status `ok`, label `Manual Deploy button`, position `upper right center`, confidence `0.9`, latency_ms `1580.0`, reasoning `minimal`.
- `grok_4_3`: status `ok`, label `Manual Deploy button`, position `top-right area of the main content panel`, confidence `0.85`, latency_ms `1300.0`, reasoning `none`.

## Decision

Run E decision: `completed`. Completed requires all three providers to return usable semantic hints through the Builder proxy without exposing or using pixel coordinates as authority.

## Raw Evidence

```json
{
  "decision": "completed",
  "builder_url_present": true,
  "builder_token_present": true,
  "input_screenshot": "docs/screenshots/run-e-vision-input.png",
  "providers_tested": [
    "gemini_flash_lite",
    "gemini_flash",
    "grok_4_3"
  ],
  "reasoning_level": "minimal",
  "results": [
    {
      "provider": "gemini_flash_lite",
      "label": "Manual Deploy button",
      "rough_position": "upper right quadrant",
      "confidence": 0.95,
      "time_ms": 1617.0,
      "raw_evidence": {
        "mode": "builder_proxy",
        "provider": "gemini_flash_lite",
        "reasoning_level": "minimal",
        "http_status": 200,
        "authority": "semantic_hint_only"
      },
      "status": "ok",
      "reasoning_level": "minimal",
      "http_status": 200,
      "error": null,
      "source": "gemini_flash_lite",
      "semantic_label": "Manual Deploy button",
      "approximate_position": "upper right quadrant",
      "latency_ms": 1617.0,
      "reasoning_level_used": "minimal"
    },
    {
      "provider": "gemini_flash",
      "label": "Manual Deploy button",
      "rough_position": "upper right center",
      "confidence": 0.9,
      "time_ms": 1580.0,
      "raw_evidence": {
        "mode": "builder_proxy",
        "provider": "gemini_flash",
        "reasoning_level": "minimal",
        "http_status": 200,
        "authority": "semantic_hint_only"
      },
      "status": "ok",
      "reasoning_level": "minimal",
      "http_status": 200,
      "error": null,
      "source": "gemini_flash",
      "semantic_label": "Manual Deploy button",
      "approximate_position": "upper right center",
      "latency_ms": 1580.0,
      "reasoning_level_used": "minimal"
    },
    {
      "provider": "grok_4_3",
      "label": "Manual Deploy button",
      "rough_position": "top-right area of the main content panel",
      "confidence": 0.85,
      "time_ms": 1300.0,
      "raw_evidence": {
        "mode": "builder_proxy",
        "provider": "grok_4_3",
        "reasoning_level": "minimal",
        "http_status": 200,
        "authority": "semantic_hint_only"
      },
      "status": "ok",
      "reasoning_level": "none",
      "http_status": 200,
      "error": null,
      "source": "grok_4_3",
      "semantic_label": "Manual Deploy button",
      "approximate_position": "top-right area of the main content panel",
      "latency_ms": 1300.0,
      "reasoning_level_used": "none"
    }
  ]
}
```
