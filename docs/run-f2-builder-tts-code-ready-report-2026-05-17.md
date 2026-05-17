# Run F2 Builder TTS Code-Ready Report

Date: 2026-05-17

## Result

Desktop-side Builder TTS support is code-ready.

Run F is still not completed because the real Builder TTS endpoint is not live yet.

Live check:

- `POST /api/goat/tts` currently returns `404`

## Endpoint Contract

Expected Builder endpoint:

```text
POST /api/goat/tts
Authorization: Bearer <goat-token>
Content-Type: application/json
```

Input:

```json
{
  "text": "Gehoert: zeige das suchfeld. Ich handle nur nach Freigabe.",
  "provider": "builder_default",
  "voice": "maya_de",
  "language": "de-DE",
  "format": "wav",
  "pronunciation_hints": {
    "GOAT": "Goat",
    "Maya": "Maya"
  }
}
```

Output:

```json
{
  "source": "builder_default",
  "voice_used": "maya_de",
  "language_used": "de-DE",
  "mime_type": "audio/wav",
  "audio_base64": "...",
  "latency_ms": 1200
}
```

## Implementation

- `src/goat_desktop/tts_hint.py`
  - `GOAT_TTS_MODE=builder_proxy`
  - `GOAT_TTS_PROVIDER=builder_default`
  - `GOAT_TTS_VOICE=maya_de`
  - `GOAT_TTS_LANGUAGE=de-DE`
  - `GOAT_TTS_TIMEOUT_SECONDS`
  - `GOAT_BUILDER_URL`
  - `GOAT_BUILDER_TOKEN`
  - optional `GOAT_BUILDER_RESOLVE_IP`
- `src/goat_desktop/livetalk.py`
  - calls Builder STT after local WAV recording
  - calls Builder TTS for the response
  - plays returned WAV locally
  - falls back to Windows SAPI only if Builder TTS is unavailable
  - marks `completion_ready=true` only when real STT and Builder TTS both succeed

## Verification

Commands:

```powershell
python -m compileall src tests
python -m pytest tests/test_tts_builder_proxy.py tests/test_stt_builder_proxy.py tests/test_livetalk_windows_provider.py -q
```

Result:

```text
13 passed
```

## Safety Notes

- Builder errors, timeout, invalid token, missing audio, and empty audio return `uncertain`.
- No generated audio file is committed.
- Windows SAPI is now a fallback only. It is not acceptance-quality Maya voice.

## Next Gate

Run F can be completed only after Soulmatch exposes `/api/goat/tts` and a real desktop microphone run returns:

- `audio_recorded=true`
- `stt_provider != manual`
- `tts_provider != windows_sapi`
- `audio_played=true`
- `completion_ready=true`
