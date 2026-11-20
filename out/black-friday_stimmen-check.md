# Stimmen-Check: Der teuerste Rabatt

**Ergebnis:** alle Zeilen bestanden  
**Modell:** `eleven_multilingual_v2`  
**Kalle:** Brian - Deep, Resonant and Comforting (`nPczCjzI2devNBz1zQrb`)  
**Byte:** Laura - Enthusiast, Quirky Attitude (`FGY2WhTYpPnrIDTdsKH5`)  
**Stimmabstand:** Median-F0 Kalle 99 Hz, Byte 226 Hz → 14.4 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  
**Natürlichkeit (UTMOS22 strong):** nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.

| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | 0% | 30 ✓ | 2.58 | 91 Hz | 3.5 st | 0.61 | 0.13 s | – | 1 | OK |
| 2 | byte | 0% | – | 2.72 | 187 Hz | 2.5 st | 0.74 | 0.17 s | – | 1 | OK |
| 3 | kalle | 0% | – | 2.65 | 150 Hz | 6.9 st | 0.54 | 0.39 s | – | 1 | OK |
| 4 | byte | 0% | 90 ✓, 1,20 ✓, eine ✓ | 2.27 | 180 Hz | 2.1 st | 0.85 | 0.17 s | – | 1 | OK |
| 5 | byte | 0% | 30 ✓, Marge ✓ | 2.70 | 166 Hz | 5.3 st | 0.75 | 0.17 s | – | 1 | OK |
| 6 | byte | 0% | 30 ✓, 84 ✓, 6 ✓ | 2.25 | 245 Hz | 4.2 st | 0.67 | 0.20 s | – | 1 | OK |
| 7 | kalle | 0% | – | 2.65 | 86 Hz | 3.2 st | 0.55 | 0.15 s | – | 1 | OK |
| 8 | byte | 0% | – | 2.74 | 248 Hz | 3.8 st | 0.60 | 0.27 s | – | 1 | OK |
| 9 | byte | 0% | 40 ✓ | 2.70 | 196 Hz | 3.5 st | 0.56 | 0.14 s | – | 3 | OK |
| 10 | byte | 0% | 17 ✓ | 2.70 | 233 Hz | 3.0 st | 0.83 | 0.36 s | – | 1 | OK |
| 11 | byte | 0% | 24 ✓, null ✓ | 2.41 | 234 Hz | 3.4 st | 0.72 | 0.12 s | – | 1 | OK |
| 12 | kalle | 0% | – | 2.65 | 99 Hz | 2.8 st | 0.54 | 0.12 s | – | 2 | OK |
| 13 | byte | 0% | – | 2.70 | 226 Hz | 2.7 st | 0.67 | 0.14 s | – | 1 | OK |
| 14 | kalle | 0% | – | 2.35 | 100 Hz | 3.7 st | 0.70 | 0.35 s | – | 2 | OK |

## Hinweise

