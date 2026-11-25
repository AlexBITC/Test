# Stimmen-Check: Erzähler Stimmtest

Erweiterter Check (Engine 2.3) für Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext`. Stimmen: ElevenLabs, Kalle = Brian, Byte = Laura, Lea = Sarah (ab 2.4), Erzähler = Daniel (ab 2.5). Atmer am Satzanfang bleiben erhalten (laute werden gedämpft). Kriterien: Wortfehler ≤ 10 % (schwäbische Wörter frei), Zahlen und Begriff exakt, Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil), Frage steigt / Aussage fällt (letztes Wort gegen den Rest der Zeile), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz (außer nach „…“). Höchstens 3 Versuche. Tempo: zuerst ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %, Spalte Tempo-Korrektur).

| # | Sprecher | ton / tempo | Modell | Versuche | WER | W/s (Ziel), Tempo-Korrektur | F0 | Spannweite | Ende | Betonung | Peak | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | erzaehler | erzaehlend / langsam | eleven_multilingual_v2 | 2 | 0% | 2,16 (2,0–2,2), x0,95 | 141 Hz | 17,4 Halbtöne | -2,7 Halbtöne (Aussage) | „Deine“ +2,1 dB / -1,6 Halbtöne | 0,62 | OK |
| 2 | kalle | fragend / normal | eleven_multilingual_v2 | 3 | 29% | 2,60 (2,3–2,6), x1,00 | 177 Hz | 21,3 Halbtöne | -15,9 Halbtöne (Aussage) | „nie“ -5,2 dB / +0,0 Halbtöne | 0,64 | FAIL: WER 29% > 10 %; Betonung 'nie' schwach (-5,2 dB, +0,0 Halbtoene) |


Erzähler und Kalle: Klangfarbe (MFCC 2–20) 51,4 → ✓ klar verschieden (Ziel ≥ 25); Tempo 2,16 gegen 2,60 Wörter/s (✓ langsamer); Spannweite der Satzmelodie im Mittel 17,4 gegen 21,3 Halbtöne (✓ gleichmäßiger),

## Sprechtext und Versuche

**1. erzaehler:** „Diese Stadt ist ein Spiel. Deine nicht.“  
- eleven_multilingual_v2 Versuch 1: „Diese Stadt ist ein Spiel. … Deine nicht.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x0.94 → Betonung 'Deine' schwach (+1,3 dB, -1,7 Halbtoene); Whisper: „Diese Stadt ist ein Spiel, deine nicht.“
- eleven_multilingual_v2 Versuch 2: „Diese Stadt ist ein Spiel. … Deine nicht.“, stability 0.55, style 0.3, speed 0.84, Tempo-Korrektur x0.95 → OK; Whisper: „Diese Stadt ist ein Spiel, deine nicht.“ ← gewählt
- eleven_v3 Versuch v3: „Diese Stadt ist ein Spiel. … Deine nicht.“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x0.92 → Betonung 'Deine' schwach (+1,3 dB, -5,7 Halbtoene); Whisper: „Diese Stadt ist ein Spiel, deine nicht.“

**2. kalle:** „I hab no nie a Spiel gspielt.“  
- eleven_multilingual_v2 Versuch 1: „I hab no nie … a Spiel gspielt.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x1.00 → WER 43% > 10 %; Whisper: „Ihr habt noch nie ein Spiel gespielt.“
- eleven_multilingual_v2 Versuch 2: „I hab no nie … a Spiel gspielt.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x1.00 → WER 29% > 10 %; Betonung 'nie' schwach (-5,2 dB, +0,0 Halbtoene); Whisper: „Ich hab noch nie ein Spiel gespielt.“ ← gewählt
- eleven_multilingual_v2 Versuch 3: „I hab no nie … a Spiel gspielt.“, stability 0.4, style 0.3, speed 0.92, Tempo-Korrektur x0.88 → WER 57% > 10 %; Whisper: „Ihr habt noch nie ein Spierge-Spier.“
- eleven_v3 Versuch v3: „I hab no nie … a Spiel gspielt.“, stability 0.5, style 0.3, speed –, Tempo-Korrektur x0.90 → WER 43% > 10 %; Betonung 'nie' schwach (+0,2 dB, -0,4 Halbtoene); Whisper: „I have no knee, a spiel gespielt.“

## eleven_v3

Für 2 Zeilen mit `ton` wurde zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag) erzeugt und mit demselben Check bewertet. Übernommen, weil besser als eleven_multilingual_v2: 0 Zeilen.

