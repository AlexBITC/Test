# Authentizitäts-Check: Viel verkauft, kein Geld

Referenz: Folge `website` (ElevenLabs `eleven_multilingual_v2`). Modell dieser Folge: `eleven_multilingual_v2`.

## 1. Gleiche Stimme wie in der Referenz

| Figur | Stimme (Voice-ID) | F0-Median Folge | F0-Median Referenz | Abstand | Klangfarbe ähnlich zur Referenz (gleiche Figur) | zum Vergleich: andere Figur | Ergebnis |
|---|---|---|---|---|---|---|---|
| Kalle | Brian (`nPczCjzI2devNBz1zQrb`) | 114 Hz | 111 Hz | +0.5 Halbtöne | 0.980 | 0.678 | ✓ gleiche Stimme |
| Byte | Laura (`FGY2WhTYpPnrIDTdsKH5`) | 188 Hz | 203 Hz | -1.3 Halbtöne | 0.985 | 0.683 | ✓ gleiche Stimme |

Klangfarbe = Kosinus-Ähnlichkeit der mittleren MFCC-Vektoren (stimmhafte Abschnitte). Gleiche Stimme, wenn sie zur Referenz derselben Figur ähnlicher ist als zur anderen Figur und die Tonlage höchstens 3 Halbtöne abweicht.

## 2. Dialekt

Methode: Whisper bewertet für jedes Dialektwort zwei Fassungen der Zeile, die sich nur in diesem Wort unterscheiden (erzwungene Ausrichtung, Log-Wahrscheinlichkeit). Δ = Dialekt − Hochdeutsch. Δ > −1: Dialekt gesprochen; Δ < −3: hochdeutsch gesprochen; dazwischen unklar. Whisper bevorzugt von sich aus leicht die Schriftsprache, deshalb die Toleranz von −1.

| Szene | Wort im Text | an die Stimme geschickt | Whisper frei | Δ Dialekt − Hochdeutsch | Ergebnis |
|---|---|---|---|---|---|
| 2 | net | net | Das Büro gegenüber zahlt seit 6 Wochen net. | +4.1 | ✓ Dialekt gesprochen |
| 3 | hol | hol | Ich hole dein Geld zurück. | -0.7 | ✓ Dialekt gesprochen |
| 7 | hab | hab | Obwohl ich so viel verkauft hab? | -0.1 | ✓ Dialekt gesprochen |
| 8 | schreib | schreib | Ich schreibe eine höfliche Erinnerung. Alle drei Rechnungen, Zahlung in sieben Tagen. | -1.9 | ? unklar |
| 9 | schreib | schreib | Höflich und klar, so schreibe ich des nie. | +0.4 | ✓ Dialekt gesprochen |
| 9 | des | des | Höflich und klar, so schreibe ich des nie. | +0.4 | ✓ Dialekt gesprochen |
| 13 | merk | Merke | Merke dir, viel verkauft heißt nicht. | -6.4 | bewusst hochdeutsch geschickt („Merke“) |

Dialektwörter: 7, davon als Dialekt gesprochen: 5.

## 3. Natürlichkeit

| Szene | Sprecher | Tempo (W/s) | Tonhöhen-Streuung | Lautheit (P90) | Status |
|---|---|---|---|---|---|
| 1 | kalle | 2.15 | 8.3 Halbtöne | -18.4 dB | ✓ |
| 2 | kalle | 2.65 | 4.3 Halbtöne | -19.4 dB | ✓ |
| 3 | byte | 2.72 | 2.4 Halbtöne | -17.5 dB | ✓ |
| 4 | byte | 2.25 | 2.8 Halbtöne | -20.7 dB | ✓ |
| 5 | kalle | 2.65 | 4.4 Halbtöne | -18.3 dB | ✓ |
| 6 | byte | 2.09 | 3.3 Halbtöne | -19.9 dB | ✓ |
| 7 | kalle | 2.69 | 3.3 Halbtöne | -17.9 dB | ✓ |
| 8 | byte | 2.42 | 3.5 Halbtöne | -18.8 dB | ✓ |
| 9 | kalle | 2.52 | 5.2 Halbtöne | -19.7 dB | ✓ |
| 10 | byte | 2.29 | 3.8 Halbtöne | -20.4 dB | ✓ |
| 11 | byte | 2.17 | 3.3 Halbtöne | -18.2 dB | ✓ |
| 12 | kalle | 2.65 | 2.9 Halbtöne | -16.8 dB | ✓ |
| 13 | byte | 2.70 | 2.7 Halbtöne | -19.1 dB | ✓ |

## 4. Stimmung

| Szene | Sprecher | Vorgabe | Erregung | F0 ggü. Figur-Mittel | Lautheit |
|---|---|---|---|---|---|
| 1 | kalle | verzweifelt, laut | hoch | -0.9 Halbtöne | -18.4 dB |
| 2 | kalle | empört, ratlos | hoch | -0.9 Halbtöne | -19.4 dB |
| 3 | byte | selbstsicher, frech | hoch | +5.8 Halbtöne | -17.5 dB |
| 4 | byte | präzise, zügig | ruhig | -0.2 Halbtöne | -20.7 dB |
| 5 | kalle | ungläubig, baff | hoch | +2.7 Halbtöne | -18.3 dB |
| 6 | byte | ernst, ruhig | ruhig | -0.7 Halbtöne | -19.9 dB |
| 7 | kalle | verwirrt, kleinlaut | ruhig | +3.9 Halbtöne | -17.9 dB |
| 8 | byte | flink, gut gelaunt | mittel | +0.5 Halbtöne | -18.8 dB |
| 9 | kalle | beeindruckt, herzlich | mittel | -1.0 Halbtöne | -19.7 dB |
| 10 | byte | klar, erklärend | ruhig | -0.6 Halbtöne | -20.4 dB |
| 11 | byte | triumphierend, frech | hoch | +1.1 Halbtöne | -18.2 dB |
| 12 | kalle | überglücklich, lachend | hoch | +0.9 Halbtöne | -16.8 dB |
| 13 | byte | verschmitzt, leise | ruhig | +0.0 Halbtöne | -19.1 dB |

Mittel F0: aufgeregte Zeilen +1.4 Halbtöne, ruhige +0.5 Halbtöne → ✓ Stimmung hörbar.

Hinweis: `eleven_multilingual_v2` bekommt keine Stimmungs-Anweisung; die Stimmung entsteht nur aus Text, Satzzeichen und Stil-Einstellung (stability/style).

