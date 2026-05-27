# STATE

last_verified_against_code: 2026-05-16

text_chat_auto_screen_context_2026_05_25:
"GOAT Desktop Textchat nutzt Bildschirmkontext jetzt automatisch fuer sichtbare Ziel-/Navigationsfragen wie `wo ist ...`, `siehst du ...`, `zeig mir ...` oder `navigier ...`. Der Hauptworkflow braucht dafuer keinen manuellen `Bildschirm pruefen`-Button: GOAT captured den sichtbaren Desktop in einem temporaeren Ordner, fragt Builder Vision nach kurzer semantischer Zusammenfassung, loescht den Screenshot automatisch und gibt den Kontext an Maya Chat weiter. Vision bleibt read-only; es werden keine Klicks, Tastatur- oder Desktop-Aktionen ausgefuehrt. Tests gruen: compileall, fokussiertes Screen/Chat/Vision-Subset und volle Suite mit 114 Tests."

text_chat_screen_context_fallback_2026_05_25:
"GOAT Desktop Textchat hat jetzt einen lokalen read-only Fallback fuer Bildschirmfragen, falls Builder-Chat inhaltlich `Maya-KI nicht erreichbar` meldet. Der Screen-/Vision-Kontext wird dann direkt als kurze Antwort genutzt; bei unsicherer Vision sagt GOAT klar, dass das Ziel nicht sicher sichtbar ist. Live-Smoke: visible_desktop capture ok, Temp-Screenshot geloescht, Vision gemini_flash_lite ok, Builder-Chat-Ausfall erkannt, finale Antwort lokal sinnvoll statt Builder-Fehler. Keine Desktop-Aktionen."

main_ux_screen_question_clarity_2026_05_25:
"Haupt-UX fuer Textchat-Screenfragen vereinfacht. Der manuelle Vision/Button-Pfad bleibt aus der sichtbaren Haupt-UI heraus; Screenfragen laufen ueber den normalen Textchat. Antworten sind jetzt klar als `Gesehen: ...` oder `Nicht sicher gesehen: ...` formuliert, und das Statusfeld zeigt kompakt `Bildschirm: Ziel gesehen` bzw. `Bildschirm: Ziel nicht sicher gesehen` statt roher Vision-Zusammenfassung. Live-Smoke: visible_desktop capture ok, Vision ok, Temp-Screenshot geloescht, finale Antwort `Nicht sicher gesehen: Ziel ist nicht klar erkennbar.` Full Suite gruen: 119 Tests."

text_chat_screen_marker_cue_2026_05_25:
"Textchat-Screenfragen koennen jetzt bei ausreichend sicherem Vision-Hinweis einen read-only Cue-Ball setzen. GOAT wandelt `rough_position` wie `oben links` oder `unten rechts` in eine grobe Bildschirmregion um und bewegt nur den Marker; keine Klicks, keine Tastatur, keine Desktop-Aktion. Unsichere Vision (`confidence=0`, `unknown`) setzt bewusst keinen Cue. Live-Smoke: aktueller Desktop capture ok, Vision unsicher -> marker=None; synthetischer read-only /screen-marker Smoke akzeptiert und effects bleiben alle false. Full Suite gruen: 121 Tests."

vision_prompt_target_fields_2026_05_25:
"Vision-Prompt und Builder-Proxy-Parser fuer Screenfragen geschaerft. GOAT fordert nun immer strukturierte Zielsignale `semantic_label`, `approximate_position`, `confidence` an und akzeptiert auch alternative Builder-Felder wie `label`/`rough_position`. Wenn Builder `target_visible=false` meldet, setzt GOAT confidence auf 0.0 und markiert nichts. Live-Smoke: Builder Vision HTTP 200, liefert `label=uncertain`, `rough_position=unknown`, `confidence=0.0`; GOAT setzt korrekt keinen Cue. Full Suite gruen: 123 Tests."

local_uia_screen_context_2026_05_25:
"Lokaler UIA-Sensor fuer Textchat-Screenfragen hinzugefuegt. GOAT liest sichtbare Windows-UIA-Elementnamen und Rechtecke read-only, matcht Zielbegriffe aus Fragen wie `Siehst du den StepStack Ordner...` und erzeugt bei Treffer direkt Kontext + Cue-Region mit Quelle `uia`. Keine Provider-Calls, keine Klicks, keine Tastatur, keine Desktop-Aktion. Wenn UIA keinen Treffer findet, bleibt Vision der Fallback. Live-Smoke: UIA ok, 80 Elemente gelesen, StepStack aktuell nicht sichtbar/gefunden -> kein Marker, effects alle false. Full Suite gruen: 127 Tests."

maya_chat_builder_proxy_code_ready_2026_05_17:
"Desktop-seitige Maya-Textchat-Anbindung vorbereitet am 2026-05-17. Implementiert: chat_hint.py mit GOAT_CHAT_MODE=builder_proxy, POST /api/goat/chat, Bearer-Auth, Reasoning-Parameter, optionalem GOAT_BUILDER_RESOLVE_IP und fail-closed uncertain bei Fehlern. Das LiveTalk-Textfeld nutzt jetzt diesen Adapter statt einer lokalen Fake-Antwort. Live-Pruefung gegen Soulmatch: /api/goat/stt, /api/goat/tts und /api/goat/vision-hint sind erreichbar; /api/goat/chat liefert aktuell 404. Deshalb ist Maya-Text-KI code_ready, aber nicht completed. Tests gruen: test_chat_builder_proxy.py plus LiveTalk/STT/TTS-Subset."

maya_chat_builder_proxy_completed_2026_05_17:
"Maya-Textchat-Anbindung abgeschlossen am 2026-05-17. Soulmatch/Builder ist auf Commit ff43b6d live und stellt POST /api/goat/chat bereit. Live-Endpoint-Check: /api/health HTTP 200 mit Commit ff43b6d, /api/goat/chat HTTP 200 mit response_text und status=ok. Desktop-Adapter-Smoke ueber chat_hint.py erfolgreich fuer builder_default (505ms), gemini_flash_lite (454ms), gemini_flash (909ms) und grok_4_3 (814ms, reasoning=none). Report: docs/maya-chat-builder-smoke-2026-05-17.md. Textchat ist damit KI-angebunden; Audio-LiveTalk nutzt die KI-Antwort noch nicht automatisch vor TTS."

livetalk_audio_routes_through_maya_chat_2026_05_17:
"LiveTalk-Audio wurde am 2026-05-17 an Maya-Textchat angeschlossen. Vorher wurde ein STT-Transcript lokal als 'Gehoert: ... Ich handle nur nach Freigabe.' wiederholt; das war keine freie KI-Antwort. Jetzt ruft der Windows-SAPI-LiveTalk-Pfad nach erfolgreicher STT-Erkennung request_chat_response() auf und spricht erst danach die Maya-Antwort per TTS. completion_ready verlangt nun STT ok + Chat ok + TTS ok. Tests gruen: LiveTalk/STT/TTS/Chat-Subset."

livetalk_latency_fast_path_2026_05_17:
"LiveTalk-Latenz-Fix am 2026-05-17: feste Aufnahmezeit von 5.0s auf 3.0s reduziert und Vorbereitungszeit von 1.0/0.8s auf 0.35s reduziert. LiveTalkResult protokolliert jetzt stt_time_ms, chat_time_ms, tts_time_ms und record_seconds; das Popup zeigt nach jeder Antwort den Breakdown in der Audio-Zeile. Ziel: sofort ca. 2.5s weniger Wartezeit und klare Sicht darauf, ob TTS der naechste Flaschenhals ist."

livetalk_tts_fallback_guard_2026_05_17:
"LiveTalk-TTS-Fallback am 2026-05-17 korrigiert. Problem im UI-Test: Wenn Builder-TTS lange hing oder fehlschlug, sprach GOAT spaet noch mit Windows-SAPI-Roboterstimme. Neu: Die Maya-Textantwort wird direkt nach dem Chat-Call im Popup angezeigt, bevor Audio fertig ist; Builder-TTS-Timeout default ist 8s statt 20s; Windows-SAPI-Fallback ist standardmaessig aus und nur mit GOAT_LIVETALK_ALLOW_SAPI_FALLBACK=1 aktiv. Dadurch kein spaetes Roboter-Nachsprechen nach Wegklicken."

livetalk_text_first_mode_2026_05_17:
"LiveTalk wurde am 2026-05-17 auf Text-first-Latenzmodus gestellt. Standard: Nach Aufnahme, STT und Maya-Chat wird die Antwort sofort angezeigt; Builder-TTS wird nicht mehr automatisch blockierend gestartet. GOAT_LIVETALK_AUTO_TTS=1 aktiviert den alten Auto-Audio-Pfad explizit. Ergebnis: gefuehlte Antwortzeit haengt nicht mehr an 3-8s TTS-Generierung oder spaetem Playback; die Audio-Zeile zeigt TTS=aus, wenn kein Audio angefordert wurde."

livetalk_audio_status_text_first_2026_05_17:
"Audio-Statusanzeige am 2026-05-17 korrigiert. Im Text-first-Standardmodus zeigte das Popup trotz deaktivierter Auto-Sprachausgabe weiter 'TTS Builder aktiv', weil nur die Builder-TTS-Konfiguration geprueft wurde. Neu: Wenn GOAT_LIVETALK_AUTO_TTS nicht aktiv ist, zeigt die UI 'STT Builder aktiv / Sprachausgabe aus'. Dadurch ist klar: Spracheingabe ist aktiv, Antwort kommt als Text, Vorlesen ist nicht automatisch eingeschaltet."

livetalk_read_aloud_button_2026_05_17:
"Optionales Vorlesen im LiveTalk-Modus am 2026-05-17 implementiert. Standard bleibt Text-first ohne Auto-TTS. Wenn eine Maya-Antwort vorhanden ist, erscheint im LiveTalk-Modus ein Button 'Vorlesen'. Klick startet Builder-TTS asynchron, zeigt waehrenddessen 'Lade Audio...' und spielt nur bei erfolgreichem Builder-WAV ab. Bei TTS-Fehlern erscheint eine sichtbare Fehlermeldung; Windows-SAPI-Fallback wird in diesem manuellen Vorlesen-Pfad nicht verwendet."

livetalk_gemini_live_provider_2026_05_18:
"GOAT Desktop hat jetzt einen `gemini_live` LiveTalk-Provider. Aktivierung: `GOAT_LIVETALK_PROVIDER=gemini_live`. Der Desktop nimmt lokal eine WAV auf, verbindet sich per WebSocket mit Builder `WSS /api/goat/voice`, sendet PCM-Audio und spielt die Gemini-Live-Audioantwort ab. Die alte STT->Chat->TTS-Pipeline bleibt als `windows_sapi` Fallback erhalten. UI-Status zeigt fuer diesen Modus `Gemini Live aktiv`. Stand heute: erster Desktop-Client ist record-then-send, noch kein echtes Push-to-talk/gleichzeitiges Streaming. Tests gruen: compileall und 31 relevante LiveTalk/Builder-Proxy-Tests."

livetalk_gemini_live_audio_fix_2026_05_18:
"Gemini-Live-Audio-Fix am 2026-05-18. Problem: Builder leitete `setupComplete` als Byte-Frame weiter; Desktop speicherte diese JSON-Nachricht faelschlich als Audio und zeigte 'Gemini Live hat Audio geliefert', obwohl die WAV nur 70 Bytes hatte. Zweites Problem: Windows-MCI nahm lokal 11025 Hz / 8-bit WAV auf, Builder markiert aber 16 kHz / 16-bit PCM. Fix: Byte-Frames werden zuerst als JSON geprueft, nur echte groessere Audioframes werden als WAV geschrieben; Eingabe-WAV wird vor dem Senden auf mono 16 kHz / 16-bit PCM normalisiert. Live-Debug mit letzter Aufnahme: transcript 'Hallo Maya, wie geht's?', response_text 'Hallo! Mir geht's gut, danke! Wie kann ich dir helfen?', Audio-WAV 181486 Bytes. Tests gruen: compileall und 33 relevante Tests. Audio-Testdateien geloescht."

