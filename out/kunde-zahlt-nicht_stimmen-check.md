# Stimmen-Check: Viel verkauft, kein Geld

**Ergebnis:** alle Zeilen bestanden  
**Modell:** `eleven_multilingual_v2`  
**Kalle:** Brian - Deep, Resonant and Comforting (`nPczCjzI2devNBz1zQrb`)  
**Byte:** Laura - Enthusiast, Quirky Attitude (`FGY2WhTYpPnrIDTdsKH5`)  
**Stimmabstand:** Median-F0 Kalle 127 Hz, Byte 189 Hz → 6.9 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  
**Natürlichkeit (UTMOS22 strong):** nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.

| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | 0% | – | 2.15 | 145 Hz | 8.2 st | 0.68 | 0.49 s | – | 1 | OK |
| 2 | kalle | 0% | 6 ✓ | 2.65 | 120 Hz | 4.4 st | 0.64 | 0.11 s | – | 1 | OK |
| 3 | byte | 0% | – | 2.72 | 266 Hz | 2.4 st | 0.61 | 0.09 s | – | 2 | OK |
| 4 | byte | 0% | 3 ✓, 620 ✓, 1.860 ✓ | 2.25 | 187 Hz | 2.8 st | 0.72 | 0.17 s | – | 2 | OK |
| 5 | kalle | 0% | 2 ✓ | 2.65 | 132 Hz | 4.7 st | 0.47 | 0.36 s | – | 1 | OK |
| 6 | byte | 0% | 1.500 ✓, 900 ✓, 600 ✓ | 2.09 | 182 Hz | 3.4 st | 0.73 | 0.24 s | – | 1 | OK |
| 7 | kalle | 0% | – | 2.69 | 143 Hz | 3.3 st | 0.53 | 0.10 s | – | 2 | OK |
| 8 | byte | 0% | 3 ✓, 7 ✓, eine ✓ | 2.42 | 193 Hz | 3.5 st | 0.79 | 0.22 s | – | 1 | OK |
| 9 | kalle | 0% | – | 2.52 | 107 Hz | 5.1 st | 0.64 | 0.32 s | – | 2 | OK |
| 10 | byte | 0% | Liquidität ✓ | 2.29 | 181 Hz | 3.8 st | 0.65 | 0.23 s | – | 1 | OK |
| 11 | byte | 0% | 2 ✓, 1.260 ✓ | 2.17 | 198 Hz | 3.2 st | 0.66 | 0.15 s | – | 1 | OK |
| 12 | kalle | 0% | – | 2.65 | 123 Hz | 2.6 st | 0.74 | 0.30 s | – | 1 | OK |
| 13 | byte | 0% | – | 2.70 | 189 Hz | 2.6 st | 0.89 | 0.13 s | – | 1 | OK |

## Hinweise

