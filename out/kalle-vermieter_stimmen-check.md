# Stimmen-Check: Meine KI macht jetzt meinen Job

Erweiterter Check (Engine 2.3) für Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext`. Stimmen: ElevenLabs, Kalle = Brian, Byte = Laura, Lea = Sarah (ab 2.4). Atmer am Satzanfang bleiben erhalten (laute werden gedämpft). Kriterien: Wortfehler ≤ 10 % (schwäbische Wörter frei), Zahlen und Begriff exakt, Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil), Frage steigt / Aussage fällt (letztes Wort gegen den Rest der Zeile), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz (außer nach „…“). Höchstens 3 Versuche. Tempo: zuerst ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %, Spalte Tempo-Korrektur).

| # | Sprecher | ton / tempo | Modell | Versuche | WER | W/s (Ziel), Tempo-Korrektur | F0 | Spannweite | Ende | Betonung | Peak | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | – | v2 | 2 | 8% | 2.65 | 103 Hz | – | – | – | – | OK |
| 2 | byte | – | v2 | 2 | 0% | 2.47 | 229 Hz | – | – | – | – | OK |
| 3 | kalle | – | v2 | 3 | 11% | 2.19 | 117 Hz | – | – | – | – | FAIL |
| 4 | byte | – | v2 | 3 | 12% | 2.59 | 199 Hz | – | – | – | – | FAIL |
| 5 | byte | – | v2 | 2 | 0% | 2.22 | 220 Hz | – | – | – | – | OK |
| 6 | kalle | begeistert / normal | eleven_multilingual_v2 | 1 | 0% | 2,56 (2,3–2,6), x0,89 | 115 Hz | 12,2 Halbtöne | -10,6 Halbtöne (Aussage) | – | 0,60 | OK |
| 7 | byte | – | v2 | 3 | 14% | 2.67 | 204 Hz | – | – | – | – | FAIL |
| 8 | kalle | – | v2 | 1 | 0% | 2.13 | 114 Hz | – | – | – | – | OK |
| 9 | byte | – | v2 | 1 | 0% | 2.17 | 208 Hz | – | – | – | – | OK |
| 10 | kalle | enttaeuscht / langsam | eleven_multilingual_v2 | 3 | 0% | 2,75 (2,0–2,2), x0,88 | 128 Hz | 10,4 Halbtöne | +0,0 Halbtöne (Aussage) | – | 0,64 | FAIL: Tempo 2,75 W/s ausserhalb 2,0–2,2 |
| 11 | byte | – | v2 | 1 | 0% | 2.74 | 212 Hz | – | – | – | – | OK |
| 12 | byte | – | v2 | 2 | 0% | 2.70 | 166 Hz | – | – | – | – | OK |
| 13 | kalle | stolz / normal | eleven_multilingual_v2 | 2 | 0% | 2,34 (2,3–2,6), x1,04 | 126 Hz | 19,8 Halbtöne | -8,5 Halbtöne (Aussage) | – | 0,60 | OK |


## Sprechtext und Versuche

**6. kalle:** „750 Euro jeden Monat? Die Wohnung zahlt sich doch von allein ab!“  
- eleven_multilingual_v2 Versuch 1: „siebenhundertfünfzig Euro jeden Monat? Die Wohnung zahlt sich doch von allein ab!“, stability 0.3, style 0.5, speed 0.92, Tempo-Korrektur x0.89 → OK; Whisper: „750 Euro jeden Monat. Die Wohnung zahlt sich doch von allein ab.“
- eleven_v3 Versuch v3: „siebenhundertfünfzig Euro jeden Monat? Die Wohnung zahlt sich doch von allein ab!“, stability 0.5, style 0.5, speed –, Tempo-Korrektur x1.00 → OK; Whisper: „750 Euro jeden Monat, die Wohnung zahlt sich doch von allein ab.“

**10. kalle:** „Dann war die Idee wohl nix.“  
- eleven_multilingual_v2 Versuch 1: „Dann war die Idee wohl nix.“, stability 0.6, style 0.2, speed 0.84, Tempo-Korrektur x0.88 → Tempo 3,48 W/s ausserhalb 2,0–2,2; Whisper: „Dann war die Idee wohl nix.“
- eleven_multilingual_v2 Versuch 2: „Dann war die Idee wohl nix.“, stability 0.6, style 0.2, speed 0.7, Tempo-Korrektur x0.88 → Tempo 2,75 W/s ausserhalb 2,0–2,2; Whisper: „Dann war die Idee wohl nix.“
- eleven_multilingual_v2 Versuch 3: „Dann war die Idee wohl nix.“, stability 0.6, style 0.2, speed 0.7, Tempo-Korrektur x0.88 → Tempo 2,93 W/s ausserhalb 2,0–2,2; Whisper: „Dann war die Idee wohl nix.“
- eleven_v3 Versuch v3: „Dann war die Idee wohl nix.“, stability 0.5, style 0.2, speed –, Tempo-Korrektur x0.88 → Tempo 3,59 W/s ausserhalb 2,0–2,2; Whisper: „Dann war die Idee wohl nix.“

**13. kalle:** „Du suchst, ich entscheide. Das ist jetzt mein Job.“  
- eleven_multilingual_v2 Versuch 1: „Du suchst, ich entscheide. Das ist jetzt mein Job.“, stability 0.45, style 0.35, speed 0.92, Tempo-Korrektur x0.88 → Tempo 2,88 W/s ausserhalb 2,3–2,6; Whisper: „Du suchst, ich entscheide. Das ist jetzt mein Job.“
- eleven_multilingual_v2 Versuch 2: „Du suchst, ich entscheide. Das ist jetzt mein Job.“, stability 0.45, style 0.35, speed 0.7, Tempo-Korrektur x1.04 → OK; Whisper: „Du suchst, ich entscheide. Das ist jetzt mein Job.“
- eleven_v3 Versuch v3: „Du suchst, ich entscheide. Das ist jetzt mein Job.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x1.00 → OK; Whisper: „Du suchst. Ich entscheide. Das ist jetzt mein Job.“

## eleven_v3

Für 3 Zeilen mit `ton` wurde zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag) erzeugt und mit demselben Check bewertet. Übernommen, weil besser als eleven_multilingual_v2: 0 Zeilen.