livetalk_gemini_live_retry_ux_2026_05_18:
"Gemini-Live-Weiterreden-UX am 2026-05-18 verbessert. Anlass: Nach zwei guten Runden war die dritte lokale Aufnahme fast still (RMS ca. 160, loud_ratio ca. 0.009), daher lieferte Gemini keine Antwort. Neu: Der LiveTalk-Button heisst im aktiven Modus `Weiter sprechen`; leise Aufnahmen werden lokal per Signalstatistik erkannt und bekommen sofort `Keine Sprache erkannt. Bitte nach dem Ton sprechen.` statt 20s Wartezeit; alte Antwort-WAVs werden vor jedem neuen Lauf geloescht, damit keine stale Audio-Datei wiederverwendet wird. Tests gruen: compileall und 35 relevante Tests. Audio-Testdateien geloescht."

livetalk_gemini_live_goat_context_2026_05_18:
"Gemini-Live-Systemanweisung am 2026-05-18 erweitert. Anlass: Maya beantwortete die Frage nach ihren GOAT-Desktop-Faehigkeiten nur allgemein. Neu: Die Default-Anweisung beschreibt GOAT Desktop als lokale Windows-App mit Sprache, Textchat, Bildschirmkontext, gelbem Cue-Ball, Builder-Proxy, Vision-Hints, lokalen Sicherheitspruefungen und gegateten Aktionen. Bei Fragen nach Faehigkeiten soll Maya konkrete GOAT-Desktop-Faehigkeiten nennen und keine Desktop-Aktion behaupten oder ausfuehren ohne explizite Freigabe. Tests gruen: compileall und 36 relevante Tests. Audio-Testdateien geloescht."

livetalk_push_to_talk_mouse_2026_05_18:
"Mouse-Hold-Push-to-talk am 2026-05-18 implementiert. Im Gemini-Live-Modus startet die linke Maustaste auf dem LiveTalk-Button die Aufnahme; solange der Button gedrueckt bleibt, wird aufgenommen; Loslassen beendet die Eingabe und sendet an Gemini Live. Der Button zeigt im aktiven Modus `Gedrueckt halten` und waehrend Aufnahme `Loslassen zum Senden`. Sicherheitslimit: `GOAT_LIVETALK_PUSH_TO_TALK_MAX_SECONDS`, Default 30s, danach wird automatisch beendet. Alte Klick-Aufnahme mit fixer 3s Dauer bleibt fuer Nicht-Gemini-Fallbacks erhalten. Tests gruen: compileall und 37 relevante Tests. Audio-Testdateien geloescht."

livetalk_gemini_live_timeout_2026_05_18:
"Gemini-Live-Antworttimeout am 2026-05-18 gesenkt. Anlass: Bei Push-to-talk konnte Maya nach Loslassen ca. 20s haengen, wenn Gemini keine Antwort lieferte. Neu: Default `GOAT_VOICE_TIMEOUT_SECONDS` ist 10s statt 20s. Wenn Gemini eine Eingabe bestaetigt, aber keine Text-/Audioantwort startet, bricht GOAT nach `GOAT_VOICE_EMPTY_RESPONSE_GRACE_SECONDS` ab, Default 4s. Tests gruen: compileall und 38 relevante Tests. Audio-Testdateien geloescht."

livetalk_push_to_talk_streaming_2026_05_18:
"Push-to-talk-Streaming am 2026-05-18 implementiert. Vorher wurde beim Halten weiter lokal aufgenommen und erst nach Loslassen als komplette WAV gesendet. Neu: GOAT nutzt Windows `waveIn*` via `winmm` direkt und streamt waehrend gedrueckter linker Maustaste 16 kHz / 16-bit / mono PCM in ca. 100ms-Chunks an Builder `WSS /api/goat/voice`. Beim Loslassen wird `audio.end` gesendet und Gemini Live kann schneller antworten, weil die Sprache schon waehrend des Sprechens uebertragen wurde. Keine neuen Python-Audio-Pakete noetig; `sounddevice`, `pyaudio`, `numpy` waren lokal nicht installiert. Sicherheitslimit bleibt `GOAT_LIVETALK_PUSH_TO_TALK_MAX_SECONDS` Default 30s. Tests gruen: compileall und 38 relevante Tests. Audio-Testdateien geloescht."

livetalk_streaming_ptt_default_off_2026_05_18:
"Push-to-talk-Streaming am 2026-05-18 auf Opt-in gestellt. Anlass: User meldete nach Streaming-Start `GOAT funktioniert nicht`; App-Prozess lief, aber der neue `waveIn*`-Pfad ist live noch nicht stabil genug. Neu: Standard ist wieder stabiler Hold-to-record/send-on-release. Streaming bleibt im Code, aber nur mit `GOAT_LIVETALK_STREAMING_PTT=1` aktiv. Tests gruen: compileall und 38 relevante Tests."

livetalk_short_audio_response_2026_05_18:
"Gemini-Live-Audio-Latenz am 2026-05-18 reduziert. Diagnose: Die letzte Push-to-talk-Aufnahme war fast 29s lang; die Antwort-WAV war 9.35s lang. Neu: Maya soll im LiveTalk normalerweise mit einem kurzen Satz und maximal 18 Woertern antworten. Der Push-to-talk-Pfad zeigt Text/Status sofort an und spielt die Antwort danach ab, statt die UI bis zum Ende der lokalen Wiedergabe zu blockieren. Ziel: kuerzere Audioantworten und weniger gefuehltes Warten. Tests gruen: compileall und 38 relevante Tests. Audio-Testdateien geloescht."

livetalk_faster_streaming_trial_2026_05_18:
"Gemini-Live-Speed-Fix am 2026-05-18 nach Nutzer-Test. Diagnose der letzten Runde: Aufnahme 2.7s, Antwort-WAV 2.31s, Antwortdatei ca. 4s nach Aufnahme-Ende. Neu: Maya soll im LiveTalk normalerweise maximal 12 Woerter nutzen. Ausserdem blockiert der Streaming-Push-to-talk-Pfad die UI nicht mehr bis zum Ende der lokalen Audiowiedergabe; Text/Status werden sofort emittiert, Audio wird danach abgespielt. Streaming bleibt bewusst Testmodus per `GOAT_LIVETALK_STREAMING_PTT=1`, bis Live-Test stabil ist. Tests gruen: compileall und 38 relevante Tests. Audio-Testdateien geloescht."

livetalk_hold_button_release_fix_2026_05_18:
"Push-to-talk-Button-Fix am 2026-05-18. Nutzerbeobachtung: Statt gedrueckt halten und loslassen musste man scheinbar einmal klicken zum Start und nochmal klicken zum Senden. Ursache im Desktop-Code: `set_livetalk_mode(True)` fokussierte beim Druecken direkt das Chat-Textfeld, wodurch der Button das Release-Event verlieren konnte. Neu: `set_livetalk_mode()` hat `focus_chat`; beim Push-to-talk bleibt der Fokus auf dem Button. Buttontext ist klarer: `Halten zum Sprechen` und waehrend Aufnahme `Loslassen zum Senden`. Tests gruen: compileall und 38 relevante Tests."

livetalk_best_known_audio_setting_2026_05_18:
"Aktueller Best-Stand fuer LiveTalk am 2026-05-18 festgehalten. Empfohlene Laufzeit-Einstellung: `GOAT_LIVETALK_PROVIDER=gemini_live`, `GOAT_LIVETALK_STREAMING_PTT` unset/aus, `GOAT_LIVETALK_AUTO_TTS` unset, `GOAT_LIVETALK_ALLOW_SAPI_FALLBACK` unset, `GOAT_BUILDER_RESOLVE_IP=216.24.57.7`. Diese Kombination ist stabiler als der Streaming-Testmodus und liefert bisher die beste Nutzer-Rueckmeldung. Maya antwortet im LiveTalk kurz, aber nicht extrem knapp: maximal 12 Woerter. Audio-Testdateien geloescht."

screen_context_vision_button_2026_05_18:
"Bildschirm-Kontext-Feature am 2026-05-18 umgesetzt. Neu: Im Vision-Panel gibt es `Bildschirm pruefen`. Der Button versteckt das GOAT-Popup kurz, nimmt einen temporaeren aktiven-Fenster-Screenshot auf, ruft Builder `/api/goat/vision-hint` mit dem ausgewaehlten Vision-Modell auf und speichert nur eine kurze semantische Zusammenfassung im Popup. Der Screenshot liegt nur in einem Temp-Ordner und wird geloescht. Die naechste Maya-Textfrage bekommt diesen Screen-Kontext im Chat-Context mit. Vision bleibt semantischer Kontext, keine Aktionsfreigabe. Live-Smoke: capture_ok=true, HTTP 200, provider gemini_flash_lite, ca. 1441ms. Tests gruen: compileall und 48 Vision/Chat/LiveTalk-Kontext-Tests."

screen_context_livetalk_followup_2026_05_18:
"Bildschirm-Kontext-UX am 2026-05-18 korrigiert. Problem: Nach `Bildschirm pruefen` war im Hauptfenster kein sichtbares Fragefeld; ausserdem bekam Gemini-Live-Audio den geprueften Kontext nicht. Neu: Das Textfeld bleibt auch im Hauptfenster sichtbar, sodass User direkt Fragen zum geprueften Bildschirm stellen kann. Der letzte Vision-Kontext wird ausserdem in die Gemini-Live-Instructions fuer Push-to-talk eingefuegt, damit Audio-Fragen wie `Siehst du StepStack?` den zuletzt geprueften Kontext nutzen. `LiveTalk beenden` bleibt der Rueckweg aus dem LiveTalk-Modus; im Hauptfenster ist kein Zurueck-Button noetig. Tests gruen: compileall und 48 relevante Tests. Audio-Testdateien geloescht."

screen_context_visible_desktop_2026_05_18:
"Bildschirm-Pruefung am 2026-05-18 von aktivem Fenster auf sichtbaren Desktop umgestellt. Problem aus UI-Test: Vision erkannte `GOAT Desktop`/Codex statt Desktop-Ordnern wie StepStack, weil nur das aktive Fenster gecaptured wurde. Neu: `Bildschirm pruefen` nutzt `capture_visible_desktop()`, also den ganzen sichtbaren Windows-Desktop nach dem Verstecken des GOAT-Popups. Der Screenshot bleibt temporaer und wird geloescht. Live-Smoke: capture_ok=true, scope=visible_desktop, Builder Vision HTTP 200, provider gemini_flash_lite, ca. 1672ms, Temp-Ordner geloescht."

gemini_live_primary_with_video_2026_05_17:
"Gemini Live API ist primaerer LiveTalk-Pfad mit kontinuierlichem Video-Frame-Streaming (~1 FPS). Das Popup instanziiert standardmaessig `GeminiLiveSession`; der alte kaskadierte LiveTalk-Pfad ist nur noch via `GOAT_LIVETALK_FALLBACK=1` erreichbar. Streaming-Push-to-talk sendet 16 kHz PCM-Audio und JPEG-Frames des sichtbaren Desktops als native `realtimeInput.video`-Nachrichten an Builder `/api/goat/voice`. `Bildschirm pruefen` ist aus der sichtbaren Hauptfenster-UI entfernt und bleibt nur als versteckter Debug/Fallback-Pfad verdrahtet. Maya sieht den Bildschirm im LiveTalk-Modus kontinuierlich, ohne dass User einen manuellen Screen-Workflow ausloesen muss."

gemini_live_video_protocol_fix_2026_05_18:
"Live-Acceptance zeigte: Maya antwortete `Ich kann deinen Bildschirm nicht sehen`, obwohl Desktop Frames sendete. Ursache: Desktop sendete `type=video.frame`, aber Builder `/api/goat/voice` leitet nur native Gemini-Live-Nachrichten wie `realtimeInput` unveraendert weiter; `video.frame` wurde als unsupported behandelt. Fix: Desktop sendet JPEG-Frames jetzt direkt als `realtimeInput.video` mit `mimeType=image/jpeg`, sodass der bestehende Builder ohne Deploy-Aenderung an Gemini Live weiterreichen kann."

gemini_live_stream_hang_fix_2026_05_18:
"Live-Acceptance zeigte nach dem Protocol-Fix einen haengenden UI-Zustand `Verarbeite Sprache / Gemini Live laeuft`. Ursache im lokalen Desktop: Der neue Streaming-Pfad nutzte `WaveInPcmStreamer`, aber `_wave_check()` fehlte in `livetalk_live.py`; dadurch crashte die Worker-Route beim Mikrofonstart. Fix: `_wave_check()` ergaenzt und per Unit-Test abgesichert. Zusaetzlich hat der Audio+Video-Sendeloop jetzt einen harten Turn-Deadline-Check, damit GOAT bei Builder/Gemini-Haengern nicht minutenlang im `Sende...`-Zustand bleibt."

