# Stimmen-Check: Das Geheimnis in Kalles Händen

Erweiterter Check (Engine 2.3) für Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext`. Stimmen: ElevenLabs, Kalle = Brian, Byte = Laura, Lea = Sarah (ab 2.4). Atmer am Satzanfang bleiben erhalten (laute werden gedämpft). Kriterien: Wortfehler ≤ 10 % (schwäbische Wörter frei), Zahlen und Begriff exakt, Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil), Frage steigt / Aussage fällt (letztes Wort gegen den Rest der Zeile), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz (außer nach „…“). Höchstens 3 Versuche. Tempo: zuerst ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %, Spalte Tempo-Korrektur).

| # | Sprecher | ton / tempo | Modell | Versuche | WER | W/s (Ziel), Tempo-Korrektur | F0 | Spannweite | Ende | Betonung | Peak | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | genervt / schnell | eleven_multilingual_v2 | 1 | 0% | 2,68 (2,6–2,9), x1,00 | 137 Hz | 17,1 Halbtöne | -11,7 Halbtöne (Aussage) | „zehnten“ +1,6 dB / +3,4 Halbtöne | 0,76 | OK |
| 2 | lea | enttaeuscht / langsam | eleven_multilingual_v2 | 3 | 0% | 2,15 (2,0–2,2), x1,00 | 283 Hz | 23,1 Halbtöne | -0,9 Halbtöne (Aussage) | „nicht“ -2,2 dB / -0,8 Halbtöne | 0,86 | FAIL: Betonung 'nicht' schwach (-2,2 dB, -0,8 Halbtoene) |
| 3 | kalle | ruhig / langsam | eleven_multilingual_v2 | 3 | 0% | 2,07 (2,0–2,2), x1,00 | 91 Hz | 15,1 Halbtöne | -6,5 Halbtöne (Aussage) | „net“ -1,9 dB / -2,5 Halbtöne | 0,56 | FAIL: Betonung 'net' schwach (-1,9 dB, -2,5 Halbtoene) |
| 4 | byte | ruhig / normal | eleven_v3 | 3 | 0% | 2,56 (2,3–2,6), x0,96 | 247 Hz | 12,4 Halbtöne | -5,8 Halbtöne (Aussage) | „langsam“ -2,0 dB / -3,7 Halbtöne | 0,79 | FAIL: Betonung 'langsam,' schwach (-2,0 dB, -3,7 Halbtoene) |
| 5 | byte | neugierig / normal | eleven_multilingual_v2 | 1 | 0% | 2,28 (2,3–2,6), x1,15 | 209 Hz | 15,4 Halbtöne | -8,4 Halbtöne (Aussage) | „Zeitlupe“ +2,5 dB / -8,8 Halbtöne | 0,69 | OK |
| 6 | byte | nachdenklich / langsam | eleven_multilingual_v2 | 3 | 8% | 2,20 (2,0–2,2), x0,88 | 214 Hz | 12,0 Halbtöne | -7,5 Halbtöne (Aussage) | „Schwung“ -2,4 dB / -0,6 Halbtöne | 0,66 | FAIL: Betonung 'Schwung' schwach (-2,4 dB, -0,6 Halbtoene) |
| 7 | kalle | fragend / normal | eleven_v3 | 3 | 0% | 2,34 (2,3–2,6), x1,05 | 119 Hz | 18,5 Halbtöne | -5,1 Halbtöne (Aussage) | „Echt“ -0,4 dB / +5,1 Halbtöne | 0,87 | OK |
| 8 | byte | ueberzeugt / normal | eleven_v3 | 3 | 0% | 2,59 (2,3–2,6), x1,00 | 214 Hz | 25,4 Halbtöne | -6,6 Halbtöne (Aussage) | „erklären“ +5,5 dB / -6,3 Halbtöne | 0,67 | OK |
| 9 | byte | verschmitzt / normal | eleven_multilingual_v2 | 3 | 0% | 2,67 (2,3–2,6), x0,88 | 244 Hz | 5,5 Halbtöne | -3,2 Halbtöne (Aussage) | „Brille“ +2,2 dB / -0,9 Halbtöne | 0,61 | FAIL: Tempo 2,67 W/s ausserhalb 2,3–2,6 |
| 10 | byte | begeistert / langsam | eleven_multilingual_v2 | 3 | 0% | 2,16 (2,0–2,2), x0,96 | 167 Hz | 21,7 Halbtöne | -1,8 Halbtöne (Aussage) | „Schwung“ +2,1 dB / -3,5 Halbtöne | 0,84 | OK |
| 11 | lea | begeistert / normal | eleven_multilingual_v2 | 3 | 0% | 2,33 (2,3–2,6), x1,00 | 285 Hz | 24,8 Halbtöne | +6,8 Halbtöne (Aussage) | „perfekt“ +2,3 dB / +2,9 Halbtöne | 0,91 | FAIL: Aussage faellt nicht (+6,8 Halbtoene am Ende) |
| 12 | kalle | geruehrt / langsam | eleven_multilingual_v2 | 1 | 0% | 2,16 (2,0–2,2), x0,97 | 96 Hz | 13,0 Halbtöne | -8,7 Halbtöne (Aussage) | „besser“ +3,1 dB / +0,0 Halbtöne | 0,65 | OK |
| 13 | lea | stolz / langsam | eleven_multilingual_v2 | 3 | 0% | 2,04 (2,0–2,2), x1,03 | 271 Hz | 9,1 Halbtöne | +4,2 Halbtöne (Aussage) | „Meine“ +4,1 dB / -2,3 Halbtöne | 0,87 | FAIL: Aussage faellt nicht (+4,2 Halbtoene am Ende) |
| 14 | kalle | verschmitzt / normal | eleven_multilingual_v2 | 3 | 0% | 2,34 (2,3–2,6), x1,00 | 88 Hz | 18,4 Halbtöne | -14,1 Halbtöne (Aussage) | „Stollen“ -0,0 dB / -9,5 Halbtöne | 0,66 | FAIL: Betonung 'Stollen,' schwach (-0,0 dB, -9,5 Halbtoene) |

Kalle und Byte: mittlere Tonhöhe 96 Hz gegen 214 Hz, Abstand 13.9 Halbtöne → ✓ klar unterscheidbar (Ziel ≥ 4).

Lea und Kalle: 283 Hz gegen 96 Hz, Lea liegt 18,8 Halbtöne höher → ✓ (Ziel ≥ 4).
Lea und Byte: Tonhöhe 283 Hz gegen 214 Hz (+4.9 Halbtöne); Klangfarbe (Abstand der mittleren MFCC 2–20): 53.6, zum Vergleich Kalle–Byte 70.3 → ✓ klar unterscheidbar (Klangfarbe) (Ziel ≥ 25).

## Zurücknahme (Zusatz-Check dieser Folge)

Zeilen müssen mindestens 3 dB leiser als der Durchschnitt der Folge (-20,5 dBFS, gesprochene Abschnitte) und langsamer als 2,2 Wörter/s sein,

| # | Sprecher | Pegel gegen Durchschnitt | W/s | Abmischung | Status |
|---|---|---|---|---|---|
| 2 | lea | -3,4 dB | 2,15 | -7,5 dB | OK |
| 3 | kalle | -3,5 dB | 2,07 | -1,8 dB | OK |
| 12 | kalle | -3,5 dB | 2,16 | -2,2 dB | OK |
| 13 | lea | -3,5 dB | 2,04 | -9,3 dB | OK |

## Sprechtext und Versuche

**1. kalle:** „Zum zehnten Mal: Bauch dick, Ärmchen dünn!“  
- eleven_multilingual_v2 Versuch 1: „Zum zehnten Mal: Bauch dick … Ärmchen dünn!“, stability 0.35, style 0.45, speed 1.0, Tempo-Korrektur x1.00 → OK; Whisper: „Zum zehnten Mal bauchdick, Ärmchen dünn.“ ← gewählt
- eleven_v3 Versuch v3: „Zum zehnten Mal: Bauch dick … Ärmchen dünn!“, stability 0.5, style 0.45, speed –, Tempo-Korrektur x1.15 → Ende wirkt abgeschnitten; Tempo 1,99 W/s ausserhalb 2,6–2,9; Whisper: „Zum zehnten Mal, Bauch dick, Ärmchen dünn.“

**2. lea:** „Ich krieg's einfach nicht hin.“  
- eleven_multilingual_v2 Versuch 1: „Ich krieg's … einfach nicht hin.“, stability 0.6, style 0.2, speed 0.84, Tempo-Korrektur x1.00 → Betonung 'nicht' schwach (-2,2 dB, -0,8 Halbtoene); Whisper: „Ich krieg's einfach nicht hin.“
- eleven_multilingual_v2 Versuch 2: „Ich krieg's … einfach, nicht hin.“, stability 0.6, style 0.2, speed 0.84, Tempo-Korrektur x1.06 → Betonung 'nicht' schwach (+1,5 dB, -1,2 Halbtoene); Whisper: „Ich krieg's einfach nicht hin.“
- eleven_multilingual_v2 Versuch 3: „Ich krieg's … einfach, nicht hin.“, stability 0.6, style 0.2, speed 0.84, Tempo-Korrektur x1.10 → Betonung 'nicht' schwach (+1,9 dB, -3,0 Halbtoene); Whisper: „Ich krieg's einfach nicht hin.“
- eleven_v3 Versuch v3: „Ich krieg's … einfach nicht hin.“, stability 0.5, style 0.2, speed –, Tempo-Korrektur x0.88 → Betonung 'nicht' schwach (-1,6 dB, -0,6 Halbtoene); Whisper: „Ich krieg's einfach nicht hin.“

**3. kalle:** „Hey … so war des net gmeint.“  
- eleven_multilingual_v2 Versuch 1: „Hey … so war des net gmeint.“, stability 0.6, style 0.15, speed 0.84, Tempo-Korrektur x0.88 → Tempo 2,53 W/s ausserhalb 2,0–2,2; Betonung 'net' schwach (-2,9 dB, -4,2 Halbtoene); Whisper: „Hey, so war das nicht gemeint.“
- eleven_multilingual_v2 Versuch 2: „Hey … so war des, net gmeint.“, stability 0.6, style 0.15, speed 0.7, Tempo-Korrektur x1.00 → Betonung 'net' schwach (-1,9 dB, -2,5 Halbtoene); Whisper: „Hey, so war das net gemeint.“
- eleven_multilingual_v2 Versuch 3: „Hey … so war des, net gmeint.“, stability 0.6, style 0.15, speed 0.7, Tempo-Korrektur x0.93 → Betonung 'net' schwach (-2,0 dB, -3,5 Halbtoene); Whisper: „Hey, so war das nicht gemeint.“
- eleven_v3 Versuch v3: „Hey … so war des, net gmeint.“, stability 0.5, style 0.15, speed –, Tempo-Korrektur x0.88 → Tempo 2,48 W/s ausserhalb 2,0–2,2; Whisper: „Hey, so war das nett gemeint.“

**4. byte:** „Kalle, mach's noch mal. Ganz langsam. Ich film mit.“  
- eleven_multilingual_v2 Versuch 1: „Kalle, mach's noch mal. Ganz langsam. Ich film mit.“, stability 0.6, style 0.15, speed 0.92, Tempo-Korrektur x0.88 → Aussage faellt nicht (+4,6 Halbtoene am Ende); Betonung 'langsam,' schwach (-0,1 dB, -5,5 Halbtoene); Whisper: „Kalle, mach's noch mal ganz langsam. Ich film mit.“
- eleven_multilingual_v2 Versuch 2: „Kalle, mach's noch mal. Ganz langsam. Ich film mit.“, stability 0.6, style 0.15, speed 0.92, Tempo-Korrektur x0.88 → Aussage faellt nicht (+8,8 Halbtoene am Ende); Betonung 'langsam,' schwach (-0,2 dB, -6,3 Halbtoene); Whisper: „Kalle, mach's noch mal. Ganz langsam. Ich film mit.“
- eleven_multilingual_v2 Versuch 3: „Kalle, mach's noch mal. Ganz langsam. Ich film mit.“, stability 0.6, style 0.15, speed 0.92, Tempo-Korrektur x0.88 → Tempo 2,87 W/s ausserhalb 2,3–2,6; Betonung 'langsam,' schwach (+0,3 dB, -2,5 Halbtoene); Whisper: „Kalle, mach's nochmal, ganz langsam, ich film mit.“
- eleven_v3 Versuch v3: „Kalle, mach's noch mal. Ganz langsam. Ich film mit.“, stability 0.5, style 0.15, speed –, Tempo-Korrektur x0.96 → Betonung 'langsam,' schwach (-2,0 dB, -3,7 Halbtoene); Whisper: „Kalle, mach's nochmal. Ganz langsam. Ich film mit.“ ← gewählt

**5. byte:** „Kalles Brezel. In fünf Schritten. In Zeitlupe.“  
- eleven_multilingual_v2 Versuch 1: „Kalles Brezel. In fünf Schritten … in Zeitlupe.“, stability 0.4, style 0.35, speed 0.92, Tempo-Korrektur x1.15 → OK; Whisper: „Kalles Brezel in 5 Schritten in Zeitlupe.“ ← gewählt
- eleven_v3 Versuch v3: „Kalles Brezel. In fünf Schritten … in Zeitlupe.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x1.15 → WER 43% > 10 %; Tempo 2,19 W/s ausserhalb 2,3–2,6; Betonung 'Zeitlupe,' schwach (+1,0 dB, -1,2 Halbtoene); Whisper: „Kalle Sprezl. In fünf Schritten in Sideloop.“

**6. byte:** „Und da: Du machst einen kleinen Schwung aus dem Handgelenk. Lea nicht.“  
- eleven_multilingual_v2 Versuch 1: „Und da … du machst einen kleinen Schwung aus dem Handgelenk. Lea nicht.“, stability 0.55, style 0.25, speed 0.84, Tempo-Korrektur x0.88 → Betonung 'Schwung' schwach (-2,4 dB, -0,6 Halbtoene); Whisper: „Und da. Du machst einen kleinen Schwung aus dem Handgelenk. Leer nicht.“ ← gewählt
- eleven_multilingual_v2 Versuch 2: „Und da … du machst einen kleinen, Schwung aus dem Handgelenk. Lea nicht.“, stability 0.55, style 0.25, speed 0.84, Tempo-Korrektur x0.89 → Aussage faellt nicht (+4,8 Halbtoene am Ende); Betonung 'Schwung' schwach (+1,2 dB, -1,8 Halbtoene); Whisper: „Und da, du machst einen kleinen Schwung aus dem Handgelenk. Lea nicht!“
- eleven_multilingual_v2 Versuch 3: „Und da … du machst einen kleinen, Schwung aus dem Handgelenk. Lea nicht.“, stability 0.55, style 0.25, speed 0.84, Tempo-Korrektur x0.88 → Aussage faellt nicht (+2,9 Halbtoene am Ende); Betonung 'Schwung' schwach (-0,3 dB, -2,6 Halbtoene); Whisper: „Und da, du machst einen kleinen Schwung aus dem Handgelenk. Leer nicht?“
- eleven_v3 Versuch v3: „Und da … du machst einen kleinen Schwung aus dem Handgelenk. Lea nicht.“, stability 0.5, style 0.25, speed –, Tempo-Korrektur x0.88 → Tempo 2,26 W/s ausserhalb 2,0–2,2; Whisper: „Und da, du machst einen kleinen Schwung aus dem Handgelenk. Leer nicht.“

**7. kalle:** „Echt? Des mach i einfach so.“  
- eleven_multilingual_v2 Versuch 1: „Echt? Des mach i … einfach so.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x1.15 → Betonung 'Echt?' schwach (+0,5 dB, +0,0 Halbtoene); Whisper: „Echt? Das mach i... einfach so.“
- eleven_multilingual_v2 Versuch 2: „Echt? Des mach i … einfach so.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x1.00 → WER 17% > 10 %; Betonung 'Echt?' schwach (+2,0 dB, +0,0 Halbtoene); Whisper: „Ehrchen, das mach ich... einfach so.“
- eleven_multilingual_v2 Versuch 3: „Echt? Des mach i … einfach so.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x1.15 → WER 33% > 10 %; monoton (Spannweite 3,2 Halbtoene < 4); Betonung 'Echt?' schwach (+0,9 dB, +0,0 Halbtoene); Whisper: „Echt? Das mache ich ja. Einfach so.“
- eleven_v3 Versuch v3: „Echt? Des mach i … einfach so.“, stability 0.5, style 0.4, speed –, Tempo-Korrektur x1.05 → OK; Whisper: „Echt? Das mach ich. Einfach so.“ ← gewählt

**8. byte:** „Das ist implizites Wissen. Du kannst es, aber du kannst es nicht erklären.“  
- eleven_multilingual_v2 Versuch 1: „Das ist implizites Wissen. Du kannst es … aber du kannst es nicht erklären.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x0.93 → Betonung 'erklären,' schwach (+0,1 dB, -3,6 Halbtoene); Whisper: „Das ist implizites Wissen. Du kannst es, aber du kannst es nicht erklären.“
- eleven_multilingual_v2 Versuch 2: „Das ist implizites Wissen. Du kannst es … aber du kannst es nicht erklären.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x0.96 → Betonung 'erklären,' schwach (+1,0 dB, +0,5 Halbtoene); Whisper: „Das ist implizites Wissen, du kannst es, aber du kannst es nicht erklären.“
- eleven_multilingual_v2 Versuch 3: „Das ist implizites Wissen. Du kannst es … aber du kannst es nicht erklären.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x0.98 → Betonung 'erklären,' schwach (+1,0 dB, -2,9 Halbtoene); Whisper: „Das ist implizites Wissen. Du kannst es, aber du kannst es nicht erklären.“
- eleven_v3 Versuch v3: „Das ist implizites Wissen. Du kannst es … aber du kannst es nicht erklären.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x1.00 → OK; Whisper: „Das ist implizites Wissen. Du kannst es, aber du kannst es nicht erklären.“ ← gewählt

**9. byte:** „Lea, setz mal die Brille auf.“  
- eleven_multilingual_v2 Versuch 1: „Lea, setz mal die Brille auf.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x0.88 → Tempo 4,23 W/s ausserhalb 2,3–2,6; Whisper: „Lea, setz mal die Brille auf.“
- eleven_multilingual_v2 Versuch 2: „Lea, setz mal die Brille auf.“, stability 0.35, style 0.45, speed 0.7, Tempo-Korrektur x0.88 → Tempo 3,09 W/s ausserhalb 2,3–2,6; Betonung 'Brille' schwach (+1,6 dB, +1,0 Halbtoene); Whisper: „Lea, setz mal die Brille auf.“
- eleven_multilingual_v2 Versuch 3: „Lea, setz mal die, Brille auf.“, stability 0.35, style 0.45, speed 0.7, Tempo-Korrektur x0.88 → Tempo 2,67 W/s ausserhalb 2,3–2,6; Whisper: „Lea, setz mal die Brille auf.“ ← gewählt
- eleven_v3 Versuch v3: „Lea, setz mal die, Brille auf.“, stability 0.5, style 0.45, speed –, Tempo-Korrektur x0.88 → Tempo 3,24 W/s ausserhalb 2,3–2,6; Betonung 'Brille' schwach (+0,1 dB, -1,2 Halbtoene); Whisper: „Lea, setz mal die Brille auf.“

**10. byte:** „Rollen. Formen. Und jetzt: Schwung.“  
- eleven_multilingual_v2 Versuch 1: „Rollen. … Formen. … Und jetzt … Schwung!“, stability 0.3, style 0.5, speed 0.84, Tempo-Korrektur x1.15 → Tempo 1,53 W/s ausserhalb 2,0–2,2; Aussage faellt nicht (+1,7 Halbtoene am Ende); Whisper: „Rollen, Formen und jetzt Schwung.“
- eleven_multilingual_v2 Versuch 2: „Rollen. … Formen. … Und jetzt … Schwung!“, stability 0.3, style 0.5, speed 1.2, Tempo-Korrektur x1.13 → Aussage faellt nicht (+4,4 Halbtoene am Ende); Betonung 'Schwung,' schwach (+0,5 dB, -1,1 Halbtoene); Whisper: „Rollen, Formen und jetzt Schwung.“
- eleven_multilingual_v2 Versuch 3: „Rollen. … Formen. … Und jetzt … Schwung!“, stability 0.3, style 0.5, speed 1.2, Tempo-Korrektur x0.96 → OK; Whisper: „Rollen, Formen und jetzt Schwung.“ ← gewählt
- eleven_v3 Versuch v3: „Rollen. … Formen. … Und jetzt … Schwung!“, stability 0.5, style 0.5, speed –, Tempo-Korrektur x1.15 → Tempo 1,57 W/s ausserhalb 2,0–2,2; Aussage faellt nicht (+10,2 Halbtoene am Ende); Whisper: „Rollen, formen und jetzt Schwung.“

**11. lea:** „Sie ist … perfekt!“  
- eleven_multilingual_v2 Versuch 1: „Sie ist … perfekt!“, stability 0.3, style 0.5, speed 0.92, Tempo-Korrektur x1.15 → Tempo 1,65 W/s ausserhalb 2,3–2,6; Aussage faellt nicht (+2,3 Halbtoene am Ende); Betonung 'perfekt!' schwach (-1,1 dB, +0,6 Halbtoene); Whisper: „Sie ist perfekt.“
- eleven_multilingual_v2 Versuch 2: „Sie ist … perfekt!“, stability 0.3, style 0.5, speed 1.2, Tempo-Korrektur x1.00 → Aussage faellt nicht (+6,8 Halbtoene am Ende); Whisper: „Sie ist perfekt.“ ← gewählt
- eleven_multilingual_v2 Versuch 3: „Sie ist … perfekt!“, stability 0.3, style 0.5, speed 1.2, Tempo-Korrektur x1.04 → Aussage faellt nicht (+2,2 Halbtoene am Ende); Betonung 'perfekt!' schwach (-1,0 dB, +0,1 Halbtoene); Whisper: „Sie ist perfekt.“
- eleven_v3 Versuch v3: „Sie ist … perfekt!“, stability 0.5, style 0.5, speed –, Tempo-Korrektur x1.15 → Tempo 1,84 W/s ausserhalb 2,3–2,6; Aussage faellt nicht (+2,3 Halbtoene am Ende); Betonung 'perfekt!' schwach (+0,9 dB, -3,8 Halbtoene); Whisper: „Sie ist perfekt.“

**12. kalle:** „Die isch besser als mei erschte.“  
- eleven_multilingual_v2 Versuch 1: „Die isch … besser als mei erschte.“, stability 0.65, style 0.2, speed 0.84, Tempo-Korrektur x0.97 → OK; Whisper: „Die isch besser als Mai Erste.“
- eleven_v3 Versuch v3: „Die isch … besser als mei erschte.“, stability 0.5, style 0.2, speed –, Tempo-Korrektur x0.88 → Tempo 2,25 W/s ausserhalb 2,0–2,2; Whisper: „Die ist besser als meine erste.“

**13. lea:** „Die hat grad jemand gekauft. Meine Brezel.“  
- eleven_multilingual_v2 Versuch 1: „Die hat grad jemand gekauft. … Meine Brezel.“, stability 0.45, style 0.35, speed 0.84, Tempo-Korrektur x1.09 → WER 14% > 10 %; Betonung 'Meine' schwach (+0,3 dB, -1,4 Halbtoene); Whisper: „Die hat grad jemand gekauft. Ähm, meine Brezel.“
- eleven_multilingual_v2 Versuch 2: „Die hat grad jemand gekauft. … Meine Brezel.“, stability 0.45, style 0.35, speed 0.84, Tempo-Korrektur x1.03 → Aussage faellt nicht (+4,2 Halbtoene am Ende); Whisper: „Die hat gerade jemand gekauft, meine Brezel.“
- eleven_multilingual_v2 Versuch 3: „Die hat grad jemand gekauft. … Meine Brezel.“, stability 0.45, style 0.35, speed 0.84, Tempo-Korrektur x1.00 → WER 14% > 10 %; Whisper: „Die hat grad jemand gekauft. Meine Breze.“
- eleven_v3 Versuch v3: „Die hat grad jemand gekauft. … Meine Brezel.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x0.88 → WER 14% > 10 %; Betonung 'Meine' schwach (+1,5 dB, -2,2 Halbtoene); Whisper: „Die hat grad jemand gekauft. Meine Breze.“

**14. kalle:** „Byte … film mi glei nochmal. Beim Stollen.“  
- eleven_multilingual_v2 Versuch 1: „Byte … film mi glei nochmal. Beim Stollen.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x1.00 → Betonung 'Stollen,' schwach (+0,5 dB, +0,4 Halbtoene); Whisper: „Byte, film mich gleich nochmal, beim Stollen.“
- eleven_multilingual_v2 Versuch 2: „Byte … film mi glei nochmal. Beim Stollen.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x0.91 → Betonung 'Stollen,' schwach (-0,4 dB, -2,2 Halbtoene); Whisper: „Byte, film mir gleich nochmal beim Stollen.“
- eleven_multilingual_v2 Versuch 3: „Byte … film mi glei nochmal. Beim Stollen.“, stability 0.35, style 0.45, speed 0.92, Tempo-Korrektur x1.00 → Betonung 'Stollen,' schwach (-0,0 dB, -9,5 Halbtoene); Whisper: „Byte, film mich gleich nochmal beim Stollen.“ ← gewählt
- eleven_v3 Versuch v3: „Byte … film mi glei nochmal. Beim Stollen.“, stability 0.5, style 0.45, speed –, Tempo-Korrektur x1.00 → WER 14% > 10 %; Ende wirkt abgeschnitten; Betonung 'Stollen,' schwach (-0,1 dB, -0,8 Halbtoene); Whisper: „Film' mich gleich nochmal beim Stollen.“

## eleven_v3

Für 14 Zeilen mit `ton` wurde zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag) erzeugt und mit demselben Check bewertet. Übernommen, weil besser als eleven_multilingual_v2: 3 Zeilen.

