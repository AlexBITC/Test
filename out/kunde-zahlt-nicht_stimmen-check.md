# Stimmen-Check: Viel verkauft, kein Geld

**Ergebnis:** nicht alle Zeilen bestanden (siehe unten)  
**Modell:** Piper (lokal, ONNX) – ElevenLabs nicht nutzbar: Kontingent des Free-Tarifs erschöpft (9.988 von 10.000 Zeichen, Reset am 13.12.2026); nötig wären mindestens 755 Zeichen.  
**Kalle:** Thorsten (`de_DE-thorsten-high`) bzw. derselbe Sprecher im Emotions-Modell (`de_DE-thorsten_emotional-medium`: surprised/amused/angry)  
**Byte:** Kerstin (`de_DE-kerstin-low`), Tempo 1,075 (length_scale 0,93)  
**Stimmabstand:** Median-F0 Kalle 128 Hz, Byte 164 Hz → 4.3 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de, Wort-Zeitstempel für Lippensync und Untertitel  
**Natürlichkeit (UTMOS):** nicht installiert/ladbar (HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 % (Dialekt net/des frei), Zahlen und „Liquidität“ exakt, 2,0–2,8 Wörter/s (Hook bis 3,0; gezählt werden gesprochene tts-Wörter), Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, nicht abgeschnitten, keine Pause > 0,4 s.

| # | Sprecher | Stimmung | WER | Zahlen/Begriff | W/s | F0 | Streuung | Pegel | Peak | Pause | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | verzweifelt, laut | 0% | – | 2.58 | 250 Hz | 2.2 st | -16.8 dB | 0.89 | 0.20 s | 3 | OK |
| 2 | kalle | empört, ratlos | 0% | 6 ✓ | 2.72 | 123 Hz | 2.8 st | -17.7 dB | 0.89 | 0.00 s | 1 | OK |
| 3 | byte | selbstsicher, frech | 0% | – | 2.75 | 178 Hz | 2.8 st | -17.5 dB | 0.89 | 0.00 s | 3 | OK |
| 4 | byte | präzise, zügig | 0% | 3 ✓, 620 ✓, 1.860 ✓ | 2.01 | 159 Hz | 2.0 st | -20.9 dB | 0.89 | 0.36 s | 1 | OK |
| 5 | kalle | ungläubig, baff | 0% | 2 ✓ | 2.33 | 138 Hz | 3.5 st | -13.9 dB | 0.89 | 0.00 s | 3 | OK |
| 6 | byte | ernst, ruhig | 0% | 1.500 ✓, 900 ✓, 600 ✓ | 2.15 | 179 Hz | 2.7 st | -18.6 dB | 0.89 | 0.38 s | 2 | OK |
| 7 | kalle | verwirrt, kleinlaut | 0% | – | 2.56 | 121 Hz | 2.2 st | -18.2 dB | 0.89 | 0.00 s | 2 | OK |
| 8 | byte | flink, gut gelaunt | 0% | 3 ✓, 7 ✓, eine ✓ | 2.75 | 164 Hz | 2.1 st | -20.7 dB | 0.89 | 0.22 s | 3 | OK |
| 9 | kalle | beeindruckt, herzlich | 0% | – | 2.50 | 132 Hz | 3.4 st | -16.6 dB | 0.89 | 0.14 s | 3 | OK |
| 10 | byte | klar, erklärend | 9% | Liquidität ✗ | 2.29 | 179 Hz | 2.2 st | -20.1 dB | 0.89 | 0.48 s | 3 | FAIL: 'Liquidität' nicht exakt erkannt; lange Pause(n) [(0.48, 'heißt:'), (0.46, 'kannst.')] |
| 11 | byte | triumphierend, frech | 0% | 2 ✓, 1.260 ✓ | 2.01 | 157 Hz | 2.2 st | -22.1 dB | 0.89 | 0.30 s | 1 | OK |
| 12 | kalle | überglücklich, lachend | 0% | – | 2.75 | 124 Hz | 2.2 st | -17.4 dB | 0.89 | 0.36 s | 2 | OK |
| 13 | byte | verschmitzt, leise | 0% | – | 2.75 | 162 Hz | 2.1 st | -19.1 dB | 0.89 | 0.22 s | 1 | OK |

## Hinweise

- Eingabe der Sprachausgabe ist das Feld `tts`; Untertitel und Bildzahlen nutzen `text` unverändert.
- Audio-Tags (`[laughs]` in Szene 12) unterstützt Piper nicht; sie werden vor der Synthese entfernt.
- Stille am Anfang/Ende wird abgeschnitten (Hook beginnt bei 0,00 s), Pausen in der Zeile auf 0,28 s gekürzt.
- Hook-Zeile: 3 Takes (Thorsten high, Thorsten emotional „surprised“, „angry“); gewählt: bestandener Take mit der höchsten Energie.
- Wort-Zeitstempel: Whisper-Wortzeiten, auf die Untertitel-Wörter abgebildet (Zahlen ausgeschrieben verglichen).
- Cache: `out/cache/<hash>.wav/.json`, Hash aus tts, Stimme, Modell und Einstellungen.

## Details pro Zeile

**1. kalle:** „Viel verkauft. Kein Geld da.“  
tts: „Viel verkauft … kein Geld da!“  
Whisper: „Viel verkauft, kein Geld da.“  
Stimme: `{"model": "de_DE-thorsten_emotional-medium", "speaker": 1, "length_scale": 1.18, "noise_scale": 0.8, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 3.12 W/s, F0 102 Hz ±4.8, -16.0 dB, Fehler: Tempo 3,12 W/s ausserhalb 2,0–3,0 – „Viel verkauft, kein Geld da.“
- Versuch/Take 2: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 2.75 W/s, F0 122 Hz ±2.9, -17.1 dB, Fehler: keine – „Viel verkauft, kein Geld da.“
- Versuch/Take 3: de_DE-thorsten_emotional-medium Sprecher 1, WER 0%, 2.58 W/s, F0 250 Hz ±2.2, -16.8 dB, Fehler: keine – „Viel verkauft, kein Geld da.“

**2. kalle:** „Das Büro gegenüber zahlt seit 6 Wochen net!“  
tts: „Das Büro gegenüber zahlt seit sechs Wochen net!“  
Whisper: „Das Büro gegenüber zahlt seit sechs Wochen Näht.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 1.2, "noise_scale": 0.8, "noise_w": 0.9}`  

**3. byte:** „Ich hol dein Geld zurück.“  
tts: „Ich hol dein Geld zurück.“  
Whisper: „Ich hole dein Geld zurück.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 2.31, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 0%, 4.31 W/s, F0 167 Hz ±3.0, -16.2 dB, Fehler: Tempo 4,31 W/s ausserhalb 2,0–2,8 – „Ich hole dein Geld zurück.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 0%, 3.09 W/s, F0 169 Hz ±3.0, -16.2 dB, Fehler: Tempo 3,09 W/s ausserhalb 2,0–2,8 – „Ich hole dein Geld zurück.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 0%, 2.75 W/s, F0 178 Hz ±2.8, -17.5 dB, Fehler: keine – „Ich hole dein Geld zurück.“

**4. byte:** „3 Rechnungen offen. Je 620 Euro, zusammen 1.860.“  
tts: „Drei Rechnungen offen. Jee sechshundertzwanzig Euro, zusammen tausendachthundertsechzig.“ – Schreibweise angepasst: 'Je' wurde als 'Die/Wir' verstanden  
Whisper: „3 Rechnungen offen, je 620 Euro zusammen 1.860.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.0, "noise_scale": 0.6, "noise_w": 0.8}`  

**5. kalle:** „Wie, in 2 Sekunden?“  
tts: „Wie … in zwei Sekunden?“  
Whisper: „Wie in zwei Sekunden.“  
Stimme: `{"model": "de_DE-thorsten_emotional-medium", "speaker": 6, "length_scale": 1.51, "noise_scale": 0.9, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 2.90 W/s, F0 135 Hz ±2.0, -13.8 dB, Fehler: Tempo 2,90 W/s ausserhalb 2,0–2,8 – „Wie in zwei Sekunden.“
- Versuch/Take 2: de_DE-thorsten_emotional-medium Sprecher 6, WER 50%, 2.33 W/s, F0 138 Hz ±2.8, -14.7 dB, Fehler: WER 50% > 10 % – „Wien zwei Sekunden.“
- Versuch/Take 3: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 2.33 W/s, F0 138 Hz ±3.5, -13.9 dB, Fehler: keine – „Wie in zwei Sekunden.“

**6. byte:** „Freitag will die Mühle 1.500 Euro. Auf dem Konto: 900. Fehlen 600.“  
tts: „Freitag willl die Mühle tausendfünfhundert Euro. Auf dem Konto neunhundert. Fehlen sechshundert.“ – Schreibweise angepasst: 'will' wurde als 'wird' verstanden; Doppelpunkte erzeugten Pausen > 0,4 s  
Whisper: „Freitag will die Mühle 1500 Euro, auf dem Konto 900, fehlen 600.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.0, "noise_scale": 0.5, "noise_w": 0.8}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 0%, 2.24 W/s, F0 176 Hz ±2.6, -18.9 dB, Fehler: lange Pause(n) [(0.42, '900.')] – „Freitag will die Mühle 1500 Euro, auf dem Konto 900, fehlen 600.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 0%, 2.15 W/s, F0 179 Hz ±2.7, -18.6 dB, Fehler: keine – „Freitag will die Mühle 1500 Euro, auf dem Konto 900, fehlen 600.“

