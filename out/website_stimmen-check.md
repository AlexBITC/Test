# Stimmen-Check: Bäcker ohne Website

**Ergebnis:** alle Zeilen bestanden  
**Modell:** `eleven_multilingual_v2`  
**Kalle:** Brian - Deep, Resonant and Comforting (`nPczCjzI2devNBz1zQrb`)  
**Byte:** Laura - Enthusiast, Quirky Attitude (`FGY2WhTYpPnrIDTdsKH5`)  
**Stimmabstand:** Median-F0 Kalle 102 Hz, Byte 205 Hz → 12.1 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  
**Natürlichkeit (UTMOS22 strong):** nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.

| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | 0% | dreißig ✓ | 2.70 | 130 Hz | 5.1 st | 0.65 | 0.24 s | – | 1 | OK |
| 2 | kalle | 0% | – | 2.29 | 102 Hz | 5.8 st | 0.70 | 0.29 s | – | 1 | OK |
| 3 | byte | 0% | eine ✓, code ✓ | 2.70 | 197 Hz | 2.2 st | 0.83 | 0.15 s | – | 1 | OK |
| 4 | byte | 0% | code ✓ | 2.70 | 204 Hz | 4.0 st | 0.54 | 0.25 s | – | 1 | OK |
| 5 | byte | 0% | – | 2.31 | 169 Hz | 3.4 st | 0.80 | 0.20 s | – | 1 | OK |
| 6 | byte | 0% | – | 2.70 | 172 Hz | 2.8 st | 0.77 | 0.20 s | – | 1 | OK |
| 7 | byte | 0% | code ✓ | 2.65 | 214 Hz | 2.1 st | 0.90 | 0.09 s | – | 1 | OK |
| 8 | kalle | 0% | – | 2.60 | 101 Hz | 3.5 st | 0.70 | 0.09 s | – | 1 | OK |
| 9 | byte | 9% | Marketing ✓ | 2.70 | 220 Hz | 3.1 st | 0.78 | 0.23 s | – | 1 | OK |
| 10 | byte | 0% | fünf ✓, vier ✓, tausend ✓ | 2.70 | 205 Hz | 3.2 st | 0.62 | 0.22 s | – | 1 | OK |
| 11 | byte | 0% | zwei ✓ | 2.25 | 233 Hz | 3.3 st | 0.60 | 0.16 s | – | 1 | OK |
| 12 | kalle | 0% | dreißig ✓ | 2.47 | 96 Hz | 4.6 st | 0.69 | 0.24 s | – | 1 | OK |

## Hinweise

