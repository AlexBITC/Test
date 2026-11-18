# KI-Staunen Video-Engine

Blender-basierte Engine (headless, Python/bpy) für vertikale TikTok-Kurzvideos (1080×1920, 30 fps) mit
Kalle (Bäckermeister) und Byte (KI-Kugel). Stimmen kommen von ElevenLabs (`eleven_multilingual_v2`),
Fallback Piper.

```bash
npm run render -- episodes/folge-03-website.json
```

Ergebnis: `out/folge-03-website.mp4`, Stimmen-Bericht `out/website_stimmen-check.md`.

Stufen: `--stage voices | style --frames 37,573 | contact | final` (Standard: alles).
`--clean` verwirft gerenderte Frames nach Änderungen an der Engine.

## Echte Website als Grundlage
`website/index.html` ist eine echte, eigenständige Seite (HTML + CSS + JS, mobile-first) für die erfundene
„Bäckerei Kalle“. Alles, was im Video als Code, Zeilenzahl oder Website erscheint, kommt von dort:

| Schritt | Werkzeug | Ergebnis |
|---|---|---|
| Zeilenzahl | `wc -l` | `website/meta.json` (`zeilen`) |
| Screenshots, Gerüst-Zustand, Abschnitte, Formular-Sequenz, Formular-Test | `node website/capture.js` (Playwright) | `website/shots/` |
| Code-Texturen mit Syntax-Highlighting (JetBrains Mono, OFL) | `python3 -m engine.codetex` | `website/shots/code/` |
| Geräte-Displays, leerer Browser | `python3 -m engine.textures` | `website/shots/geraete/` |

Die Render-Pipeline führt diese Schritte automatisch als Stufe 0 aus.

## Render-Engine
Zuerst Eevee: 10 Frames werden gerendert und die Gesamtzeit hochgerechnet (`out/work/<slug>/engine.json`).
Über 30 Minuten → Workbench (Flat Lighting, Objektfarben/Texturen, Kavität). Läuft Eevee nicht, wird Cycles
(CPU, 16 Samples, Denoiser) geprüft. `RENDER_ENGINE=eevee|cycles|workbench` erzwingt eine Engine.

## Voraussetzungen
- Blender 5.2 LTS im `PATH` (oder `BLENDER=/pfad/zu/blender`); headless ohne GPU über Mesa (`libegl1`, `EGL_PLATFORM=surfaceless`)
- ffmpeg mit `rubberband`-Filter, Node mit Playwright (Chromium)
- Python 3 mit `faster-whisper numpy soundfile librosa pillow scipy` (optional `piper-tts` für den Fallback)
- `ELEVENLABS_API_KEY` (nur aus der Umgebung gelesen); optional `ELEVENLABS_VOICE_KALLE`, `ELEVENLABS_VOICE_BYTE`

## Aufbau
| Datei | Aufgabe |
|---|---|
| `engine/render.py` | Pipeline: Website → Stimmen → Stimmen-Check → Timeline → Screen-Texturen → Engine-Wahl → Blender → Overlays → Mix → Encoding |
| `engine/build_world.py` | Sets (theke, buero, studio), Kamera-Rig, Welt-Aufbau |
| `engine/characters.py` | Kalle, Byte (inkl. Code-Gesicht), Idle, Lippensynchron, Reaktionen (neutral, zweifel, staunen, schock, jubel) |
| `engine/props.py` | Requisiten und Effekte (Bestellzettel, Rezeptkarte, Code-Platten, Code-Turm, Teigschüssel, Website-Ebene, Farbwelle, Gebäck, Geräte, Finger, Mini-Laden, Kunden, Münzsäule, Konfetti/Mehl) |
| `engine/tts.py` / `engine/voicecheck.py` | ElevenLabs `with-timestamps` (Fallback Piper), Whisper-Stimmen-Check |
| `engine/scene.py` | Blender-Einstieg: Render-Engine, Rendern, Anker-Export |
| `engine/choreo/<slug>.py` | Regie pro Episode |
| `engine/overlays.py`, `engine/timing.py` | 2D-Ebene (Hook, Kapitel-Banner, Kapitel-Leiste, Begriff, Benachrichtigung, Untertitel), Screen-Texturen |
| `engine/sfx.py` / `engine/composite.py` | Soundeffekte aus ffmpeg (Sinus/Rauschen), loudnorm-Mix; Compositing und Encoding |

Schriften: Lilita One und JetBrains Mono (SIL Open Font License, `engine/fonts/`).
