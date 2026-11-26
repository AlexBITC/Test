# KI-Staunen Video-Engine

Blender-basierte Engine (headless, Python) für vertikale TikTok-Kurzvideos (1080×1920, 30 fps) mit
Kalle (Bäckermeister) und Byte (KI-Kugel). Stimmen kommen von ElevenLabs.

```bash
npm run render -- episodes/folge-02-drei-helfer.json
```

Stufen: `--stage voices | style --frames 37,573 | contact | final` (Standard: alles).
`--clean` verwirft gerenderte Frames nach Änderungen an der Engine.

## Voraussetzungen
- Blender 5.x im `PATH` (oder `BLENDER=/pfad/zu/blender`), ffmpeg mit `rubberband`-Filter
- Python 3 mit `faster-whisper numpy soundfile librosa pillow scipy`
- `ELEVENLABS_API_KEY` (wird nur aus der Umgebung gelesen); optional `ELEVENLABS_VOICE_KALLE`, `ELEVENLABS_VOICE_BYTE`

## Aufbau
| Datei | Aufgabe |
|---|---|
| `engine/render.py` | Pipeline: Stimmen → Stimmen-Check → Timeline (Beats) → Screen-Texturen → Blender → Overlays → Mix → Encoding |
| `engine/tts.py` | ElevenLabs `with-timestamps`, Zahlen ausschreiben, Cache in `out/cache/` |
| `engine/voicecheck.py` | Whisper-Rücktranskription, WER, Zahlen/Begriff exakt, Tempo, Tonhöhe, Clipping, Pausen |
| `engine/scene.py` | baut die Blender-Szene, Kamera-Rig, Bake, Culling, Rendern, Anker-Export |
| `engine/characters.py` | Kalle, Byte, Helfer-Bytes, Idle, Lippensynchron, Reaktionen, Posen |
| `engine/sets.py` / `engine/props.py` | Sets (theke, buero, studio), Requisiten und Partikel |
| `engine/anim.py` | Easing, Federn, Rauschen mit Seed, Layer-Bake in Keyframes, nahtloser Loop |
| `engine/choreo/` | Regie pro Episode (`<slug>.py`), sonst `generic.py` |
| `engine/overlays.py` | 2D-Ebene (Hook, Kapitel-Banner, Kapitel-Leiste, Begriff-Karte, Untertitel, Screen-Texturen) |
| `engine/sfx.py` / `engine/composite.py` | Soundeffekte aus ffmpeg, Mix mit loudnorm; Compositing und Encoding |

Beats: In `visual` steht `Beat bei 'Wort'`; die Aktion startet 3 Frames vor dem Wort-Zeitstempel.
Schrift: Lilita One (SIL Open Font License, `engine/fonts/OFL.txt`).

## Motivationsvideo „Don't put off until tomorrow“ (`motivation/`)

Eigenständige Pipeline für ein englisches TikTok-Video (1080×1920, 30 fps, 35,3 s, nahtloser Loop):
Neon-Linien auf Schwarz, Bloom, goldene Akzente (#F5C451), abstrakte Low-Poly-Figur ohne Gesicht.

```bash
python3 -m motivation.make                 # alles
python3 -m motivation.make --from audio    # ab einer Stufe
```

| Datei | Aufgabe |
|---|---|
| `motivation/script.json` | Skript (10 Sätze, wörtlich), Stimmung pro Satz, Stimme + Einstellungen |
| `motivation/voice.py` | ElevenLabs `eleven_multilingual_v2`, Satz für Satz, je 3 Takes; Whisper-Prüfung (Wörter + Satzmelodie), Auswahl |
| `motivation/timeline.py` | saubere Schnitte, Pausen nach hörbaren Grenzen, Wortzeiten |
| `motivation/scene.py` | Blender-Szene (Cycles CPU, headless): Kalender, TOMORROW zerbricht, Berg, Weg, Sanduhr, Lauf + Lichtexplosion |
| `motivation/audio.py` | selbst synthetisierte Musik + Soundeffekte, Ducking, Stimme −16 LUFS, Endmix −14 LUFS, True Peak < −1 dBTP |
| `motivation/post.py` | Staub, Bokeh, Schlagzeilen, wortgenaue Untertitel, Lichtblitz, H.264/AAC |
| `motivation/cover.py`, `motivation/qa.py` | Cover-Bild; Prüfung (Format, Lautheit, leere Frames, Loop-Naht, Kontaktbögen, Whisper) |

Stimme: „Fernanda – Calm Storytelling“ (Voice Library), Voice-ID `hnFidmF05jrIKH0LAjEc`,
stability 0.40, similarity_boost 0.80, style 0.30, Speaker Boost an. Der API-Schlüssel wird nur aus
`ELEVENLABS_API_KEY` gelesen (fehlt er, ersetzt ein authentifizierender Proxy den Platzhalter).
Schriften: Anton (OFL, `motivation/fonts/OFL-Anton.txt`), Inter (OFL, `motivation/fonts/LICENSE-Inter.txt`).
