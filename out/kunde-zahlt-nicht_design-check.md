# Design-Check: Viel verkauft, kein Geld

Gesamt-Render: Workbench (wie letzte Folge), Flat Lighting, Kavität, Texturen; Motion Blur über 2 Unterbilder je Frame
(±¼ Frame, 180°-Verschluss, je 5 AA-Samples), Render-Auflösung 70 % mit Hochskalierung/Schärfung im Compositing.
10-Frame-Test: 12,5 s/Frame bei 100 % (Hochrechnung ~100 min) → 75 %: ~62 min → 70 %: ~54 min. Tatsächlich:
3D 49,6 min, gesamt 51,8 min (ohne den vorgeschalteten Stimmen-Check).

## Stufe A – Figuren und Requisiten (`out/kunde-zahlt-nicht_figuren.png`)
| Merkmal | Ergebnis |
|---|---|
| Mütze mit 6-Kugel-Puff, 5° nach rechts | ✓ (6. Puff und Neigung als zuschaltbares Merkmal ergänzt; ältere Folgen unverändert) |
| Walross-Schnurrbart, große Augen mit Glanzpunkt | ✓ (wie bisher) |
| graue Schläfen, 2 Knöpfe, kariertes Geschirrtuch | ✓ neu ergänzt (Knöpfe nach 1. Sichtung nach vorn gesetzt, Schläfen verkleinert) |
| Schürze mit Mehlfleck | ✓ (wie bisher) |
| Byte: türkis facettiert, dunkles Display, Pixelaugen, gelbe Antennenkugel | ✓ (wie bisher) |
| Byte: Ohr-Ringe | ✓ neu ergänzt |
| Neue Requisiten | Motte, Rechnungsblatt + Stempel, Münzen/Münzsäule, Kontoglas, Kalenderblatt, Stoppuhr, Umschlag, Mühlrad-Zettel, Vitrine ✓ |

## Stufe B – Style-Frames (Bewertung 1–10: Licht, Farbe, Komposition, Detail, Lesbarkeit, Treue zum Look)
| Prüf-Frame | Runde 1 | Runde 2 | Runde 3/4 | Endstand | Funde / Korrekturen |
|---|---|---|---|---|---|
| Szene 1, 0,0 s | 8 | 8 | 8 | **8** | Gesicht unter der Hook-Karte, Hand auf der Taste, Schublade in Bewegung |
| Szene 1, 1,5 s | 6 | 6 | 8 | **8** | Pupillen verschwanden (Pivot statt Mesh skaliert) → behoben |
| Szene 4 | 7 | 7 | 7 | **7** | Monitor groß und lesbar, Stempel-Blätter beim Einrollen; Münzsäule klein knapp unter dem Untertitel |
| Szene 6 | 6 | 8 | 8 | **8** | Dolly-Ende zu nah → weiter; Glas höher neben Kalles Kopf, rote Lücke sichtbar |
| Szene 10 | 7 | 7 | 7 | **7** | Gesicht nicht mehr unter Untertitel; Kalle am linken Rand leicht angeschnitten, Glas klein |
| Szene 11 | 6 | 6 | 7 | **7** | Theke hat keinen Screen → schwebender Screen ergänzt (3 Zeilen, große Zahlen); verdeckt Kalles Mützenspitze |
| Szene 12 | 8 | 8 | 8 | **8** | Jubel, Konfetti, Byte-Looping, grüner Ring |
| letztes Frame | 8 | 8 | 8 | **8** | Bildausschnitt = Frame 1 |

Drei Runden ausgeschöpft; Szene 4, 10 und 11 bleiben bei 7 (siehe offene Punkte).

## Stufe C – Bewegung (`out/kunde-zahlt-nicht_bewegung.png`)
Szenen 1, 2, 4, 6, 8, 10, 11, 13 mit je 6 Frames (Szenenanfang, Beat-Wörter +4 Frames, Ende). Alle Beat-Aktionen
landen auf ihrem Wort (Start 3 Frames vorher, Sound auf dem Wort, siehe Timing). Pops mit Ease/Overshoot, keine
abrupten Sprünge. Szenenanfänge 4, 6, 11 zeigen die gewollten Whip-Pans mit Bewegungsunschärfe.

## Stufe D – Endkontrolle (`out/work/kunde-zahlt-nicht/qa/`)
| Prüfung | Ergebnis |
|---|---|
| ffprobe | 1080×1920, 30 fps, h264 High, yuv420p, AAC 48 kHz (~155 kbit/s bei 160k), 48,03 s, 28,0 MB ✓ |
| Lautheit | −13,9 LUFS integriert, Spitze −2,7 dBFS ✓ |
| 0,0 / 0,5 / 1,5 s | Hook lesbar ab Frame 1, Bewegung Frame 0→1 (mittl. Differenz 3,4), Stimme ab 0,002 s ✓ |
| Prüf-Frames | Figuren sichtbar, kein Gesicht unter Untertiteln, Zahlen = Sprechtext (1.860, 600, 900/1.500/1.860, 1.260), Kapitel-Leiste korrekt, bei kapitel null kein Banner, keine Folgennummer ✓ |
| Safe Zone | oben 220 / rechts 160 / unten 420 frei von Wichtigem ✓ (Szene-11-Screen beginnt bei y ≈ 275) |
| Loop | 3D-Bild erstes vs. letztes Frame: mittl. Abweichung 4,7 (Kamera, Kalle, Theke gleich; Byte, Glas, Münzen, Mehlsack weg; Schublade zu statt 5 % offen) ✓ |
| 6 verteilte Frames | kein Clipping (≤ 1,5 % Pixel ≥ 254, Lichter/Mehl), keine leeren Hintergründe, keine Ruckler sichtbar ✓ |

## Offene Punkte
- Während Screen-Zahlen hochzählen, mittelt das Motion Blur zwei Zahlenstände (Ziffern kurz verschmiert); Endwerte scharf.
- Szene 4: Münzsäule klein; Szene 10: Kalle leicht angeschnitten; Szene 11: Screen überdeckt die Mützenspitze.
- Render-Auflösung 70 % statt 100 % (Zeitvorgabe < 60 min mit Motion Blur).
