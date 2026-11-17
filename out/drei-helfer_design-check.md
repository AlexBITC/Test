# Design-Check: Byte schickt drei Helfer los

**Ergebnis:** Nach 3 Style-Runden und 2 Kontaktbogen-Runden erreicht nicht jede Kategorie die 8 (Details unten).
Die übrigen Abweichungen sind dokumentiert, nicht kaschiert.

**Renderer:** Blender 5.2.3 LTS, Eevee (headless über Mesa/llvmpipe, keine GPU), 4 Samples, Motion Blur,
Tiefenunschärfe, Ambient Occlusion (Fast GI), Bloom im Compositor. Interne Auflösung 720×1280, hochskaliert
(Lanczos + leichtes Schärfen) auf 1080×1920. Overlays und Text in voller Auflösung.
**Renderzeit:** 115 min für den Gesamt-Render (Ziel: < 30 min, **verfehlt**). Messung vorab: 7,7 s/Frame
bei 1080×1920 (8 Samples), 4,7 s bei 720×1280. Nach der Vorgabe wurden zuerst die Samples gesenkt (8 → 4);
dazu kommt Culling unsichtbarer Objekte (−20 %). Weiter ließ sich ohne Abstriche an Design und Animation
nicht sparen, weil die Software-GPU fast nur pixelgebunden rechnet.

## Style-Frames (Szene 1, 4, 7, 8) – Bewertung 1–10

Bewertet wurden die Frames 37 (Szene 1, Sack-Aufprall), 573 (Szene 4, nach „15,50“),
1218 (Szene 7, nach „1.800“) und 1279 (Szene 8, Jubel), jeweils mit der finalen Pipeline gerendert.

### Runde 1
| Szene | Licht | Farbe | Komposition | Detail | Lesbarkeit | Hauptproblem |
|---|---|---|---|---|---|---|
| 1 | 5 | 6 | 6 | 7 | 7 | Theke überbelichtet, Byte ausgebrannt |
| 4 | 7 | 7 | 3 | 6 | 4 | Säcke verdecken den Screen-Text |
| 7 | 6 | 7 | 4 | 6 | 4 | Waage über dem Screen, doppelte Zahl |
| 8 | 5 | 6 | 4 | 7 | 6 | Jubel-Arme vor dem Gesicht (Vorzeichenfehler) |

Änderungen: Licht in Theke/Büro gesenkt, Belichtung −0,45, Byte-Emission halbiert, Jubel-Arme korrigiert,
Untertitel-Abstände (Kontur fraß Leerzeichen), Studio neu aufgeteilt (Screen hoch, Requisiten-Band darunter,
Kamera mit definierter Neigung).

### Runde 2
| Szene | Licht | Farbe | Komposition | Detail | Lesbarkeit |
|---|---|---|---|---|---|
| 1 | 7 | 6 | 7 | 7 | 8 |
| 4 | 7 | 8 | 5 | 7 | 6 |
| 7 | 7 | 7 | 4 | 6 | 5 |
| 8 | 7 | 7 | 7 | 7 | 8 |

Änderungen: Bytes Licht auf Kalle reduziert (grünliche Haut), Screen-Text zentriert, Kamera Szene 4 weniger
Untersicht, Mehlwolke halbtransparent statt opaker Kugeln, Waage auf Sockel, Münzreihe versetzt.

### Runde 3 (final)
| Szene | Licht | Farbe | Komposition | Detail | Lesbarkeit |
|---|---|---|---|---|---|
| 1 | 7 | 7 | 7 | 7 | 8 |
| 4 | 8 | 8 | 7 | 7 | 8 |
| 7 | 7 | 8 | 6 | 7 | 7 |
| 8 | 7 | 8 | 8 | 7 | 8 |

**Unter 8 bleiben:** Licht (Szene 1, 7, 8): Eevee mit 4 Samples zeigt in Weichschatten leichtes Rauschen,
die Theke wirkt etwas flach. Komposition Szene 7: Kalle steht am Bildrand und ist zu Beginn angeschnitten.
Detailgrad allgemein 7: Die hochskalierte 720p-Grafik ist sichtbar weicher als nativ 1080p.

## Kontaktbögen (6 Frames je Szene: Anfang, Beats, Ende)

Die Bögen liegen in `out/work/drei-helfer/kontakt_szeneN.png` (nicht im Repo, da Arbeitsdateien).

