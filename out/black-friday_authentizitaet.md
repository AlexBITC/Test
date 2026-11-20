# Authentizitäts-Check: Der teuerste Rabatt

Referenz: Folge `website` (ElevenLabs `eleven_multilingual_v2`). Modell dieser Folge: `eleven_multilingual_v2`.

## 1. Gleiche Stimme wie in der Referenz

| Figur | Stimme (Voice-ID) | F0-Median Folge | F0-Median Referenz | Abstand | Klangfarbe ähnlich zur Referenz (gleiche Figur) | zum Vergleich: andere Figur | Ergebnis |
|---|---|---|---|---|---|---|---|
| Kalle | Brian (`nPczCjzI2devNBz1zQrb`) | 100 Hz | 111 Hz | -1.8 Halbtöne | 0.991 | 0.679 | ✓ gleiche Stimme |
| Byte | Laura (`FGY2WhTYpPnrIDTdsKH5`) | 195 Hz | 203 Hz | -0.7 Halbtöne | 0.997 | 0.675 | ✓ gleiche Stimme |

Klangfarbe = Kosinus-Ähnlichkeit der mittleren MFCC-Vektoren (stimmhafte Abschnitte). Gleiche Stimme, wenn sie zur Referenz derselben Figur ähnlicher ist als zur anderen Figur und die Tonlage höchstens 3 Halbtöne abweicht.

## 2. Dialekt

Methode: Whisper bewertet für jedes Dialektwort zwei Fassungen der Zeile, die sich nur in diesem Wort unterscheiden (erzwungene Ausrichtung, Log-Wahrscheinlichkeit). Δ = Dialekt − Hochdeutsch. Δ > −1: Dialekt gesprochen; Δ < −3: hochdeutsch gesprochen; dazwischen unklar. Whisper bevorzugt von sich aus leicht die Schriftsprache, deshalb die Toleranz von −1.

| Szene | Wort im Text | an die Stimme geschickt | Whisper frei | Δ Dialekt − Hochdeutsch | Ergebnis |
|---|---|---|---|---|---|
| 3 | des | des | Geld verlieren? Mit Rabatt? Das geht doch gar nicht! | -6.7 | ✗ hochdeutsch gesprochen |
| 3 | net | net | Geld verlieren? Mit Rabatt? Das geht doch gar nicht! | +0.1 | ✓ Dialekt gesprochen |
| 7 | i | ich | Und je mehr ich verkaufe, desto mehr verliere ich. | -3.7 | bewusst hochdeutsch geschickt („ich“) |
| 7 | verkauf | verkauf | Und je mehr ich verkaufe, desto mehr verliere ich. | +2.9 | ✓ Dialekt gesprochen |
| 7 | verlier | verlier | Und je mehr ich verkaufe, desto mehr verliere ich. | +2.2 | ✓ Dialekt gesprochen |
| 7 | i | ich | Und je mehr ich verkaufe, desto mehr verliere ich. | -2.6 | bewusst hochdeutsch geschickt („ich“) |
| 8 | hab | hab | Genau, aber ich hab was Besseres. | +0.7 | ✓ Dialekt gesprochen |
| 14 | mei | mei | Gut, aber mein Schild behalte ich. | -2.8 | ? unklar |
| 14 | behalt | behalt | Gut, aber mein Schild behalte ich. | -0.2 | ✓ Dialekt gesprochen |
| 14 | i | i | Gut, aber mein Schild behalte ich. | +3.8 | ✓ Dialekt gesprochen |

Dialektwörter: 10, davon als Dialekt gesprochen: 6.

## 3. Natürlichkeit

| Szene | Sprecher | Tempo (W/s) | Tonhöhen-Streuung | Lautheit (P90) | Status |
|---|---|---|---|---|---|
| 1 | kalle | 2.58 | 3.4 Halbtöne | -19.6 dB | ✓ |
| 2 | byte | 2.72 | 3.2 Halbtöne | -18.5 dB | ✓ |
| 3 | kalle | 2.65 | 6.6 Halbtöne | -16.8 dB | ✓ |
| 4 | byte | 2.27 | 3.9 Halbtöne | -19.9 dB | ✓ |
| 5 | byte | 2.70 | 1.8 Halbtöne | -18.6 dB | ✓ |
| 6 | byte | 2.25 | 4.4 Halbtöne | -19.7 dB | ✓ |
| 7 | kalle | 2.65 | 3.3 Halbtöne | -20.6 dB | ✓ |
| 8 | byte | 2.74 | 3.9 Halbtöne | -17.1 dB | ✓ |
| 9 | byte | 2.70 | 3.5 Halbtöne | -19.6 dB | ✓ |
| 10 | byte | 2.70 | 3.0 Halbtöne | -16.9 dB | ✓ |
| 11 | byte | 2.41 | 3.5 Halbtöne | -19.1 dB | ✓ |
| 12 | kalle | 2.65 | 3.1 Halbtöne | -19.5 dB | ✓ |
| 13 | byte | 2.70 | 2.7 Halbtöne | -17.2 dB | ✓ |
| 14 | kalle | 2.35 | 3.6 Halbtöne | -18.2 dB | ✓ |

## 4. Stimmung

| Szene | Sprecher | Vorgabe | Erregung | F0 ggü. Figur-Mittel | Lautheit |
|---|---|---|---|---|---|
| 1 | kalle | Satzzeichen: ! | hoch | -1.7 Halbtöne | -19.6 dB |
| 2 | byte | Satzzeichen: ! | hoch | -0.8 Halbtöne | -18.5 dB |
| 3 | kalle | Satzzeichen: ? | mittel | +7.3 Halbtöne | -16.8 dB |
| 4 | byte | Satzzeichen: . | ruhig | -1.6 Halbtöne | -19.9 dB |
| 5 | byte | Satzzeichen: . | ruhig | -2.5 Halbtöne | -18.6 dB |
| 6 | byte | Satzzeichen: . | ruhig | -0.8 Halbtöne | -19.7 dB |
| 7 | kalle | Satzzeichen: ! | hoch | -2.6 Halbtöne | -20.6 dB |
| 8 | byte | Satzzeichen: . | ruhig | +4.2 Halbtöne | -17.1 dB |
| 9 | byte | Satzzeichen: . | ruhig | +0.0 Halbtöne | -19.6 dB |
| 10 | byte | Satzzeichen: . | ruhig | +3.2 Halbtöne | -16.9 dB |
| 11 | byte | Satzzeichen: . | ruhig | +3.2 Halbtöne | -19.1 dB |
| 12 | kalle | Satzzeichen: ? | mittel | +0.5 Halbtöne | -19.5 dB |
| 13 | byte | Satzzeichen: . | ruhig | +2.3 Halbtöne | -17.2 dB |
| 14 | kalle | Satzzeichen: ! | hoch | +0.0 Halbtöne | -18.2 dB |

Mittel F0: aufgeregte Zeilen -1.3 Halbtöne, ruhige +1.0 Halbtöne → ✗ kaum Unterschied.

Hinweis: `eleven_multilingual_v2` bekommt keine Stimmungs-Anweisung; die Stimmung entsteht nur aus Text, Satzzeichen und Stil-Einstellung (stability/style).

