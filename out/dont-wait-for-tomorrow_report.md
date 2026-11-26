# Prüfbericht: „Don't put off until tomorrow“ (TikTok, EN)

## Ergebnis
| Prüfpunkt | Vorgabe | Ist |
|---|---|---|
| Format | 1080×1920, 30 fps, H.264 + AAC | H.264 High, 1080×1920, 30 fps, yuv420p; AAC 48 kHz Stereo 192 kbit/s |
| Dauer | 35–45 s | 35,3 s (1059 Frames) |
| Dateigröße | < 50 MB | ca. 41 MB |
| Stimme | −16 LUFS | −16,0 LUFS (Stimm-Spur vor dem Mastering) |
| Endmix | −14 LUFS, True Peak < −1 dB | −14,1 LUFS, −2,5 dBTP (gemessen in der fertigen MP4 nach AAC) |
| Spracherkennung Endmix | wortgenau | Whisper medium.en: 0 Wortfehler |
| Untertitel-Zeiten | echte Wortzeiten | ElevenLabs-Zeichenzeiten; gegen Whisper: Median 0,06 s, 90 % < 0,13 s |
| Leere Frames | keine | keine (min. Helligkeit YAVG 37) |
| Text am Rand abgeschnitten | nein | keine Treffer (automatische Prüfung aller Frames) |
| Loop | nahtlos | Unterschied letzter→erster Frame 2,95 (normaler Frame-zu-Frame-Wert 3,37) |
| Hook | in 1,5 s | Schlagzeile ab Frame 0, Stimme ab 0,25 s, Goldkreis um die „1“ ab 0,95 s |

## Stimme
- Fernanda – Calm Storytelling (ElevenLabs Voice Library), Voice-ID `hnFidmF05jrIKH0LAjEc`
- Modell `eleven_multilingual_v2`; stability 0.40, similarity_boost 0.80, style 0.30, Speaker Boost an
- `speed` 0,71–0,78 (sonst nur ~28 s Gesamtlänge); Stimmung pro Satz über unsichtbaren Kontext (`next_text`)
- Je Satz 3 Takes. Ein Take kommt nur in Frage, wenn Whisper alle Wörter exakt erkennt, die Satzzeichen passen (Frage- statt Aussagemelodie fällt durch) und die Tonhöhe nicht monoton ist (Streuung ≥ 1,2 Halbtöne). Satz 6 brauchte 3 Runden (9 Takes).
- Jeder Satz wird 0,08 s vor dem ersten bis 0,30 s nach dem letzten Wort geschnitten; damit fallen kurze Klick- und Atemgeräusche am Dateiende weg.
- Pausen (Stille zwischen den hörbaren Grenzen): 0,5 s; vor Satz 8 0,8 s.

## Ton
Musik selbst synthetisiert (Pads Am–F–C–G, Bass, Pluck-Arpeggio ab Satz 5, Herzschlag-Kick, Riser, Impact). Soundeffekte ebenfalls synthetisch: Blätter, Neon-Brummen, Riss, Zerbrechen, Grollen, Schritte, Gold-Glöckchen, Ticken, Explosion. Musik wird unter der Stimme um bis zu 6 dB abgesenkt, die Effekte um bis zu 4,4 dB. Der Hall ist zirkulär gerechnet: die Hallfahnen laufen über den Loop-Punkt.

## Gefundene und behobene Fehler
1. Die Figur lief rückwärts („Moonwalk“): Das Knie beugte sich im falschen Gangabschnitt.
2. Graues Rauschen auf den fliegenden Kalenderblättern: kam von der Bewegungsunschärfe, die ist jetzt aus.
3. Kalenderseiten schimmerten durch: Seitenabstand vergrößert.
4. Der Goldkreis (Hook) war verdeckt, weil zwei Sichtbarkeits-Keys sich überschrieben.
5. Untertitel lagen auf der Bodenlinie: Kamera tiefer gesetzt.
6. Klicks am Clip-Ende verfälschten die Pausen: Schnitt nach Wortzeiten.
7. In Szene 5–7 verschwand die Figur vor dem weißen Berggitter: Der Berg weicht jetzt nach rechts aus.
8. True Peak lag nach der AAC-Kodierung bei −0,5 dBTP: Limiter auf −3 dBTP gesenkt.
9. Alte und neue Schlagzeile bzw. Untertitel überlagerten sich beim Wechsel: Überblendungen zeitlich getrennt.
10. Der Wort-Pop ließ Wortabstände verschwinden: auf 4 % reduziert.

## Offen / Hinweise
- Den Klang konnte ich nicht anhören. Geprüft habe ich ihn nur über Messungen (Lautheit, Whisper, Tonhöhe). Bitte einmal mit Kopfhörern gegenhören.
- Das Outro nach „Start now.“ dauert 5 s (Explosion mit Push-in), damit die Mindestlänge von 35 s erreicht wird.
- Schriften: Anton und Inter (beide SIL Open Font License). Musik und Effekte sind selbst erzeugt, keine fremden Inhalte.
