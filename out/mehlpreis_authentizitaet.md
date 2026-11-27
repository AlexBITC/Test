# Authentizitäts-Check: Byte telefoniert

Referenz: Folge `website` (ElevenLabs `eleven_multilingual_v2`). Modell dieser Folge: `eleven_multilingual_v2`.

## 1. Gleiche Stimme wie in der Referenz

| Figur | Stimme (Voice-ID) | F0-Median Folge | F0-Median Referenz | Abstand | Klangfarbe ähnlich zur Referenz (gleiche Figur) | zum Vergleich: andere Figur | Ergebnis |
|---|---|---|---|---|---|---|---|
| Kalle | Brian (`nPczCjzI2devNBz1zQrb`) | 109 Hz | 111 Hz | -0.3 Halbtöne | 0.967 | 0.716 | ✓ gleiche Stimme |
| Byte | Laura (`FGY2WhTYpPnrIDTdsKH5`) | 200 Hz | 203 Hz | -0.3 Halbtöne | 0.988 | 0.664 | ✓ gleiche Stimme |

Klangfarbe = Kosinus-Ähnlichkeit der mittleren MFCC-Vektoren (stimmhafte Abschnitte). Gleiche Stimme, wenn sie zur Referenz derselben Figur ähnlicher ist als zur anderen Figur und die Tonlage höchstens 3 Halbtöne abweicht.

## 2. Dialekt

Methode: Whisper bewertet für jedes Dialektwort zwei Fassungen der Zeile, die sich nur in diesem Wort unterscheiden (erzwungene Ausrichtung, Log-Wahrscheinlichkeit). Δ = Dialekt − Hochdeutsch. Δ > −1: Dialekt gesprochen; Δ < −3: hochdeutsch gesprochen; dazwischen unklar. Whisper bevorzugt von sich aus leicht die Schriftsprache, deshalb die Toleranz von −1.

| Szene | Wort im Text | an die Stimme geschickt | Whisper frei | Δ Dialekt − Hochdeutsch | Ergebnis |
|---|---|---|---|---|---|
| 1 | en | 'n | 24 Euro für ein Sack Mehl? Die spinnet doch! | -0.1 | ✓ Dialekt gesprochen |
| 1 | spinnet | spinnet | 24 Euro für ein Sack Mehl? Die spinnet doch! | +6.0 | ✓ Dialekt gesprochen |
| 2 | telefonier | telefonier | Ich telefonier das mal schnell weg. | +0.8 | ✓ Dialekt gesprochen |
| 3 | net | net | Du telefonieren, du hast doch nicht mal Ohren. | -0.6 | ✓ Dialekt gesprochen |
| 4 | brauch | brauch | Brauche ich nicht. Ich habe drei Hörer. | +0.3 | ✓ Dialekt gesprochen |
| 4 | hab | hab | Brauche ich nicht. Ich habe drei Hörer. | +2.5 | ✓ Dialekt gesprochen |
| 10 | des | des | Bärte, das ist mein Müller, der kennt mich. | -0.8 | ✓ Dialekt gesprochen |
| 10 | isch | isch | Bärte, das ist mein Müller, der kennt mich. | +2.9 | ✓ Dialekt gesprochen |
| 10 | mi | mi | Bärte, das ist mein Müller, der kennt mich. | +0.9 | ✓ Dialekt gesprochen |
| 14 | i | ich | Und ich hab jahrelang einfach bezahlt. | -10.3 | bewusst hochdeutsch geschickt („ich“) |
| 14 | hab | hab | Und ich hab jahrelang einfach bezahlt. | +1.0 | ✓ Dialekt gesprochen |

Dialektwörter: 11, davon als Dialekt gesprochen: 10.

## 3. Natürlichkeit

| Szene | Sprecher | Tempo (W/s) | Tonhöhen-Streuung | Lautheit (P90) | Status |
|---|---|---|---|---|---|
| 1 | kalle | 2.84 | 5.2 Halbtöne | -16.8 dB | ✓ |
| 2 | byte | 2.45 | 2.5 Halbtöne | -20.9 dB | ✓ |
| 3 | kalle | 2.65 | 4.1 Halbtöne | -18.5 dB | ✓ |
| 4 | byte | 2.40 | 2.8 Halbtöne | -18.5 dB | ✓ |
| 5 | byte | 2.70 | 2.2 Halbtöne | -17.2 dB | ✓ |
| 6 | byte | 2.25 | 3.9 Halbtöne | -18.1 dB | ✓ |
| 7 | kalle | 2.01 | 2.3 Halbtöne | -17.0 dB | ✓ |
| 8 | byte | 2.60 | 2.0 Halbtöne | -16.9 dB | ✓ |
| 9 | byte | 2.28 | 3.2 Halbtöne | -19.9 dB | ✓ |
| 10 | kalle | 2.65 | 4.9 Halbtöne | -19.4 dB | ✓ |
| 11 | byte | 2.25 | 2.9 Halbtöne | -20.1 dB | ✓ |
| 12 | kalle | 2.65 | 5.3 Halbtöne | -18.7 dB | ✓ |
| 13 | byte | 2.70 | 3.1 Halbtöne | -18.8 dB | ✓ |
| 14 | kalle | 2.38 | 2.0 Halbtöne | -20.0 dB | ✓ |

## 4. Stimmung

| Szene | Sprecher | Vorgabe | Erregung | F0 ggü. Figur-Mittel | Lautheit |
|---|---|---|---|---|---|
| 1 | kalle | Satzzeichen: ! | hoch | +7.9 Halbtöne | -16.8 dB |
| 2 | byte | Satzzeichen: . | ruhig | -0.1 Halbtöne | -20.9 dB |
| 3 | kalle | Satzzeichen: ! | hoch | +1.3 Halbtöne | -18.5 dB |
| 4 | byte | Satzzeichen: . | ruhig | -3.1 Halbtöne | -18.5 dB |
| 5 | byte | Satzzeichen: ! | hoch | +3.2 Halbtöne | -17.2 dB |
| 6 | byte | Satzzeichen: . | ruhig | -1.3 Halbtöne | -18.1 dB |
| 7 | kalle | Satzzeichen: ! | hoch | +5.3 Halbtöne | -17.0 dB |
| 8 | byte | Satzzeichen: . | ruhig | -5.4 Halbtöne | -16.9 dB |
| 9 | byte | Satzzeichen: ? | mittel | +2.8 Halbtöne | -19.9 dB |
| 10 | kalle | Satzzeichen: ! | hoch | -2.7 Halbtöne | -19.4 dB |
| 11 | byte | Satzzeichen: . | ruhig | +0.1 Halbtöne | -20.1 dB |
| 12 | kalle | Satzzeichen: ! | hoch | -1.5 Halbtöne | -18.7 dB |
| 13 | byte | Satzzeichen: . | ruhig | +1.2 Halbtöne | -18.8 dB |
| 14 | kalle | Satzzeichen: . | ruhig | -4.2 Halbtöne | -20.0 dB |

Mittel F0: aufgeregte Zeilen +2.3 Halbtöne, ruhige -1.8 Halbtöne → ✓ Stimmung hörbar.

Hinweis: `eleven_multilingual_v2` bekommt keine Stimmungs-Anweisung; die Stimmung entsteht nur aus Text, Satzzeichen und Stil-Einstellung (stability/style).

