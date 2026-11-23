# Stimmen-Check: Wo kommt Filiale Nr. 2 hin?

Erweiterter Check (Engine 2.3) für Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext`. Stimmen: ElevenLabs, Kalle = Brian, Byte = Laura. Kriterien: Wortfehler ≤ 10 % (schwäbische Wörter frei), Zahlen und Begriff exakt, Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil), Frage steigt / Aussage fällt (letztes Wort gegen den Rest der Zeile), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz (außer nach „…“). Höchstens 3 Versuche. Tempo: zuerst ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %, Spalte Tempo-Korrektur).

| # | Sprecher | ton / tempo | Modell | Versuche | WER | W/s (Ziel), Tempo-Korrektur | F0 | Spannweite | Ende | Betonung | Peak | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | begeistert / normal | eleven_v3 | 3 | 0% | 2,34 (2,3–2,6), x1,02 | 147 Hz | 13,9 Halbtöne | +0,7 Halbtöne (Aussage) | „zweite“ -0,4 dB / +2,8 Halbtöne | 0,94 | OK |
| 2 | byte | verschmitzt / normal | eleven_multilingual_v2 | 3 | 0% | 2,33 (2,3–2,6), x1,00 | 178 Hz | 10,6 Halbtöne | -2,8 Halbtöne (Aussage) | „oben“ +0,1 dB / -3,5 Halbtöne | 0,65 | FAIL: Betonung 'oben,' schwach (+0,1 dB, -3,5 Halbtoene) |
| 3 | byte | ueberzeugt / normal | eleven_multilingual_v2 | 2 | 0% | 2,37 (2,3–2,6), x1,00 | 264 Hz | 7,9 Halbtöne | -4,4 Halbtöne (Aussage) | „Drei“ +2,8 dB / -1,1 Halbtöne | 0,80 | OK |
| 4 | kalle | begeistert / schnell | eleven_multilingual_v2 | 3 | 0% | 2,64 (2,6–2,9), x1,14 | 170 Hz | 19,2 Halbtöne | -16,6 Halbtöne (Aussage) | „schönsten“ -0,3 dB / -0,7 Halbtöne | 0,52 | FAIL: Betonung 'schönsten,' schwach (-0,3 dB, -0,7 Halbtoene) |
| 5 | byte | nachdenklich / normal | eleven_multilingual_v2 | 1 | 0% | 2,34 (2,3–2,6), x1,02 | 254 Hz | 8,0 Halbtöne | -2,5 Halbtöne (Aussage) | „zwei“ +2,1 dB / -2,5 Halbtöne | 0,58 | OK |
| 6 | byte | ruhig / langsam | eleven_multilingual_v2 | 2 | 0% | 2,16 (2,0–2,2), x0,89 | 232 Hz | 11,0 Halbtöne | -8,9 Halbtöne (Aussage) | „Zu“ +2,8 dB / +2,8 Halbtöne | 0,59 | OK |
| 7 | byte | begeistert / normal | eleven_v3 | 1 | 0% | 2,34 (2,3–2,6), x1,03 | 218 Hz | 12,4 Halbtöne | -5,4 Halbtöne (Aussage) | „8.000“ -0,1 dB / +2,9 Halbtöne | 0,80 | OK |
| 8 | kalle | fragend / normal | eleven_multilingual_v2 | 3 | 0% | 2,95 (2,3–2,6), x0,88 | 95 Hz | 7,4 Halbtöne | +1,9 Halbtöne (Frage) | „mir“ -1,9 dB / +0,1 Halbtöne | 0,51 | FAIL: Tempo 2,95 W/s ausserhalb 2,3–2,6; Betonung 'mir?' schwach (-1,9 dB, +0,1 Halbtoene) |
| 9 | byte | nachdenklich / langsam | eleven_multilingual_v2 | 3 | 0% | 2,17 (2,0–2,2), x0,88 | 176 Hz | 4,0 Halbtöne | +1,2 Halbtöne (Aussage) | „drei“ +2,4 dB / +0,1 Halbtöne | 0,63 | FAIL: monoton (Spannweite 4,0 Halbtoene < 4) |
| 10 | byte | ueberzeugt / normal | eleven_v3 | 3 | 0% | 2,28 (2,3–2,6), x1,15 | 204 Hz | 11,9 Halbtöne | – | „240“ +3,3 dB / +2,7 Halbtöne | 0,81 | OK |
| 11 | kalle | fragend / normal | eleven_multilingual_v2 | 3 | 0% | 2,34 (2,3–2,6), x1,00 | 115 Hz | 13,2 Halbtöne | -6,3 Halbtöne (Frage) | „warum“ +1,4 dB / +6,5 Halbtöne | 0,58 | FAIL: Frage steigt nicht (-6,3 Halbtoene am Ende) |
| 12 | byte | verschmitzt / normal | eleven_multilingual_v2 | 2 | 0% | 2,39 (2,3–2,6), x1,00 | 171 Hz | 11,7 Halbtöne | -0,5 Halbtöne (Aussage) | „aufgebackenen“ +2,7 dB / -6,5 Halbtöne | 0,64 | OK |
| 13 | kalle | begeistert / schnell | eleven_v3 | 3 | 10% | 2,95 (2,6–2,9), x0,88 | 111 Hz | 18,1 Halbtöne | -11,4 Halbtöne (Aussage) | „echte“ +6,0 dB / +2,8 Halbtöne | 0,93 | OK |

Kalle und Byte: mittlere Tonhöhe 115 Hz gegen 211 Hz, Abstand 10.6 Halbtöne → ✓ klar unterscheidbar (Ziel ≥ 4).

## Sprechtext und Versuche

**1. kalle:** „Byte, ich will eine zweite Filiale!“  
- eleven_multilingual_v2 Versuch 1: „Byte, ich will eine zweite Filiale!“, stability 0.3, style 0.5, speed 0.92, Tempo-Korrektur x0.88 → Tempo 2,71 W/s ausserhalb 2,3–2,6; Betonung 'zweite' schwach (-1,0 dB, -1,5 Halbtoene); Whisper: „Byte, ich will eine zweite Filiale.“
- eleven_multilingual_v2 Versuch 2: „Byte, ich will eine, zweite Filiale!“, stability 0.3, style 0.5, speed 0.73, Tempo-Korrektur x1.15 → Tempo 2,19 W/s ausserhalb 2,3–2,6; Whisper: „Byte, ich will eine zweite Filiale.“
- eleven_multilingual_v2 Versuch 3: „Byte, ich will eine, zweite Filiale!“, stability 0.3, style 0.5, speed 0.94, Tempo-Korrektur x1.00 → WER 17% > 10 %; Betonung 'zweite' schwach (-1,3 dB, -0,2 Halbtoene); Whisper: „Byker, ich will eine zweite Filiale.“
- eleven_v3 Versuch v3: „Byte, ich will eine, zweite Filiale!“, stability 0.5, style 0.5, speed –, Tempo-Korrektur x1.02 → OK; Whisper: „Byte, ich will eine, zweite Filiale.“ ← gewählt

**2. byte:** „Gute Idee. Ich zeig dir die Stadt. Von oben.“  
- eleven_multilingual_v2 Versuch 1: „Gute Idee. Ich zeig dir die Stadt … von oben.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x0.88 → WER 11% > 10 %; Tempo 2,94 W/s ausserhalb 2,3–2,6; Betonung 'oben,' schwach (+1,1 dB, -4,9 Halbtoene); Whisper: „Gute Idee, ich zeig dir die Stadt von ober.“
- eleven_multilingual_v2 Versuch 2: „Gute Idee. Ich zeig dir die Stadt … von oben.“, stability 0.35, style 0.45, speed 0.7, Tempo-Korrektur x1.00 → Betonung 'oben,' schwach (+0,1 dB, -3,5 Halbtoene); Whisper: „Gute Idee. Ich zeig dir die Stadt von oben.“ ← gewählt
- eleven_multilingual_v2 Versuch 3: „Gute Idee. Ich zeig dir die Stadt … von oben.“, stability 0.35, style 0.45, speed 0.7, Tempo-Korrektur x1.00 → WER 11% > 10 %; Whisper: „Gute Idee. Ich zeig dir die Stadt von ober.“
- eleven_v3 Versuch v3: „Gute Idee. Ich zeig dir die Stadt … von oben.“, stability 0.5, style 0.45, speed –, Tempo-Korrektur x0.93 → WER 11% > 10 %; Betonung 'oben,' schwach (+0,4 dB, -1,7 Halbtoene); Whisper: „Gute Idee! Ich zeige dir die Stadt von oben.“

**3. byte:** „Drei Plätze kommen in Frage. Altstadt, Neubaugebiet, Bahnhof.“  
- eleven_multilingual_v2 Versuch 1: „Drei Plätze kommen in Frage. Altstadt … Neubaugebiet … Bahnhof.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.15 → Tempo 2,01 W/s ausserhalb 2,3–2,6; Whisper: „Drei Plätze kommen in Frage. Altstadt, Neubaugebiet, Bahnhof.“
- eleven_multilingual_v2 Versuch 2: „Drei Plätze kommen in Frage. Altstadt … Neubaugebiet … Bahnhof.“, stability 0.45, style 0.35, speed 1.2, Tempo-Korrektur x1.00 → OK; Whisper: „Drei Plätze kommen in Frage. Altstadt, Neubaugebiet, Bahnhof.“ ← gewählt
- eleven_v3 Versuch v3: „Drei Plätze kommen in Frage. Altstadt … Neubaugebiet … Bahnhof.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x1.15 → Tempo 1,84 W/s ausserhalb 2,3–2,6; Whisper: „Drei Plätze kommen in Frage. Altstadt, Neubaugebiet, Bahnhof.“

**4. kalle:** „Altstadt! Da isch's am schönsten.“  
- eleven_multilingual_v2 Versuch 1: „Altstadt! Da isch's am schönsten.“, stability 0.3, style 0.5, speed 1.0, Tempo-Korrektur x1.14 → Betonung 'schönsten,' schwach (-0,3 dB, -0,7 Halbtoene); Whisper: „Altstadt, da ist es am schönsten.“ ← gewählt
- eleven_multilingual_v2 Versuch 2: „Altstadt! Da isch's am schönsten.“, stability 0.3, style 0.5, speed 1.0, Tempo-Korrektur x1.15 → WER 17% > 10 %; Tempo 2,40 W/s ausserhalb 2,6–2,9; Betonung 'schönsten,' schwach (-2,7 dB, -9,0 Halbtoene); Whisper: „Altstadt, der ist es am schönsten.“
- eleven_multilingual_v2 Versuch 3: „Altstadt! Da isch's am schönsten.“, stability 0.3, style 0.5, speed 1.2, Tempo-Korrektur x1.04 → WER 50% > 10 %; monoton (Spannweite 0,9 Halbtoene < 4); Betonung 'schönsten,' schwach (-2,5 dB, +0,0 Halbtoene); Whisper: „Als Start, da ist es so am schönsten.“
- eleven_v3 Versuch v3: „Altstadt! Da isch's am schönsten.“, stability 0.5, style 0.6, speed –, Tempo-Korrektur x1.15 → WER 17% > 10 %; Tempo 2,14 W/s ausserhalb 2,6–2,9; Whisper: „Outstart, da ist es am schönsten.“

**5. byte:** „Schön, ja. Aber da gibt's schon zwei Bäckereien.“  
- eleven_multilingual_v2 Versuch 1: „Schön, ja. Aber da gibt's schon … zwei Bäckereien.“, stability 0.55, style 0.25, speed 0.92, Tempo-Korrektur x1.02 → OK; Whisper: „Schön, ja, aber da gibt's schon zwei Bäckereien.“ ← gewählt
- eleven_v3 Versuch v3: „Schön, ja. Aber da gibt's schon … zwei Bäckereien.“, stability 0.5, style 0.25, speed –, Tempo-Korrektur x1.14 → Ende wirkt abgeschnitten; Betonung 'zwei' schwach (-0,5 dB, -2,6 Halbtoene); Whisper: „Schön, ja, aber da gibt's schon zwei Bäckereien.“

**6. byte:** „Im Neubaugebiet ist es ruhig. Zu ruhig.“  
- eleven_multilingual_v2 Versuch 1: „Im Neubaugebiet ist es ruhig. Zu ruhig.“, stability 0.6, style 0.15, speed 0.84, Tempo-Korrektur x0.88 → Betonung 'Zu' schwach (+1,2 dB, -1,2 Halbtoene); Whisper: „Im Neubaugebiet ist es ruhig. Zu ruhig.“
- eleven_multilingual_v2 Versuch 2: „Im Neubaugebiet ist es ruhig., Zu ruhig.“, stability 0.6, style 0.15, speed 0.84, Tempo-Korrektur x0.89 → OK; Whisper: „Im Neubaugebiet ist es ruhig, zu ruhig.“ ← gewählt
- eleven_v3 Versuch v3: „Im Neubaugebiet ist es ruhig., Zu ruhig.“, stability 0.5, style 0.15, speed –, Tempo-Korrektur x0.89 → Betonung 'Zu' schwach (+0,3 dB, +0,8 Halbtoene); Whisper: „Im Neubaugebiet ist es ruhig, zu ruhig.“

**7. byte:** „Aber am Bahnhof … laufen jeden Morgen 8.000 Leute vorbei.“  
- eleven_multilingual_v2 Versuch 1: „Aber am Bahnhof … laufen jeden Morgen achttausend Leute vorbei.“, stability 0.3, style 0.5, speed 0.92, Tempo-Korrektur x1.00 → OK; Whisper: „Aber am Bahnhof laufen jeden Morgen 8.000 Leute vorbei.“
- eleven_v3 Versuch v3: „Aber am Bahnhof … laufen jeden Morgen achttausend Leute vorbei.“, stability 0.5, style 0.5, speed –, Tempo-Korrektur x1.03 → OK; Whisper: „Aber am Bahnhof laufen jeden Morgen 8000 Leute vorbei.“ ← gewählt

**8. kalle:** „Und wie viele davon kaufet bei mir?“  
- eleven_multilingual_v2 Versuch 1: „Und wie viele davon kaufet bei mir?“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x0.88 → Tempo 3,14 W/s ausserhalb 2,3–2,6; Betonung 'mir?' schwach (-2,3 dB, +0,7 Halbtoene); Whisper: „Und wie viele davon kaufet bei mir?“
- eleven_multilingual_v2 Versuch 2: „Und wie viele davon kaufet bei mir?“, stability 0.4, style 0.3, speed 0.7, Tempo-Korrektur x0.88 → Tempo 2,95 W/s ausserhalb 2,3–2,6; Betonung 'mir?' schwach (-1,9 dB, +0,1 Halbtoene); Whisper: „Und wie viele davon kaufet bei mir?“ ← gewählt
- eleven_multilingual_v2 Versuch 3: „Und wie viele davon kaufet bei mir?“, stability 0.4, style 0.3, speed 0.7, Tempo-Korrektur x0.88 → WER 14% > 10 %; Tempo 3,06 W/s ausserhalb 2,3–2,6; Whisper: „Und wie viel davon kaufet bei mir?“
- eleven_v3 Versuch v3: „Und wie viele davon kaufet bei mir?“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x0.88 → Ende wirkt abgeschnitten; Tempo 3,63 W/s ausserhalb 2,3–2,6; Betonung 'mir?' schwach (+0,2 dB, +0,6 Halbtoene); Whisper: „Und wie viele davon kaufet bei mir?“

**9. byte:** „Wenn nur drei von hundert stehen bleiben …“  
- eleven_multilingual_v2 Versuch 1: „Wenn nur drei von hundert stehen bleiben …“, stability 0.55, style 0.25, speed 0.84, Tempo-Korrektur x0.88 → Tempo 2,89 W/s ausserhalb 2,0–2,2; Betonung 'drei' schwach (+1,8 dB, -0,3 Halbtoene); Whisper: „Wenn nur drei von hundert stehen bleiben.“
- eleven_multilingual_v2 Versuch 2: „Wenn nur, drei von hundert stehen bleiben …“, stability 0.55, style 0.25, speed 0.7, Tempo-Korrektur x0.88 → Tempo 2,44 W/s ausserhalb 2,0–2,2; Betonung 'drei' schwach (+1,8 dB, -1,5 Halbtoene); Whisper: „Wenn nur drei von hundert stehenbleiben...“
- eleven_multilingual_v2 Versuch 3: „Wenn nur, drei von hundert stehen bleiben …“, stability 0.55, style 0.25, speed 0.7, Tempo-Korrektur x0.88 → monoton (Spannweite 4,0 Halbtoene < 4); Whisper: „Wenn nur drei von hundert stehen bleiben.“ ← gewählt
- eleven_v3 Versuch v3: „Wenn nur, drei von hundert stehen bleiben …“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x0.88 → Tempo 3,29 W/s ausserhalb 2,0–2,2; Whisper: „Wenn nur drei von hundert stehenbleiben?“

**10. byte:** „… sind das 240 Kunden. Jeden Tag.“  
- eleven_multilingual_v2 Versuch 1: „… sind das zweihundertvierzig Kunden. Jeden Tag.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.07 → Betonung '240' schwach (-0,3 dB, +0,2 Halbtoene); Whisper: „Sind das 240 Kunden. Jeden Tag.“
- eleven_multilingual_v2 Versuch 2: „… sind das, zweihundertvierzig Kunden. Jeden Tag.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.13 → Betonung '240' schwach (+0,7 dB, -1,9 Halbtoene); Whisper: „Sind das 240 Kunden. Jeden Tag.“
- eleven_multilingual_v2 Versuch 3: „… sind das, zweihundertvierzig Kunden. Jeden Tag.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.15 → WER 17% > 10 %; Tempo 2,25 W/s ausserhalb 2,3–2,6; Whisper: „In sind das 240 Kunden. Jeden Tag.“
- eleven_v3 Versuch v3: „… sind das, zweihundertvierzig Kunden. Jeden Tag.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x1.15 → OK; Whisper: „Sind das 240 Kunden. Jeden Tag.“ ← gewählt

**11. kalle:** „Und warum hat da noch koiner a Bäckerei?“  
- eleven_multilingual_v2 Versuch 1: „Und warum hat da noch koiner a Bäckerei?“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x0.88 → Tempo 2,68 W/s ausserhalb 2,3–2,6; Frage steigt nicht (-11,6 Halbtoene am Ende); Whisper: „Und warum hat da noch Keuner A. Bäckerei?“
- eleven_multilingual_v2 Versuch 2: „Und warum hat da noch koiner a Bäckerei?“, stability 0.32, style 0.4, speed 0.74, Tempo-Korrektur x0.88 → Frage steigt nicht (-8,7 Halbtoene am Ende); Whisper: „Und warum hat da noch keiner a Bäckerei?“
- eleven_multilingual_v2 Versuch 3: „Und warum hat da noch koiner a Bäckerei?“, stability 0.25, style 0.5, speed 0.74, Tempo-Korrektur x1.00 → Frage steigt nicht (-6,3 Halbtoene am Ende); Whisper: „Und warum hat da noch keiner a Bäckerei?“ ← gewählt
- eleven_v3 Versuch v3: „Und warum hat da noch koiner a Bäckerei?“, stability 0.5, style 0.6, speed –, Tempo-Korrektur x0.88 → WER 25% > 10 %; Tempo 3,21 W/s ausserhalb 2,3–2,6; Frage steigt nicht (+0,0 Halbtoene am Ende); Whisper: „Und warum hat er noch keine Bäckerei?“

**12. byte:** „Da gibt's nur einen Kiosk. Mit aufgebackenen Brötchen.“  
- eleven_multilingual_v2 Versuch 1: „Da gibt's nur einen Kiosk. Mit … aufgebackenen Brötchen.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x1.15 → Aussage faellt nicht (+1,2 Halbtoene am Ende); Whisper: „Da gibt's nur einen Kiosk mit aufgebackenen Brötchen.“
- eleven_multilingual_v2 Versuch 2: „Da gibt's nur einen Kiosk. Mit … aufgebackenen Brötchen.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x1.00 → OK; Whisper: „Da gibt's nur einen Kiosk mit aufgebackenen Brötchen.“ ← gewählt
- eleven_v3 Versuch v3: „Da gibt's nur einen Kiosk. Mit … aufgebackenen Brötchen.“, stability 0.5, style 0.45, speed –, Tempo-Korrektur x1.06 → OK; Whisper: „Da gibt's nur einen Kiosk mit aufgebackenen Brötchen.“

**13. kalle:** „Dann zeig i denen mal, was a echte Brezel isch!“  
- eleven_multilingual_v2 Versuch 1: „Dann zeig i denen mal, was a echte Brezel isch!“, stability 0.3, style 0.5, speed 1.0, Tempo-Korrektur x0.88 → Tempo 3,58 W/s ausserhalb 2,6–2,9; Betonung 'echte' schwach (+0,8 dB, -0,6 Halbtoene); Whisper: „Dann zeig ich denen mal, was er echte Brezel ist.“
- eleven_multilingual_v2 Versuch 2: „Dann zeig i denen mal, was a, echte Brezel isch!“, stability 0.3, style 0.5, speed 0.7, Tempo-Korrektur x1.04 → WER 30% > 10 %; Whisper: „Dann zeige ich denen mal, was ein echter Brezel ist.“
- eleven_multilingual_v2 Versuch 3: „Dann zeig i denen mal, was a, echte Brezel isch!“, stability 0.3, style 0.5, speed 0.7, Tempo-Korrektur x1.10 → WER 20% > 10 %; Betonung 'echte' schwach (+1,2 dB, +0,0 Halbtoene); Whisper: „Dann zeig i den mal, was ah, echte Brezel isch.“
- eleven_v3 Versuch v3: „Dann zeig i denen mal, was a, echte Brezel isch!“, stability 0.5, style 0.5, speed –, Tempo-Korrektur x0.88 → OK; Whisper: „Dann zeig i den mal, was a echte Brezel isch.“ ← gewählt

## eleven_v3

Für 13 Zeilen mit `ton` wurde zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag) erzeugt und mit demselben Check bewertet. Übernommen, weil besser als eleven_multilingual_v2: 4 Zeilen.