gemini_live_turn_coverage_fix_2026_05_18:
"Maschineller SAPI-Acceptance-Test erkannte die Audiofrage korrekt (`Siehst du den Step Stack Ordner...`) und sendete einen Video-Frame, Gemini antwortete aber trotzdem, es sehe den Ordner nicht. Ursache: Das Setup nutzte die Builder-Session-Abstraktion ohne `realtimeInputConfig.turnCoverage`; laut Gemini Live API kann Video ausserhalb der Audio-Aktivitaet sonst aus dem Turn fallen. Fix: Desktop sendet jetzt natives Gemini-Live-`setup` mit `TURN_INCLUDES_AUDIO_ACTIVITY_AND_ALL_VIDEO`, damit alle Video-Frames des Turns in die Antwort einbezogen werden."

gemini_live_streaming_default_video_toggle_2026_05_18:
"Zielarchitektur korrigiert: LiveTalk nutzt wieder den echten Gemini-Live-Streaming-Pfad als Default; alter kaskadierter Fallback bleibt nur via `GOAT_LIVETALK_FALLBACK=1`. Video-Frames sind gebaut, aber konservativ default aus via `GOAT_LIVETALK_VIDEO_FRAMES=0`; User kann im LiveTalk-Popup `Maya sieht Bildschirm` einschalten. Modus `1` sendet ca. 1 FPS, Modus `2` ca. 0.5 FPS. Headless-Latenzmessung mit 5 Streaming-Runs: ohne Video median first_response_ms 3970ms / total 6097ms, mit Video median first_response_ms 5113ms / total 6996ms. Ergebnis: Video ist funktionsfaehig, aber nicht kostenlos; default bleibt aus."

livetalk_recorded_ptt_default_2026_05_18:
"Live-Usertest zeigte: Der Streaming-Mikrofonpfad (`waveIn`) startet, liefert auf dem Zielsystem aber keine erkannte Sprache (`Keine Sprache erkannt`). Korrektur: Hold-to-talk nutzt default wieder den stabilen Windows-WAV-Aufnahmepfad und sendet danach an Gemini Live. Reines Streaming bleibt optional via `GOAT_LIVETALK_STREAMING_PTT=1`; alter kaskadierter Fallback bleibt separat via `GOAT_LIVETALK_FALLBACK=1`."

run_0a_completed_2026_05_16:
"Wahrheitsklaerung GOAT Control Adapter 79ec22b durchgefuehrt am 2026-05-16. Ergebnis: phantom_claim. Hash existiert in keinem der vier Repos (Big-Bro, Maya, aicos-registry, soulmatch), weder lokal noch remote. GOAT Desktop startet ohne Vorgaenger-Code. Detail-Bericht: docs/run-0a-truth-report-2026-05-16.md."

run_0b_completed_2026_05_16:
"UFO2 Library-Spike durchgefuehrt am 2026-05-16. Ergebnis: low-level Module potentiell wiederverwendbar, aber UFO2 als Library-Fundament nicht ueberzeugend. Full Install scheitert wegen Python-Pins (faiss-cpu, pandas). ControlPhotographer-Messung: 2.27s Mittelwert pro Screen-Sensor-Aufruf - zu langsam fuer CNC-Anchor-Protokoll ohne Optimierung. Codex-Empfehlung: kein UFO-Agent-Loop, nur schmal gewrappte Low-Level-Module. Architektur-Frage offen: UFO2 vs Slim Stack (mss + pywinauto + OmniParser direkt). Detail-Bericht: docs/run-0b-ufo2-spike-2026-05-16.md."

run_0c_completed_2026_05_17:
"Coordinate Broker Core Spike durchgefuehrt am 2026-05-17. Ergebnis: zweistufiger Broker (Candidate Builder + Local Verifier) ist als Architektur tragfaehig, wenn mindestens eine lokale Geometriequelle valide Bounds liefert. Chrome-Testseite mit --force-renderer-accessibility: UIA traf Senden-Button und Search-Input gegen DOM-Ground-Truth mit IoU 0.9714/0.98 bei ca. 547 ms Screenshot+UIA+Broker. OCR war nicht verfuegbar (Tesseract-Binary fehlt), Vision-LLM wurde bewusst uebersprungen. Notepad-Menue zeigte einen sauberen Stop-Fall, weil Save-As nicht exponiert wurde. Empfehlung: v1.1 auf Slim Stack + Coordinate Broker schreiben; OmniParser nur als separater Run 0d fuer UIA-Luecken testen. Detail-Bericht: docs/run-0c-coordinate-broker-spike-2026-05-17.md."

v1_1_published_2026_05_17:
"GOAT Desktop Vision v1.1 ist die neue kanonische Master-Spec. Aenderungen gegenueber v1.0: UFO2 raus (Run 0b: 2.27 s Latenz und Python-Pin-Konflikte in dieser Umgebung), Slim Stack rein (mss + pywinauto + optionale OCR/Vision-LLM), Coordinate Broker mit Local Verifier als Geometrie-Autoritaet (Run 0c: IoU 0.9714/0.98 auf Chrome HTML-Test), Authority-Split: Vision-LLM kann niemals allein accept. Provider-Versionen werden erst nach separater Verifikation als Default festgeschrieben. Phase 1 startet mit Run A."

run_a_started_2026_05_17:
"Run A gestartet am 2026-05-17. Scope: native PyQt6-Tray-App mit verschiebbarem Mini-Popup, ohne Overlay, Bridge, Vision, UIA oder Aktionen."

run_a_code_ready_2026_05_17:
"Run A Code-Stand angelegt am 2026-05-17. Erstes natives PyQt6-Projekt mit src/goat_desktop, Tray-Icon, Rechtsklick-Menue mit Beenden, Linksklick/DoubleClick oeffnet Popup, verschiebbares Status-Popup mit offline-Verbindung, leerem Screen-Kontext, Pause/Stop-Button und LiveTalk-Platzhalter. Compile-Check bestanden. Acceptance-Screenshot wurde nicht committed, weil im Desktop-Hintergrund ein sensibles .env-Notepad sichtbar war. Run A ist erst nach sauberem Screenshot vollstaendig completed."

run_a_completed_2026_05_17:
"Run A abgeschlossen am 2026-05-17. Sauberer Acceptance-Screenshot committed unter docs/screenshots/run-a-acceptance-2026-05-17.png. Screenshot zeigt native GOAT-Popup-Schale mit Statusfeldern, Pause/Stop, LiveTalk-Platzhalter und Windows-Taskleiste mit aktiver App. Keine sensitiven Fensterinhalte im Acceptance-Artefakt."

run_b_started_2026_05_17:
"Run B gestartet am 2026-05-17. Pflichtreferenz err-dev-002 gelesen. Scope: PyQt6 Overlay/gelber Ball, click-through, Popup-Steuerung, globaler Kill-Switch. Kein Bridge, UIA, OCR, Vision oder Action-Layer."

run_b_code_ready_2026_05_17:
"Run B Code-Stand angelegt am 2026-05-17. Fullscreen-Overlay-Ansatz wurde verworfen, weil er schwarz renderte und damit err-dev-002-Risiko zeigte. Implementiert ist stattdessen ein kleines click-through Topmost-Cue-Window mit gelbem Ball, Popup-Buttons zum Bewegen/Verbergen und globalem Ctrl+Alt+Esc-Hotkey. Runtime-Checks: overlay_click_through=True, hotkey_registered=True. Visual Check: docs/screenshots/run-b-code-ready-visual-check-2026-05-17.png. Run B ist noch nicht completed, weil Screencast und manueller Click-through-Test ueber zwei externe Apps fehlen."

run_b_completed_2026_05_17:
"Run B abgeschlossen am 2026-05-17. Acceptance-Evidenz committed unter docs/run-b-acceptance-report-2026-05-17.md sowie docs/screenshots/run-b-acceptance-context-1.png und docs/screenshots/run-b-acceptance-context-2.png. Verifiziert: gelber Ball sichtbar ueber externer Chrome/Render-UI in zwei Positionen, WS_EX_TRANSPARENT=True, WS_EX_LAYERED=True, Hit-Tests resolve nicht auf das Overlay, Ctrl+Alt+Esc versteckt Overlay und Popup. Der sicherere kleine Cue-Window-Ansatz bleibt bewusst gesetzt; kein Fullscreen-Overlay."

run_c_started_2026_05_17:
"Run C gestartet am 2026-05-17. Pflichtanker sol-cross-062 und sol-cross-063 gelesen. Scope: lokale Bridge auf 127.0.0.1, aktive Fensterdaten, Window-only Screenshot, Coordinate Broker + Local Verifier, Cue-Dispatch an den gelben Ball. Kein Builder-WebSocket, keine OCR, kein Vision-Provider, keine Action-Ausfuehrung."

run_c_code_ready_2026_05_17:
"Run C Code-Stand angelegt am 2026-05-17. Implementiert: FastAPI-Bridge mit /healthz, /active-window, /screen-capture, /screen-cue; screen.py fuer active-window und mss Window-Capture; broker.py mit Local-Geometry-Verifier; Tray-Integration mit Qt-Signal fuer Cue-Dispatch. Verifiziert per lokalem HTTP-Call: /screen-cue liefert safety_state=accept, anchors[] und broker_decision; Ball springt sichtbar auf die Cue-Koordinate. Bericht/Screenshot: docs/run-c-acceptance-report-2026-05-17.md und docs/screenshots/run-c-bridge-cue-acceptance-2026-05-17.png. Run C ist noch nicht completed, weil der strenge Popup-Klick/Screencast-Pfad aus der Master-Spec fehlt."

run_c_completed_2026_05_17:
"Run C abgeschlossen am 2026-05-17. Popup-Button 'Cue testen' triggert den lokalen /screen-cue-Endpunkt, Broker liefert safety_state=accept mit anchors[] und broker_decision, und der gelbe Ball springt sichtbar auf die akzeptierte Cue-Koordinate ueber externer Chrome/Render-UI. Acceptance-Artefakte: docs/run-c-completion-report-2026-05-17.md, docs/screenshots/run-c-popup-cue-before-2026-05-17.png und docs/screenshots/run-c-popup-cue-after-2026-05-17.png. Nicht enthalten: Builder-WebSocket, Vision-Provider, OCR, Action-Ausfuehrung."

run_d_started_2026_05_17:
"Run D gestartet am 2026-05-17. Pflichtanker sol-cross-032 und sol-cross-044 gelesen. Scope: Desktop-initiiertes outbound WebSocket zu Builder/Testserver, Token-Auth, Reconnect/Timeout-Disziplin, Builder-Test-Cue als Vorschlag, explizite User-Freigabe vor Rendering. Kein offener Inbound-Port, keine Action-Ausfuehrung, keine Vision/OCR."

run_d_completed_2026_05_17:
"Run D abgeschlossen am 2026-05-17. Implementiert: BuilderBridgeClient als outbound-only WebSocket-Client mit Authorization-Header, hello-Capabilities, Reconnect-Loop und Timeouts; Popup zeigt Builder-Cue als wartende Vorschau mit 'Cue freigeben'/'Cue ablehnen'; Freigabe leitet Cue ueber lokalen /screen-cue-Endpunkt zum Broker, erst danach rendert der Ball. Acceptance-Artefakte: docs/run-d-completion-report-2026-05-17.md, docs/screenshots/run-d-builder-cue-preview-2026-05-17.png und docs/screenshots/run-d-builder-cue-approved-2026-05-17.png."

run_e_started_2026_05_17:
"Run E gestartet am 2026-05-17. Scope: Vision-LLM als semantischer Hint-Provider, niemals als Koordinatenquelle. Konkrete Provider-Defaults bleiben gesperrt, bis echte Provider-Messungen mit Key, Latenz, JSON-Stabilitaet und UI-Semantik vorliegen."

run_e_code_ready_2026_05_17:
"Run E Code-Stand angelegt am 2026-05-17. Implementiert: vision_hint.py mit disabled/mock/openai_compatible Provider-Modi, /vision-hint Endpoint, Broker-Protokollierung von vision_hint als reine Semantik, expliziter Schutz gegen Vision-only accept. Mock-Acceptance verifiziert: /vision-hint liefert authority=semantic_hint_only, /screen-cue nimmt den Hint ins Log, finaler Broker-Pfad bleibt active_window_local_geometry_accept. Artefakte: docs/run-e-code-ready-report-2026-05-17.md, docs/screenshots/run-e-vision-input.png, docs/screenshots/run-e-mock-vision-hint-2026-05-17.png. Run E ist nicht completed, weil kein echter Provider-Key in der sichtbaren Umgebung konfiguriert ist."