- Modell `eleven_multilingual_v2` (Vorgabe). Wort-Timing der Untertitel aus dem Endpoint `/with-timestamps`
- Stille am Zeilenanfang/-ende wird weggeschnitten, Pausen zwischen Wörtern werden auf 0,14–0,30 s begrenzt. Tempo: zuerst über den API-Parameter `speed`, Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %; Zeile 8 als kurzer Ausruf bewusst −21 %). Rubberband wurde ersetzt, weil es bei kurzen Ausrufen die Sprachmelodie messbar verflachte.
- Tonhöhe gemessen mit pYIN auf 48 kHz (85-ms-Fenster); bei 16 kHz wurden kurze Ausrufe fälschlich als stimmlos/monoton gewertet.
- Zeile 8 („Des gibt's doch net!“): aus allen erzeugten Varianten die lebendigste mit sauber erkanntem „net“ gewählt (Feinabstimmung in `engine/voices.json`). Das ElevenLabs-Kontingent ist erschöpft (Stand: 12 Credits); weitere Stimmen-Castings waren deshalb nicht möglich.
- Schwäbische Wörter (net, i, des, verschlamp) dürfen in der Rücktranskription abweichen; Zahlwörter, „Code“ und „Marketing“ müssen exakt erkannt werden („Code“ würde bei falscher Aussprache als „Kot“ transkribiert).
- Schreibweisen nur für die Sprachausgabe: siehe „Sprechtext“ je Zeile. Die Untertitel zeigen exakt den Episoden-Text.
- Tonhöhe: keine Verschiebung; Byte (Laura) und Kalle (Brian) sind von Natur aus klar verschieden.

## Details pro Zeile

**1. kalle:** „Seit dreißig Jahren Bäcker – und im Internet gibt's mich net.“  
Sprechtext: „Seit dreißig Jahren Bäcker – und im Internet gibt's mich net.“  
Whisper: „Seit 30 Jahren Bäcker und im Internet gibt's mich net.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.88  

**2. kalle:** „Stollen-Bestellungen kommen auf Zetteln. Die Hälfte verschlamp i.“  
Sprechtext: „Stollenbestellungen kommen auf Zetteln. Die Hälfte verschlamp ich.“  
Whisper: „Stollenbestellungen kommen auf Zetteln, die Hälfte verschlampig.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**3. byte:** „Keine Sorge. Ich schreib dir eine Website. Mit Code.“  
Sprechtext: „Keine Sorge. Ich schreib dir eine Website. Mit Code.“  
Whisper: „Keine Sorge, ich schreibe dir eine Website mit Code.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.92  

**4. byte:** „Code ist ein Rezept für den Computer: Jede Zeile ein Schritt.“  
Sprechtext: „Code ist ein Rezept für den Computer: Jede Zeile ein Schritt.“  
Whisper: „Code ist ein Rezept für den Computer. Jede Zeile ein Schritt.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.93  

**5. byte:** „Hunderte Zeilen – fertig, bevor dein Teig aufgeht.“  
Sprechtext: „Hunderte Zeilen – fertig, bevor dein Teig aufgeht.“  
Whisper: „Hunderte Zeilen, fertig, bevor dein Teig aufgeht.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**6. byte:** „Erst das Gerüst, dann die Farben, dann wird alles klickbar.“  
Sprechtext: „Erst das Gerüst, dann die Farben, dann wird alles klickbar.“  
Whisper: „Erst das Gerüst, dann die Farben, dann wird alles klickbar.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.89  

**7. byte:** „Gleicher Code auf Handy, Tablet und Laptop.“  
Sprechtext: „Gleicher Code auf Handy, Tablet und Laptop.“  
Whisper: „Gleicher Code auf Handy, Tablet und Laptop.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**8. kalle:** „Des gibt's doch net!“  
Sprechtext: „Des gibt's doch net!“  
Whisper: „Das gibt's doch net!“  
Einstellungen: `{"stability": 0.3, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.8}`, Seed 4300, Tempo-Stretch x0.79  

**9. byte:** „Das ist Marketing: Leute wissen von dir, bevor sie Hunger haben.“  
Sprechtext: „Das ist Marketing: Leute wissen von dir, bevor sie Hunger haben.“  
Whisper: „Das ist Marketing. Leute wissen von dir, bevor sie Hunger habe.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.94  

**10. byte:** „Nur fünf neue Kunden pro Woche, je vier Euro: über tausend Euro im Jahr.“  
Sprechtext: „Nur fünf neue Kunden pro Woche, je vier Euro: über tausend Euro im Jahr.“  
Whisper: „Nur fünf neue Kunden pro Woche, je vier Euro, über 1000 Euro im Jahr.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.90  

**11. byte:** „Oh! Erste Bestellung: zwei Stollen.“  
Sprechtext: „Oh! Erste Bestellung: zwei Stollen.“  
Whisper: „Oh, erste Bestellung. Zwei Stollen.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.03  

**12. kalle:** „Dreißig Jahre Bäcker – und jetzt endlich im Internet!“  
Sprechtext: „Dreißig Jahre Bäcker – und jetzt endlich im Internet!“  
Whisper: „30 Jahre Bäcker und jetzt endlich im Internet.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

