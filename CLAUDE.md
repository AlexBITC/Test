# KI-Staunen Video-Engine – Hinweise für Claude

Blender-Engine (headless) für vertikale Kurzvideos (1080×1920, 30 fps) mit Kalle (Bäckermeister) und
Byte (KI-Kugel). Überblick, Voraussetzungen und Aufbau: `README.md`.

## Befehle
```bash
npm run preview -- episodes/<datei>.json --clean   # Kontaktbögen je Szene (out/work/<slug>/kontakt_szene*.png)
npm run final -- episodes/<datei>.json --clean     # komplettes Video nach out/<datei>.mp4
```
Bisher verwendete Umgebung für Final-Renders: `RENDER_ENGINE=workbench MB_SUBFRAMES=2 RENDER_SCALE=0.7 RENDER_WORKERS=3`.

## Regeln
- ElevenLabs-Key nur aus der Umgebung, nie in Code, JSON, Logs oder Commits.
- Verwendete Sprachdateien liegen in `out/cache/` (gitignored) und werden mit `git add -f` committet.
- Episoden-JSON in `episodes/`, Regie-Zusätze (Stimme, Pausen, Hook-Karte) in `episodes/<datei>.regie.json`.

## Folgenspezifische Assets
- Requisiten: `assets/props/<slug>.py` (Übersicht in `assets/manifest.json`), Import in der Regie über `sys.path`.
- Bildschirm-Inhalte: `assets/screens/<slug>.py` mit `frame(tl, szene, f)`; `engine/overlays.screen_frame` lädt die Datei
  automatisch. Die Bildfolge liegt auf dem Studio-Screen; die Regie kann sie per UV auch auf ein Laptop-Display legen
  (siehe `laptop_display` in `engine/choreo/viral.py`).

## Engine-Version
Die aktuelle Version steht in `engine/VERSION`.

### 2.1 – Byte-Upgrade (nur Byte geändert)
Byte bekommt mehr Details, Form, Farbe, Größe und Antenne bleiben gleich. Alle Änderungen liegen in
`engine/characters.py` (Klasse `Byte`, Funktionen `byte_*`, `antenna_spring`). Die Helfer-Bytes aus
„Drei Helfer“ bleiben unverändert (`Helper` nutzt `v21=False`).

| Merkmal | Umsetzung |
|---|---|
| Display-Gesicht | Augen als glatte Leuchtformen statt Pixel, Glasreflex oben links, leuchtender Innenrand |
| Augen je Reaktion | `neutral` rund, `jubel` Halbmonde, `staunen` groß mit Glanzpunkt, `schock` Zickzack, `zweifel` schräg (halb geschlossen), dazu `wink` |
| Alte Ausdrucksnamen | `byte_face` setzt sie um: happy → jubel, surprised/curious → staunen, worried → schock, serious → zweifel |
| Nahtlinien | feine leuchtende Linien entlang der Kanten der Hülle (nicht auf der Vorderseite) |
| Lüftungsgitter | kleine Platte mit vier Lamellen oben seitlich |
| Status-LED | grüne LED auf der Brust; atmet im Ruhezustand, pulsiert beim Sprechen mit der Lautstärke (`byte_speak`) |
| Antenne | zwei Glieder; die leuchtende Spitze (mit Halo) schwingt verzögert nach (`antenna_spring`) |
| Arme mit Händen | `byte_arm` (Armhaltung), `byte_hand` (`rest`, `offen`, `point`, `grab`, `snap`), `byte_snap` (Schnippen), `byte_type` (Tippen); Ruhehaltung pendelt leicht |
| Schwebe-Effekt mit Schatten | `byte_shadow` (aus `byte_idle`): Scheibe auf der Fläche unter Byte (Raycast gegen die statische Szene), kleiner, je höher Byte schwebt |

Bestehende Regie-Dateien müssen nicht angepasst werden: `byte_idle`, `antenna_spring`, `byte_speak` und
`byte_face` bringen die neuen Merkmale automatisch mit.
