# Stimmen-Check: Bytes Nachtschicht

**Ergebnis:** nicht alle Zeilen bestanden (siehe unten)  
**Modell:** `eleven_multilingual_v2`  
**Kalle:** Brian - Deep, Resonant and Comforting (`nPczCjzI2devNBz1zQrb`)  
**Byte:** Laura - Enthusiast, Quirky Attitude (`FGY2WhTYpPnrIDTdsKH5`)  
**Stimmabstand:** Median-F0 Kalle 105 Hz, Byte 208 Hz → 11.7 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  
**Natürlichkeit (UTMOS22 strong):** nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.

| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | byte | 0% | – | 2.70 | 238 Hz | 2.9 st | 0.75 | 0.19 s | – | 1 | OK |
| 2 | kalle | 43% | vier ✓ | 2.75 | 147 Hz | 4.0 st | 0.53 | 0.13 s | – | 3 | FAIL: WER 43% > 10 % |
| 3 | byte | 0% | 37 ✓, drei ✓ | 2.25 | 208 Hz | 3.4 st | 0.83 | 0.19 s | – | 1 | OK |
| 4 | byte | 0% | 1,10 ✓ | 2.28 | 208 Hz | 2.7 st | 0.84 | 0.08 s | – | 1 | OK |
| 5 | byte | 0% | 4,8 ✓, 4,1 ✓ | 2.25 | 234 Hz | 3.0 st | 0.83 | 0.26 s | – | 1 | OK |
| 6 | byte | 0% | 62 ✓ | 2.25 | 217 Hz | 2.4 st | 0.64 | 0.20 s | – | 1 | OK |
| 7 | kalle | 33% | – | 2.25 | 128 Hz | 1.8 st | 0.61 | 0.41 s | – | 3 | FAIL: WER 33% > 10 % |
| 8 | kalle | 0% | – | 2.65 | 82 Hz | 3.6 st | 0.49 | 0.09 s | – | 2 | OK |
| 9 | byte | 0% | – | 2.70 | 224 Hz | 3.6 st | 0.67 | 0.26 s | – | 2 | OK |
| 10 | byte | 0% | – | 2.54 | 179 Hz | 2.4 st | 0.52 | 0.33 s | – | 2 | OK |
| 11 | byte | 0% | drei ✓ | 2.71 | 187 Hz | 3.8 st | 0.64 | 0.09 s | – | 1 | OK |
| 12 | kalle | 0% | – | 2.42 | 83 Hz | 3.6 st | 0.46 | 0.57 s | – | 3 | OK |
| 13 | byte | 0% | – | 2.71 | 208 Hz | 2.1 st | 0.71 | 0.15 s | – | 1 | OK |

## Hinweise

- Modell `eleven_multilingual_v2` (Vorgabe). Wort-Timing der Untertitel aus dem Endpoint `/with-timestamps`
- Stille am Zeilenanfang/-ende wird weggeschnitten, Pausen zwischen Wörtern werden auf 0,14–0,30 s begrenzt. Tempo: zuerst über den API-Parameter `speed`, Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %; Zeile 8 als kurzer Ausruf bewusst −21 %). Rubberband wurde ersetzt, weil es bei kurzen Ausrufen die Sprachmelodie messbar verflachte.
- Tonhöhe gemessen mit pYIN auf 48 kHz (85-ms-Fenster); bei 16 kHz wurden kurze Ausrufe fälschlich als stimmlos/monoton gewertet.
- Zeile 8 („Des gibt's doch net!“): aus allen erzeugten Varianten die lebendigste mit sauber erkanntem „net“ gewählt (Feinabstimmung in `engine/voices.json`). Das ElevenLabs-Kontingent ist erschöpft (Stand: 12 Credits); weitere Stimmen-Castings waren deshalb nicht möglich.
- Schwäbische Wörter (net, i, des, verschlamp) dürfen in der Rücktranskription abweichen; Zahlwörter, „Code“ und „Marketing“ müssen exakt erkannt werden („Code“ würde bei falscher Aussprache als „Kot“ transkribiert).
- Schreibweisen nur für die Sprachausgabe: siehe „Sprechtext“ je Zeile. Die Untertitel zeigen exakt den Episoden-Text.
- Tonhöhe: keine Verschiebung; Byte (Laura) und Kalle (Brian) sind von Natur aus klar verschieden.

## Details pro Zeile

**1. byte:** „Morgen, Kalle! Ich war die ganze Nacht fleißig.“  
Sprechtext: „Morgen, Kalle! Ich war die ganze Nacht fleißig.“  
Whisper: „Morgen, Kalle. Ich war die ganze Nacht fleißig.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.93  

**2. kalle:** „Um vier Uhr früh? Was hasch gmacht?“  
Sprechtext: „Um vier Uhr früh? Was hasch gmacht?“  
Whisper: „Um 4 Uhr früh, was hast du gemacht?“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.88  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 43%, 2.75 W/s, Schreibweise –, Fehler: WER 43% > 10 % – „Um 4 Uhr früh, was hast du gemacht?“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.00, WER 43%, 2.63 W/s, Schreibweise –, Fehler: WER 43% > 10 % – „Um 4 Uhr früh, was hast du gemacht?“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x1.00, WER 43%, 2.59 W/s, Schreibweise –, Fehler: WER 43% > 10 % – „Um 4 Uhr früh. Was hast du gemacht?“

**3. byte:** „Ich hab 37 Bewerbungen gelesen. Drei passen perfekt.“  
Sprechtext: „Ich hab siebenunddreißig Bewerbungen gelesen. Drei passen perfekt.“  
Whisper: „Ich habe 37 Bewerbungen gelesen. Drei passen perfekt.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.11  

**4. byte:** „Die Bäckerei am Marktplatz verkauft Brezeln für 1,10.“  
Sprechtext: „Die Bäckerei am Marktplatz verkauft Brezeln für ein Euro zehn.“  
Whisper: „Die Bäckerei am Marktplatz verkauft Brezeln für 1,10 Euro.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**5. byte:** „Aber du hast die besseren Bewertungen. 4,8 gegen 4,1.“  
Sprechtext: „Aber du hast die besseren Bewertungen. vier Komma acht gegen vier Komma eins.“  
Whisper: „Aber du hast die besseren Bewertungen. 4,8 gegen 4,1.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.15  

**6. byte:** „Und 62 Bestellungen für heute. Alle bestätigt.“  
Sprechtext: „Und zweiundsechzig Bestellungen für heute. Alle bestätigt.“  
Whisper: „Und 62 Bestellungen für heute. Alle bestätigt.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.15  

**7. kalle:** „Alle … scho bestätigt?“  
Sprechtext: „Alle … scho bestätigt?“  
Whisper: „Alle schon bestätigt?“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 1.2}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x1.15, WER 67%, 1.68 W/s, Schreibweise –, Fehler: WER 67% > 10 %; Tempo 1,68 W/s ausserhalb 2,0–2,8 – „Hallo? Show bestätigt?“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.00, WER 33%, 2.25 W/s, Schreibweise –, Fehler: WER 33% > 10 % – „Alle schon bestätigt?“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x1.15, WER 67%, 1.88 W/s, Schreibweise –, Fehler: WER 67% > 10 %; Tempo 1,88 W/s ausserhalb 2,0–2,8 – „Allergie schon bestätigt?“