run_f_started_2026_05_17:
"Run F gestartet am 2026-05-17. Scope: LiveTalk Half-Duplex-Schale fuer Mikrofon/STT/TTS. Ohne echte STT/TTS-Provider-Entscheidung oder lokale Audio-Verifikation nur code_ready, nicht completed."

run_f_code_ready_2026_05_17:
"Run F Code-Stand angelegt am 2026-05-17. Implementiert: livetalk.py mit deterministischem Mock-Half-Duplex-Roundtrip, aktivierter LiveTalk-Button im Popup, Statusanzeige fuer Transkript und Maya-Antwort. Mock-Acceptance verifiziert: Button triggert Roundtrip, Transkript 'zeig mir das Suchfeld' und Antwort 'Ich zeige das Suchfeld nur nach Freigabe.' erscheinen lesbar im Popup. Artefakte: docs/run-f-code-ready-report-2026-05-17.md und docs/screenshots/run-f-livetalk-mock-2026-05-17.png. Run F ist nicht completed, weil kein echtes Audio aufgenommen/abgespielt und kein STT/TTS-Provider validiert wurde."

run_f_windows_audio_probe_2026_05_17:
"Windows-Audio-Probe fuer Run F durchgefuehrt am 2026-05-17. Implementiert: windows_sapi LiveTalk-Provider mit lokaler WAV-Aufnahme via Windows MCI und Sprachausgabe via Windows SAPI. Lokal verifiziert: audio_recorded=true, audio_played=true, tts_provider=windows_sapi. STT ist weiterhin nicht echt validiert: stt_provider=manual, completion_ready=false. Mikrofon-WAV wurde aus Datenschutzgruenden nicht committed; JSON enthaelt nur Metadaten. Artefakte: docs/run-f-windows-audio-probe-report-2026-05-17.md und docs/run-f-windows-audio-probe-2026-05-17.json. Run F bleibt code_ready, nicht completed."

run_f_stt_builder_proxy_code_ready_2026_05_17:
"Desktop-seitiger STT Builder-Proxy fuer Run F angelegt am 2026-05-17. Implementiert: stt_hint.py mit GOAT_STT_MODE=builder_proxy, POST /api/goat/stt, Bearer-Auth, Timeout, optionalem GOAT_BUILDER_RESOLVE_IP und fail-closed uncertain bei Fehlern. LiveTalk windows_sapi ruft nach WAV-Aufnahme zuerst Builder-STT auf; manual transcript bleibt nur Probe-Fallback und setzt completion_ready nicht. Tests gruen: 17 passed fuer LiveTalk/STT/Vision-Proxy-Subset. Artefakt: docs/run-f-stt-builder-proxy-code-ready-report-2026-05-17.md. Run F bleibt nicht completed, bis Soulmatch /api/goat/stt live ist und ein echter Desktop-Probe-Call completion_ready=true liefert."

run_f_stt_builder_smoke_2026_05_17:
"Live Soulmatch Builder-STT-Smoke durchgefuehrt am 2026-05-17. /api/goat/stt ist erreichbar: ohne Token 401, mit gesetztem GOAT_BUILDER_TOKEN und synthetischer SAPI-WAV HTTP 200. Ergebnis: status=ok, provider=builder_default, transcript='Sieh das Suchfeld', confidence=0.95, latency 2146ms. WAV wurde nach dem Test geloescht und nicht committed. Artefakte: docs/run-f-stt-builder-smoke-report-2026-05-17.md und docs/run-f-stt-builder-smoke-2026-05-17.json. Run F bleibt noch nicht completed, weil die finale Live-Mikrofon-Acceptance aussteht."

run_f_live_microphone_attempt_2026_05_17:
"Live-Mikrofon-Acceptance fuer Run F versucht am 2026-05-17. Technischer Pfad funktioniert: audio_recorded=true, Builder-STT antwortet, audio_played=true. Acceptance nicht bestanden: erwarteter Satz 'zeige das suchfeld', erkannt wurde 'GOAT Desktop'. TTS wurde daraufhin auf deutsche Windows-SAPI-Stimme priorisiert (German/Deutsch/Hedda; auf dieser Maschine Microsoft Hedda Desktop - German vorhanden). Audio-WAV wurde geloescht und nicht committed. Artefakte: docs/run-f-live-microphone-attempt-report-2026-05-17.md und docs/run-f-live-microphone-acceptance-2026-05-17.json. Run F bleibt nicht completed."

run_f2_builder_tts_code_ready_2026_05_17:
"Desktop-seitiger Builder-TTS-Proxy fuer Run F2 angelegt am 2026-05-17. Implementiert: tts_hint.py mit GOAT_TTS_MODE=builder_proxy, POST /api/goat/tts, Bearer-Auth, deutschem Default GOAT_TTS_LANGUAGE=de-DE, GOAT_TTS_VOICE=maya_de und Aussprache-Hints fuer GOAT/Maya. LiveTalk nutzt jetzt Builder-TTS fuer die Antwort und Windows-SAPI nur noch als Fallback; completion_ready wird nur true, wenn realer STT und Builder-TTS beide erfolgreich sind. Live-Check: /api/goat/tts liefert aktuell 404, Builder-Endpunkt fehlt noch. Tests gruen: 13 passed fuer TTS/STT/LiveTalk-Subset. Artefakt: docs/run-f2-builder-tts-code-ready-report-2026-05-17.md."

run_f2_builder_tts_smoke_2026_05_17:
"Live Soulmatch Builder-TTS-Smoke durchgefuehrt am 2026-05-17. /api/goat/tts ist erreichbar: ohne Token 401, mit gesetztem GOAT_BUILDER_TOKEN HTTP 200. Ergebnis: status=ok, provider=builder_default, voice=maya_de, language=de-DE, mime_type=audio/wav, audio_file_size_bytes=309690, latency 5350ms. WAV wurde nach dem Test geloescht und nicht committed. Artefakte: docs/run-f2-builder-tts-smoke-report-2026-05-17.md und docs/run-f2-builder-tts-smoke-2026-05-17.json. Finaler Run-F-Mikrofon-Test mit Builder-STT+Builder-TTS ist jetzt moeglich."

run_f_final_live_attempt_2026_05_17:
"Finaler Run-F-Liveversuch am 2026-05-17 durchgefuehrt mit Mikrofon -> Builder-STT -> Builder-TTS -> lokaler WAV-Wiedergabe. Technischer Pfad funktioniert: audio_recorded=true, stt_provider=builder_default, tts_provider=builder_default, audio_played=true, completion_ready=true. Acceptance nicht bestanden: erwarteter Satz 'zeige das suchfeld', erkannt wurde nur 'So'. Erster Full-Path-Versuch deckte zusaetzlich einen MCI-Long-Path-Fehler bei TTS-Wiedergabe auf; Playback wurde auf kurze Temp-WAV korrigiert. Audio-WAVs wurden geloescht und nicht committed. Artefakte: docs/run-f-final-live-attempt-report-2026-05-17.md und docs/run-f-final-live-acceptance-2026-05-17.json. Run F bleibt nicht completed."

run_f_recording_cue_code_ready_2026_05_17:
"LiveTalk-Aufnahme-Cue ergaenzt, nachdem der erste finale Liveversuch wahrscheinlich am Anfang abgeschnitten wurde. Popup zeigt jetzt vor der Aufnahme 'Gleich sprechen' und nach dem Start 'Nimmt auf / Jetzt sprechen'. Direkt vor Aufnahmebeginn ertönt ein kurzer Signalton. Default-Aufnahmedauer wurde von 1.0s auf 5.0s erhoeht; Vorlaufzeit ist ueber GOAT_LIVETALK_PREPARE_SECONDS konfigurierbar. Tests gruen: compileall und 14 LiveTalk/STT/TTS-Tests. Run F bleibt bis zu einem erfolgreichen Mikrofon-Acceptance-Pass nicht completed."

run_f_builder_audio_auto_mode_2026_05_17:
"STT/TTS-Konfiguration fuer LiveTalk robuster gemacht. Wenn GOAT_BUILDER_URL und GOAT_BUILDER_TOKEN im Prozess sichtbar sind, aktivieren load_stt_config() und load_tts_config() automatisch builder_proxy, auch wenn GOAT_STT_MODE oder GOAT_TTS_MODE nicht separat gesetzt sind. Anlass: UI-Test zeigte 'Audio wurde aufgenommen. STT ist noch nicht konfiguriert.', obwohl Builder-Zugang als User-Environment vorhanden war. Tests gruen: compileall und 16 LiveTalk/STT/TTS-Tests. Run F bleibt bis erfolgreicher UI-Mikrofon-Acceptance nicht completed."

run_f_builder_audio_user_env_fallback_2026_05_17:
"STT/TTS-Konfiguration liest GOAT_BUILDER_URL und GOAT_BUILDER_TOKEN jetzt bei fehlender Prozess-Env direkt aus Windows HKCU/Environment. Anlass: sichtbare GOAT-UI lief ohne Prozess-Env und zeigte weiter 'STT ist noch nicht konfiguriert'. Verifikation: Python-Prozess ohne GOAT_BUILDER_URL/GOAT_BUILDER_TOKEN in os.environ laedt beide Werte aus User-Env und setzt stt_mode=builder_proxy sowie tts_mode=builder_proxy. Tests gruen: compileall und 16 LiveTalk/STT/TTS-Tests. Keine Secrets committed."

run_f_audio_status_ui_2026_05_17:
"GOAT-Popup zeigt jetzt eine eigene Audio-Zeile an. Erwarteter gueltiger Zustand fuer Run-F-Acceptance: 'STT Builder aktiv / TTS Builder aktiv'. Dadurch ist sichtbar, ob der geoeffnete Desktop-Prozess den Builder-Audio-Pfad wirklich geladen hat, bevor der User spricht. Anlass: wiederholte UI-Tests zeigten 'STT ist noch nicht konfiguriert', obwohl lokale Import-Checks builder_proxy korrekt luden. Tests gruen: compileall und 16 LiveTalk/STT/TTS-Tests."

run_f_stt_error_text_fix_2026_05_17:
"LiveTalk-Maya-Text fuer aktive Builder-STT-Fehler korrigiert. Wenn Builder-STT aktiv ist, aber keinen Text erkennt, zeigt Maya jetzt 'Audio wurde aufgenommen, aber Builder-STT hat keinen Text erkannt.' statt der irrefuehrenden Meldung 'STT ist noch nicht konfiguriert'. Popup-Groesse erhoeht, damit die neue Audio-Zeile und Maya-Status nicht abgeschnitten werden. Tests gruen: compileall und 17 LiveTalk/STT/TTS-Tests."

run_f_dns_override_fix_2026_05_17:
"Run-F-UI-Test zeigte Builder-STT-Fehler 'URLError'. Direkte Diagnose: GOAT_BUILDER_URL=https://soulmatch-1.onrender.com ist gesetzt, aber curl/Python konnten den Host lokal nicht aufloesen, waehrend Resolve-DnsName Render-IPs fand. Mit GOAT_BUILDER_RESOLVE_IP=216.24.57.7 funktioniert derselbe lokale WAV-Test: Builder-STT erkannte 'Zeige mir das Suchfeld' mit confidence=0.98. STT/TTS Resolve-Override liest GOAT_BUILDER_RESOLVE_IP jetzt ebenfalls aus Windows User-Environment. Keine Audio-Artefakte committed."

run_f_completed_2026_05_17:
"Run F final live acceptance bestanden am 2026-05-17. Sichtbare GOAT-Desktop-UI zeigte Audio-Status 'STT Builder aktiv / TTS Builder aktiv'. User sprach nach Aufnahme-Cue; Builder-STT erkannte 'Zeige mir das Suchfeld.' und Builder-TTS antwortete mit KI-Stimme: 'Gehoert: Zeige mir das Suchfeld.. Ich handle nur nach Freigabe.' Akzeptierter Pfad: sichtbare UI -> Mikrofon -> Builder-STT -> Builder-TTS -> lokale Wiedergabe. Screenshot: docs/screenshots/run-f-final-acceptance-2026-05-17.png. Report: docs/run-f-completion-report-2026-05-17.md. Audio-WAVs wurden geloescht und nicht committed."

