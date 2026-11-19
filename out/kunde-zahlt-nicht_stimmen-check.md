# Stimmen-Check: Viel verkauft, kein Geld

**Ergebnis:** alle Zeilen bestanden  
**Modell:** Piper (lokal, ONNX) – ElevenLabs nicht nutzbar: Kontingent des Free-Tarifs erschöpft (9.988 von 10.000 Zeichen, Reset am 13.12.2026); nötig wären mindestens 755 Zeichen.  
**Kalle:** Thorsten (`de_DE-thorsten-high`) bzw. derselbe Sprecher im Emotions-Modell (`de_DE-thorsten_emotional-medium`: surprised/amused/angry)  
**Byte:** Kerstin (`de_DE-kerstin-low`), Tempo je Zeile per length_scale geregelt (Ziel 2,0–2,8 W/s)  
**Stimmabstand:** Median-F0 Kalle 121 Hz, Byte 163 Hz → 5.1 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de, Wort-Zeitstempel für Lippensync und Untertitel  
**Natürlichkeit (UTMOS):** nicht installiert/ladbar (HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 % (Dialekt net/des frei), Zahlen und „Liquidität“ exakt, 2,0–2,8 Wörter/s (Hook bis 3,0; gezählt werden gesprochene tts-Wörter), Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, nicht abgeschnitten, keine Pause > 0,4 s.

| # | Sprecher | Stimmung | WER | Zahlen/Begriff | W/s | F0 | Streuung | Pegel | Peak | Pause | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | verzweifelt, laut | 0% | – | 2.75 | 240 Hz | 2.6 st | -13.7 dB | 0.89 | 0.09 s | 3 | OK |
| 2 | kalle | empört, ratlos | 0% | 6 ✓ | 2.67 | 117 Hz | 3.4 st | -16.9 dB | 0.89 | 0.14 s | 2 | OK |
| 3 | byte | selbstsicher, frech | 0% | – | 2.63 | 177 Hz | 2.9 st | -17.1 dB | 0.89 | 0.16 s | 3 | OK |
| 4 | byte | präzise, zügig | 0% | 3 ✓, 620 ✓, 1.860 ✓ | 2.02 | 163 Hz | 2.1 st | -20.8 dB | 0.89 | 0.22 s | 2 | OK |
| 5 | kalle | ungläubig, baff | 0% | 2 ✓ | 2.30 | 143 Hz | 2.7 st | -13.8 dB | 0.89 | 0.12 s | 2 | OK |
| 6 | byte | ernst, ruhig | 0% | 1.500 ✓, 900 ✓, 600 ✓ | 2.21 | 177 Hz | 2.6 st | -18.5 dB | 0.89 | 0.23 s | 1 | OK |
| 7 | kalle | verwirrt, kleinlaut | 0% | – | 2.78 | 120 Hz | 3.7 st | -18.1 dB | 0.89 | 0.14 s | 2 | OK |
| 8 | byte | flink, gut gelaunt | 8% | 3 ✓, 7 ✓, eine ✓ | 2.61 | 161 Hz | 2.2 st | -21.2 dB | 0.89 | 0.21 s | 2 | OK |
| 9 | kalle | beeindruckt, herzlich | 0% | – | 2.63 | 123 Hz | 3.5 st | -17.3 dB | 0.89 | 0.22 s | 2 | OK |
| 10 | byte | klar, erklärend | 0% | Liquidität ✓ | 2.23 | 180 Hz | 2.2 st | -20.4 dB | 0.89 | 0.26 s | 2 | OK |
| 11 | byte | triumphierend, frech | 0% | 2 ✓, 1.260 ✓ | 2.00 | 155 Hz | 2.3 st | -22.8 dB | 0.89 | 0.26 s | 1 | OK |
| 12 | kalle | überglücklich, lachend | 0% | – | 2.56 | 117 Hz | 2.6 st | -16.9 dB | 0.89 | 0.26 s | 3 | OK |
| 13 | byte | verschmitzt, leise | 0% | – | 2.70 | 161 Hz | 2.2 st | -19.1 dB | 0.89 | 0.22 s | 1 | OK |

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
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 3.21 W/s, F0 107 Hz ±4.9, -16.2 dB, Fehler: Tempo 3,21 W/s ausserhalb 2,0–3,0 – „Viel verkauft, kein Geld da.“
- Versuch/Take 2: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 2.87 W/s, F0 123 Hz ±3.1, -17.0 dB, Fehler: keine – „Viel verkauft kein Geld da.“
- Versuch/Take 3: de_DE-thorsten_emotional-medium Sprecher 1, WER 0%, 2.75 W/s, F0 240 Hz ±2.6, -13.7 dB, Fehler: keine – „Viel verkauft, kein Geld da.“

**2. kalle:** „Das Büro gegenüber zahlt seit 6 Wochen net!“  
tts: „Das Büro gegenüber zahlt seit sechs Wochen net!“  
Whisper: „Das Büro gegenüber zahlt seit sechs Wochen nicht.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 1.455, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 25%, 2.91 W/s, F0 119 Hz ±3.2, -16.3 dB, Fehler: WER 25% > 10 %; Tempo 2,91 W/s ausserhalb 2,0–2,8 – „Das Büro wiegen über, zahlt seit sechs Wochen Näht.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 2.67 W/s, F0 117 Hz ±3.4, -16.9 dB, Fehler: keine – „Das Büro gegenüber zahlt seit sechs Wochen nicht.“

**3. byte:** „Ich hol dein Geld zurück.“  
tts: „Ich hol dein Geld zurück.“  
Whisper: „Ich hole dein Geld zurück.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 2.26, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 0%, 4.17 W/s, F0 181 Hz ±2.3, -16.1 dB, Fehler: Tempo 4,17 W/s ausserhalb 2,0–2,8 – „Ich hole dein Geld zurück.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 0%, 3.12 W/s, F0 177 Hz ±3.5, -16.7 dB, Fehler: Tempo 3,12 W/s ausserhalb 2,0–2,8 – „Ich hole dein Geld zurück.“
- Versuch/Take 3: de_DE-kerstin-low Sprecher None, WER 0%, 2.63 W/s, F0 177 Hz ±2.9, -17.1 dB, Fehler: keine – „Ich hole dein Geld zurück.“

**4. byte:** „3 Rechnungen offen. Je 620 Euro, zusammen 1.860.“  
tts: „Drei Rechnungen offen. Jee sechshundertzwanzig Euro, zusammen tausendachthundertsechzig.“ – Schreibweise angepasst: 'Je' wurde als 'Die/Wir' verstanden  
Whisper: „Drei Rechnungen offen, je 620 Euro, zusammen 1.860.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.0, "noise_scale": 0.5, "noise_w": 0.8}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 50%, 2.06 W/s, F0 162 Hz ±2.0, -20.2 dB, Fehler: WER 50% > 10 %; '1.860' nicht exakt erkannt – „Drei Rechnungen offen. Hier 620 Euro, zusammen 1000 nach 160.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 0%, 2.02 W/s, F0 163 Hz ±2.1, -20.8 dB, Fehler: keine – „Drei Rechnungen offen, je 620 Euro, zusammen 1.860.“

