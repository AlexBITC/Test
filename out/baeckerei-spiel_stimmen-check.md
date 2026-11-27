# Stimmen-Check: Diese Stadt ist ein Spiel

Erweiterter Check (Engine 2.3) für Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext`. Stimmen: ElevenLabs, Kalle = Brian, Byte = Laura, Lea = Sarah (ab 2.4), Erzähler = Daniel (ab 2.5). Atmer am Satzanfang bleiben erhalten (laute werden gedämpft). Kriterien: Wortfehler ≤ 10 % (schwäbische Wörter frei), Zahlen und Begriff exakt, Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil), Frage steigt / Aussage fällt (letztes Wort gegen den Rest der Zeile), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz (außer nach „…“). Höchstens 3 Versuche. Tempo: zuerst ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %, Spalte Tempo-Korrektur).

| # | Sprecher | ton / tempo | Modell | Versuche | WER | W/s (Ziel), Tempo-Korrektur | F0 | Spannweite | Ende | Betonung | Peak | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | erzaehler | erzaehlend / langsam | eleven_multilingual_v2 | 3 | 0% | 2,16 (2,0–2,2), x0,98 | 150 Hz | 19,2 Halbtöne | -14,0 Halbtöne (Aussage) | „Spiel“ -0,9 dB / +0,4 Halbtöne | 0,48 | FAIL: Betonung 'Spiel,' schwach (-0,9 dB, +0,4 Halbtoene) |
| 2 | erzaehler | erzaehlend / langsam | eleven_v3 | 3 | 0% | 2,16 (2,0–2,2), x0,94 | 139 Hz | 13,7 Halbtöne | – | „besten“ -1,0 dB / +0,3 Halbtöne | 0,89 | FAIL: Betonung 'besten' schwach (-1,0 dB, +0,3 Halbtoene) |
| 3 | byte | verschmitzt / normal | eleven_v3 | 3 | 0% | 2,56 (2,3–2,6), x0,93 | 214 Hz | 15,5 Halbtöne | -3,9 Halbtöne (Aussage) | „Nacht“ -0,1 dB / -2,6 Halbtöne | 0,83 | FAIL: Betonung 'Nacht' schwach (-0,1 dB, -2,6 Halbtoene) |
| 4 | kalle | fragend / normal | eleven_multilingual_v2 | 3 | 0% | 2,56 (2,3–2,6), x0,90 | 119 Hz | 16,6 Halbtöne | -11,4 Halbtöne (Aussage) | „nie“ -1,9 dB / -1,6 Halbtöne | 0,45 | FAIL: Betonung 'nie' schwach (-1,9 dB, -1,6 Halbtoene) |
| 5 | kalle | begeistert / schnell | eleven_multilingual_v2 | 2 | 0% | 2,68 (2,6–2,9), x1,00 | 167 Hz | 17,8 Halbtöne | -15,1 Halbtöne (Aussage) | „fünfzig“ +3,3 dB / +4,2 Halbtöne | 0,80 | OK |
| 6 | byte | nachdenklich / normal | eleven_v3 | 3 | 0% | 2,31 (2,3–2,6), x1,15 | 179 Hz | 29,1 Halbtöne | +9,5 Halbtöne (Aussage) | „neunzig“ +0,6 dB / +5,3 Halbtöne | 0,88 | FAIL: Aussage faellt nicht (+9,5 Halbtoene am Ende) |
| 7 | erzaehler | erzaehlend / langsam | eleven_multilingual_v2 | 2 | 0% | 2,04 (2,0–2,2), x1,10 | 136 Hz | 20,5 Halbtöne | -8,8 Halbtöne (Aussage) | „500“ +0,8 dB / +2,7 Halbtöne | 0,55 | OK |
| 8 | kalle | genervt / schnell | eleven_multilingual_v2 | 3 | 0% | 2,37 (2,6–2,9), x1,15 | 184 Hz | 11,0 Halbtöne | +4,3 Halbtöne (Aussage) | „zwei“ -0,9 dB / -1,9 Halbtöne | 0,62 | FAIL: Tempo 2,37 W/s ausserhalb 2,6–2,9; Aussage faellt nicht (+4,3 Halbtoene am Ende); Betonung 'zwei' schwach (-0,9 dB, -1,9 Halbtoene) |
| 9 | lea | verschmitzt / normal | eleven_multilingual_v2 | 3 | 0% | 1,67 (2,3–2,6), x1,15 | 186 Hz | 4,6 Halbtöne | -4,0 Halbtöne (Aussage) | „mich“ +1,2 dB / +0,6 Halbtöne | 0,86 | FAIL: Tempo 1,67 W/s ausserhalb 2,3–2,6; Betonung 'mich' schwach (+1,2 dB, +0,6 Halbtoene) |
| 10 | byte | ueberzeugt / normal | eleven_multilingual_v2 | 3 | 9% | 2,42 (2,3–2,6), x1,00 | 227 Hz | 9,6 Halbtöne | -2,6 Halbtöne (Aussage) | „Wetter“ -0,3 dB / -5,1 Halbtöne | 0,77 | FAIL: Betonung 'Wetter,' schwach (-0,3 dB, -5,1 Halbtoene) |
| 11 | erzaehler | erzaehlend / langsam | eleven_v3 | 2 | 0% | 2,04 (2,0–2,2), x1,12 | 135 Hz | 15,2 Halbtöne | -11,6 Halbtöne (Aussage) | „Bahnhof“ +2,4 dB / +2,3 Halbtöne | 0,86 | OK |
| 12 | kalle | geruehrt / langsam | eleven_multilingual_v2 | 3 | 0% | 2,16 (2,0–2,2), x0,90 | 94 Hz | 15,3 Halbtöne | -10,8 Halbtöne (Aussage) | „besser“ +3,5 dB / +0,0 Halbtöne | 0,72 | OK |
| 13 | byte | ueberzeugt / normal | eleven_v3 | 3 | 0% | 2,34 (2,3–2,6), x1,05 | 170 Hz | 25,6 Halbtöne | -4,7 Halbtöne (Aussage) | „nichts“ -3,1 dB / -6,1 Halbtöne | 0,81 | FAIL: Betonung 'nichts,' schwach (-3,1 dB, -6,1 Halbtoene) |
| 14 | erzaehler | erzaehlend / langsam | eleven_multilingual_v2 | 2 | 0% | 2,16 (2,0–2,2), x0,91 | 137 Hz | 18,7 Halbtöne | -10,0 Halbtöne (Aussage) | „Deine“ +1,4 dB / +2,1 Halbtöne | 0,61 | OK |

Kalle und Byte: mittlere Tonhöhe 143 Hz gegen 196 Hz, Abstand 5.5 Halbtöne → ✓ klar unterscheidbar (Ziel ≥ 4).

Lea und Kalle: 186 Hz gegen 143 Hz, Lea liegt 4,6 Halbtöne höher → ✓ (Ziel ≥ 4).
Lea und Byte: Tonhöhe 186 Hz gegen 196 Hz (-0.9 Halbtöne); Klangfarbe (Abstand der mittleren MFCC 2–20): 62.7, zum Vergleich Kalle–Byte 65.8 → ✓ klar unterscheidbar (Klangfarbe) (Ziel ≥ 25).

Erzähler und Kalle: Klangfarbe (MFCC 2–20) 33,3 → ✓ klar verschieden (Ziel ≥ 25); Tempo 2,11 gegen 2,44 Wörter/s (✓ langsamer); Spannweite der Satzmelodie im Mittel 17,5 gegen 15,2 Halbtöne (✗ nicht gleichmäßiger),

## Sprechtext und Versuche

**1. erzaehler:** „Diese Stadt ist ein Spiel.“  
- eleven_multilingual_v2 Versuch 1: „Diese Stadt … ist ein Spiel.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x0.93 → Betonung 'Spiel,' schwach (-1,5 dB, -0,8 Halbtoene); Whisper: „Diese Stadt ist ein Spiel.“
- eleven_multilingual_v2 Versuch 2: „Diese Stadt … ist ein Spiel.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x0.98 → Betonung 'Spiel,' schwach (-0,9 dB, +0,4 Halbtoene); Whisper: „Diese Stadt ist ein Spiel.“ ← gewählt
- eleven_multilingual_v2 Versuch 3: „Diese Stadt … ist ein Spiel.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x0.94 → Betonung 'Spiel,' schwach (-0,7 dB, +1,4 Halbtoene); Whisper: „Diese Stadt ist ein Spiel.“
- eleven_v3 Versuch v3: „Diese Stadt … ist ein Spiel.“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x0.88 → Tempo 2,29 W/s ausserhalb 2,0–2,2; Betonung 'Spiel,' schwach (-2,5 dB, -1,3 Halbtoene); Whisper: „Diese Stadt ist ein Spiel.“

**2. erzaehler:** „Deine Aufgabe: Mach deine Bäckerei zur besten der Stadt.“  
- eleven_multilingual_v2 Versuch 1: „Deine Aufgabe: … Mach deine Bäckerei zur besten der Stadt.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x1.00 → Betonung 'besten' schwach (-0,4 dB, -1,9 Halbtoene); Whisper: „Deine Aufgabe, mach deine Bäckerei zur besten der Stadt.“
- eleven_multilingual_v2 Versuch 2: „Deine Aufgabe: … Mach deine Bäckerei zur, besten der Stadt.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x0.90 → Betonung 'besten' schwach (+0,6 dB, -3,1 Halbtoene); Whisper: „Deine Aufgabe, mach deine Bäckerei zur Besten der Stadt.“
- eleven_multilingual_v2 Versuch 3: „Deine Aufgabe: … Mach deine Bäckerei zur, besten der Stadt.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x1.00 → Betonung 'besten' schwach (+0,5 dB, -1,0 Halbtoene); Whisper: „Deine Aufgabe, mach deine Bäckerei zur besten der Stadt.“
- eleven_v3 Versuch v3: „Deine Aufgabe: … Mach deine Bäckerei zur, besten der Stadt.“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x0.94 → Betonung 'besten' schwach (-1,0 dB, +0,3 Halbtoene); Whisper: „Deine Aufgabe. Mach deine Bäckerei zur Besten der Stadt.“ ← gewählt

**3. byte:** „Und? Gefällt's dir? Hab ich heute Nacht gebaut.“  
- eleven_multilingual_v2 Versuch 1: „Und? Gefällt's dir? … Hab ich heute Nacht gebaut.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x0.94 → Betonung 'Nacht' schwach (+1,2 dB, -3,9 Halbtoene); Whisper: „Und? Gefällt's dir? Habe ich heute Nacht gebaut.“
- eleven_multilingual_v2 Versuch 2: „Und? Gefällt's dir? … Hab ich heute, Nacht gebaut.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x1.02 → Betonung 'Nacht' schwach (+0,1 dB, -2,4 Halbtoene); Whisper: „Und? Gefällt's dir? Hab ich heute Nacht gebaut.“
- eleven_multilingual_v2 Versuch 3: „Und? Gefällt's dir? … Hab ich heute, Nacht gebaut.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x1.00 → Betonung 'Nacht' schwach (+1,2 dB, -6,6 Halbtoene); Whisper: „Und? Gefällt's dir? Hab ich heute Nacht gebaut.“
- eleven_v3 Versuch v3: „Und? Gefällt's dir? … Hab ich heute, Nacht gebaut.“, stability 0.5, style 0.45, speed –, Tempo-Korrektur x0.93 → Betonung 'Nacht' schwach (-0,1 dB, -2,6 Halbtoene); Whisper: „Und? Gefällt's dir? Hab ich heute Nacht gebaut.“

**4. kalle:** „I hab no nie a Spiel gspielt.“  
- eleven_multilingual_v2 Versuch 1: „I hab no nie … a Spiel gspielt.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x0.90 → Betonung 'nie' schwach (-1,9 dB, -1,6 Halbtoene); Whisper: „Ich habe noch nie ein Spiel gespielt.“
- eleven_multilingual_v2 Versuch 2: „I hab no nie … a Spiel gspielt.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x0.93 → Betonung 'nie' schwach (-2,0 dB, +0,5 Halbtoene); Whisper: „Ich habe noch nie ein Spiel gespielt.“
- eleven_multilingual_v2 Versuch 3: „I hab no nie … a Spiel gspielt.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x1.00 → WER 29% > 10 %; Betonung 'nie' schwach (-1,9 dB, -0,4 Halbtoene); Whisper: „Ihr habt noch nie ein Speer, Speer.“
- eleven_v3 Versuch v3: „I hab no nie … a Spiel gspielt.“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x0.98 → WER 29% > 10 %; Whisper: „I have no knee, a spiel gespielt.“

**5. kalle:** „Brezeln für fünfzig Cent! Da kommet alle!“  
- eleven_multilingual_v2 Versuch 1: „Brezeln für fünfzig Cent! Da kommet alle!“, stability 0.3, style 0.5, speed 1.0, Tempo-Korrektur x0.94 → Aussage faellt nicht (+3,0 Halbtoene am Ende); Betonung 'fünfzig' schwach (+1,4 dB, -0,4 Halbtoene); Whisper: „Brezeln für 50 Cent. Da kommen alle.“
- eleven_multilingual_v2 Versuch 2: „Brezeln für, fünfzig Cent! Da kommet alle!“, stability 0.3, style 0.5, speed 1.0, Tempo-Korrektur x1.00 → OK; Whisper: „Brezeln für 50 Cent, da kommet alle.“
- eleven_v3 Versuch v3: „Brezeln für, fünfzig Cent! Da kommet alle!“, stability 0.5, style 0.5, speed –, Tempo-Korrektur x1.15 → WER 29% > 10 %; Tempo 2,26 W/s ausserhalb 2,6–2,9; Whisper: „Breseln Führer, 50 Cent, da kommet alle.“

**6. byte:** „Kommen sie. Aber jede kostet dich neunzig.“  
- eleven_multilingual_v2 Versuch 1: „Kommen sie. Aber jede … kostet dich neunzig.“, stability 0.55, style 0.25, speed 0.92, Tempo-Korrektur x1.00 → Aussage faellt nicht (+4,8 Halbtoene am Ende); Whisper: „Kommen Sie, aber jede kostet Dich 90.“
- eleven_multilingual_v2 Versuch 2: „Kommen sie. Aber jede … kostet dich neunzig.“, stability 0.55, style 0.25, speed 0.92, Tempo-Korrektur x1.04 → Betonung 'neunzig,' schwach (-1,8 dB, +0,6 Halbtoene); Whisper: „Kommen Sie, aber jede kostet Dich 90.“
- eleven_multilingual_v2 Versuch 3: „Kommen sie. Aber jede … kostet dich neunzig.“, stability 0.55, style 0.25, speed 0.92, Tempo-Korrektur x1.00 → Betonung 'neunzig,' schwach (-2,4 dB, -5,6 Halbtoene); Whisper: „Kommen Sie, aber jede kostet Dich 90.“
- eleven_v3 Versuch v3: „Kommen sie. Aber jede … kostet dich neunzig.“, stability 0.5, style 0.25, speed –, Tempo-Korrektur x1.15 → Aussage faellt nicht (+9,5 Halbtoene am Ende); Whisper: „Kommen Sie. Aber jede kostet Dich 90.“

**7. erzaehler:** „Tag zwei. Regen. 500 Brezeln im Ofen.“  
- eleven_multilingual_v2 Versuch 1: „Tag zwei. … Regen. … Fünfhundert Brezeln im Ofen.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x1.15 → Tempo 1,91 W/s ausserhalb 2,0–2,2; Whisper: „Tag 2. Regen. 500 Brezeln im Ofen.“
- eleven_multilingual_v2 Versuch 2: „Tag zwei. … Regen. … Fünfhundert Brezeln im Ofen.“, stability 0.55, style 0.3, speed 1.06, Tempo-Korrektur x1.10 → OK; Whisper: „Tag 2. Regen. 500 Brezeln im Ofen.“ ← gewählt
- eleven_v3 Versuch v3: „Tag zwei. … Regen. … Fünfhundert Brezeln im Ofen.“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x1.10 → OK; Whisper: „Tag 2. Regen. 500 Brezeln im Ofen.“

**8. kalle:** „Pleite?! Nach zwei Tag?!“  
- eleven_multilingual_v2 Versuch 1: „Pleite?! Nach zwei Tag?!“, stability 0.35, style 0.45, speed 1.0, Tempo-Korrektur x1.06 → WER 25% > 10 %; Betonung 'zwei' schwach (-0,3 dB, +0,0 Halbtoene); Whisper: „Pleite nach zwei Tagen?“
- eleven_multilingual_v2 Versuch 2: „Pleite?! Nach, zwei Tag?!“, stability 0.35, style 0.45, speed 1.0, Tempo-Korrektur x1.15 → Tempo 2,37 W/s ausserhalb 2,6–2,9; Aussage faellt nicht (+4,3 Halbtoene am Ende); Betonung 'zwei' schwach (-0,9 dB, -1,9 Halbtoene); Whisper: „Pleite? Nach? Zwei Tag?“ ← gewählt
- eleven_multilingual_v2 Versuch 3: „Pleite?! Nach, zwei Tag?!“, stability 0.35, style 0.45, speed 1.2, Tempo-Korrektur x1.00 → WER 25% > 10 %; Betonung 'zwei' schwach (-2,3 dB, +0,0 Halbtoene); Whisper: „Pleite nach zwei Tagen?“
- eleven_v3 Versuch v3: „Pleite?! Nach, zwei Tag?!“, stability 0.5, style 0.45, speed –, Tempo-Korrektur x1.15 → WER 25% > 10 %; Ende wirkt abgeschnitten; Tempo 2,02 W/s ausserhalb 2,6–2,9; Betonung 'zwei' schwach (-0,4 dB, -3,4 Halbtoene); Whisper: „Pleite nach zwei Tagen.“

**9. lea:** „Lass mich mal.“  
- eleven_multilingual_v2 Versuch 1: „Lass mich mal.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x0.88 → Tempo 3,39 W/s ausserhalb 2,3–2,6; Betonung 'mich' schwach (-0,6 dB, +0,2 Halbtoene); Whisper: „Lass mich mal.“
- eleven_multilingual_v2 Versuch 2: „Lass, mich mal.“, stability 0.35, style 0.45, speed 0.7, Tempo-Korrektur x1.15 → Tempo 1,67 W/s ausserhalb 2,3–2,6; Betonung 'mich' schwach (+1,2 dB, +0,6 Halbtoene); Whisper: „Lass mich mal.“
- eleven_multilingual_v2 Versuch 3: „Lass, mich mal.“, stability 0.35, style 0.45, speed 1.18, Tempo-Korrektur x0.88 → Tempo 3,73 W/s ausserhalb 2,3–2,6; Betonung 'mich' schwach (+0,1 dB, +0,2 Halbtoene); Whisper: „Lass mich mal.“
- eleven_v3 Versuch v3: „Lass, mich mal.“, stability 0.5, style 0.45, speed –, Tempo-Korrektur x0.88 → Tempo 3,24 W/s ausserhalb 2,3–2,6; Betonung 'mich' schwach (-1,7 dB, -1,4 Halbtoene); Whisper: „Lass mich mal.“

**10. byte:** „Lea backt nach Wetter. Reste gibt's ab 17 Uhr billiger.“  
- eleven_multilingual_v2 Versuch 1: „Lea backt nach Wetter. Reste gibt's … ab siebzehn Uhr billiger.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.00 → WER 18% > 10 %; Betonung 'Wetter,' schwach (+0,1 dB, +0,0 Halbtoene); Whisper: „Leerback nach Wetter. Reste gibt's ab 17 Uhr billiger.“
- eleven_multilingual_v2 Versuch 2: „Lea backt nach Wetter. Reste gibt's … ab siebzehn Uhr billiger.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.00 → Betonung 'Wetter,' schwach (-0,3 dB, -5,1 Halbtoene); Whisper: „Leer backt nach Wetter. Reste gibt's ab 17 Uhr billiger.“
- eleven_multilingual_v2 Versuch 3: „Lea backt nach Wetter. Reste gibt's … ab siebzehn Uhr billiger.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x0.93 → WER 36% > 10 %; Betonung 'Wetter,' schwach (-0,0 dB, -3,7 Halbtoene); Whisper: „Leer Backnachwetter. Reste gibt's ab 17 Uhr billiger.“
- eleven_v3 Versuch v3: „Lea backt nach Wetter. Reste gibt's … ab siebzehn Uhr billiger.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x1.00 → Ende wirkt abgeschnitten; Betonung 'Wetter,' schwach (+1,2 dB, -0,0 Halbtoene); Whisper: „Leer backt nach Wetter. Reste gibt's ab 17 Uhr billiger.“

**11. erzaehler:** „Tag 30. Und am Bahnhof … eröffnet Filiale zwei.“  
- eleven_multilingual_v2 Versuch 1: „Tag dreißig. … Und am Bahnhof … eröffnet Filiale zwei.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x1.15 → Tempo 1,88 W/s ausserhalb 2,0–2,2; Whisper: „Tag 30 und am Bahnhof eröffnet Filiale 2.“
- eleven_multilingual_v2 Versuch 2: „Tag dreißig. … Und am Bahnhof … eröffnet Filiale zwei.“, stability 0.55, style 0.3, speed 1.08, Tempo-Korrektur x1.03 → OK; Whisper: „Tag 30 und am Bahnhof eröffnet Filiale 2.“
- eleven_v3 Versuch v3: „Tag dreißig. … Und am Bahnhof … eröffnet Filiale zwei.“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x1.12 → OK; Whisper: „Tag 30 und am Bahnhof eröffnet Filiale 2.“ ← gewählt

**12. kalle:** „Die Azubi isch besser als der Meister.“  
- eleven_multilingual_v2 Versuch 1: „Die Azubi isch … besser als der Meister.“, stability 0.65, style 0.2, speed 0.84, Tempo-Korrektur x0.88 → WER 43% > 10 %; Whisper: „Die Azubi-ish, besser als der meiste.“
- eleven_multilingual_v2 Versuch 2: „Die Azubi isch … besser als der Meister.“, stability 0.65, style 0.2, speed 0.84, Tempo-Korrektur x0.88 → WER 29% > 10 %; Whisper: „Die Azubi-ish, besser als der Meister.“
- eleven_multilingual_v2 Versuch 3: „Die Azubi isch … besser als der Meister.“, stability 0.65, style 0.2, speed 0.84, Tempo-Korrektur x0.90 → OK; Whisper: „Die Azubi isch besser als der Meister.“ ← gewählt
- eleven_v3 Versuch v3: „Die Azubi isch … besser als der Meister.“, stability 0.5, style 0.2, speed –, Tempo-Korrektur x0.93 → WER 43% > 10 %; Whisper: „Die Azubi-ish besser aus der Meister.“

**13. byte:** „Ein Planspiel. Fehler kosten hier nichts.“  
- eleven_multilingual_v2 Versuch 1: „Ein Planspiel. … Fehler kosten hier nichts.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.09 → Aussage faellt nicht (+3,8 Halbtoene am Ende); Betonung 'nichts,' schwach (-5,6 dB, +0,4 Halbtoene); Whisper: „Ein Planspiel. Fehler kosten hier nichts.“
- eleven_multilingual_v2 Versuch 2: „Ein Planspiel. … Fehler kosten hier nichts.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.00 → Aussage faellt nicht (+7,5 Halbtoene am Ende); Whisper: „Ein Planspiel. Fehler kosten hier nichts.“
- eleven_multilingual_v2 Versuch 3: „Ein Planspiel. … Fehler kosten hier nichts.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x1.07 → Aussage faellt nicht (+1,6 Halbtoene am Ende); Betonung 'nichts,' schwach (-2,9 dB, +0,5 Halbtoene); Whisper: „Ein Planspiel. Fehler kosten hier nichts.“
- eleven_v3 Versuch v3: „Ein Planspiel. … Fehler kosten hier nichts.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x1.05 → Betonung 'nichts,' schwach (-3,1 dB, -6,1 Halbtoene); Whisper: „Ein Planspiel. Fehler kosten hier nichts.“ ← gewählt

**14. erzaehler:** „Diese Stadt ist ein Spiel. Deine nicht.“  
- eleven_multilingual_v2 Versuch 1: „Diese Stadt ist ein Spiel. … Deine nicht.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x0.88 → Betonung 'Deine' schwach (+1,3 dB, -0,7 Halbtoene); Whisper: „Diese Stadt ist ein Spiel, deine nicht.“
- eleven_multilingual_v2 Versuch 2: „Diese Stadt ist ein Spiel. … Deine nicht.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x0.91 → OK; Whisper: „Diese Stadt ist ein Spiel, deine nicht.“
- eleven_v3 Versuch v3: „Diese Stadt ist ein Spiel. … Deine nicht.“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x0.88 → Tempo 2,58 W/s ausserhalb 2,0–2,2; Betonung 'Deine' schwach (+1,7 dB, -5,4 Halbtoene); Whisper: „Diese Stadt ist ein Spiel, deine nicht.“

## eleven_v3

Für 14 Zeilen mit `ton` wurde zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag) erzeugt und mit demselben Check bewertet. Übernommen, weil besser als eleven_multilingual_v2: 5 Zeilen.