popup_recovery_fix_2026_05_17:
"GOAT-Popup-Wiederherstellung verbessert, nachdem das minimierte/maximierte Fenster nicht mehr auffindbar war und nur der gelbe Overlay-Ball sichtbar blieb. Neues Verhalten: Ctrl+Alt+G holt das Popup global zurueck; show_popup nutzt showNormal(), raise und activateWindow; Popup wird beim Platzieren in den sichtbaren Bildschirmbereich geklemmt; Standardfenster ist groesser (1040x720, Minimum 860x620), damit LiveTalk-Ausgaben ohne Maximieren lesbar sind. Ctrl+Alt+Esc bleibt Emergency Stop. Tests gruen: compileall und 17 LiveTalk/STT/TTS-Tests."

popup_recovery_size_normalization_2026_05_17:
"Popup-Recovery normalisiert jetzt auch die Fenstergroesse. Anlass: Nach Maximieren/Minimieren stellte Qt das Fenster zwar wieder sichtbar her, aber in einer extrem grossen Geometrie. ensure_visible() setzt Fenster ueber 1400px Breite oder 900px Hoehe beim Wiederanzeigen auf die bevorzugte Groesse 1040x720 zurueck und klemmt es danach in den sichtbaren Bereich."

popup_recovery_preferred_size_2026_05_17:
"Popup-Recovery setzt beim Wiederanzeigen jetzt aktiv die bevorzugte Fenstergroesse 920x640 und klemmt danach in den sichtbaren Bereich. Anlass: Windows-DPI/Qt-Geometrie liess die vorherige Oversize-Erkennung zu spaet greifen. Minimum reduziert auf 760x540, damit die UI lesbar bleibt ohne maximiertes Fenster."

popup_minimize_recovery_2026_05_17:
"GOAT-Popup faengt WindowStateChange=minimized jetzt ab und stellt sich automatisch mit showNormal(), bevorzugter Groesse und On-Screen-Clamping wieder her. Anlass: Windows legte das minimierte Popup bei -32000/-32000 ab; damit blieb nur der gelbe Overlay-Ball sichtbar. Minimieren wird fuer GOAT vorerst als Recovery-Fall behandelt, nicht als dauerhafter Hidden-State."

local_uia_search_status_source_2026_05_25:
"Lokaler UIA-Screen-Kontext verbreitert: GOAT liest sichtbare Fenster plus Desktop/Shell-Roots read-only aus, dedupliziert UIA-Elemente und normalisiert deutsche Umlaut-/ASCII-Schreibweisen fuer Treffer wie Schaltflaeche. Textchat-Screenfragen zeigen jetzt klarer die Quelle: `Bildschirm: UIA gesehen`, `Bildschirm: Vision gesehen`, `Bildschirm: Ziel nicht sicher gesehen` oder `Bildschirm: nicht gelesen`. Fallback-Antworten benennen UIA explizit als lokale Sichtquelle."

screen_question_local_direct_answer_2026_05_25:
"Textchat-Screenfragen werden direkt lokal beantwortet, wenn GOAT einen klaren UIA- oder Vision-Kontext hat. Dadurch wartet GOAT bei Fragen wie `Siehst du StepStack?` nicht mehr auf den Builder-Chat, sondern nutzt den bereits geprueften Screen-Kontext. Bei unsicherem oder nicht verfuegbarem Screen-Kontext bleibt der normale Builder-Chat/Fallback-Pfad erhalten."

desktop_icon_fast_path_2026_05_25:
"Screenfragen nach Desktop-Icons nutzen jetzt zuerst einen read-only Win32-Desktop-Icon-Pfad vor dem langsameren UIA-Fallback. Live-Smoke mit sichtbarem `stepstack` fand das Ziel im isolierten ersten Lauf in ca. 1767ms und danach warm in ca. 244-316ms, statt mehrere Sekunden UIA-Vollscan. Der Status zeigt dafuer `Bildschirm: Desktop gesehen`; Cue-Marker behalten die Quelle `win32_desktop`."

bridge_screen_question_smoke_2026_05_25:
"Lokaler Bridge-Endpunkt `/chat/screen-question` ergaenzt, damit der laufende GOAT-Prozess Screenfragen ohne UI-Klick smoke-testen kann. Der Endpoint nutzt denselben Tray-Screen-Resolver und dieselbe `chat_finished`-Popup-Route wie Textchat. Live-Smoke gegen `http://127.0.0.1:8765/chat/screen-question` mit `Siehst du den StepStack Ordner auf meinem Desktop?` lieferte `Gesehen per Desktop: stepstack (ListItem) sichtbar.`, Markerquelle `win32_desktop`, Provider `goat_local_screen_context` und keine Desktop-/Maus-/Keyboard-/Provider-Aktionen."

bridge_screen_question_polish_2026_05_26:
"Bridge-Screen-Smoke gibt jetzt `time_ms` und kompakte Evidence (`screen_context`, `marker_source`, `chat_provider`) zurueck. Sichtbare Desktop-Namen werden im Antwort-/Markertext sauberer dargestellt; bekannter `stepstack`-Iconname erscheint als `StepStack`. Live-Smoke am 2026-05-26 gegen den laufenden GOAT-Prozess: `/chat/screen-question` antwortete in 314.48ms mit `Gesehen per Desktop: StepStack (ListItem) sichtbar.`, Markerquelle `win32_desktop`, keine Desktop-/Maus-/Keyboard-/Provider-Aktion."

screen_target_fast_paths_2026_05_26:
"Screenfragen nutzen jetzt zielbezogene Fast-Paths vor dem generischen UIA/Vision-Fallback: Desktop-Icons via Win32-Desktopliste, Fensterfragen via sichtbarer Win32-Fensterliste, Taskleistenfragen gezielt via Shell_TrayWnd/UIA. Kontextwoerter wie Taskleiste/Fenster werden nicht mehr als Zielbegriffe gewertet; `GOAT Desktop` bleibt als Phrase erhalten. Live-Smoke: GOAT-Desktop-Fenster 465.15ms via `win32_window`, Codex-Taskleiste kalt 3083.43ms und danach warm 223-302ms via `uia_taskbar`, Google-Chrome-Desktopicon 10.78ms via `win32_desktop`. Keine Provider-/Desktop-/Maus-/Keyboard-Aktionen."

taskbar_cache_warmup_2026_05_26:
"Taskleisten-UIA wird beim GOAT-Start read-only im Hintergrund vorgeladen und fuer 15s gecacht. Direkte Messung: Warmup selbst ca. 2446ms, danach Taskleistenfrage `Codex in der Taskleiste` ca. 0.9-2.4ms im selben Prozess. Live-Smoke nach GOAT-Neustart mit 5s Warmup: erste Bridge-Frage 1.43ms, danach 0.84/0.83/0.93ms, Quelle `uia_taskbar`, keine Provider-/Desktop-/Maus-/Keyboard-Aktionen. Chat/STT/TTS-Mockserver wurden ebenfalls stabilisiert, indem Request-Bodies vor Test-HTTP-Fehlerantworten gelesen werden."

screen_resolver_evidence_2026_05_26:
"Bridge-Screen-Smoke zeigt jetzt Resolver-Evidence: `source_path`, `cache_hit` und `elements_scanned`. Taskleisten-Smoke belegt beide Pfade: Scan-Pfad `uia_taskbar_scan` mit `cache_hit=false`, danach Cache-Pfad `uia_taskbar_cache` mit `cache_hit=true` in ca. 0.65ms. Diese Evidence wird aus dem Tray-Screen-Resolver bis `/chat/screen-question` durchgereicht; keine Provider-/Desktop-/Maus-/Keyboard-Aktionen."

taskbar_cache_sliding_ttl_2026_05_26:
"Taskleisten-Cache nutzt jetzt eine Sliding-TTL von 120s: jeder Cache-Treffer verlaengert die Frische, statt nach 15s hart kalt zu werden. Direkte Messung nach Warmup: Taskleistenfrage ca. 0.25-0.36ms auch nach kurzer Pause. Live-Smoke nach GOAT-Neustart und Warmup: erster Bridge-Treffer 0.45ms, zweiter nach 3s 0.60ms, jeweils `source_path=uia_taskbar_cache`, `cache_hit=true`, keine Provider-/Desktop-/Maus-/Keyboard-Aktionen."

taskbar_cache_miss_refresh_2026_05_26:
"Taskleisten-Cache-Miss fuehrt jetzt einmalig zu einem Live-Scan und aktualisiert den Cache, statt beim alten Cache stehenzubleiben. Bridge-Evidence enthaelt `cache_refreshed`, sodass Scan/Cache/Refresh unterscheidbar sind. Unit-Test deckt warmen Cache ohne Ziel -> Live-Scan -> Cache-Ersetzung ab. Live-Smoke gegen laufenden GOAT-Prozess: erster Taskleistenrequest `source_path=uia_taskbar_scan`, `cache_hit=false`, `cache_refreshed=false`, 900.62ms Resolverzeit; zweiter Request `source_path=uia_taskbar_cache`, `cache_hit=true`, 0.62ms Resolverzeit. Keine Provider-/Desktop-/Maus-/Keyboard-Aktionen."

bridge_resolver_object_2026_05_26:
"Bridge-Screen-Smoke gibt Resolverdaten jetzt konsistent unter `evidence.resolver` aus: `source`, `source_path`, `cache_hit`, `cache_refreshed`, `time_ms`, `elements_scanned`. Die alten flachen Evidence-Felder bleiben als Kompatibilitaets-Alias erhalten. Live-Smoke: `resolver.source=uia_taskbar`, `source_path=uia_taskbar_scan`, `cache_hit=false`, `time_ms=621.14`, Antwort `Gesehen per Taskleiste: Codex - 1 aktives Fenster angeheftet...`, keine Provider-/Desktop-/Maus-/Keyboard-Aktionen."

popup_product_simplification_2026_05_17:
"Popup-UI produktnaeher verschlankt. Entfernt aus sichtbarer Haupt-UI: statische Tabellenbeschriftungen, Dev-Button 'Cue testen' und manuelle Ball-Pfeiltasten. Ballsteuerung bleibt im Tray-Menue fuer Debug/Recovery, aber normaler Produktpfad ist GOAT setzt den Ball auf erkannte Ziele/Felder/Buttons. Status wird als kompakte Chips angezeigt; Screen-Kontext, Maya-Antwort und Zielmarkierung sind groessere Ausgabefelder. Bevorzugte Popup-Groesse bleibt kompakt."

livetalk_compact_mode_2026_05_17:
"LiveTalk bekommt einen eigenen kompakten Anzeigemodus. Beim Klick auf LiveTalk werden Einstellungen, Freigabe-Buttons, Zielmarkierung und Verbindungschip ausgeblendet; sichtbar bleiben Audio-Status, erkannter Text, Maya-Antwort, 'Nochmal sprechen' und 'LiveTalk beenden'. Nach 'LiveTalk beenden' kehrt das normale Fenster mit Provider-/Denkmodus-Einstellungen zurueck. Reasoning-Dropdown wurde von unklarem 'Minimal/Niedrig/Mittel/Hoch' auf 'Denkmodus: schnell/niedrig/mittel/hoch' umbenannt. Tests gruen: compileall und 17 LiveTalk/STT/TTS-Tests."

livetalk_chat_mode_polish_2026_05_17:
"LiveTalk-Modus weiter verdichtet und um Texteingabe erweitert. Logische Fenstergroessen: Normalmodus 620x450 px, LiveTalk 430x320 px (vorher LiveTalk 520x360 px; reale Bildschirmgroesse haengt von Windows-DPI/Qt-Skalierung ab). LiveTalk zeigt jetzt Audio-Status, erkannte/geschriebene Eingabe, Maya-Antwort, Texteingabe, Senden, Nochmal sprechen und LiveTalk beenden. Minimieren in die Taskleiste ist wieder erlaubt; Ctrl+Alt+G bleibt Recovery-Hotkey. Optik verbessert: rundere Ecken und Hover-/Pressed-States fuer Buttons/Eingaben."

