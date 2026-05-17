# Run F Windows Audio Probe Report

Date: 2026-05-17

## Result

Run F is improved, but still not completed.

Verified locally:

- Windows SAPI TTS is available.
- Windows MCI can record a short WAV from the default recording path.
- The `windows_sapi` LiveTalk provider can perform a half-duplex local audio loop.

Not verified:

- real STT
- provider transcript quality
- live microphone-to-intent path

## Evidence

- Probe JSON: `docs/run-f-windows-audio-probe-2026-05-17.json`
- Tests: `tests/test_livetalk_windows_provider.py`

Probe result:

- `audio_recorded = true`
- `audio_played = true`
- `stt_provider = manual`
- `tts_provider = windows_sapi`
- `completion_ready = false`

The recording file itself was not committed. Real microphone recordings may contain private ambient audio. The probe JSON records `audio_file_size_bytes` and `audio_artifact_committed = false`.

## Implementation

- `GOAT_LIVETALK_PROVIDER=windows_sapi`
- `GOAT_LIVETALK_RECORD_SECONDS`
- `GOAT_LIVETALK_MANUAL_TRANSCRIPT`
- local WAV recording via Windows MCI
- local speech playback via Windows SAPI

## Decision

Run F remains `code_ready`, not `completed`.

The next required step is a real STT provider path. Manual transcript is useful for local audio-loop testing, but it is not a real speech-to-text acceptance.
