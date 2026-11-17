# KI-Staunen Video-Engine

Vertikale TikTok-Kurzvideos (1080×1920, 30 fps) mit Kalle (Bäckermeister) und Byte (KI-Kugel).

**Prinzip:** Blender rendert die Figuren und Sets **einmal** als Asset-Bibliothek. Jede Episode wird danach
in 2D zusammengesetzt (`engine/compose.py`) – ohne Blender, in Minuten statt Stunden. Fertige Szenen und
Stimmen landen nach Text-Hash im Cache; eine geänderte Zeile rendert nur ihre Szene neu.

```bash
./setup.sh                                          # Blender, ffmpeg, rubberband, Python-Pakete, Piper-Stimmen
npm run assets                                      # einmalig: Clips + Sets rendern (~1–2 h auf 4 CPU-Kernen)
npm run compose -- episodes/folge-02-drei-helfer.json            # Episode -> out/folge-02-drei-helfer.mp4
npm run compose -- episodes/… --stills 0,150,300                 # nur Kontroll-Standbilder
npm run compose -- episodes/… --tts piper                        # Stimmen offline (ohne ElevenLabs)
```

## Aufbau

```
setup.sh                 installiert Blender 5.1, ffmpeg, rubberband-cli, Python-Pakete, Piper-Stimmen
.claude/settings.json    SessionStart-Hook: startet setup.sh in jeder Cloud-Sitzung
assets/clips/            Kalle: neutral, zweifel, staunen, schock, jubel   (in + loop, 2,5 s loopbar)
                         Byte:  schweben, sprechen                       (loop, gleiche Schwebe-Bewegung)
                         kalle_*/mund_{zu,halb,auf}/  Mund-Ausschnitte für Lippensynchron
assets/sets/             theke, buero, studio: bg.webp (Hintergrund), fg.webp (Theke/Tisch davor), meta.json
assets/manifest.json     Asset-Version (geht in den Szenen-Hash ein)
engine/compose.py        setzt Clips, Kamera, Zahlen, Texte zusammen
cache/voices/            Stimmen nach Text-Hash (nicht im Git)
cache/scenes/            fertige Szenen als MP4 nach Szenen-Hash (nicht im Git)
```

| Datei | Aufgabe |
|---|---|
| `engine/build_assets.py` | startet Blender je Asset (parallel), wandelt PNG → WebP, schreibt `assets/manifest.json` |
| `engine/assets_blender.py` | Blender-Seite: Figur im Ursprung, kanonische Kamera (440 px/m), Loop-Schluss, Mund-Ausschnitte per Border-Render; Plates mit 1,5× Overscan, Anker (Fußpunkt, px/m), Screen-Ecken |
| `engine/compose.py` | Timeline aus Wort-Zeitstempeln, 2D-Kamera, Figuren-Zustände, Lippensynchron, Screen-Inhalt, Zahlen-Pop, Overlays, Szenen-Cache, Ton-Mix, Encoding |
| `engine/voice.py` | ElevenLabs (Standard) oder Piper (offline), Tempo/Tonhöhe per rubberband, Cache nach Hash |
| `engine/overlays.py` | Hook, Kapitel-Banner/-Leiste, Begriff-Karte, Untertitel, Studio-Screen-Inhalte |
| `engine/composite.py`, `engine/sfx.py` | Whip-Unschärfe, Vignette, Korn; Soundeffekte und Mix (loudnorm −14 LUFS) |
| `engine/render.py`, `engine/scene.py`, `engine/choreo/` | alte Voll-3D-Pipeline pro Episode (Requisiten-Choreografie), weiter nutzbar: `npm run render` |

## Wie compose eine Szene baut
1. **Stimme** → Wort-Zeitstempel (ElevenLabs liefert sie; bei Piper anteilig geschätzt).
2. **Kalle-Zustand:** Szene beginnt in der Reaktion der Vorszene; 6 Frames vor dem ersten Highlight-Wort
   startet der `in`-Teil der neuen Reaktion (Akzent liegt auf dem Wort), danach der Loop. 4 Frames Überblendung.
3. **Lippensynchron:** spricht Kalle, wird pro Frame der Mund-Ausschnitt zu/halb/auf nach Lautstärke eingesetzt
   (weiche Kante). Byte wechselt zwischen `schweben` und `sprechen` – beide Clips haben dieselbe Schwebebahn.
4. **Kamera:** Push-in 1,18 → 1,32 pro Szene, Handheld-Drift, Punch-in 4 % auf Highlights, Whip-Pan bei Set-Wechsel.
5. **Ebenen:** Plate-Hintergrund → Studio-Screen (perspektivisch eingesetzt) → Kalle (+ Schatten) → Vordergrund → Byte
   → Vignette/Korn → Zahlen-Pop über Byte (außerhalb des Studios) → Overlays.

Episoden-JSON wie bisher (`sprecher`, `text`, `highlight`, `reaktion`, `set`, `kapitel`, `visual`).
`Beat bei '…'` aus `visual` steuert die Screen-Inhalte; die übrige `visual`-Choreografie
(Requisiten wie Mehlsäcke, Münzen, Helfer) setzt nur die alte 3D-Pipeline um.

## Voraussetzungen
- Linux x64, ~3 GB Platz. `setup.sh` installiert alles (Root nötig für apt und `/opt`).
- `ELEVENLABS_API_KEY` aus der Umgebung (in der Claude-Cloud ergänzt der Proxy ihn). Ohne Kontingent
  fällt `--tts auto` für die ganze Episode auf Piper zurück (keine gemischten Stimmen).
- Schrift: Lilita One (SIL Open Font License, `engine/fonts/OFL.txt`).
