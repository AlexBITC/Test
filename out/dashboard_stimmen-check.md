# Stimmen-Check: Kalles Ausgaben-Dashboard

**Ergebnis:** nicht alle Zeilen bestanden (siehe unten)  
**Modell:** `eleven_multilingual_v2`  
**Kalle:** Brian - Deep, Resonant and Comforting (`nPczCjzI2devNBz1zQrb`)  
**Byte:** Laura - Enthusiast, Quirky Attitude (`FGY2WhTYpPnrIDTdsKH5`)  
**Stimmabstand:** Median-F0 Kalle 108 Hz, Byte 191 Hz → 9.9 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  
**Natürlichkeit (UTMOS22 strong):** nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.

| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | byte | 0% | eine ✓ | 2.70 | 206 Hz | 2.2 st | 0.63 | 0.12 s | – | 2 | OK |
| 2 | kalle | 14% | – | 2.69 | 104 Hz | 4.5 st | 0.46 | 0.09 s | – | 3 | FAIL: WER 14% > 10 % |
| 3 | byte | 0% | – | 2.34 | 178 Hz | 3.6 st | 0.85 | 0.24 s | – | 1 | OK |
| 4 | byte | 0% | 1.200 ✓, zwei ✓ | 2.13 | 212 Hz | 4.1 st | 0.68 | 0.18 s | – | 1 | OK |
| 5 | byte | 0% | drei ✓, Fixkosten ✓ | 2.37 | 206 Hz | 2.9 st | 0.69 | 0.30 s | – | 1 | OK |
| 6 | byte | 0% | 49 ✓, 2022 ✓ | 2.01 | 191 Hz | 3.2 st | 0.70 | 0.21 s | – | 1 | OK |
| 7 | kalle | 38% | 2022 ✓ | 2.15 | 139 Hz | 2.8 st | 0.77 | 0.21 s | – | 3 | FAIL: WER 38% > 10 % |
| 8 | byte | 0% | 29 ✓, 60 ✓ | 2.25 | 198 Hz | 3.7 st | 0.88 | 0.14 s | – | 2 | OK |
| 9 | byte | 0% | einen ✓ | 2.70 | 188 Hz | 2.8 st | 0.64 | 0.14 s | – | 1 | OK |
| 10 | kalle | 0% | 138 ✓ | 2.15 | 111 Hz | 5.7 st | 0.64 | 0.48 s | – | 1 | OK |
| 11 | byte | 0% | drei ✓ | 2.22 | 178 Hz | 3.0 st | 0.87 | 0.16 s | – | 2 | OK |
| 12 | byte | 0% | 1.600 ✓ | 2.43 | 178 Hz | 3.4 st | 0.65 | 0.28 s | – | 1 | OK |
| 13 | kalle | 14% | – | 2.12 | 96 Hz | 2.9 st | 0.52 | 0.52 s | – | 3 | FAIL: WER 14% > 10 % |

## Hinweise

