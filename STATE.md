# STATE

last_verified_against_code: 2026-05-16

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
