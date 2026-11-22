# Authentizitäts-Check: Bytes Nachtschicht

Referenz: Folge `website` (ElevenLabs `eleven_multilingual_v2`). Modell dieser Folge: `eleven_multilingual_v2`.

## 1. Gleiche Stimme wie in der Referenz

| Figur | Stimme (Voice-ID) | F0-Median Folge | F0-Median Referenz | Abstand | Klangfarbe ähnlich zur Referenz (gleiche Figur) | zum Vergleich: andere Figur | Ergebnis |
|---|---|---|---|---|---|---|---|
| Kalle | Brian (`nPczCjzI2devNBz1zQrb`) | 109 Hz | 111 Hz | -0.2 Halbtöne | 0.958 | 0.622 | ✓ gleiche Stimme |
| Byte | Laura (`FGY2WhTYpPnrIDTdsKH5`) | 210 Hz | 203 Hz | +0.6 Halbtöne | 0.994 | 0.662 | ✓ gleiche Stimme |

Klangfarbe = Kosinus-Ähnlichkeit der mittleren MFCC-Vektoren (stimmhafte Abschnitte). Gleiche Stimme, wenn sie zur Referenz derselben Figur ähnlicher ist als zur anderen Figur und die Tonlage höchstens 3 Halbtöne abweicht.

## 2. Dialekt

Methode: Whisper bewertet für jedes Dialektwort zwei Fassungen der Zeile, die sich nur in diesem Wort unterscheiden (erzwungene Ausrichtung, Log-Wahrscheinlichkeit). Δ = Dialekt − Hochdeutsch. Δ > −1: Dialekt gesprochen; Δ < −3: hochdeutsch gesprochen; dazwischen unklar. Whisper bevorzugt von sich aus leicht die Schriftsprache, deshalb die Toleranz von −1.

| Szene | Wort im Text | an die Stimme geschickt | Whisper frei | Δ Dialekt − Hochdeutsch | Ergebnis |
|---|---|---|---|---|---|
| 3 | hab | hab | Ich habe 37 Bewerbungen gelesen, drei passen perfekt. | -1.8 | ? unklar |
| 12 | i | i | Na dann, back ihr jetzt mal Brezeln. | +3.1 | ✓ Dialekt gesprochen |

Dialektwörter: 2, davon als Dialekt gesprochen: 1.

## 3. Natürlichkeit

| Szene | Sprecher | Tempo (W/s) | Tonhöhen-Streuung | Lautheit (P90) | Status |
|---|---|---|---|---|---|
| 1 | byte | 2.70 | 3.2 Halbtöne | -15.8 dB | ✓ |
| 2 | kalle | 2.75 | 4.4 Halbtöne | -17.3 dB | ✓ |
| 3 | byte | 2.25 | 3.5 Halbtöne | -18.4 dB | ✓ |
| 4 | byte | 2.28 | 2.6 Halbtöne | -20.1 dB | ✓ |
| 5 | byte | 2.25 | 3.6 Halbtöne | -19.1 dB | ✓ |
| 6 | byte | 2.25 | 2.3 Halbtöne | -19.0 dB | ✓ |
| 7 | kalle | 2.25 | 1.8 Halbtöne | -17.6 dB | ✓ |
| 8 | kalle | 2.65 | 3.6 Halbtöne | -21.0 dB | ✓ |
| 9 | byte | 2.70 | 3.5 Halbtöne | -17.2 dB | ✓ |
| 10 | byte | 2.54 | 2.6 Halbtöne | -19.6 dB | ✓ |
| 11 | byte | 2.71 | 3.8 Halbtöne | -17.0 dB | ✓ |
| 12 | kalle | 2.42 | 3.5 Halbtöne | -20.1 dB | ✓ |
| 13 | byte | 2.71 | 2.1 Halbtöne | -17.7 dB | ✓ |

## 4. Stimmung

| Szene | Sprecher | Vorgabe | Erregung | F0 ggü. Figur-Mittel | Lautheit |
|---|---|---|---|---|---|
| 1 | byte | Satzzeichen: ! | hoch | +0.3 Halbtöne | -15.8 dB |
| 2 | kalle | Satzzeichen: ? | mittel | +4.8 Halbtöne | -17.3 dB |
| 3 | byte | Satzzeichen: . | ruhig | -0.2 Halbtöne | -18.4 dB |
| 4 | byte | Satzzeichen: . | ruhig | -0.5 Halbtöne | -20.1 dB |
| 5 | byte | Satzzeichen: . | ruhig | +1.3 Halbtöne | -19.1 dB |
| 6 | byte | Satzzeichen: . | ruhig | +0.3 Halbtöne | -19.0 dB |
| 7 | kalle | Satzzeichen: ? | mittel | +3.8 Halbtöne | -17.6 dB |
| 8 | kalle | Satzzeichen: ? | mittel | -5.6 Halbtöne | -21.0 dB |
| 9 | byte | Satzzeichen: . | ruhig | +1.0 Halbtöne | -17.2 dB |
| 10 | byte | Satzzeichen: . | ruhig | -2.7 Halbtöne | -19.6 dB |
| 11 | byte | Satzzeichen: . | ruhig | -2.0 Halbtöne | -17.0 dB |
| 12 | kalle | Satzzeichen: . | ruhig | -4.9 Halbtöne | -20.1 dB |
| 13 | byte | Satzzeichen: . | ruhig | +0.0 Halbtöne | -17.7 dB |

Mittel F0: aufgeregte Zeilen +0.3 Halbtöne, ruhige -0.9 Halbtöne → ✓ Stimmung hörbar.

Hinweis: `eleven_multilingual_v2` bekommt keine Stimmungs-Anweisung; die Stimmung entsteht nur aus Text, Satzzeichen und Stil-Einstellung (stability/style).

