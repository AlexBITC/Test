# Stimmen-Check: Viel verkauft, kein Geld

**Ergebnis:** nicht alle Zeilen bestanden (siehe unten)  
**Modell:** Piper (lokal, ONNX) – ElevenLabs nicht nutzbar: Kontingent des Free-Tarifs erschöpft (9.988 von 10.000 Zeichen, Reset am 13.12.2026); nötig wären mindestens 755 Zeichen.  
**Kalle:** Thorsten (`de_DE-thorsten-high`) bzw. derselbe Sprecher im Emotions-Modell (`de_DE-thorsten_emotional-medium`: surprised/amused/angry)  
**Byte:** Kerstin (`de_DE-kerstin-low`), Tempo 1,075 (length_scale 0,93)  
**Stimmabstand:** Median-F0 Kalle 128 Hz, Byte 167 Hz → 4.6 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de, Wort-Zeitstempel für Lippensync und Untertitel  
**Natürlichkeit (UTMOS):** nicht installiert/ladbar (HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 % (Dialekt net/des frei), Zahlen und „Liquidität“ exakt, 2,0–2,8 Wörter/s (Hook bis 3,0; gezählt werden gesprochene tts-Wörter), Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, nicht abgeschnitten, keine Pause > 0,4 s.

| # | Sprecher | Stimmung | WER | Zahlen/Begriff | W/s | F0 | Streuung | Pegel | Peak | Pause | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | verzweifelt, laut | 0% | – | 3.47 | 105 Hz | 4.5 st | -17.5 dB | 0.89 | 0.00 s | 3 | FAIL: Tempo 3,47 W/s ausserhalb 2,0–3,0 |
| 2 | kalle | empört, ratlos | 0% | 6 ✓ | 3.36 | 123 Hz | 2.8 st | -18.1 dB | 0.89 | 0.00 s | 3 | FAIL: Tempo 3,36 W/s ausserhalb 2,0–2,8 |
| 3 | byte | selbstsicher, frech | 20% | – | 2.69 | 171 Hz | 3.3 st | -16.7 dB | 0.89 | 0.01 s | 3 | FAIL: WER 20% > 10 % |
| 4 | byte | präzise, zügig | 12% | 3 ✓, 620 ✓, 1.860 ✓ | 2.48 | 163 Hz | 1.7 st | -20.4 dB | 0.89 | 0.00 s | 3 | FAIL: WER 12% > 10 % |
| 5 | kalle | ungläubig, baff | 0% | 2 ✓ | 2.47 | 132 Hz | 2.1 st | -14.1 dB | 0.89 | 0.00 s | 3 | FAIL: Ende wirkt abgeschnitten |
| 6 | byte | ernst, ruhig | 17% | 1.500 ✓, 900 ✓, 600 ✓ | 2.34 | 171 Hz | 2.4 st | -18.3 dB | 0.89 | 0.28 s | 3 | FAIL: WER 17% > 10 % |
| 7 | kalle | verwirrt, kleinlaut | 0% | – | 2.56 | 123 Hz | 2.4 st | -18.6 dB | 0.89 | 0.00 s | 3 | OK |
| 8 | byte | flink, gut gelaunt | 8% | 3 ✓, 7 ✓, eine ✓ | 2.67 | 163 Hz | 2.2 st | -21.0 dB | 0.89 | 0.24 s | 2 | OK |
| 9 | kalle | beeindruckt, herzlich | 0% | – | 2.27 | 156 Hz | 4.7 st | -16.0 dB | 0.89 | 0.12 s | 3 | OK |
| 10 | byte | klar, erklärend | 0% | Liquidität ✓ | 2.13 | 174 Hz | 2.3 st | -21.1 dB | 0.89 | 0.40 s | 3 | OK |
| 11 | byte | triumphierend, frech | 0% | 2 ✓, 1.260 ✓ | 2.12 | 156 Hz | 2.2 st | -23.1 dB | 0.89 | 0.22 s | 2 | OK |
| 12 | kalle | überglücklich, lachend | 33% | – | 2.68 | 171 Hz | 4.8 st | -13.5 dB | 0.89 | 0.40 s | 3 | FAIL: WER 33% > 10 %; lange Pause(n) [(0.4, 'Byte,')] |
| 13 | byte | verschmitzt, leise | 33% | – | 2.70 | 167 Hz | 2.3 st | -20.2 dB | 0.89 | 0.40 s | 3 | FAIL: WER 33% > 10 %; lange Pause(n) [(0.4, 'dir:')] |

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
Whisper: „Viel verkauft kein Geld da.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 0.92, "noise_scale": 0.8, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 3.47 W/s, F0 105 Hz ±4.5, -17.5 dB, Fehler: Tempo 3,47 W/s ausserhalb 2,0–3,0 – „Viel verkauft kein Geld da.“
- Versuch/Take 2: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 3.12 W/s, F0 133 Hz ±3.2, -16.6 dB, Fehler: Tempo 3,12 W/s ausserhalb 2,0–3,0; Ende wirkt abgeschnitten – „Viel verkauft kein Geld da.“
- Versuch/Take 3: de_DE-thorsten_emotional-medium Sprecher 1, WER 20%, 3.05 W/s, F0 240 Hz ±3.5, -16.2 dB, Fehler: WER 20% > 10 %; Tempo 3,05 W/s ausserhalb 2,0–3,0 – „Verkauft kein Geld da!“

**2. kalle:** „Das Büro gegenüber zahlt seit 6 Wochen net!“  
tts: „Das Büro gegenüber zahlt seit sechs Wochen net!“  
Whisper: „Das Büro gegenüber zahlt seit sechs Wochen nicht.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 0.93, "noise_scale": 0.85, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 3.36 W/s, F0 123 Hz ±2.8, -18.1 dB, Fehler: Tempo 3,36 W/s ausserhalb 2,0–2,8 – „Das Büro gegenüber zahlt seit sechs Wochen nicht.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 2.86 W/s, F0 121 Hz ±2.6, -16.3 dB, Fehler: Tempo 2,86 W/s ausserhalb 2,0–2,8 – „das Büro gegenüber zahlt seit sechs Wochen nicht.“
- Versuch/Take 3: de_DE-thorsten-high Sprecher None, WER 12%, 2.35 W/s, F0 119 Hz ±3.4, -17.9 dB, Fehler: WER 12% > 10 % – „das Büro gegenüber zahls seit sechs Wochen näht.“

**3. byte:** „Ich hol dein Geld zurück.“  
tts: „Ich hol dein Geld zurück.“  
Whisper: „Ich hole dein Geld zurück.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 2.383, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 20%, 4.31 W/s, F0 180 Hz ±2.3, -16.9 dB, Fehler: WER 20% > 10 %; Tempo 4,31 W/s ausserhalb 2,0–2,8 – „Ich hole dein Geld zurück.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 20%, 3.42 W/s, F0 188 Hz ±2.9, -16.2 dB, Fehler: WER 20% > 10 %; Tempo 3,42 W/s ausserhalb 2,0–2,8 – „Ich hole dein Geld zurück.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 20%, 2.69 W/s, F0 171 Hz ±3.3, -16.7 dB, Fehler: WER 20% > 10 % – „Ich hole dein Geld zurück.“

**4. byte:** „3 Rechnungen offen. Je 620 Euro, zusammen 1.860.“  
tts: „Drei Rechnungen offen. Je sechshundertzwanzig Euro, zusammen tausendachthundertsechzig.“  
Whisper: „Drei Rechnungen offen. Wir 620 Euro zusammen 1.860.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 0.575, "noise_scale": 0.6, "noise_w": 0.8}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 38%, 2.00 W/s, F0 164 Hz ±2.0, -20.8 dB, Fehler: WER 38% > 10 %; Tempo 2,00 W/s ausserhalb 2,0–2,8 – „drei Rechnungen offen. Die 620 Euro zusammen mit 1.860 Euro.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 12%, 1.79 W/s, F0 164 Hz ±2.0, -20.6 dB, Fehler: WER 12% > 10 %; Tempo 1,79 W/s ausserhalb 2,0–2,8 – „Drei Rechnungen offen, hier 620 Euro zusammen 1860.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 12%, 2.48 W/s, F0 163 Hz ±1.7, -20.4 dB, Fehler: WER 12% > 10 % – „Drei Rechnungen offen. Wir 620 Euro zusammen 1.860.“