run_e_multi_provider_code_ready_2026_05_17:
"vision_hint.py wurde um Multi-Provider-Vision-Hint erweitert (gemini_flash_lite, grok_4_3, gemini_flash). Reasoning-Level konfigurierbar (minimal, low, medium, high). User-Wahl im Popup ueber zwei Dropdowns, Persistierung in vision_config.json unter APPDATA/GoatDesktop. Default: gemini_flash_lite + minimal. Builder-Proxy-Modus nutzt GOAT_VISION_MODE=builder_proxy, GOAT_BUILDER_URL, GOAT_BUILDER_TOKEN, GOAT_VISION_PROVIDER und GOAT_VISION_REASONING. Unit-Tests mit Mock-Server gruen: 8 passed. Acceptance gegen echten /api/goat/vision-hint folgt sobald Soulmatch-Builder den Endpoint gepusht hat. Fail-Safe bei Builder-Offline/Timeout/HTTP-Fehler: uncertain-Hint, kein stiller Mock-Switch. run_e_completed bleibt bewusst nicht gesetzt."

run_e_completed_2026_05_17:
"Run E abgeschlossen am 2026-05-17. Echter Builder-Proxy-Smoke gegen https://soulmatch-1.onrender.com/api/goat/vision-hint durchgefuehrt mit gesetztem GOAT_BUILDER_TOKEN. Alle drei Provider liefern nutzbare semantische Hints ohne Pixel-Koordinatenautoritaet: gemini_flash_lite minimal 1617ms, gemini_flash minimal 1580ms, grok_4_3 requested minimal / used none 1300ms. Alle Antworten http_status=200, Labels zeigen semantisch auf den Manual-Deploy-Button. Artefakt: docs/run-e-completion-report-2026-05-17.md. Lokaler DNS-Resolver brauchte fuer den Test GOAT_BUILDER_RESOLVE_IP=216.24.57.7; Code unterstuetzt diesen optionalen Override, bleibt aber standardmaessig bei normaler DNS-Aufloesung."

run_g1_code_ready_2026_05_17:
"Run G1 Code-Stand angelegt am 2026-05-17. Pflichtanker sol-cross-062, sol-cross-063, sol-cross-042, sol-cross-038, sol-cross-014 und sol-cross-034 gelesen. Implementiert: action_gate.py mit konservativer Stufenklassifikation (1 Navigation, 2 Preview, 3 harte Freigabe, 4 technische Sperre), Broker accept als harte Vorbedingung, Unknown=Stage3, Stage4=locked; audit_log.py mit JSONL-Claim-Lineage und Assumptions. Tests gruen: 15 passed. Dry-run-Artefakte: docs/run-g1-code-ready-report-2026-05-17.md, docs/run-g1-action-gate-dry-run-results.json, docs/run-g1-action-gate-audit-sample.jsonl. Keine OS-Action ausgefuehrt; Run G1 ist code_ready, nicht completed."

run_g2_code_ready_2026_05_17:
"Run G2 Code-Stand angelegt am 2026-05-17. Implementiert: stage1_executor.py als eng allowlist-basierter Stage-1-Ausfuehrungspfad fuer Scroll und Hover/Pointer-Move, mit Broker-accept ueber action_gate.py, zusaetzlicher Stage-1-Pruefung im Executor und JSONL-Audit. /action/stage1 Bridge-Endpunkt defaults auf dry_run=true. Stage 2, Stage 3 und Stage 4 werden im Executor auch dann geblockt, wenn ein Caller ihn direkt erreicht. open menu bleibt in G2 bewusst geblockt, weil es meist Click-Semantik braucht. Tests gruen: 24 passed. Artefakte: docs/run-g2-code-ready-report-2026-05-17.md, docs/run-g2-stage1-executor-results.json, docs/run-g2-stage1-audit-sample.jsonl. Evidence nutzt RecordingMouseBackend; keine echte Desktop-OS-Action wurde in diesem Codex-Lauf ausgefuehrt. Run G2 ist code_ready, nicht completed."

run_g2_completed_2026_05_17:
"Run G2 abgeschlossen am 2026-05-17. Kontrollierte reale Stage-1-Acceptance auf dediziertem Tk-Testfenster 'GOAT G2 Safe Acceptance Window' durchgefuehrt. Ausgefuehrt wurden nur Hover/Pointer-Move zum Broker-accepted bbox center und Scroll im harmlosen Dummy-Textfenster. Kein Click, keine Texteingabe, kein File-Dialog, keine Stage-2/3/4-Action. Der erste Notepad-Screenshot-Versuch wurde wegen sichtbarer .env-Tabnamen verworfen und nicht committed. Finale Artefakte: docs/run-g2-completion-report-2026-05-17.md, docs/run-g2-real-acceptance-results.json, docs/run-g2-real-acceptance-audit.jsonl, docs/screenshots/run-g2-stage1-before-2026-05-17.png und docs/screenshots/run-g2-stage1-after-2026-05-17.png."

run_g3_code_ready_2026_05_17:
"Run G3 Code-Stand angelegt am 2026-05-17. Implementiert: stage2_executor.py fuer einzeilige Stage-2-Texteingabe nach Preview-Approval, Broker-accept, user_approved=true und safe_text_context=true. Text ist auf 120 Zeichen begrenzt, Mehrzeilen sind geblockt. Stage 3 und Stage 4 werden im Executor auch dann geblockt, wenn ein Caller ihn direkt erreicht. /action/stage2/text Bridge-Endpunkt defaults auf dry_run=true. Tests gruen: 34 passed. Artefakte: docs/run-g3-code-ready-report-2026-05-17.md, docs/run-g3-stage2-executor-results.json, docs/run-g3-stage2-audit-sample.jsonl. Evidence nutzt RecordingTextBackend; keine echte Desktop-OS-Texteingabe wurde in diesem Code-ready-Sample ausgefuehrt. Run G3 ist code_ready, nicht completed."

run_g3_completed_2026_05_17:
"Run G3 abgeschlossen am 2026-05-17. Kontrollierte reale Stage-2-Acceptance auf dediziertem Tk-Testfenster 'GOAT G3 Safe Text Acceptance Window' durchgefuehrt. Erst Preview ohne Ausfuehrung, danach explizit approved Texteingabe 'GOAT safe input' in ein leeres Testfeld. Kein File-Dialog, keine Stage-3/4-Action, keine Mehrzeileneingabe. Ein erster Realversuch schlug fail-closed fehl, weil die Win32-SendInput-Struktur zu klein war; Backend wurde auf volle INPUT-Union korrigiert und der erfolgreiche Versuch danach dokumentiert. Finale Artefakte: docs/run-g3-completion-report-2026-05-17.md, docs/run-g3-real-acceptance-results.json, docs/run-g3-real-acceptance-audit.jsonl, docs/screenshots/run-g3-stage2-before-2026-05-17.png und docs/screenshots/run-g3-stage2-after-2026-05-17.png."

run_g4_completed_2026_05_17:
"Run G4 abgeschlossen am 2026-05-17. Implementiert und verifiziert: stage3_approval.py fuer harte Stage-3-Approval-Pruefung ohne OS-Ausfuehrung. Gepruefte Pfade: needs_approval ohne User-Freigabe, approval_phrase_mismatch bei falscher Phrase, approved_not_executed bei exakter Phrase 'I approve this stage 3 action', Stage-4 locked bleibt nicht ueberschreibbar. /action/stage3/review Bridge-Endpunkt ergaenzt. Tests gruen: 42 passed. Artefakte: docs/run-g4-completion-report-2026-05-17.md, docs/run-g4-stage3-approval-results.json, docs/run-g4-stage3-approval-audit-sample.jsonl. Run G4 fuehrt bewusst keine Stage-3-OS-Action aus; terminaler Erfolg ist approved_not_executed."

run_g5_completed_2026_05_17:
"Run G5 abgeschlossen am 2026-05-17. Action-Klassifikator gehaertet: erweiterte deutsche/englische Stage-Begriffe, Stage-4-Prioritaet vor allen niedrigeren Stufen, Unknown bleibt Stage 3, Kontextfelder wie input_type/control_type/aria_label koennen klassifizieren. Audit enthaelt jetzt classification mit matched_term, reason und normalized_text. Tests gruen: 60 passed. Artefakte: docs/run-g5-completion-report-2026-05-17.md und docs/run-g5-classification-matrix-results.json. Run G5 fuehrt keine OS-Action aus."

run_g_integration_completed_2026_05_17:
"Run-G-Integration abgeschlossen am 2026-05-17. G1-G5 Entscheidungskette zusammen getestet: Stage1 scroll executed via RecordingMouseBackend, Stage2 preview ohne Approval, Stage2 executed mit Approval und safe_text_context via RecordingTextBackend, Stage3 approved_not_executed mit exakter Approval-Phrase, Stage4 locked, Unknown needs_approval/Stage3. Tests gruen: 61 passed. Artefakte: docs/run-g-integration-completion-report-2026-05-17.md, docs/run-g-integration-results-2026-05-17.json, docs/run-g-integration-audit-sample.jsonl. Keine neue OS-Action-Faehigkeit eingefuehrt."

bridge_screen_question_diagnostic_scope_2026_05_26:
"/chat/screen-question ist explizit als lokaler Diagnose-/Smoke-Pfad markiert und liefert diagnostic=true sowie scope=local_screen_question_smoke. Der Pfad bleibt read-only: keine Desktop-Aktionen, keine Provider-Calls, keine Maus-/Tastatursteuerung. Live-Smoke am 2026-05-26 gegen laufende GOAT-Bridge: Frage 'Siehst du Codex in der Taskleiste?' wurde lokal aus uia_taskbar_scan beantwortet, cache_hit=false, cache_refreshed=false, resolver time_ms=143.1, Antwort: 'Gesehen per Taskleiste: Codex - 1 aktives Fenster angeheftet (Button) sichtbar.'"

screen_question_answer_polish_2026_05_26:
"Lokale Screenfrage-Antworten im sichtbaren Produktpfad sind klarer und weniger technisch: gesehen-Antworten starten einheitlich mit 'Gesehen:' und nennen die Quelle menschenlesbar als Desktop, Fensterliste, Taskleiste oder Lokale UI. Technische Control-Type-Hinweise wie (Button), (ListItem) und (Window) werden aus dem Antworttext entfernt; die technische Resolver-Evidence bleibt im Diagnose-Endpunkt erhalten. Live-Smoke nach Neustart: 'Siehst du Codex in der Taskleiste?' -> 'Gesehen: Codex - 1 aktives Fenster angeheftet sichtbar. Quelle: Taskleiste.', diagnostic=true, scope=local_screen_question_smoke, source_path=uia_taskbar_cache, cache_hit=true, resolver time_ms=0.81, keine Provider-/Desktop-/Maus-/Keyboard-Aktion."

screen_question_uncertain_answer_polish_2026_05_26:
"Unsichere Screenfrage-Antworten bleiben jetzt lokal und fail-closed, statt nach einem gelesenen aber unsicheren Bildschirmkontext an Maya/Builder weiterzureichen. Sichtbarer Text unterscheidet klar: Ziel nicht sicher gesehen im aktuellen Bildschirmbild, mit kurzem Grund wie Position unklar, kein verlaesslicher Treffer, Vision-Auswertung fehlgeschlagen oder Vision-Builder nicht konfiguriert. '-' ohne echten Kontext bleibt kein lokaler Screen-Kontext. Tests gruen: 149 passed; lokale Bridge /healthz ok."

screen_question_vision_fallback_gate_2026_05_26:
"Screenfragen trennen lokalen Hauptpfad und langsamen Vision-Fallback klarer. Normale Fragen wie 'Siehst du X auf dem Desktop?' nutzen nur lokale UIA/Win32/Taskleisten-Erkennung und liefern bei Miss eine lokale 'Nicht sicher gesehen'-Antwort; kein Builder-/Vision-Call und kein Screenshot. Vision-Fallback laeuft nur bei expliziten Formulierungen wie 'pruef genau', 'mit Vision', 'per Vision', 'Screenshot' oder 'Bildschirm pruefen'. Live-Smoke nach Neustart: 'Siehst du DiesesZielGibtEsNicht auf dem Desktop?' -> provider goat_local_screen_context, providerCallsMade=false, source_path=uia_scan, elements_scanned=105, time_ms=1663.01, keine Desktop-/Maus-/Keyboard-Aktion. Tests gruen: 153 passed."

