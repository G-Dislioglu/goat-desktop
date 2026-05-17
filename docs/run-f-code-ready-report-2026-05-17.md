# Run F Code-Ready Report - 2026-05-17

Scope: LiveTalk Half-Duplex shell with deterministic mock provider. This is not a real microphone/STT/TTS acceptance: no real voice provider is configured or measured.

## Evidence

- Popup `LiveTalk` button is enabled.
- Button triggers one half-duplex mock roundtrip.
- Mock transcript: `zeig mir das Suchfeld`.
- Mock spoken response is rendered in the Maya status field.
- No audio is recorded or played in this code-ready run.
- Screenshot: `docs/screenshots/run-f-livetalk-mock-2026-05-17.png`.

## Decision

Run F decision: `code_ready`, not `completed`. Completion still requires a real audio recording plus spoken response path using an explicitly chosen STT/TTS provider.

## Raw Evidence

```json
{
  "provider": "mock",
  "state_after_roundtrip": "idle",
  "last_result": {
    "provider": "mock",
    "mode": "half_duplex",
    "transcript": "zeig mir das Suchfeld",
    "response_text": "Ich zeige das Suchfeld nur nach Freigabe.",
    "time_ms": 0.01,
    "audio_recorded": false,
    "audio_played": false
  },
  "talk_button_enabled_after_roundtrip": true,
  "screen_context_text": "zeig mir das Suchfeld",
  "maya_text": "Ich zeige das Suchfeld nur nach Freigabe.",
  "screenshot": "docs\\screenshots\\run-f-livetalk-mock-2026-05-17.png"
}
```
