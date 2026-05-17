# Run F2 Builder TTS Smoke Report

Date: 2026-05-17

## Result

The live Soulmatch Builder TTS endpoint is reachable and returns WAV audio.

Endpoint:

```text
POST https://soulmatch-1.onrender.com/api/goat/tts
```

Verified:

- `/api/goat/tts` without token returns `401`.
- With the configured Builder token, TTS returns `status=ok`.
- Response metadata reports `voice=maya_de`, `language=de-DE`, and `mime_type=audio/wav`.

## Smoke Result

Stored metadata:

- `docs/run-f2-builder-tts-smoke-2026-05-17.json`

Observed values:

- `http_status = 200`
- `status = ok`
- `provider = builder_default`
- `voice = maya_de`
- `language = de-DE`
- `mime_type = audio/wav`
- `audio_file_size_bytes = 309690`
- `time_ms = 5350.0`

The returned WAV file was deleted after the smoke test and was not committed.

## Decision

Builder TTS is live. Run F can now proceed to the final microphone acceptance: microphone recording -> Builder STT -> Builder TTS -> local playback.
