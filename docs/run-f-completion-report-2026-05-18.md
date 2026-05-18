# Run F Completion Report - 2026-05-18

## Ergebnis

Gemini Live ist der Default-LiveTalk-Pfad. Der alte kaskadierte Pfad ist nur noch ueber `GOAT_LIVETALK_FALLBACK=1` erreichbar.

Video-Frames sind implementiert, aber default aus:
- `GOAT_LIVETALK_VIDEO_FRAMES=0`: aus
- `GOAT_LIVETALK_VIDEO_FRAMES=1`: ca. 1 FPS
- `GOAT_LIVETALK_VIDEO_FRAMES=2`: ca. 0.5 FPS

Im LiveTalk-Popup gibt es den Schalter `Maya sieht Bildschirm`.

## Latenzmessung

Headless-Smoke mit 100ms PCM-Chunks ueber Gemini Live und Builder-Proxy.

| Modus | Runs | Median first_response_ms | Median total_ms |
|---|---:|---:|---:|
| ohne Video | 5 | 3970 | 6097 |
| mit Video | 5 | 5113 | 6996 |

Bewertung: Video ist funktionsfaehig, aber in der lokalen Messung nicht kostenlos. Deshalb bleibt Video default aus und wird bewusst zugeschaltet.

## Verifikation

- `python -m compileall src tests`
- `pytest tests/test_livetalk_gemini_live.py tests/test_livetalk_windows_provider.py -q`
- Headless Gemini-Live-Latenzsmoke 5x ohne Video, 5x mit Video

Keine Secrets dokumentiert.
