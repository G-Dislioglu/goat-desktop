# Run F STT Builder Smoke Report

Date: 2026-05-17

## Result

The live Soulmatch Builder STT endpoint is reachable and returns a transcript.

Endpoint:

```text
POST https://soulmatch-1.onrender.com/api/goat/stt
```

Verified:

- `/api/goat/stt` without token returns `401`.
- With the configured Builder token, STT returns `status=ok`.
- Synthetic SAPI WAV input produced a transcript.

## Smoke Result

Stored metadata:

- `docs/run-f-stt-builder-smoke-2026-05-17.json`

Observed values:

- `http_status = 200`
- `status = ok`
- `provider = builder_default`
- `transcript = Sieh das Suchfeld`
- `confidence = 0.95`
- `time_ms = 2146.0`

The synthetic WAV file was deleted after the smoke test and was not committed.

## Decision

This proves the Builder STT path, but Run F is still not marked `completed`.

Reason: Run F completion requires a live microphone-to-STT-to-SAPI loop. This smoke used a synthetic SAPI WAV file to avoid committing or exposing private microphone audio.

## Next Acceptance

For full Run F completion, run a short live microphone test:

1. User says: `zeige das suchfeld`.
2. Desktop records a short WAV.
3. Desktop sends WAV to Builder STT.
4. Builder returns a transcript.
5. Desktop speaks a SAPI response.
6. No raw audio is committed; only metadata is committed.
