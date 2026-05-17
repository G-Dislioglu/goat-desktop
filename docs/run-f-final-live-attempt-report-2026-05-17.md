# Run F Final Live Attempt Report

Date: 2026-05-17

## Result

Final Run F live acceptance was attempted with the full target path:

```text
microphone -> Builder STT -> Builder TTS -> local WAV playback
```

The technical path worked, but the acceptance phrase was not recognized correctly.

Observed:

- `audio_recorded = true`
- `stt_provider = builder_default`
- `tts_provider = builder_default`
- `audio_played = true`
- `completion_ready = true`
- `transcript = So`
- `acceptance_passed = false`

Expected transcript:

```text
zeige das suchfeld
```

## Implementation Fix During Attempt

The first full-path attempt reached Builder TTS but failed during local WAV playback because Windows MCI rejected the long response-audio path. Playback was fixed by copying the returned WAV to a short temp path before MCI playback.

## Evidence

- Metadata: `docs/run-f-final-live-acceptance-2026-05-17.json`

No microphone WAV and no generated TTS WAV are committed.

## Decision

Do not set `run_f_completed`.

The final architecture path is connected and plays Builder-TTS audio, but the microphone/STT acceptance phrase still needs a clean recognition pass.