**5. kalle:** „Wie, in 2 Sekunden?“  
tts: „Wie … in zwei Sekunden?“  
Whisper: „Wie in zwei Sekunden.“  
Stimme: `{"model": "de_DE-thorsten_emotional-medium", "speaker": 6, "length_scale": 1.488, "noise_scale": 0.7, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 2.86 W/s, F0 154 Hz ±3.1, -13.2 dB, Fehler: Tempo 2,86 W/s ausserhalb 2,0–2,8 – „Wie in zwei Sekunden.“
- Versuch/Take 2: de_DE-thorsten_emotional-medium Sprecher 6, WER 0%, 2.30 W/s, F0 143 Hz ±2.7, -13.8 dB, Fehler: keine – „Wie in zwei Sekunden.“

**6. byte:** „Freitag will die Mühle 1.500 Euro. Auf dem Konto: 900. Fehlen 600.“  
tts: „Freitag willl die Mühle tausendfünfhundert Euro. Auf dem Konto neunhundert. Fehlen sechshundert.“ – Schreibweise angepasst: 'will' wurde als 'wird' verstanden; Doppelpunkte erzeugten Pausen > 0,4 s  
Whisper: „Freitag will die Mühle 1500 Euro, auf dem Konto 900, fehlen 600.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.0, "noise_scale": 0.6, "noise_w": 0.8}`  

**7. kalle:** „Obwohl ich so viel verkauft hab?“  
tts: „Obwohl ich so viel verkauft hab?“  
Whisper: „Obwohl ich so viel verkauft habe.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 1.912, "noise_scale": 0.75, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 0%, 3.53 W/s, F0 120 Hz ±2.3, -18.4 dB, Fehler: Tempo 3,53 W/s ausserhalb 2,0–2,8 – „Obwohl ich so viel verkauft habe.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 2.78 W/s, F0 120 Hz ±3.7, -18.1 dB, Fehler: keine – „Obwohl ich so viel verkauft habe.“

