# Checkliste: Viel verkauft, kein Geld

Stand: angelegt in Schritt 0, wird am Ende mit Belegen abgehakt.

## Schritt 0 – Bestand
- [ ] git pull, Überblick engine/, episodes/, out/
- [ ] nichts in engine/, episodes/, out/*.mp4, out/cache/ gelöscht
- [ ] ElevenLabs geprüft (Key, GET /v1/models)
- [ ] Checkliste angelegt

## Schritt 1 – Ergänzen
- [ ] Neue Requisiten in engine/props.py (Motte, Rechnungsblatt + Stempel, Münze/Münzsäule, Kontoglas, Kalenderblatt, Stoppuhr, Briefumschlag, Mühlrad-Zettel)
- [ ] Vorhandenes wiederverwendet (Mehlsack, Konfetti, Partikel, Figuren, Sets, Licht)
- [ ] Neue Beat-Aktionen ergänzt, nichts Altes ersetzt
- [ ] Rückwärts-Check ältere Episoden (Parse + Szenenaufbau)
- [ ] Gleiche Render-Engine/Einstellungen wie letzte Folge, 10 Testframes, Hochrechnung < 60 min
- [ ] Feste Seeds, Motion Blur an

## Schritt 2/3 – Stimmen
- [ ] Gleiches Modell und gleiche Stimmen wie bisher
- [ ] Eingabe "tts", Untertitel "text", "stimmung" steuert Einstellungen
- [ ] Audio-Tags nur, wenn unterstützt
- [ ] Hook: 3 Takes, bester gewählt, Beginn bei 0,00 s
- [ ] Stille > 0,08 s abgeschnitten, Szenenlänge = Audio + 0,25 s
- [ ] Cache in out/cache/
- [ ] Whisper ≤ 10 % WER, Zahlen und "Liquidität" exakt
- [ ] Tempo 2,0–2,8 W/s (Hook bis 3,0)
- [ ] Tonhöhe abwechslungsreich, Byte klar anders als Kalle
- [ ] Kein Übersteuern, nichts abgeschnitten, keine Pause > 0,4 s
- [ ] UTMOS (falls installiert) ≥ 3,5
- [ ] Bericht out/kunde-zahlt-nicht_stimmen-check.md

## Schritt 4 – Timing, Overlays, Ton
- [ ] Lippensync aus Zeitstempeln, Byte-Pixelbalken nach Lautstärke
- [ ] Beat-Aktion 3 Frames vor dem Wort, Sound exakt auf dem Wort
- [ ] Untertitel 2–4 Wörter, Highlight #FFE14D, y 1250–1450, nie über einem Gesicht
- [ ] Hook-Karte ab Frame 1, y 230–520, "Kein Geld" #FFE14D, ≥ 1,5 s
- [ ] Kapitel-Banner mit Fortschritt, Kapitel-Leiste ✓/aktiv/grau, bei kapitel null kein Banner
- [ ] Screen-Zahlen ≥ 90 px, ease-out hochzählend
- [ ] Safe Zone oben 220, rechts 160, unten 420 px
- [ ] Soundeffekte 6 dB unter Sprache, keine Musik
- [ ] Audio loudnorm I=-14, TP=-1,5, AAC 160 kbit/s, 48 kHz
- [ ] Video 1080x1920, 30 fps, libx264 high, yuv420p, crf 20, veryfast, faststart, < 50 MB
- [ ] out/kunde-zahlt-nicht_timing.md

## Schritt 5 – Abnahme
- [ ] Stufe A: Kontaktbogen Figuren + Requisiten, Kernmerkmale geprüft
- [ ] Stufe B: Style-Frames bewertet (≥ 8)
- [ ] Stufe C: Bewegungs-Kontaktbögen Szenen 1, 2, 4, 6, 8, 10, 11, 13
- [ ] Stufe D a) ffprobe-Werte, Dauer 35–50 s
- [ ] Stufe D b) 0,0 / 0,5 / 1,5 s: Hook lesbar, Bewegung, Stimme ab 0,0 s
- [ ] Stufe D c) Prüf-Frames und letztes Frame
- [ ] Stufe D d) Loop-Test
- [ ] Stufe D e) 6 Frames auf Clipping, leere Hintergründe, Ruckler
- [ ] Design-Check out/kunde-zahlt-nicht_design-check.md

## Schritt 6 – Abschluss
- [ ] Commit und Push auf main (ohne Key)