- Modell `eleven_multilingual_v2` (Vorgabe). Wort-Timing der Untertitel aus dem Endpoint `/with-timestamps`
- Stille am Zeilenanfang/-ende wird weggeschnitten, Pausen zwischen Wörtern werden auf 0,14–0,30 s begrenzt. Tempo: zuerst über den API-Parameter `speed`, Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %; Zeile 8 als kurzer Ausruf bewusst −21 %). Rubberband wurde ersetzt, weil es bei kurzen Ausrufen die Sprachmelodie messbar verflachte.
- Tonhöhe gemessen mit pYIN auf 48 kHz (85-ms-Fenster); bei 16 kHz wurden kurze Ausrufe fälschlich als stimmlos/monoton gewertet.
- Zeile 8 („Des gibt's doch net!“): aus allen erzeugten Varianten die lebendigste mit sauber erkanntem „net“ gewählt (Feinabstimmung in `engine/voices.json`). Das ElevenLabs-Kontingent ist erschöpft (Stand: 12 Credits); weitere Stimmen-Castings waren deshalb nicht möglich.
- Schwäbische Wörter (net, i, des, verschlamp) dürfen in der Rücktranskription abweichen; Zahlwörter, „Code“ und „Marketing“ müssen exakt erkannt werden („Code“ würde bei falscher Aussprache als „Kot“ transkribiert).
- Schreibweisen nur für die Sprachausgabe: siehe „Sprechtext“ je Zeile. Die Untertitel zeigen exakt den Episoden-Text.
- Tonhöhe: keine Verschiebung; Byte (Laura) und Kalle (Brian) sind von Natur aus klar verschieden.

## Details pro Zeile

**1. kalle:** „Black Friday! 30 Prozent auf alles!“  
Sprechtext: „Black Friday! dreißig Prozent auf alles!“  
Whisper: „Black Friday, 30% auf alles.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**2. byte:** „Stopp! Dann verlierst du bei jeder Brezel Geld.“  
Sprechtext: „Stopp! Dann verlierst du bei jeder Brezel Geld.“  
Whisper: „Stop, dann verlierst du bei jeder Brezel Geld.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**3. kalle:** „Geld verlieren? Mit Rabatt? Des geht doch gar net.“  
Sprechtext: „Geld verlieren? Mit Rabatt? Des geht doch gar net.“  
Whisper: „Geld verlieren. Mit Rabatt? Das geht doch gar nicht.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.88  

**4. byte:** „Eine Brezel kostet dich 90 Cent. Du verkaufst sie für 1,20.“  
Sprechtext: „Eine Brezel kostet dich neunzig Cent. Du verkaufst sie für einen Euro zwanzig.“  
Whisper: „Eine Brezel kostet dich 90 Cent. Du verkaufst sie für 1,20 Euro.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**5. byte:** „Bleiben 30 Cent. Das ist deine Marge.“  
Sprechtext: „Bleiben dreißig Cent. Das ist deine Marge.“  
Whisper: „Bleiben 30 Cent. Das ist deine Marge.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.94  

**6. byte:** „Minus 30 Prozent: 84 Cent. Also 6 Cent Verlust. Pro Brezel.“  
Sprechtext: „Minus dreißig Prozent: vierundachtzig Cent. Also sechs Cent Verlust. Pro Brezel.“  
Whisper: „Minus 30 Prozent, 84 Cent, also 6 Cent Verlust pro Brezel.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.06  

**7. kalle:** „Und je mehr i verkauf, desto mehr verlier i?!“  
Sprechtext: „Und je mehr ich verkauf, desto mehr verlier ich?!“  
Whisper: „Und je mehr ich verkauf, desto mehr verlier ich.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.91  

**8. byte:** „Genau. Aber ich hab was Besseres.“  
Sprechtext: „Genau. Aber ich hab was Besseres.“  
Whisper: „Genau, aber ich hab was Besseres.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**9. byte:** „Jeden Abend landen 40 Brezeln im Müll.“  
Sprechtext: „Jeden Abend landen vierzig Brezeln im Müll.“  
Whisper: „Jeden Abend landen 40 Brezeln im Müll.“  
Einstellungen: `{"stability": 0.45, "similarity_boost": 0.75, "style": 0.1, "use_speaker_boost": true, "speed": 0.9}`, Seed 4234, Tempo-Stretch x0.92  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.94, WER 29%, 2.70 W/s, Schreibweise –, Fehler: WER 29% > 10 % – „Jeden Abend landen 40 Brezelne Müll.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x0.93, WER 29%, 2.70 W/s, Schreibweise –, Fehler: WER 29% > 10 % – „Jeden Abend landen 40 Brezelne Müll.“
- Versuch 3: Stabilität 0.45, Seed 4234, Stretch x0.92, WER 0%, 2.70 W/s, Schreibweise –, Fehler: keine – „Jeden Abend landen 40 Brezeln im Müll.“

**10. byte:** „Ab 17 Uhr: halber Preis. Nur auf die Reste.“  
Sprechtext: „Ab siebzehn Uhr: halber Preis. Nur auf die Reste.“  
Whisper: „Ab 17 Uhr halber Preis, nur auf die Reste.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.96  

**11. byte:** „Macht 24 Euro extra. Statt null.“  
Sprechtext: „Macht vierundzwanzig Euro extra. Statt null.“  
Whisper: „Macht 24 Euro extra statt Null.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**12. kalle:** „Und den Rest vom Tag zahlen alle voll?“  
Sprechtext: „Und den Rest vom Tag zahlen alle voll?“  
Whisper: „Und den Rest vom Tag zahlen alle voll.“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x0.98  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 0%, 3.00 W/s, Schreibweise –, Fehler: Tempo 3,00 W/s ausserhalb 2,0–2,8 – „Und den Rest vom Tag zahlen alle voll.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.98, WER 0%, 2.65 W/s, Schreibweise –, Fehler: keine – „Und den Rest vom Tag zahlen alle voll.“

**13. byte:** „Genau. Und das Plakat ist schon fertig.“  
Sprechtext: „Genau. Und das Plakat ist schon fertig.“  
Whisper: „Genau, und das Plakat ist schon fertig.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.97  

**14. kalle:** „Gut. Aber mei Schild behalt i!“  
Sprechtext: „Gut. Aber mei Schild behalt i!“  
Whisper: „Gut, aber mein Schild behalte ich.“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 0%, 2.92 W/s, Schreibweise –, Fehler: Tempo 2,92 W/s ausserhalb 2,0–2,8 – „Gut, aber mein Schild behalte ich...“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.00, WER 0%, 2.35 W/s, Schreibweise –, Fehler: keine – „Gut, aber mein Schild behalte ich.“

