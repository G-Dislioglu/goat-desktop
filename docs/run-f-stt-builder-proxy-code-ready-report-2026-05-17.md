# Run F STT Builder Proxy Code-Ready Report

Date: 2026-05-17

## Result

Desktop-side STT Builder proxy support is code-ready.

Run F is still not completed because the real Builder STT endpoint has not been accepted from this desktop yet.

## Endpoint Contract

Expected Builder endpoint:

```text
POST /api/goat/stt
Authorization: Bearer <goat-token>
Content-Type: application/json
```

Input:

```json
{
  "audio_base64": "...",
  "mime_type": "audio/wav",
  "provider": "builder_default"
}
```

Output:

```json
{
  "source": "builder_default",
  "transcript": "zeige das suchfeld",
  "confidence": 0.91,
  "latency_ms": 456
}
```

## Implementation

- `src/goat_desktop/stt_hint.py`
  - `GOAT_STT_MODE=builder_proxy`
  - `GOAT_STT_PROVIDER=builder_default`
  - `GOAT_STT_TIMEOUT_SECONDS`
  - `GOAT_BUILDER_URL`
  - `GOAT_BUILDER_TOKEN`
  - optional `GOAT_BUILDER_RESOLVE_IP`
- `src/goat_desktop/livetalk.py`
  - records WAV locally
  - calls Builder STT
  - falls back to manual transcript only for local probe work
  - marks `completion_ready=true` only when real STT returns `status=ok`

## Verification

Commands:

```powershell
python -m compileall src tests
python -m pytest tests/test_livetalk_windows_provider.py tests/test_stt_builder_proxy.py tests/test_vision_hint_multi_provider.py -q
```

Result:

```text
17 passed
```

## Safety Notes

- Builder errors, timeout, invalid token, missing audio, and empty transcript return `uncertain`.
- No audio file is committed.
- Manual transcript is not accepted as real STT completion.

## Next Gate

Run F can be completed only after Soulmatch exposes `/api/goat/stt` and a real desktop probe returns:

- `audio_recorded=true`
- `audio_played=true`
- `stt_provider != manual`
- `completion_ready=true`