desktop_question_miss_fastpath_2026_05_26:
"Explizite Desktop-Fragen stoppen nach einem Win32-Desktop-Icon-Miss und fallen nicht mehr automatisch in den langsameren UIA-Vollscan. Ergebnis: nicht existierendes Desktop-Ziel bleibt lokal/fail-closed mit source_path=win32_desktop_miss. Live-Smoke nach Neustart: 'Siehst du DiesesZielGibtEsNicht auf dem Desktop?' -> time_ms=97.54, elements_scanned=57, providerCallsMade=false, keine Screenshot-/Vision-/Desktop-/Maus-/Keyboard-Aktion. Vorheriger Vergleichswert desselben Pfads lag bei ca. 1663ms via uia_scan. Tests gruen: 154 passed."

taskbar_question_miss_fastpath_2026_05_26:
"Explizite Taskleistenfragen stoppen nach Cache-/Taskbar-Miss und fallen nicht mehr in den allgemeinen UIA-Vollscan. Fuzzy-Matching wurde gehaertet, damit kurze Common-Word-Prefixe wie 'dieses' nicht mehr lange Zielwoerter wie 'DiesesZielGibtEsNicht' matchen. Live-Smoke nach Neustart: 'Siehst du DiesesZielGibtEsNicht in der Taskleiste?' -> source_path=uia_taskbar_miss, cache_hit=true, cache_refreshed=false, resolver time_ms=0.15, total time_ms=0.37, providerCallsMade=false, keine Screenshot-/Vision-/Desktop-/Maus-/Keyboard-Aktion. Tests gruen: 158 passed."

window_question_miss_fastpath_2026_05_26:
"Explizite Fensterfragen stoppen nach Win32-Fenster-Miss und fallen nicht mehr in den allgemeinen UIA-Vollscan. Zieltext-Bereinigung entfernt Fenster/window aus der sichtbaren Miss-Antwort. Live-Smoke nach Neustart: 'Siehst du DiesesZielGibtEsNicht Fenster?' -> source_path=win32_window_miss, elements_scanned=6, resolver time_ms=513.78, total time_ms=514.03, providerCallsMade=false, keine Screenshot-/Vision-/Desktop-/Maus-/Keyboard-Aktion. Tests gruen: 160 passed. Naechster Performance-Hebel waere Fensterlisten-Cache."

window_question_cache_2026_05_26:
"Fensterfragen nutzen jetzt einen warmen Win32-Fensterlisten-Cache mit Sliding-TTL, analog zur Taskleisten-Cache-Logik. GOAT waermt den Cache beim Start im Hintergrund vor; Fenster-Matches und Fenster-Misses koennen danach ohne synchronen Win32-Fensterscan beantwortet werden. Live-Smoke nach Neustart: 'Siehst du DiesesZielGibtEsNicht Fenster?' -> source_path=win32_window_miss, cache_hit=true, elements_scanned=6, resolver time_ms=0.09, total time_ms=0.42, providerCallsMade=false, keine Screenshot-/Vision-/Desktop-/Maus-/Keyboard-Aktion. Vorheriger Vergleichswert desselben Pfads lag bei ca. 514ms. Tests gruen: 164 passed."

local_screen_miss_copy_2026_05_26:
"Lokale Miss-Antworten im sichtbaren Hauptpfad sind umbenannt: statt 'Bildschirm: Ziel nicht sicher gesehen' und 'Nicht sicher gesehen...' zeigt GOAT jetzt fuer lokale Resolver-Misses 'Bildschirm: lokal geprueft, kein Treffer (Quelle)' und 'Nicht gefunden: Ich habe lokal geprueft, aber keinen passenden Treffer gesehen. Quelle: ...'. Vision-/Provider-Unsicherheit bleibt weiterhin als 'Nicht sicher gesehen' erkennbar. Live-Smoke nach Neustart: Fenster-Miss -> response_text 'Nicht gefunden: Ich habe lokal geprueft, aber keinen passenden Treffer gesehen. Quelle: Fensterliste.', cache_hit=true, resolver time_ms=0.07, providerCallsMade=false. Tests gruen: 166 passed."

broad_screen_window_resolution_2026_05_26:
"Breite Bildschirmfragen wie 'Siehst du GOAT Desktop auf dem Bildschirm?' werden nicht mehr als reine Desktop-Icon-Fragen behandelt. GOAT prueft bei Bildschirm/screen-Kontext sichtbare Fenster aus dem warmen Fensterlisten-Cache vor Desktop-Icon-Miss und entfernt 'dem' aus den Zielbegriffen. Live-Smoke nach Neustart: 'Siehst du GOAT Desktop auf dem Bildschirm?' -> 'Gesehen: GOAT Desktop sichtbar. Quelle: Fensterliste.', source_path=win32_window_cache, cache_hit=true, resolver time_ms=0.53, total time_ms=1.02, providerCallsMade=false, keine Screenshot-/Vision-/Desktop-/Maus-/Keyboard-Aktion. Tests gruen: 167 passed."

screen_question_formulation_regression_matrix_2026_05_26:
"Regression-Matrix fuer echte Screenfrage-Formulierungen ergaenzt. Festgeschriebene Routen: 'GOAT Desktop auf dem Bildschirm' -> win32_window_cache, 'GOAT Desktop Fenster' -> win32_window_cache, 'Codex in der Taskleiste' -> uia_taskbar_cache, 'StepStack auf dem Desktop' -> win32_desktop. Ziel ist, dass breite Bildschirmfragen, Fensterfragen, Taskleistenfragen und Desktopfragen nicht wieder in falsche Resolverkategorien driften. Tests gruen: Fokus 57 passed, Full Suite 168 passed, lokale Bridge /healthz ok."

## Current State

Repo initialized from GOAT Desktop Vision v1.1. Run A native tray shell is completed. Run B overlay/cue-ball safety layer is completed. Run C local bridge + Coordinate Broker path is completed. Run D outbound Builder bridge is completed against a local test Builder. Run E multi-provider Vision-Hint via Builder proxy is completed. Run F LiveTalk shell is code-ready with Windows audio record/playback probe, desktop-side STT Builder proxy, live Builder-STT smoke, desktop-side Builder-TTS proxy, and live Builder-TTS smoke. Final live microphone acceptance with Builder STT+TTS is pending. Run G1 action-gating skeleton is code-ready. Run G2 controlled Stage-1 executor is completed for hover and scroll only. Run G3 Stage-2 text input is completed for one-line safe-context input only. Run G4 Stage-3 hard approval review is completed without OS execution. Run G5 classification hardening is completed. G1-G5 integration chain is completed.

## Verified

- Documentation-only repository scaffold exists.
- Canonical spec v1.1 is stored at `docs/GOAT-DESKTOP-VISION.md`.
- AICOS references are listed at `docs/AICOS-REFERENCES.md`.
- Run A native PyQt6 tray app and mini-popup code compile successfully.
- Run A acceptance screenshot is committed at `docs/screenshots/run-a-acceptance-2026-05-17.png`.
- Run B overlay code compiles and runtime checks confirm click-through style plus global hotkey registration.
- Run B acceptance evidence is committed at `docs/run-b-acceptance-report-2026-05-17.md` with two visual screenshots.
- Run C local bridge endpoints respond in-process and `/screen-cue` moves the yellow ball after Broker `accept`.
- Run C popup-triggered acceptance is committed at `docs/run-c-completion-report-2026-05-17.md`.
- Run D outbound WebSocket bridge connects to a test Builder, receives a test cue, requires user approval, then renders the ball through the local Broker path.
- Run E mock provider wiring preserves the authority boundary: Vision hint is logged as semantic context, while Broker accept remains local-geometry based.
- Run E multi-provider Builder-proxy tests pass against a local Mock-Server; Vision-only remains `uncertain`, never `accept`.
- Run E real Builder-proxy smoke passes for gemini_flash_lite, gemini_flash, and grok_4_3 using semantic hints only.
- Run F mock LiveTalk path shows a half-duplex transcript and Maya response in the popup.
- Run F Windows audio probe records a local WAV and plays a SAPI response; real STT remains unverified.
- Run F desktop-side STT Builder proxy tests pass against a local mock server; real Soulmatch endpoint is pending.
- Run F live Builder-STT endpoint smoke passes with a synthetic SAPI WAV and returns transcript plus confidence.
- Run F2 desktop-side Builder-TTS proxy tests pass against a local mock server; live /api/goat/tts currently returns 404.
- Run F2 live Builder-TTS endpoint smoke passes and returns de-DE WAV audio.
- Run G1 action-gate tests pass and audit lineage is written for dry-run decisions.
- Run G2 Stage-1 executor tests pass and mock-backend audit lineage is written for executed scroll/hover plus blocked non-scope actions.
- Run G2 real desktop acceptance executed hover and scroll in a dedicated safe Tk window, with visually clean before/after screenshots.
- Run G3 Stage-2 text input tests pass and mock-backend audit lineage is written for preview, executed, and blocked paths.
- Run G3 real desktop acceptance entered one-line dummy text in a dedicated safe Tk field after preview approval, with visually clean before/after screenshots.
- Run G4 Stage-3 hard approval review tests pass; exact phrase approval reaches approved_not_executed, not OS execution.
- Run G5 action-classification matrix tests pass; audit payload records matched term and reason.
- Run G integration test passes across Stage 1, Stage 2, Stage 3 review, Stage 4 lock, and Unknown=Stage3.

## Not Yet Verified

- OCR defaults are not selected yet.
- Run F final live microphone acceptance with Builder STT+TTS is pending; latest full-path attempt recognized only "So".
- Stage 3 real OS-level action execution does not exist yet.
- Stage 4 remains a technical lock.

resolver_cache_health_2026_05_26:
"Lokale Bridge-Health und Screen-Smoke zeigen jetzt den read-only Resolver-Cache-Status fuer Taskleiste und Fensterliste: warm/stale, Elementzahl, age_ms und ttl_ms. Der Status waermt keine Caches an und startet keine UIA-/Win32-Scans. Live-Smoke nach Neustart: /healthz ok mit taskbar warm=true, elements=26 und windows warm=true, elements=6; /chat/screen-question 'Siehst du GOAT Desktop auf dem Bildschirm?' -> source_path=win32_window_cache, cache_hit=true, resolver time_ms=0.36, Antwort 'Gesehen: GOAT Desktop sichtbar. Quelle: Fensterliste.', providerCallsMade=false, desktopActionsExecuted=false. Tests gruen: 171 passed; compileall gruen."

resolver_cache_periodic_refresh_2026_05_26:
"GOAT waermt Taskleisten- und Fensterlisten-Resolver-Caches jetzt nicht nur beim Start, sondern periodisch read-only nach. Standardintervall: 60s, testbar/steuerbar ueber GOAT_RESOLVER_CACHE_REFRESH_MS mit 10s Untergrenze. Live-Smoke mit GOAT_RESOLVER_CACHE_REFRESH_MS=10000 nach Neustart und >12s Wartezeit: /healthz zeigte taskbar warm=true, elements=26, age_ms=6684.1 und windows warm=true, elements=7, age_ms=7235.86. Damit fallen lokale Screenfragen nach Leerlauf nicht direkt wieder in kalte UIA-/Win32-Scans. Tests gruen: 173 passed; compileall gruen."

resolver_cache_startup_state_2026_05_26:
"Resolver-Cache-Health unterscheidet jetzt cold, warming, warm, stale und failed pro Cache sowie ready/warming/partial/degraded/cold als Gesamtstatus. Direkt nach GOAT-Start sieht /healthz dadurch nicht mehr wie ein leerer Fehlerzustand aus, sondern meldet warming bis der read-only Warmup fertig ist. Live-Smoke nach Neustart: erster /healthz-State `warming` mit taskbar/windows `warming`; nach 8s `ready` mit taskbar warm elements=26 und windows warm elements=7; Screenfrage 'Siehst du GOAT Desktop auf dem Bildschirm?' -> win32_window_cache, cache_hit=true, resolver time_ms=0.25, keine Provider-/Desktop-Aktion. Tests gruen: 174 passed; compileall gruen."