**7. kalle:** „Obwohl ich so viel verkauft hab?“  
tts: „Obwohl ich so viel verkauft hab?“  
Whisper: „Obwohl ich so viel verkauft habe.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 2.107, "noise_scale": 0.8, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 4.29 W/s, F0 127 Hz ±2.2, -16.9 dB, Fehler: Tempo 4,29 W/s ausserhalb 2,0–2,8 – „Obwohl ich so viel verkauft habe.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 2.56 W/s, F0 121 Hz ±2.2, -18.2 dB, Fehler: keine – „Obwohl ich so viel verkauft habe.“

**8. byte:** „Ich schreib eine höfliche Erinnerung: alle 3 Rechnungen, Zahlung in 7 Tagen.“  
tts: „Ich schreib eine höfliche Erinnerung: alle drei Rechnungen, Zahlung in sieben Tagen.“  
Whisper: „Ich schreibe eine höfliche Erinnerung, alle drei Rechnungen, Zahlung in sieben Tagen.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.208, "noise_scale": 0.9, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 8%, 2.90 W/s, F0 164 Hz ±2.3, -21.9 dB, Fehler: Tempo 2,90 W/s ausserhalb 2,0–2,8 – „Ich schreibe eine höfliche Erinnerung. Alle drei Rechnungen, Zahlungen in sieben Tagen.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 17%, 2.53 W/s, F0 161 Hz ±2.4, -21.4 dB, Fehler: WER 17% > 10 % – „Ich schreibe eine höfliche Erinnerung, alle drei Rechnungen und Zahlungen in sieben Tagen.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 0%, 2.75 W/s, F0 164 Hz ±2.1, -20.7 dB, Fehler: keine – „Ich schreibe eine höfliche Erinnerung, alle drei Rechnungen, Zahlung in sieben Tagen.“

