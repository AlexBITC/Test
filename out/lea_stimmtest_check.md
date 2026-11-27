# Stimmen-Check: Lea Stimmtest

Erweiterter Check (Engine 2.3) für Zeilen mit `ton`/`betonung`/`tempo`/`sprechtext`. Stimmen: ElevenLabs, Kalle = Brian, Byte = Laura, Lea = Sarah (ab 2.4). Atmer am Satzanfang bleiben erhalten (laute werden gedämpft). Kriterien: Wortfehler ≤ 10 % (schwäbische Wörter frei), Zahlen und Begriff exakt, Spannweite der Satzmelodie ≥ 4 Halbtöne (5.–95. Perzentil), Frage steigt / Aussage fällt (letztes Wort gegen den Rest der Zeile), Betonungswort ≥ +2 dB oder ≥ +1,5 Halbtöne gegenüber dem Durchschnitt aller Wörter der Zeile (je Wort Spitzenpegel = 95. Perzentil, Tonhöhe = 90. Perzentil), Tempo im Zielbereich, kein Übersteuern, keine Pause > 0,6 s mitten im Satz (außer nach „…“). Höchstens 3 Versuche. Tempo: zuerst ElevenLabs `speed` (0,7–1,2), am Anschlag zusätzlich Satzform (Komma), Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %, Spalte Tempo-Korrektur).

| # | Sprecher | ton / tempo | Modell | Versuche | WER | W/s (Ziel), Tempo-Korrektur | F0 | Spannweite | Ende | Betonung | Peak | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | lea | enttaeuscht / langsam | eleven_multilingual_v2 | 3 | 0% | 2,04 (2,0–2,2), x1,08 | 209 Hz | 10,0 Halbtöne | -4,5 Halbtöne (Aussage) | „nicht“ +3,0 dB / -1,5 Halbtöne | 0,86 | OK |
| 2 | lea | stolz / langsam | eleven_multilingual_v2 | 2 | 0% | 2,01 (2,0–2,2), x1,00 | 198 Hz | 24,5 Halbtöne | -2,8 Halbtöne (Aussage) | „Meine“ +3,4 dB / -5,0 Halbtöne | 0,85 | OK |



## Sprechtext und Versuche

**1. lea:** „Ich krieg's einfach nicht hin.“  
- eleven_multilingual_v2 Versuch 1: „Ich krieg's … einfach nicht hin.“, stability 0.6, style 0.2, speed 0.84, Tempo-Korrektur x1.00 → Betonung 'nicht' schwach (-1,2 dB, -3,3 Halbtoene); Whisper: „Ich krieg's einfach nicht hin.“
- eleven_multilingual_v2 Versuch 2: „Ich krieg's … einfach, nicht hin.“, stability 0.6, style 0.2, speed 0.84, Tempo-Korrektur x1.00 → Aussage faellt nicht (+1,6 Halbtoene am Ende); Whisper: „Ich krieg's einfach nicht hin.“
- eleven_multilingual_v2 Versuch 3: „Ich krieg's … einfach, nicht hin.“, stability 0.6, style 0.2, speed 0.84, Tempo-Korrektur x1.08 → OK; Whisper: „Ich krieg's einfach nicht hin.“ ← gewählt
- eleven_v3 Versuch v3: „Ich krieg's … einfach, nicht hin.“, stability 0.5, style 0.2, speed –, Tempo-Korrektur x1.15 → OK; Whisper: „Ich krieg's einfach nicht hin.“

**2. lea:** „Die hat grad jemand gekauft. Meine Brezel.“  
- eleven_multilingual_v2 Versuch 1: „Die hat grad jemand gekauft. … Meine Brezel.“, stability 0.45, style 0.35, speed 0.84, Tempo-Korrektur x0.96 → Aussage faellt nicht (+3,8 Halbtoene am Ende); Betonung 'Meine' schwach (+1,1 dB, -5,6 Halbtoene); Whisper: „Die hat grad jemand gekauft. Meine Brezel.“
- eleven_multilingual_v2 Versuch 2: „Die hat grad jemand gekauft. … Meine Brezel.“, stability 0.45, style 0.35, speed 0.84, Tempo-Korrektur x1.00 → OK; Whisper: „Die hat grad jemand gekauft. Meine Brezel.“ ← gewählt
- eleven_v3 Versuch v3: „Die hat grad jemand gekauft. … Meine Brezel.“, stability 0.5, style 0.35, speed –, Tempo-Korrektur x0.88 → WER 14% > 10 %; Tempo 2,37 W/s ausserhalb 2,0–2,2; Whisper: „Die hat grad jemand gekauft. Meine Breze.“

## eleven_v3

Für 2 Zeilen mit `ton` wurde zusätzlich eine eleven_v3-Variante (mit Stimmungs-Tag) erzeugt und mit demselben Check bewertet. Übernommen, weil besser als eleven_multilingual_v2: 0 Zeilen.