- Modell `eleven_multilingual_v2` (Vorgabe). Wort-Timing der Untertitel aus dem Endpoint `/with-timestamps`
- Stille am Zeilenanfang/-ende wird weggeschnitten, Pausen zwischen Wörtern werden auf 0,14–0,30 s begrenzt. Tempo: zuerst über den API-Parameter `speed`, Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %; Zeile 8 als kurzer Ausruf bewusst −21 %). Rubberband wurde ersetzt, weil es bei kurzen Ausrufen die Sprachmelodie messbar verflachte.
- Tonhöhe gemessen mit pYIN auf 48 kHz (85-ms-Fenster); bei 16 kHz wurden kurze Ausrufe fälschlich als stimmlos/monoton gewertet.
- Zeile 8 („Des gibt's doch net!“): aus allen erzeugten Varianten die lebendigste mit sauber erkanntem „net“ gewählt (Feinabstimmung in `engine/voices.json`). Das ElevenLabs-Kontingent ist erschöpft (Stand: 12 Credits); weitere Stimmen-Castings waren deshalb nicht möglich.
- Schwäbische Wörter (net, i, des, verschlamp) dürfen in der Rücktranskription abweichen; Zahlwörter, „Code“ und „Marketing“ müssen exakt erkannt werden („Code“ würde bei falscher Aussprache als „Kot“ transkribiert).
- Schreibweisen nur für die Sprachausgabe: siehe „Sprechtext“ je Zeile. Die Untertitel zeigen exakt den Episoden-Text.
- Tonhöhe: keine Verschiebung; Byte (Laura) und Kalle (Brian) sind von Natur aus klar verschieden.

## Details pro Zeile

**1. byte:** „Kalle, du zahlst für eine Kaffeemaschine, die du gar nicht mehr hast.“  
Sprechtext: „Kalle, du zahlst für eine Kaffeemaschine, die du gar nicht mehr hast.“  
Whisper: „Kalle, du zahlst für eine Kaffeemaschine, die du gar nicht mehr hast.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x0.96  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.88, WER 0%, 3.02 W/s, Schreibweise –, Fehler: Tempo 3,02 W/s ausserhalb 2,0–2,8 – „Kalle, du zahlst für eine Kaffeemaschine, die du gar nicht mehr hast.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x0.96, WER 0%, 2.70 W/s, Schreibweise –, Fehler: keine – „Kalle, du zahlst für eine Kaffeemaschine, die du gar nicht mehr hast.“

**2. kalle:** „Quatsch. Wie willsch du des überhaupt wissen?“  
Sprechtext: „Quatsch. Wie willsch du des überhaupt wissen?“  
Whisper: „Quatsch, wie willst du das überhaupt wissen?“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.88  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 14%, 2.69 W/s, Schreibweise –, Fehler: WER 14% > 10 % – „Quatsch, wie willst du das überhaupt wissen?“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.91, WER 14%, 2.65 W/s, Schreibweise –, Fehler: WER 14% > 10 % – „Quatsch! Wie willst du das überhaupt wissen?“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x0.92, WER 14%, 2.65 W/s, Schreibweise –, Fehler: WER 14% > 10 % – „Quatsch. Wie willst du das überhaupt wissen?“

**3. byte:** „Ganz einfach. Zieh deine Kontoauszüge hier rein.“  
Sprechtext: „Ganz einfach. Zieh deine Kontoauszüge hier rein.“  
Whisper: „Ganz einfach. Zieh deine Kontoauszüge hier rein.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**4. byte:** „1.200 Buchungen. In zwei Sekunden sortiert.“  
Sprechtext: „tausendzweihundert Buchungen. In zwei Sekunden sortiert.“  
Whisper: „1200 Buchungen, in zwei Sekunden sortiert.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.15  

**5. byte:** „Drei rote Punkte. Fixkosten, die du nicht brauchst.“  
Sprechtext: „Drei rote Punkte. Fixkosten, die du nicht brauchst.“  
Whisper: „Drei rote Punkte. Fixkosten, die du nicht brauchst.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**6. byte:** „49 Euro Miete für die alte Kaffeemaschine. Seit 2022.“  
Sprechtext: „neunundvierzig Euro Miete für die alte Kaffeemaschine. Seit zweitausendzweiundzwanzig.“  
Whisper: „49 Euro Miete für die alte Kaffeemaschine seit 2022.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.15  

**7. kalle:** „Seit 2022?! Die steht doch längst auf'm Schrott!“  
Sprechtext: „Seit zweitausendzweiundzwanzig?! Die steht doch längst auf'm Schrott!“  
Whisper: „Seit 2022, die steht auch längst auf dem Schrott.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.03  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x1.03, WER 38%, 2.15 W/s, Schreibweise –, Fehler: WER 38% > 10 % – „Seit 2022, die steht auch längst auf dem Schrott.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.07, WER 50%, 2.15 W/s, Schreibweise –, Fehler: WER 50% > 10 % – „Seit 2022, die steht auch längst auf dem Schrot.“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x1.05, WER 38%, 2.15 W/s, Schreibweise –, Fehler: WER 38% > 10 % – „Seit 2022, die steht auch längst auf dem Schrott.“

**8. byte:** „Kassenprogramm doppelt: 29 Euro. Stromvertrag still verlängert: 60 Euro.“  
Sprechtext: „Kassenprogramm doppelt: neunundzwanzig Euro. Stromvertrag still verlängert: sechzig Euro.“  
Whisper: „Kassenprogramm doppelt 29 Euro, Stromvertrag still verlängert 60 Euro.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 1.2}`, Seed 4217, Tempo-Stretch x1.08  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x1.15, WER 0%, 1.64 W/s, Schreibweise –, Fehler: Tempo 1,64 W/s ausserhalb 2,0–2,8 – „Kassenprogramm doppelt. 29 Euro. Stromvertrag still verlängert. 60 Euro.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.08, WER 0%, 2.25 W/s, Schreibweise –, Fehler: keine – „Kassenprogramm doppelt 29 Euro, Stromvertrag still verlängert 60 Euro.“

**9. byte:** „Hier, dein Dashboard. Alles auf einen Blick.“  
Sprechtext: „Hier, dein Dashboard. Alles auf einen Blick.“  
Whisper: „Hier dein Dashboard. Alles auf einen Blick.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.88  

**10. kalle:** „138 Euro im Monat … für nix?“  
Sprechtext: „hundertachtunddreißig Euro im Monat … für nix?“  
Whisper: „138 Euro im Monat. Für nix.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.04  

**11. byte:** „Ein Klick, drei Kündigungen. Zum nächstmöglichen Termin.“  
Sprechtext: „Ein Klick, drei Kündigungen. Zum nächstmöglichen Termin.“  
Whisper: „Ein Klick, drei Kündigungen. Zum nächstmöglichen Termin.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x1.07, WER 29%, 2.25 W/s, Schreibweise –, Fehler: WER 29% > 10 % – „Ein Klick, drei Kündigungen. Zum nächsten möglichen Termin.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.00, WER 0%, 2.22 W/s, Schreibweise –, Fehler: keine – „Ein Klick, drei Kündigungen. Zum nächstmöglichen Termin.“

**12. byte:** „Über 1.600 Euro im Jahr. Für dich.“  
Sprechtext: „Über tausendsechshundert Euro im Jahr. Für dich.“  
Whisper: „Über 1600 Euro im Jahr. Für dich.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**13. kalle:** „Byte … was koschtesch eigentlich du im Monat?“  
Sprechtext: „Byte … was koschtesch eigentlich du im Monat?“  
Whisper: „Byte, was kostest eigentlich du im Monat?“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x1.00, WER 14%, 2.12 W/s, Schreibweise –, Fehler: WER 14% > 10 % – „Byte, was kostest eigentlich du im Monat?“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.00, WER 14%, 2.27 W/s, Schreibweise –, Fehler: WER 14% > 10 % – „Byte, was kostest eigentlich du im Monat?“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x1.00, WER 29%, 2.13 W/s, Schreibweise –, Fehler: WER 29% > 10 % – „Was kostest eigentlich du im Monat?“