**8. byte:** „Ich schreib eine höfliche Erinnerung: alle 3 Rechnungen, Zahlung in 7 Tagen.“  
tts: „Ich schreib eine höfliche Erinnerung: alle drei Rechnungen, Zahlung in sieben Tagen.“  
Whisper: „Ich schreibe eine höfliche Erinnerung. Alle drei Rechnungen, Zahlungen in sieben Tagen.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.196, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 0%, 2.87 W/s, F0 163 Hz ±2.2, -20.7 dB, Fehler: Tempo 2,87 W/s ausserhalb 2,0–2,8 – „Ich schreibe eine höfliche Erinnerung, alle drei Rechnungen, Zahlung in sieben Tagen.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 8%, 2.61 W/s, F0 161 Hz ±2.2, -21.2 dB, Fehler: keine – „Ich schreibe eine höfliche Erinnerung. Alle drei Rechnungen, Zahlungen in sieben Tagen.“

**9. kalle:** „Höflich und klar. So schreib ich des nie!“  
tts: „Höflich und klar. So schreib ich des nie!“  
Whisper: „Höflich und klar. So schreibe ich das nie.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 1.935, "noise_scale": 0.8, "noise_w": 0.9}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 12%, 3.57 W/s, F0 126 Hz ±3.5, -15.0 dB, Fehler: WER 12% > 10 %; Tempo 3,57 W/s ausserhalb 2,0–2,8 – „Höflich und klar, so schreite ich das nie.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 2.63 W/s, F0 123 Hz ±3.5, -17.3 dB, Fehler: keine – „Höflich und klar. So schreibe ich das nie.“

**10. byte:** „Liquidität heißt: Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“  
tts: „Li-quidität heißt: Geld, das du jetzt zahlen kannst. Nicht versprochenes Geld.“ – Schreibweise angepasst: 'Liquidität' wurde als 'Dequitität/Die Qualität' verstanden  
Whisper: „Liquidität heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.0, "noise_scale": 0.5, "noise_w": 0.8}`  
- Versuch/Take 1: de_DE-kerstin-low Sprecher None, WER 9%, 2.33 W/s, F0 174 Hz ±2.1, -20.7 dB, Fehler: 'Liquidität' nicht exakt erkannt – „Dequity-Tield heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“
- Versuch/Take 2: de_DE-kerstin-low Sprecher None, WER 0%, 2.23 W/s, F0 180 Hz ±2.2, -20.4 dB, Fehler: keine – „Liquidität heißt, Geld, das du jetzt zahlen kannst, nicht versprochenes Geld.“

**11. byte:** „2 Tage später: Geld da, Mühle bezahlt, 1.260 Euro übrig.“  
tts: „Zwei Tage später: Geld da, Mühle bezahlt, tausendzweihundertsechzig Euro übrig.“  
Whisper: „Zwei Tage später, Geld da, Mühle bezahlt, 1260 Euro übrig.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.0, "noise_scale": 0.8, "noise_w": 0.9}`  

**12. kalle:** „Ha! Byte, du bist Gold wert!“  
tts: „Ha! Bait, du bist Gold wert!“ (Tag entfernt) – Schreibweise angepasst: Emotions-Modell sprach 'Herr Veit'; 'Byte' englisch ausgesprochen ('Bait')  
Whisper: „Ha, Byte, du bist Gold wert.“  
Stimme: `{"model": "de_DE-thorsten-high", "speaker": null, "length_scale": 1.704, "noise_scale": 0.7, "noise_w": 0.85}`  
- Versuch/Take 1: de_DE-thorsten-high Sprecher None, WER 17%, 3.37 W/s, F0 121 Hz ±2.3, -17.0 dB, Fehler: WER 17% > 10 %; Tempo 3,37 W/s ausserhalb 2,0–2,8 – „Ha, Byte, du bist kult wert.“
- Versuch/Take 2: de_DE-thorsten-high Sprecher None, WER 0%, 2.91 W/s, F0 116 Hz ±2.3, -17.0 dB, Fehler: Tempo 2,91 W/s ausserhalb 2,0–2,8 – „Ha, Byte, du bist Gold wert.“
- Versuch/Take 3: de_DE-thorsten-high Sprecher None, WER 0%, 2.56 W/s, F0 117 Hz ±2.6, -16.9 dB, Fehler: keine – „Ha, Byte, du bist Gold wert.“

**13. byte:** „Merk dir: Viel verkauft heißt nicht …“  
tts: „merk dirr: Viel verkauft … heißt nicht …“ – Schreibweise angepasst: 'Merk dir' wurde als 'Merkt ihr' verstanden  
Whisper: „Merk dir, viel verkauft heißt nicht.“  
Stimme: `{"model": "de_DE-kerstin-low", "speaker": null, "length_scale": 1.05, "noise_scale": 0.75, "noise_w": 0.8}`  