**5. kalle:** „Wie, in 2 Sekunden?“  
tts: „Wie … in zwei Sekunden?“  
Whisper: „wie in zwei Sekunden.“  
Stimme: `{"model": "de_DE-thorsten_emotional-medium", "speaker": 6, "length_scale": 1.412, "noise_scale": 0.7, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 3.39 W/s, F0 137 Hz ±2.0, -13.5 dB, Fehler: Tempo 3,39 W/s ausserhalb 2,0–2,8; Ende wirkt abgeschnitten – „Wie in zwei Sekunden!“
- Versuch/Take 2: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 2.47 W/s, F0 132 Hz ±2.1, -14.1 dB, Fehler: Ende wirkt abgeschnitten – „wie in zwei Sekunden.“
- Versuch/Take 3: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 2.56 W/s, F0 140 Hz ±2.7, -13.4 dB, Fehler: Ende wirkt abgeschnitten – „wie in zwei Sekunden.“

**6. byte:** „Freitag will die Mühle 1.500 Euro. Auf dem Konto: 900. Fehlen 600.“  
tts: „Freitag will die Mühle tausendfünfhundert Euro. Auf dem Konto: neunhundert. Fehlen: sechshundert.“  
Whisper: „Freitag wird die Mühle 1500 Euro. Auf dem Konto hoch 900. Fehlen 600.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 0.93, "noise_scale": 0.5, "noise_w": 0.8}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 25%, 2.22 W/s, F0 175 Hz ±2.3, -18.6 dB, Fehler: WER 25% > 10 %; lange Pause(n) [(0.53, 'Fehlen')] – „Freitag wird die Mühle 1500 Euro, auf dem Konto 900, wähle nur 600.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 17%, 2.34 W/s, F0 171 Hz ±2.4, -18.3 dB, Fehler: WER 17% > 10 % – „Freitag wird die Mühle 1500 Euro. Auf dem Konto hoch 900. Fehlen 600.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 17%, 2.27 W/s, F0 174 Hz ±2.6, -19.0 dB, Fehler: WER 17% > 10 %; lange Pause(n) [(0.4, '900.')] – „Freitag will die Mühle 1500 Euro, auf dem Konto auch 900, fehlen nur 600.“

**7. kalle:** „Obwohl ich so viel verkauft hab?“  
tts: „Obwohl ich so viel verkauft hab?“  
Whisper: „Obwohl ich so viel verkauft habe.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 2.105, "noise_scale": 0.8, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 4.35 W/s, F0 117 Hz ±2.9, -17.4 dB, Fehler: Tempo 4,35 W/s ausserhalb 2,0–2,8 – „Obwohl ich so viel verkauft habe.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 3.03 W/s, F0 122 Hz ±2.3, -17.9 dB, Fehler: Tempo 3,03 W/s ausserhalb 2,0–2,8 – „Obwohl ich so viel verkauft habe.“
- Versuch/Take 3: de_DE-thorsten-high Sprecher None, WER 0%, 2.56 W/s, F0 123 Hz ±2.4, -18.6 dB, Fehler: keine – „Obwohl ich so viel verkauft habe.“

**8. byte:** „Ich schreib eine höfliche Erinnerung: alle 3 Rechnungen, Zahlung in 7 Tagen.“  
tts: „Ich schreib eine höfliche Erinnerung: alle drei Rechnungen, Zahlung in sieben Tagen.“  
Whisper: „Ich schreibe eine höfliche Erinnerung, alle drei Rechnungen, Zahlungen in sieben Tagen.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.129, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 0%, 2.91 W/s, F0 164 Hz ±2.2, -20.0 dB, Fehler: Tempo 2,91 W/s ausserhalb 2,0–2,8 – „Ich schreibe eine höfliche Erinnerung, alle drei Rechnungen, Zahlung in sieben Tagen.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 8%, 2.67 W/s, F0 163 Hz ±2.2, -21.0 dB, Fehler: keine – „Ich schreibe eine höfliche Erinnerung, alle drei Rechnungen, Zahlungen in sieben Tagen.“

**9. kalle:** „Höflich und klar. So schreib ich des nie!“  
tts: „Höflich und klar. So schreib ich des nie!“  
Whisper: „Höflich und klar, so schreibe ich das nie.“  
Stimme: `{"model": "de_DE-thorsten_emotional-medium", "speaker": 0, "length_scale": 1.577, "noise_scale": 0.7, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten_emotional-medium Sprecher 0, WER 0%, 3.23 W/s, F0 186 Hz ±5.1, -16.1 dB, Fehler: Tempo 3,23 W/s ausserhalb 2,0–2,8; Ende wirkt abgeschnitten – „Höflich und klar, so schreibe ich das nie.“
- Versuch/Take 2: de_DE-thorsten_emotional-medium Sprecher 0, WER 0%, 2.82 W/s, F0 177 Hz ±5.4, -15.6 dB, Fehler: Tempo 2,82 W/s ausserhalb 2,0–2,8; Ende wirkt abgeschnitten – „Höflich und klar, so schreibe ich das nie.“
- Versuch/Take 3: de_DE-thorsten_emotional-medium Sprecher 0, WER 0%, 2.27 W/s, F0 156 Hz ±4.7, -16.0 dB, Fehler: keine – „Höflich und klar, so schreibe ich das nie.“

**10. byte:** „Liquidität heißt: Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“  
tts: „Liquidität heißt: Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“  
Whisper: „Liquidität heißt, Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 0.93, "noise_scale": 0.9, "noise_w": 0.8}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 36%, 2.09 W/s, F0 178 Hz ±2.2, -21.8 dB, Fehler: WER 36% > 10 %; 'Liquidität' nicht exakt erkannt; lange Pause(n) [(0.69, 'Liquidität'), (0.54, 'kannst.')] – „Die Qualität heißt, dass du jetzt zahlen kannst, nicht versprochenes Geld.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 9%, 2.17 W/s, F0 179 Hz ±2.4, -21.1 dB, Fehler: 'Liquidität' nicht exakt erkannt; lange Pause(n) [(0.65, 'Liquidität'), (0.54, 'kannst.')] – „Dequitität heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 0%, 2.13 W/s, F0 174 Hz ±2.3, -21.1 dB, Fehler: keine – „Liquidität heißt, Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“