### Runde 1 – gefundene Fehler
- Szene 1: rotes Preisschild ab Frame 1 sichtbar → Beat-Name „zu viel“ falsch abgefragt (nur „zu“). **Behoben.**
- Szene 3: Start zu nah; ein Helfer schwebt vor Kalles Gesicht. **Behoben** (Formation rechts, Kamera weiter).
- Szene 5: Screen-Text hinter Banner/Kapitel-Leiste (Kamera zu hoch); 60er-Raster flach, kaum lesbar.
  **Behoben** (Kamera tiefer, Raster um 30° gekippt).
- Szene 6: Mail-Text zu klein (Screen bei 70 % Bildbreite). **Behoben** (64 → 76 px in der Textur).
- Szene 7: Kalle groß mitten vor der Waage. **Behoben** (Kreisfahrt-Richtung umgedreht, 45° → 0°).
- Szene 8: Senden-Button vom Laptop-Deckel verdeckt. **Behoben** (Button vorne auf der Theke).
- Szene 9: Untertitel über dem Gesicht beim harten Zoom. **Behoben** (45 mm statt 75 mm, Gesicht höher im Bild).
- Animation allgemein: Bewegung in jedem Frame erkennbar, Whip-Pans mit Unschärfe, Pops mit Overshoot,
  Squash beim Aufprall sichtbar.

### Runde 2 – Rest
- Byte schwebte in Szene 4–6 vor Kalles Gesicht bzw. in Szene 7 auf seiner Mütze. **Behoben.**

### Nach dem Gesamt-Render (Prüfung der fertigen MP4)
- Szene 3 (Nahaufnahme) und Szene 6 (Totale): Untertitel lag über Kalles Gesicht; Szene 5: Bytes
  Gesicht ragte in die Untertitelzone; Lichtblitz in Szene 3 überstrahlte Kalle.
  **Behoben** durch neue Kameraneigung bzw. Byte-Position; diese drei Szenen wurden neu gerendert.
- Szene 3: Byte verdeckte danach in der Nahaufnahme Kalles Auge → Byte neben die Schulter gesetzt, Szene 3 neu gerendert.

## Prüfung der finalen MP4 (`out/folge-02-drei-helfer.mp4`)

| Prüfpunkt | Ergebnis |
|---|---|
| ffprobe | h264 High, 1080×1920, 30 fps, yuv420p, AAC 48 kHz Stereo, 48,73 s, 38,5 MB |
| Lautheit | −14,6 LUFS integriert (Ziel −14), Peak −4,3 dBFS |
| Frame 0,5 s | Hook-Karte lesbar, Byte mitten in der Drehung (Bewegungsunschärfe), Kalle wischt |
| Szene 5 (Mitte) | Screen „2,50 € × 60 Säcke“ = Sprechtext, Kapitel-Leiste ✓1 / 2 aktiv / 3 grau, Banner „2 · ERSPARNIS RECHNEN“ |
| Szene 7 (Mitte) | kein Kapitel-Banner (kapitel null), Begriff-Karte „BESCHAFFUNG“, Screen „150 € × 12“ |
| letztes Frame | identische Einstellung wie Frame 0 |
| Loop-Test | Frame 0 vs. 1461: mittlere Pixelabweichung 2,5 von 255 (Korn und erster Untertitel); Kamera, Kalle, Byte, Kasse und Theke stimmen überein |
| Folgennummer/Serienname | nirgends im Bild |
| Kalles Gesicht im Untertitelband | 0 Frames (automatisch über projizierte Anker geprüft) |
| Kalles Gesicht bei y 800–1150 | 944 von 1042 sichtbaren Frames; höher (bis y 607) in der Nahaufnahme von Szene 3, beim Zoom in Szene 9 und am Ende von Szene 6, damit der Untertitel frei bleibt |
| Byte x ≤ 880 | Ausnahmen nur beim Hereinfliegen (Szene 2 Frames 132–142, Szene 3 Frames 266–275), im Whip-Pan-Frame 384 und 7 Frames in der Rückfahrt von Szene 9 |
| Byte im Untertitelband | 5 Frames (623–627) beim Aufsteigen zu Beginn von Szene 5 |
| Gleichmäßig verteilte Frames (0, 292, 584, 876, 1168, 1460) | kein schwarzes Bild, kein leerer Hintergrund, kein Clipping der Figuren; Kalle in Szene 7 zu Beginn am linken Rand angeschnitten |