**9. kalle:** „Höflich und klar. So schreib ich des nie!“  
tts: „Höflich und klar. So schreib ich des nie!“  
Whisper: „Höflich und klar, so schreibe ich das nie.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 1.939, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 3.01 W/s, F0 124 Hz ±3.6, -15.5 dB, Fehler: Tempo 3,01 W/s ausserhalb 2,0–2,8 – „Höflich und klar, so schreibe ich das nie.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 2.86 W/s, F0 135 Hz ±3.5, -16.3 dB, Fehler: Tempo 2,86 W/s ausserhalb 2,0–2,8 – „Höflich und klar. So schreibe ich das nie.“
- Versuch/Take 3: de_DE-thorsten-high Sprecher None, WER 0%, 2.50 W/s, F0 132 Hz ±3.4, -16.6 dB, Fehler: keine – „Höflich und klar, so schreibe ich das nie.“

**10. byte:** „Liquidität heißt: Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“  
tts: „Liquidität heißt: Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“  
Whisper: „Dequitität heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.0, "noise_scale": 0.5, "noise_w": 0.8}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 18%, 2.28 W/s, F0 178 Hz ±2.5, -20.2 dB, Fehler: WER 18% > 10 %; 'Liquidität' nicht exakt erkannt; lange Pause(n) [(0.52, 'kannst.')] – „Die Qualität heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 9%, 2.29 W/s, F0 179 Hz ±2.2, -20.1 dB, Fehler: 'Liquidität' nicht exakt erkannt; lange Pause(n) [(0.48, 'heißt:'), (0.46, 'kannst.')] – „Dequitität heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 9%, 2.25 W/s, F0 179 Hz ±2.6, -20.6 dB, Fehler: 'Liquidität' nicht exakt erkannt; lange Pause(n) [(0.5, 'kannst.')] – „Dequitität heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“

**11. byte:** „2 Tage später: Geld da, Mühle bezahlt, 1.260 Euro übrig.“  
tts: „Zwei Tage später: Geld da, Mühle bezahlt, tausendzweihundertsechzig Euro übrig.“  
Whisper: „Zwei Tage später Geld da, Mühle bezahlt, 1260 Euro übrig.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.0, "noise_scale": 0.8, "noise_w": 0.9}`  

**12. kalle:** „Ha! Byte, du bist Gold wert!“  
tts: „Ha! Bait, du bist Gold wert!“ (Tag entfernt) – Schreibweise angepasst: Emotions-Modell sprach 'Herr Veit'; 'Byte' englisch ausgesprochen ('Bait')  
Whisper: „Ha, Byte, du bist Gold wert.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 1.506, "noise_scale": 0.7, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 3.61 W/s, F0 124 Hz ±1.9, -17.6 dB, Fehler: Tempo 3,61 W/s ausserhalb 2,0–2,8 – „Ha, Byte, du bist Gold wert.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 2.75 W/s, F0 124 Hz ±2.2, -17.4 dB, Fehler: keine – „Ha, Byte, du bist Gold wert.“

**13. byte:** „Merk dir: Viel verkauft heißt nicht …“  
tts: „merk dirr: Viel verkauft … heißt nicht …“ – Schreibweise angepasst: 'Merk dir' wurde als 'Merkt ihr' verstanden  
Whisper: „Merk dir, viel verkauft heißt nicht.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.05, "noise_scale": 0.75, "noise_w": 0.8}`  

