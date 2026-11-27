# Stimmen-Check: Ein Video – und der Laden platzt

Erweiterter Check (Engine 2.3) für Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext`. Stimmen: ElevenLabs, Kalle = Brian, Byte = Laura, Lea = Sarah (ab 2.4). Atmer am Satzanfang bleiben erhalten (laute werden gedämpft). Kriterien: Wortfehler ≤ 10 % (schwäbische Wörter frei), Zahlen und Begriff exakt, Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil), Frage steigt / Aussage fällt (letztes Wort gegen den Rest der Zeile), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz (außer nach „…“). Höchstens 3 Versuche. Tempo: zuerst ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %, Spalte Tempo-Korrektur).

| # | Sprecher | ton / tempo | Modell | Versuche | WER | W/s (Ziel), Tempo-Korrektur | F0 | Spannweite | Ende | Betonung | Peak | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | – | v2 | 2 | 0% | 2.45 | 95 Hz | – | – | – | – | OK |
| 2 | kalle | nachdenklich / langsam | eleven_multilingual_v2 | 3 | 0% | 2,27 (2,0–2,2), x0,88 | 82 Hz | 10,9 Halbtöne | -3,4 Halbtöne (Aussage) | – | 0,75 | FAIL: Tempo 2,27 W/s ausserhalb 2,0–2,2 |
| 3 | byte | – | v2 | 2 | 0% | 2.46 | 183 Hz | – | – | – | – | OK |
| 4 | kalle | nachdenklich / langsam | eleven_multilingual_v2 | 3 | 0% | 2,16 (2,0–2,2), x0,89 | 106 Hz | 11,9 Halbtöne | -8,5 Halbtöne (Aussage) | – | 0,68 | OK |
| 5 | byte | – | v2 | 1 | 0% | 2.72 | 209 Hz | – | – | – | – | OK |
| 6 | byte | – | v2 | 1 | 9% | 2.71 | 205 Hz | – | – | – | – | OK |
| 7 | byte | – | v2 | 1 | 0% | 2.47 | 214 Hz | – | – | – | – | OK |
| 8 | byte | – | v2 | 1 | 0% | 2.70 | 223 Hz | – | – | – | – | OK |
| 9 | kalle | fragend / normal | eleven_multilingual_v2 | 2 | 0% | 2,48 (2,3–2,6), x1,00 | 141 Hz | 15,9 Halbtöne | +7,1 Halbtöne (Frage) | – | 0,71 | OK |
| 10 | byte | – | v2 | 1 | 0% | 2.44 | 216 Hz | – | – | – | – | OK |
| 11 | kalle | begeistert / normal | eleven_multilingual_v2 | 2 | 0% | 2,49 (2,3–2,6), x1,00 | 79 Hz | 8,9 Halbtöne | -5,2 Halbtöne (Aussage) | – | 0,46 | OK |
| 12 | byte | ruhig / normal | eleven_multilingual_v2 | 1 | 0% | 2,34 (2,3–2,6), x1,02 | 166 Hz | 4,2 Halbtöne | -2,6 Halbtöne (Aussage) | – | 0,60 | OK |

Kalle und Byte: mittlere Tonhöhe 94 Hz gegen 166 Hz, Abstand 9.9 Halbtöne → ✓ klar unterscheidbar (Ziel ≥ 4).

## Sprechtext und Versuche

**2. kalle:** „Dabei war hier gestern noch gähnende Leere.“  
- eleven_multilingual_v2 Versuch 1: „Dabei war hier gestern noch gähnende Leere.“, stability 0.55, style 0.25, speed 0.84, Tempo-Korrektur x0.88 → Tempo 2,27 W/s ausserhalb 2,0–2,2; Whisper: „Dabei war hier gestern noch gähnende Leere.“
- eleven_multilingual_v2 Versuch 2: „Dabei war hier gestern noch gähnende Leere.“, stability 0.55, style 0.25, speed 0.7, Tempo-Korrektur x0.95 → WER 14% > 10 %; Whisper: „Dabei war hier gestern noch gähnende Lehre.“
- eleven_multilingual_v2 Versuch 3: „Dabei war hier gestern noch gähnende Leere.“, stability 0.55, style 0.25, speed 0.7, Tempo-Korrektur x0.95 → WER 14% > 10 %; Whisper: „Dabei war hier gestern noch gehende Leere.“
- eleven_v3 Versuch v3: „Dabei war hier gestern noch gähnende Leere.“, stability 0.5, style 0.25, speed –, Tempo-Korrektur x0.88 → Tempo 2,84 W/s ausserhalb 2,0–2,2; Whisper: „Dabei war hier gestern noch gähnende Leere.“

**4. kalle:** „Ich und Videos? Ich kann doch nur backen.“  
- eleven_multilingual_v2 Versuch 1: „Ich und Videos? Ich kann doch nur backen.“, stability 0.55, style 0.25, speed 0.84, Tempo-Korrektur x0.88 → Tempo 2,61 W/s ausserhalb 2,0–2,2; Whisper: „Ich und Videos, ich kann doch nur backen.“
- eleven_multilingual_v2 Versuch 2: „Ich und Videos? Ich kann doch nur backen.“, stability 0.55, style 0.25, speed 0.7, Tempo-Korrektur x0.88 → Tempo 2,79 W/s ausserhalb 2,0–2,2; Whisper: „Ich und Videos? Ich kann doch nur backen.“
- eleven_multilingual_v2 Versuch 3: „Ich und Videos? Ich kann doch nur backen.“, stability 0.55, style 0.25, speed 0.7, Tempo-Korrektur x0.89 → OK; Whisper: „Ich und Videos? Ich kann doch nur backen.“
- eleven_v3 Versuch v3: „Ich und Videos? Ich kann doch nur backen.“, stability 0.5, style 0.25, speed –, Tempo-Korrektur x0.88 → Tempo 2,88 W/s ausserhalb 2,0–2,2; Whisper: „Ich und Videos? Ich kann doch nur backen.“

**9. kalle:** „Byte! 50.000 Aufrufe? Über Nacht?“  
- eleven_multilingual_v2 Versuch 1: „Byte! fünfzigtausend Aufrufe? Über Nacht?“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x1.15 → Tempo 2,10 W/s ausserhalb 2,3–2,6; Whisper: „Byte, 50.000 Aufrufe über Nacht.“
- eleven_multilingual_v2 Versuch 2: „Byte! fünfzigtausend Aufrufe? Über Nacht?“, stability 0.4, style 0.3, speed 1.2, Tempo-Korrektur x1.00 → OK; Whisper: „Byte. 50.000 Aufrufe über Nacht.“
- eleven_v3 Versuch v3: „Byte! fünfzigtausend Aufrufe? Über Nacht?“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x1.15 → Tempo 1,74 W/s ausserhalb 2,3–2,6; Frage steigt nicht (-10,0 Halbtoene am Ende); Whisper: „Byte. 50.000 Aufrufe über Nacht.“

**11. kalle:** „Und jetzt stehen sie alle hier. Byte, wir brauchen mehr Brezeln!“  
- eleven_multilingual_v2 Versuch 1: „Und jetzt stehen sie alle hier. Byte, wir brauchen mehr Brezeln!“, stability 0.3, style 0.5, speed 0.92, Tempo-Korrektur x0.88 → Tempo 2,82 W/s ausserhalb 2,3–2,6; Whisper: „Und jetzt stehen Sie alle hier, Byte. Wir brauchen mehr Brezeln.“
- eleven_multilingual_v2 Versuch 2: „Und jetzt stehen sie alle hier. Byte, wir brauchen mehr Brezeln!“, stability 0.3, style 0.5, speed 0.7, Tempo-Korrektur x1.00 → OK; Whisper: „Und jetzt stehen sie alle hier, Byte, wir brauchen mehr Brezeln.“
- eleven_v3 Versuch v3: „Und jetzt stehen sie alle hier. Byte, wir brauchen mehr Brezeln!“, stability 0.5, style 0.5, speed –, Tempo-Korrektur x0.92 → Ende wirkt abgeschnitten; Whisper: „Und jetzt stehen sie alle hier. Byte, wir brauchen mehr Brezeln.“

**12. byte:** „Schon bestellt.“  
- eleven_multilingual_v2 Versuch 1: „Schon bestellt.“, stability 0.6, style 0.15, speed 0.92, Tempo-Korrektur x1.02 → OK; Whisper: „Schon bestellt.“
- eleven_v3 Versuch v3: „Schon bestellt.“, stability 0.5, style 0.15, speed –, Tempo-Korrektur x0.88 → Tempo 2,70 W/s ausserhalb 2,3–2,6; Whisper: „Schon bestellt.“

## eleven_v3

Für 5 Zeilen mit `ton` wurde zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag) erzeugt und mit demselben Check bewertet. Übernommen, weil besser als eleven_multilingual_v2: 0 Zeilen.