user_friendly_screen_status_2026_05_26:
"Sichtbare Screen-UX weiter vereinfacht fuer Nutzer mit wenig PC-Kenntnis: Produkttexte vermeiden `UIA`, `Fensterliste`, `Vision gesehen` und technische Miss-Formulierungen. Statusanzeigen sagen jetzt z.B. `Bildschirm wird vorbereitet`, `Bildschirm bereit`, `Fenster gefunden`, `Desktop gefunden`, `Nicht gefunden`. /healthz enthaelt zusaetzlich `localScreen` mit ready/statusText/reason fuer einfache Diagnose. Live-Smoke nach Neustart: erster /healthz localScreen `Bildschirm wird vorbereitet`, nach 8s `Bildschirm bereit`; Screenfrage GOAT Desktop -> `Gesehen: GOAT Desktop sichtbar. Quelle: Fenster.`, Resolver win32_window_cache 0.12ms; Miss -> `Nicht gefunden... Quelle: Fenster.` Keine Provider-/Desktop-Aktion. Tests gruen: 175 passed; compileall gruen."

assistant_first_popup_ux_2026_05_26:
"Popup-Hauptpfad weiter auf Assistenz statt Debug getrimmt: Antwortbereiche sind als `Deine Frage` und `Maya` beschriftet, Starttext lautet `Bereit. Frag mich, was ich fuer dich finden soll.`, LiveTalk-Button heisst `Mit Maya sprechen`, Cue-Freigaben heissen `Ziel verwenden` / `Nein, anderes Ziel`. Laufende Statusmeldungen wurden vereinfacht (`Ich hoere zu`, `Ich denke nach`, `Ich schaue nach`, `Bitte pruefe das markierte Ziel`). Vision-/Debug-Panel bleibt versteckt; Qt-Test sichert Hauptlabels und LiveTalk-Sichtbarkeit. Live-Smoke: /healthz `Bildschirm bereit`, Screenfrage GOAT Desktop -> `Gesehen: GOAT Desktop sichtbar. Quelle: Fenster.`, win32_window_cache 0.1ms, keine Provider-/Desktop-Aktion. Tests gruen: 177 passed; compileall gruen."

action_preview_gate_ux_2026_05_26:
"Read-only Freigabe-Vorschau fuer kommende Maus-/Tastatursteuerung ergaenzt: neues Modul action_preview.py und Bridge-Endpunkt /action/preview erzeugen einfache Nutzertexte wie `GOAT kann dich navigieren`, `Freigabe fuer Eingabe`, `Wichtige Aktion braucht Freigabe` oder `Bitte selbst erledigen`. Preview loest keine Maus-/Tastatur-/Desktop-Aktion aus und liefert effects alle false. Gate-Logik verbessert: reine Navigation `hover/move/scroll` bleibt Stage 1 auch bei Zielnamen wie `Senden Button`; sensible Ziele wie `Passwortfeld` bleiben Stage 4 locked. Live-Smoke: /action/preview hover `Senden Button` -> Stage 1, mayExecute=false, keine Mouse/Keyboard-Aktion; hover `Passwortfeld` -> locked Stage 4. Tests gruen: 185 passed; compileall gruen."

stage1_navigation_bridge_gate_2026_05_26:
"Stage-1 Navigation ist jetzt live ueber die lokale Bridge angebunden, aber echte Mausbewegung verlangt explizit `user_approved=true`. /action/stage1 mit dry_run=false ohne Freigabe liefert `preview_required` und fuehrt nichts aus; Standard bleibt dry_run/read-only. Mit Freigabe darf nur Stage-1-Allowlist laufen: hover/move/scroll, kein Klick, kein Tippen. Live-Smoke nach Neustart: unapproved hover -> preview_required, executed=false, mouseActions=false; dry-run hover -> blocked, executed=false; approved hover auf harmlosen bbox -> executed=true, action_type=hover, target=(40,40), mouseActions=true, keyboardActions=false. Tests gruen: 187 passed; compileall gruen."

stage1_navigation_popup_ux_2026_05_26:
"Stage-1 Navigation ist jetzt in den Popup-Freigabepfad verdrahtet. Builder-/Cue-Nachrichten mit action_type hover/move/scroll zeigen zuerst `Ziel pruefen`; nach lokalem Broker-Accept zeigt GOAT die Vorschau `GOAT kann dich navigieren` mit Button `Navigieren`; erst danach ruft der Popup-Pfad /action/stage1 mit user_approved=true und dry_run=false auf. Erfolgreiche Navigation zeigt `Navigation ausgefuehrt`; Ablehnen setzt Ziel und Pending-Action zurueck. UI-Tests decken Zielpruefung, Navigationsvorschau, Abschluss und Ablehnung ab. Live-Smoke: /action/preview hover `Senden Button` -> `Navigieren`, mayExecute=false; /action/stage1 ohne Freigabe -> preview_required; mit Freigabe -> hover target=(50,50), mouseActions=true, keyboardActions=false. Tests gruen: 191 passed; compileall gruen."

stage1_scroll_popup_ux_2026_05_26:
"Stage-1 Scroll ist im gleichen Popup-Freigabepfad sauber ausgearbeitet. Action-Preview benennt die Richtung nutzerverstaendlich (`auf der Seite nach unten/oben scrollen`) und zeigt fuer Scroll den Button `Scrollen` statt generischem `Navigieren`. Bridge reicht scroll_amount in den Preview-Kontext durch; Popup nutzt scroll_amount ebenfalls fuer die Vorschau. UI-Tests decken Scroll-Cue -> Broker-Accept -> Scroll-Vorschau ab. Live-Smoke: /action/preview scroll amount=360 -> Button `Scrollen`, Text `nach oben scrollen`, mayExecute=false; /action/stage1 scroll ohne Freigabe -> preview_required; mit Freigabe -> executed=true, action_type=scroll, scroll_amount=120, mouseActions=true, keyboardActions=false. /healthz danach `Bildschirm bereit`. Tests gruen: 194 passed; compileall gruen."

stage2_text_preview_popup_ux_2026_05_26:
"Stage-2 Texteingabe ist in Preview/Bridge/Popup vorbereitet, ohne ungefragte echte Texteingabe. /action/stage2/text verlangt fuer echte Ausfuehrung weiterhin user_approved=true und safe_text_context=true; ohne Freigabe liefert die Bridge `preview_required`, ohne sicheren Kontext bleibt der Executor bei Preview. Popup-Cue-Pfad erkennt action_type type/text/input, zeigt erst `Ziel pruefen`, danach `Freigabe fuer Eingabe` mit Button `Eingabe ausfuehren`; der Button bleibt deaktiviert, wenn safe_text_context fehlt. UI-Tests decken Stage-2 Cue, Preview, fehlenden Safe-Kontext und Abschluss ab. Live-Smoke ohne reale Texteingabe: /action/preview type Suchfeld StepStack -> `Freigabe fuer Eingabe`, Button `Eingabe ausfuehren`, mayExecute=false; /action/stage2/text ohne Freigabe -> preview_required, keyboardActions=false; mit Freigabe aber safe_text_context=false -> preview, executed=false, keyboardActions=false. Tests gruen: 201 passed; compileall gruen."

stage2_text_input_plain_ux_2026_05_26:
"Stage-2 Texteingabe ist fuer normale Nutzer klarer formuliert. Popup zeigt bei Textaktionen `Eingabefeld: ...` und `Bitte pruefe das Eingabefeld` statt generischem Zieltext. Wenn safe_text_context fehlt, bleibt der Ausfuehren-Button deaktiviert und heisst `Nicht sicher`; Maya erklaert kurz: `Ich tippe hier noch nicht. Ich habe das Eingabefeld nicht sicher genug erkannt.` Interne technische Gruende wie `safe_text_context` werden beim Abschluss in nutzerverstaendliche Hinweise uebersetzt. Keine neue Aktionserlaubnis eingefuehrt. Tests gruen: 202 passed; compileall gruen."

action_execution_failure_guard_2026_05_26:
"Stage-1 Mausnavigation und Stage-2 Texteingabe melden Backend-/OS-Fehler nicht mehr als erledigt. Executor fangen Backend-Exceptions ab, auditieren `failed` mit `executed=false` und geben keine rohen Stacktraces in die Haupt-UX. Popup uebersetzt solche Fehler zu `Die Navigation hat nicht geklappt. Ich melde sie nicht als erledigt.` bzw. `Die Eingabe hat nicht geklappt. Ich melde sie nicht als erledigt.` Lokale Action-HTTP-Calls im Tray haben nun 2s Timeout statt 5s, damit die UI bei lokalen Fehlern schneller frei wird. Keine neue Aktionserlaubnis eingefuehrt. Tests gruen: 207 passed; compileall gruen."

action_post_execution_verification_2026_05_26:
"Stage-1 Hover/Move und Stage-2 Texteingabe haben jetzt eine leichte Nachpruefung. Stage-1 prueft nach Mausbewegung, wenn das Backend es kann, ob der Cursor am Zielzentrum angekommen ist; Fehlschlag wird als `failed` mit `executed=false` auditiert. Stage-2 unterstuetzt einen optionalen `typed_text_matches`-Verifier; wenn die Verifikation fehlschlaegt, meldet GOAT nicht erledigt. Popup uebersetzt Verifikationsfehler in normale Sprache: `Ich bin nicht sicher, ob ... angekommen ist. Ich melde sie nicht als erledigt.` Keine Provider-Calls, keine Vision-Runde, keine neue Aktionserlaubnis. Tests gruen: 211 passed; compileall gruen."

action_result_plain_next_step_2026_05_26:
"Popup-Ergebnisanzeige nach lokalen Aktionen ist normalnutzerfreundlicher. Nach Stage-1 Hover/Move sagt GOAT konkret `Ich habe den Mauszeiger zum Ziel bewegt...`; nach Scroll nennt GOAT die Richtung und fordert den naechsten Schritt an. Nach Stage-2 Texteingabe nennt GOAT das Eingabefeld und bittet um kurze Sichtpruefung. Fehler-/Nicht-erledigt-Texte bleiben unveraendert sicher. Keine neue Aktionserlaubnis, keine Provider-Calls. Tests gruen: 212 passed; compileall gruen."

plain_approval_buttons_2026_05_26:
"Sichtbarer Freigabepfad nutzt jetzt einfache Buttontexte: `Pruefen`, `Ausfuehren`, `Abbrechen`. Alte Hauptpfad-Begriffe wie `Ziel verwenden`, `Ziel pruefen` und `Nein, anderes Ziel` sind aus Popup/Tray entfernt. Abbruchstatus heisst `Abgebrochen`. Action-Logik und Sicherheitsgates unveraendert; keine neue Aktionserlaubnis. Tests gruen: 212 passed; compileall gruen."

plain_main_status_chips_2026_05_27:
"Sichtbare Hauptstatus-Chips sind normalnutzerfreundlicher. Statt `Verbindung: ...` und `Audio: ...` zeigt das Popup jetzt `Status: Bereit/Verbunden/Verbinde neu` und `Sprache: Bereit/Arbeitet/Fertig/Problem`. Interne Detailwerte bleiben fuer Code/Diagnose erhalten, werden aber im Hauptpfad nicht roh angezeigt. Action-Logik unveraendert; keine neue Aktionserlaubnis. Tests gruen: 214 passed; compileall gruen."

single_instance_bridge_guard_2026_05_27:
"GOAT erkennt jetzt beim Start, wenn der lokale Bridge-Port 127.0.0.1:8765 bereits belegt ist. LocalBridge startet dann keinen zweiten Bridge-Server, gibt `port_in_use` zurueck und das Popup zeigt normalnutzerfreundlich `GOAT ist bereits offen` / `Bitte nutze das vorhandene GOAT-Fenster. Diese Instanz fuehrt nichts aus.` Status-Chip: `Status: Schon offen`. Live-Smoke: zweite gestartete Instanz hat den Listener nicht uebernommen (`listenerUnchanged=true`), /healthz der ersten Instanz blieb ok. Keine neue Aktionserlaubnis. Tests gruen: 216 passed; compileall gruen."

dpi_aware_stage1_smoke_2026_05_27:
"GOAT setzt beim Start DPI-Awareness vor QApplication, damit Stage-1 Mauskoordinaten unter Windows-Skalierung stabiler sind. Live-Smoke nach Neustart: /healthz ok, `Bildschirm bereit`, Preview Hover read-only (`mayExecute=false`, mouse=false, keyboard=false), Stage-1 Hover ohne Freigabe -> `preview_required`, executed=false, Stage-1 Hover mit Freigabe auf aktuelle Mausposition -> `executed=true`, mouse=true, keyboard=false, target x=431/y=688. Externe DPI-aware Nachmessung nach 100ms: x=431/y=688, Delta 0/0. Kein Klick, kein Tippen, keine Screenshot-/Audio-Artefakte. Tests gruen: 218 passed; compileall gruen."