**11. byte:** „2 Tage später: Geld da, Mühle bezahlt, 1.260 Euro übrig.“  
tts: „Zwei Tage später: Geld da, Mühle bezahlt, tausendzweihundertsechzig Euro übrig.“  
Whisper: „Zwei Tage später Geld da, Mühle bezahlt, 1260 Euro übrig.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 0.766, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 0%, 1.98 W/s, F0 156 Hz ±2.8, -22.3 dB, Fehler: Tempo 1,98 W/s ausserhalb 2,0–2,8 – „Zwei Tage später, Geld da, Mühle bezahlt, 1260 Euro übrig.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 0%, 2.12 W/s, F0 156 Hz ±2.2, -23.1 dB, Fehler: keine – „Zwei Tage später Geld da, Mühle bezahlt, 1260 Euro übrig.“

**12. kalle:** „Ha! Byte, du bist Gold wert!“  
tts: „Ha! Byte, du bist Gold wert!“ (Tag entfernt)  
Whisper: „Heid, du bist Gold wert!“  
Stimme: `{"model": "de_DE-thorsten_emotional-medium", "speaker": 0, "length_scale": 1.398, "noise_scale": 0.7, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten_emotional-medium Sprecher 0, WER 67%, 3.36 W/s, F0 164 Hz ±3.9, -14.3 dB, Fehler: WER 67% > 10 %; Tempo 3,36 W/s ausserhalb 2,0–2,8; Ende wirkt abgeschnitten – „Da weit, du bist Goldwerf!“
- Versuch/Take 2: de_DE-thorsten_emotional-medium Sprecher 0, WER 33%, 2.68 W/s, F0 171 Hz ±4.8, -13.5 dB, Fehler: WER 33% > 10 %; lange Pause(n) [(0.4, 'Byte,')] – „Heid, du bist Gold wert!“
- Versuch/Take 3: de_DE-thorsten_emotional-medium Sprecher 0, WER 33%, 2.88 W/s, F0 180 Hz ±5.5, -14.5 dB, Fehler: WER 33% > 10 %; Tempo 2,88 W/s ausserhalb 2,0–2,8 – „Äh, Veit, du bist Gold wert?“

**13. byte:** „Merk dir: Viel verkauft heißt nicht …“  
tts: „Merk dir: Viel verkauft … heißt nicht …“  
Whisper: „Merkt ihr, viel verkauft heißt nicht.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 0.97, "noise_scale": 0.75, "noise_w": 0.8}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 33%, 2.70 W/s, F0 167 Hz ±2.3, -20.2 dB, Fehler: WER 33% > 10 %; lange Pause(n) [(0.4, 'dir:')] – „Merkt ihr, viel verkauft heißt nicht.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 33%, 2.83 W/s, F0 163 Hz ±2.3, -20.2 dB, Fehler: WER 33% > 10 %; Tempo 2,83 W/s ausserhalb 2,0–2,8 – „Merkt ihr, viel verkauft heißt nicht.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 33%, 2.46 W/s, F0 162 Hz ±2.4, -20.6 dB, Fehler: WER 33% > 10 %; lange Pause(n) [(0.5, 'dir:')] – „Merkt ihr, viel verkauft heißt nicht.“