**8. kalle:** „Wofür brauchst du mich dann eigentlich noch?“  
Sprechtext: „Wofür brauchst du mich dann eigentlich noch?“  
Whisper: „Wofür brauchst du mich dann eigentlich noch?“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x0.92  
- Versuch 1: Stabilität 0.72, Seed 4200, Stretch x0.88, WER 0%, 3.41 W/s, Schreibweise –, Fehler: Tempo 3,41 W/s ausserhalb 2,0–2,8 – „Wofür brauchst du mich dann eigentlich noch?“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.92, WER 0%, 2.65 W/s, Schreibweise –, Fehler: keine – „Wofür brauchst du mich dann eigentlich noch?“

**9. byte:** „Kalle … ich kann rechnen. Aber backen kann ich nicht.“  
Sprechtext: „Kalle … ich kann rechnen. Aber backen kann ich nicht.“  
Whisper: „Kalle, ich kann rechnen, aber backen kann ich nicht.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4217, Tempo-Stretch x0.91  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.95, WER 11%, 2.70 W/s, Schreibweise –, Fehler: WER 11% > 10 % – „Kalle, ich kann rechnen, aber buggen kann ich nicht.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x0.91, WER 0%, 2.70 W/s, Schreibweise –, Fehler: keine – „Kalle, ich kann rechnen, aber backen kann ich nicht.“

**10. byte:** „Die Leute kommen nicht wegen mir. Sie kommen wegen dir.“  
Sprechtext: „Die Leute kommen nicht wegen mir. Sie kommen wegen dir.“  
Whisper: „Die Leute kommen nicht wegen mir, sie kommen wegen dir.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.88, WER 0%, 2.88 W/s, Schreibweise –, Fehler: Tempo 2,88 W/s ausserhalb 2,0–2,8 – „Die Leute kommen nicht wegen mir, sie kommen wegen dir.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.00, WER 0%, 2.54 W/s, Schreibweise –, Fehler: keine – „Die Leute kommen nicht wegen mir, sie kommen wegen dir.“

**11. byte:** „Und die drei Bewerber wollen dich kennenlernen.“  
Sprechtext: „Und die drei Bewerber wollen dich kennenlernen.“  
Whisper: „Und die drei Bewerber wollen dich kennenlernen.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.88  

**12. kalle:** „Na dann … back i jetzt mal Brezeln.“  
Sprechtext: „Na dann … back i jetzt mal Brezeln.“  
Whisper: „Na dann, back i jetzt mal Brezeln.“  
Einstellungen: `{"stability": 0.35, "similarity_boost": 0.75, "style": 0.2, "use_speaker_boost": true, "speed": 0.7}`, Seed 4234, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x1.00, WER 14%, 2.63 W/s, Schreibweise –, Fehler: WER 14% > 10 % – „Na dann, Baki, jetzt mal brezeln.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.88, WER 14%, 2.85 W/s, Schreibweise –, Fehler: WER 14% > 10 %; Tempo 2,85 W/s ausserhalb 2,0–2,8 – „Na dann, Backe jetzt mal brezeln.“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x1.00, WER 0%, 2.42 W/s, Schreibweise –, Fehler: keine – „Na dann, back i jetzt mal Brezeln.“

**13. byte:** „Und ich arbeite heute Nacht weiter.“  
Sprechtext: „Und ich arbeite heute Nacht weiter.“  
Whisper: „Und ich arbeite heute Nacht weiter.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.88  

