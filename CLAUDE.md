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

### Erlaubte Werte im Episoden-JSON
- `reaktion`: `neutral`, `zweifel`, `staunen`, `schock`, `jubel`, `traurig` (ab 2.2), siehe `characters.REAKTIONEN`
- `set`: `theke`, `buero`, `studio`, `backstube` (ab 2.2)
- `licht` (optional, ab 2.2): `nacht`, `frueh`, `morgen` für `backstube` und `theke`. Ohne Feld: Theke wie bisher,
  Backstube `frueh`.

### 2.2 – Kalle detaillierter, Reaktion „traurig“, Set „backstube“, Lichtstimmungen
| Bereich | Umsetzung |
|---|---|
| Kalle (`Kalle._details_v22`) | Augenlider (`k.lid`, standardmäßig unsichtbar), Lachfalten an den Augen, Mehlspuren auf Händen und Unterarmen, Mehlstaub auf dem Mützenband, Schürzenbänder mit Schleife am Rücken (Enden schwingen in `kalle_idle` nach), Mundwinkel-Bogen für „traurig“ (`k.frown`) |
| Kalle Hände | `kalle_haende(T, k, art, f0, f1)`: `kneten`, `greifen`, `stuetzen` |
| Kalle „traurig“ | `kalle_react(..., "traurig")` bzw. `kalle_traurig`: Lider halb gesenkt, Brauen schräg nach innen, Mundwinkel nach unten, Schultern hängen, Kopf und Blick gesenkt (langsame Rampe) |
| Byte „traurig“ | Display-Augen als flache, nach außen abfallende Bögen; `byte_face` mit Ausdruck `traurig` ruft `byte_traurig` auf: Antenne knickt langsam ein, Brust-LED pulsiert langsamer und gedimmt, Halo kleiner |
| Set `backstube` (`build_world.build_backstube`) | Ursprung (120, 0, 0). Gemauerter Holzofen mit Glut (Rückwand links, Maul zur Kamera), Arbeitstisch mit Mehl, Teigresten, Teigschaber und Nudelholz, Teigknetmaschine „KNETER“, Blechwagen mit Brezeln, Mehlsäcke „WEIZEN 550“, Fenster zur Straße, Neonröhre, Mehl auf dem Boden, offene Tür mit Blick auf den Verkaufsraum und die Theke von hinten. Kameras: `S.cams["totale"]` (Ofen bis Tür), `S.cams["nah"]` (Arbeitstisch). Glut: `build_world.glut(T, S, f0, f1, level_fn)` |
| Lichtstimmungen (`build_world.apply_licht`) | Feld `licht` pro Szene. Workbench kennt kein Licht: die Stimmung tönt die Objektfarben aller Materialien (außer Byte und Leuchtteilen) während der Szene. `nacht`: dunkel, blaues Mondlicht durchs Fenster, nur Glut und Byte leuchten; `frueh`: Neonröhre an, kühl; `morgen`: warme Sonne, Lichtstrahl mit tanzendem Mehlstaub. In der Theke nur die Tönung |
| Sound (`engine/sfx.py`) | zwei leise Atmosphäre-Geräusche: `knistern` (Glut), `ticken` (Uhr) |
| Timeline (`engine/render.py`) | Szenenfeld `licht` wird durchgereicht |
| Licht-Abschnitte der Regie | `W.licht_extra = [(f0, f1, set, stimmung), ...]` hat Vorrang vor dem Feld `licht` (Neonröhre flackert an, Zeitraffer) |
| Culling (`engine/scene.py`) | `SET_X` kennt die Backstube |
| Hook-Karte (`engine/overlays.py`) | `gelb` aus mehreren Wörtern wird auch über einen Zeilenumbruch hervorgehoben (nur wenn das Stück in keiner Zeile ganz steht; bisherige Folgen unverändert) |

Bisherige Folgen sind unverändert, bis auf Kalles neue Details (Lachfalten, Mehlspuren, Mehlstaub auf der Mütze,
Schürzenbänder). Die Backstube liegt weit entfernt und ist in anderen Folgen nicht im Bild.

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
