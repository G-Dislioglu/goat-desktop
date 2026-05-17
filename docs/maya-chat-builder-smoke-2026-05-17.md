# Maya Chat Builder Smoke - 2026-05-17

## Scope

Verify that GOAT Desktop text chat can reach the live Soulmatch Builder endpoint:

- `POST /api/goat/chat`
- Auth via `GOAT_BUILDER_TOKEN`
- Optional `GOAT_BUILDER_RESOLVE_IP` used by the local desktop process when DNS resolution is unreliable.

## Repo / Live Evidence

- Soulmatch `origin/main`: `ff43b6d62e1160c48bdf49913f80179455b9562d`
- Commit title: `feat(goat): add builder chat proxy endpoint`
- Render `/api/health`: HTTP 200, commit `ff43b6d62e1160c48bdf49913f80179455b9562d`
- Desktop adapter: `src/goat_desktop/chat_hint.py`

## Live Endpoint Check

`/api/goat/chat` returned HTTP 200 for an authenticated smoke request:

```json
{
  "source": "builder_default",
  "provider": "builder_default",
  "response_text": "Hallo. Wie kann ich dir bei deinem Projekt helfen?",
  "reasoning_level_used": "minimal",
  "confidence": 0.75,
  "latency_ms": 528,
  "status": "ok"
}
```

## Desktop Adapter Smoke

Prompt: `hallo Maya. Antworte kurz auf Deutsch.`

| Provider | Status | HTTP | Latency | Reasoning | Response excerpt |
| --- | --- | ---: | ---: | --- | --- |
| `builder_default` | ok | 200 | 505 ms | minimal | Hallo. Ich bin bereit - womit kann ich dir am Desktop helfen? |
| `gemini_flash_lite` | ok | 200 | 454 ms | minimal | Hallo. Ich bin bereit - womit kann ich dir am Desktop helfen? |
| `gemini_flash` | ok | 200 | 909 ms | minimal | Hallo! Ich bin Maya. Wie kann ich dir heute bei deinem Desktop oder deinen Projekten helfen? |
| `grok_4_3` | ok | 200 | 814 ms | none | Hallo! Wie kann ich helfen? |

## Result

Maya text chat is now connected through Builder for normal desktop text input. This completes the first real text-KI binding for GOAT Desktop.

The endpoint is still advisory only. Desktop actions remain gated by the existing approval and coordinate-broker rules.

## Follow-Up

- Route spoken LiveTalk transcripts through the same chat endpoint before TTS.
- Keep action execution separate: chat may suggest, but it must not execute desktop actions.
- Move provider model names toward a provider-spec/env layer if they become operational defaults beyond this smoke stage.