- Modell `eleven_multilingual_v2` (Vorgabe). Wort-Timing der Untertitel aus dem Endpoint `/with-timestamps`
- Stille am Zeilenanfang/-ende wird weggeschnitten, Pausen zwischen Wörtern werden auf 0,14–0,30 s begrenzt. Tempo: zuerst über den API-Parameter `speed`, Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %; Zeile 8 als kurzer Ausruf bewusst −21 %). Rubberband wurde ersetzt, weil es bei kurzen Ausrufen die Sprachmelodie messbar verflachte.
- Tonhöhe gemessen mit pYIN auf 48 kHz (85-ms-Fenster); bei 16 kHz wurden kurze Ausrufe fälschlich als stimmlos/monoton gewertet.
- Zeile 8 („Des gibt's doch net!“): aus allen erzeugten Varianten die lebendigste mit sauber erkanntem „net“ gewählt (Feinabstimmung in `engine/voices.json`). Das ElevenLabs-Kontingent ist erschöpft (Stand: 12 Credits); weitere Stimmen-Castings waren deshalb nicht möglich.
- Schwäbische Wörter (net, i, des, verschlamp) dürfen in der Rücktranskription abweichen; Zahlwörter, „Code“ und „Marketing“ müssen exakt erkannt werden („Code“ würde bei falscher Aussprache als „Kot“ transkribiert).
- Schreibweisen nur für die Sprachausgabe: siehe „Sprechtext“ je Zeile. Die Untertitel zeigen exakt den Episoden-Text.
- Tonhöhe: keine Verschiebung; Byte (Laura) und Kalle (Brian) sind von Natur aus klar verschieden.

## Details pro Zeile

**1. kalle:** „Viel verkauft. Kein Geld da.“  
Sprechtext: „Viel verkauft … Kein Geld da!“  
Whisper: „Viel verkauft. Kein Geld da.“  
Einstellungen: `{"stability": 0.3, "similarity_boost": 0.75, "style": 0.6, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.04  

**2. kalle:** „Das Büro gegenüber zahlt seit 6 Wochen net!“  
Sprechtext: „Das Büro gegenüber zahlt seit sechs Wochen net!“  
Whisper: „Das Büro gegenüber zahlt seit sechs Wochen net.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.94  

**3. byte:** „Ich hol dein Geld zurück.“  
Sprechtext: „Ich hol dein Geld zurück.“  
Whisper: „Ich hole dein Geld zurück.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x0.88  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.88, WER 0%, 3.54 W/s, Schreibweise –, Fehler: Tempo 3,54 W/s ausserhalb 2,0–2,8 – „Ich hol dein Geld zurück.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x0.88, WER 0%, 2.72 W/s, Schreibweise –, Fehler: keine – „Ich hole dein Geld zurück.“

**4. byte:** „3 Rechnungen offen. Je 620 Euro, zusammen 1.860.“  
Sprechtext: „drei Rechnungen offen. Je sechshundertzwanzig Euro, zusammen tausendachthundertsechzig.“  
Whisper: „Drei Rechnungen offen. Je 620 Euro zusammen 1.860.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 1.2}`, Seed 4217, Tempo-Stretch x1.11  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x1.15, WER 0%, 1.62 W/s, Schreibweise –, Fehler: Tempo 1,62 W/s ausserhalb 2,0–2,8 – „Drei Rechnungen offen, je 620 Euro, zusammen 1.860.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.11, WER 0%, 2.25 W/s, Schreibweise –, Fehler: keine – „Drei Rechnungen offen. Je 620 Euro zusammen 1.860.“

**5. kalle:** „Wie, in 2 Sekunden?“  
Sprechtext: „Wie, in zwei Sekunden?“  
Whisper: „Wie? In zwei Sekunden?“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.91  

**6. byte:** „Freitag will die Mühle 1.500 Euro. Auf dem Konto: 900. Fehlen 600.“  
Sprechtext: „Freitag will die Mühle tausendfünfhundert Euro. Auf dem Konto: neunhundert. Fehlen sechshundert.“  
Whisper: „Freitag will die Mühle 1500 Euro, auf dem Konto 900, fehlen 600.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.15  

**7. kalle:** „Obwohl ich so viel verkauft hab?“  
Sprechtext: „Obwohl ich so viel verkauft hab?“  
Whisper: „Obwohl ich so viel verkauft hab?“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 0%, 2.91 W/s, Schreibweise –, Fehler: Tempo 2,91 W/s ausserhalb 2,0–2,8 – „Obwohl ich so viel verkauft habe?“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.00, WER 0%, 2.69 W/s, Schreibweise –, Fehler: keine – „Obwohl ich so viel verkauft hab?“

**8. byte:** „Ich schreib eine höfliche Erinnerung: alle 3 Rechnungen, Zahlung in 7 Tagen.“  
Sprechtext: „Ich schreib eine höfliche Erinnerung: alle drei Rechnungen, Zahlung in sieben Tagen.“  
Whisper: „Ich schreibe eine höfliche Erinnerung. Alle drei Rechnungen, Zahlung in sieben Tagen.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**9. kalle:** „Höflich und klar. So schreib ich des nie!“  
Sprechtext: „Höflich und klar. So schreib ich des nie!“  
Whisper: „Höflich und klar. So schreibe ich des nie.“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 0%, 3.10 W/s, Schreibweise –, Fehler: Tempo 3,10 W/s ausserhalb 2,0–2,8 – „Höflich und klar. So schreibe ich das nie.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.00, WER 0%, 2.52 W/s, Schreibweise –, Fehler: keine – „Höflich und klar. So schreibe ich des nie.“

**10. byte:** „Liquidität heißt: Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“  
Sprechtext: „Liquidität heißt: Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“  
Whisper: „Liquidität heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**11. byte:** „2 Tage später: Geld da, Mühle bezahlt, 1.260 Euro übrig.“  
Sprechtext: „zwei Tage später: Geld da, Mühle bezahlt, tausendzweihundertsechzig Euro übrig.“  
Whisper: „Zwei Tage später, Geld da, Mühle bezahlt, 1260 Euro übrig.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.15  

**12. kalle:** „Ha! Byte, du bist Gold wert!“  
Sprechtext: „Haha! Byte, du bist Gold wert!“  
Whisper: „Haha, Byte, du bist Gold wert.“  
Einstellungen: `{"stability": 0.3, "similarity_boost": 0.75, "style": 0.65, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.88  

**13. byte:** „Merk dir: Viel verkauft heißt nicht …“  
Sprechtext: „Merke dir: Viel verkauft heißt nicht …“  
Whisper: „Merke dir, viel verkauft heißt nicht.“  
Einstellungen: `{"stability": 0.6, "similarity_boost": 0.75, "style": 0.1, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.94  

