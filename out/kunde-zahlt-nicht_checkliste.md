# Checkliste: Viel verkauft, kein Geld

Legende: [x] erfüllt (mit Beleg) · [~] teilweise / Abweichung (Begründung) · [ ] nicht erfüllt

## Schritt 0 – Bestand
- [x] git pull, Überblick engine/, episodes/, out/ – Beleg: Stand `ea9021f`, letzte Folge `folge-03-website`
- [x] nichts in engine/, episodes/, out/*.mp4, out/cache/ gelöscht – Beleg: `git log --stat` (nur Ergänzungen; `sets.py` war schon früher in `build_world.py` umbenannt)
- [~] ElevenLabs geprüft – `GET /v1/models` antwortet (11 Modelle). `ELEVENLABS_API_KEY` ist nicht als Variable gesetzt, der Key wird vom Proxy eingesetzt. Kontingent erschöpft (9.988/10.000 Zeichen, Reset 13.12.2026, nötig ≥ 755). Auf Anweisung ohne ElevenLabs mit Piper weitergearbeitet.
- [x] Checkliste angelegt – diese Datei

## Schritt 1 – Ergänzen
- [x] Neue Requisiten in engine/props.py – `moth`, `invoice` (+ Stempel), `coin_small`/`coin_stack`, `konto_glas` + `glas_level`, `calendar_sheet`, `stopwatch`, `envelope_mail`, `muehlrad_zettel`, dazu `vitrine`, Partikel `crumb`/`pix`/`sweat`/`flourdust` – Beleg: `out/kunde-zahlt-nicht_figuren.png`
- [x] Vorhandenes wiederverwendet – Kalle/Byte, Sets, Licht, Kamera-Rig, Mehlsack, Konfetti, Partikel, Overlays, Sounds, Pipeline
- [x] Neue Beat-Aktionen ergänzt, nichts Altes ersetzt – Regie `engine/choreo/kunde_zahlt_nicht.py`; neue Figurenmerkmale nur über `extras` (ältere Folgen unverändert). Hinweis: Die Engine heißt `anim.py` (kein `animate.py`).
- [x] Rückwärts-Check – `folge-02-drei-helfer.json` und `folge-03-website.json` laden; Szenenaufbau ohne Rendern: „BACKCHECK OK drei-helfer 882 Frames“, „BACKCHECK OK website 1368 Frames“
- [~] Gleiche Render-Engine (Workbench) wie letzte Folge, 10 Testframes: 12,5 s/Frame → ~100 min bei 100 %. Vereinfacht wie bisher über Render-Auflösung (70 %, hochskaliert), Figuren/Design/Animation unverändert. Tatsächlich: 3D 49,6 min, gesamt 51,8 min ✓ < 60 min
- [x] Feste Seeds, Motion Blur an – alle Partikel mit Seed; Motion Blur: 2 Unterbilder je Frame (Workbench hat kein eigenes Motion Blur)

## Schritt 2/3 – Stimmen
- [~] Gleiches Modell und gleiche Stimmen wie bisher – nicht möglich (ElevenLabs-Kontingent). Piper: Kalle = Thorsten (high/emotional), Byte = Kerstin. Siehe Stimmen-Check.
- [x] Eingabe "tts", Untertitel "text", "stimmung" steuert Einstellungen – `voices.json` → `piper.stimmungen`
- [x] Audio-Tags nur, wenn unterstützt – Piper unterstützt keine; `[laughs]` (Szene 12) vor der Synthese entfernt
- [x] Hook: 3 Takes, bester gewählt, Beginn bei 0,00 s – Take 3 (bestanden, höchste Energie −13,7 dB); Stimme hörbar ab 0,002 s
- [x] Stille > 0,08 s abgeschnitten, Szenenlänge = Audio + 0,25 s – `tts._trim_and_compress`, `render.build_timeline`
- [x] Cache in out/cache/ – Hash aus tts, Stimme, Modell, Einstellungen; verwendete Zeilen committet
- [x] Whisper ≤ 10 % WER, Zahlen und "Liquidität" exakt – alle 13 Zeilen (max. 8 %), alle Zahlen ✓, „Liquidität“ ✓
- [x] Tempo 2,0–2,8 W/s (Hook bis 3,0) – 2,00–2,78; Hook 2,75
- [x] Tonhöhe abwechslungsreich, Byte klar anders – Streuung 2,0–3,7 Halbtöne; Median Kalle 121 Hz, Byte 163 Hz (5,1 Halbtöne, zudem männlich/weiblich)
- [x] Kein Übersteuern, nichts abgeschnitten, keine Pause > 0,4 s – Peak 0,89, längste Pause 0,26 s
- [~] UTMOS – nicht installiert/ladbar (Modell liegt auf GitHub, Zugriff blockiert)
- [x] Bericht – `out/kunde-zahlt-nicht_stimmen-check.md`

## Schritt 4 – Timing, Overlays, Ton
- [x] Lippensync aus Zeitstempeln (Whisper-Wortzeiten + Lautstärke-Hüllkurve), Byte-Pixelbalken nach Lautstärke
- [x] Beat-Aktion 3 Frames vor dem Wort, Sound exakt auf dem Wort – `out/kunde-zahlt-nicht_timing.md`
- [x] Untertitel 2–4 Wörter, Highlight #FFE14D, y 1250–1450 (Mitte 1330), nie über einem Gesicht – Prüf-Frames
- [x] Hook-Karte ab Frame 1, y 230–520, „Kein Geld“ #FFE14D, sichtbar bis 1,87 s – `qa/0.0s.png`, `qa/1.5s.png`
- [x] Kapitel-Banner mit Fortschritt, Kapitel-Leiste ✓/aktiv/grau, bei kapitel null kein Banner – `qa/s4.png`, `qa/s6.png`, `qa/s10.png`, `qa/s11.png`
- [~] Screen-Zahlen ≥ 90 px, ease-out hochzählend – Zahlen mit großer Schrift (Studio/Büro ≈ 100–150 px Schriftgröße im Bild), zählen hoch; während des Zählens durch Motion Blur kurz verschmiert
- [x] Safe Zone oben 220, rechts 160, unten 420 px – Prüf-Frames
- [x] Soundeffekte 6 dB unter Sprache (Effekt-Spitze = halbe Sprach-Spitze), keine Musik – `engine/sfx.py`
- [x] Audio loudnorm I=-14, TP=-1,5, AAC 160 kbit/s, 48 kHz – gemessen −13,9 LUFS, Peak −2,7 dBFS
- [x] Video 1080x1920, 30 fps, libx264 high, yuv420p, crf 20, veryfast, faststart, < 50 MB – 28,0 MB
- [x] `out/kunde-zahlt-nicht_timing.md`

## Schritt 5 – Abnahme
- [x] Stufe A – `out/kunde-zahlt-nicht_figuren.png` (Kernmerkmale ergänzt/geprüft)
- [~] Stufe B – Endstand 8/8/7/8/7/7/8/8 (3 Runden ausgeschöpft; Details im Design-Check)
- [x] Stufe C – `out/kunde-zahlt-nicht_bewegung.png`
- [x] Stufe D a) 1080x1920, 30 fps, h264, yuv420p, aac, 48,03 s
- [x] Stufe D b) Hook lesbar, Bewegung im ersten Frame, Stimme ab 0,0 s
- [x] Stufe D c) Prüf-Frames und letztes Frame
- [x] Stufe D d) Loop-Test (3D-Abweichung 4,7)
- [x] Stufe D e) 6 verteilte Frames ohne Clipping/leere Hintergründe/Ruckler
- [x] `out/kunde-zahlt-nicht_design-check.md`

## Schritt 6 – Abschluss
- [x] Commit und Push auf main (ohne Key)
