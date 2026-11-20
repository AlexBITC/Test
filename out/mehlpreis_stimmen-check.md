# Stimmen-Check: Byte telefoniert

**Ergebnis:** nicht alle Zeilen bestanden (siehe unten)  
**Modell:** `eleven_multilingual_v2`  
**Kalle:** Brian - Deep, Resonant and Comforting (`nPczCjzI2devNBz1zQrb`)  
**Byte:** Laura - Enthusiast, Quirky Attitude (`FGY2WhTYpPnrIDTdsKH5`)  
**Stimmabstand:** Median-F0 Kalle 113 Hz, Byte 193 Hz → 9.3 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  
**Natürlichkeit (UTMOS22 strong):** nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.

| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kalle | 0% | 24 ✓ | 2.84 | 172 Hz | 5.0 st | 0.71 | 0.23 s | – | 3 | FAIL: Tempo 2,84 W/s ausserhalb 2,0–2,8 |
| 2 | byte | 0% | – | 2.45 | 196 Hz | 2.6 st | 0.52 | 0.10 s | – | 2 | OK |
| 3 | kalle | 0% | – | 2.65 | 121 Hz | 3.9 st | 0.63 | 0.10 s | – | 1 | OK |
| 4 | byte | 0% | drei ✓ | 2.40 | 166 Hz | 2.5 st | 0.68 | 0.29 s | – | 3 | OK |
| 5 | byte | 0% | – | 2.70 | 242 Hz | 2.3 st | 0.84 | 0.20 s | – | 1 | OK |
| 6 | byte | 0% | 23 ✓, 21 ✓, 22 ✓, drei ✓ | 2.25 | 182 Hz | 3.7 st | 0.86 | 0.16 s | – | 2 | OK |
| 7 | kalle | 0% | 21 ✓ | 2.01 | 153 Hz | 1.3 st | 0.69 | 0.15 s | – | 3 | FAIL: monoton (Tonhoehen-Streuung 1.3 Halbtoene) |
| 8 | byte | 0% | – | 2.60 | 148 Hz | 2.1 st | 0.82 | 0.15 s | – | 1 | OK |
| 9 | byte | 0% | 21 ✓ | 2.28 | 238 Hz | 3.2 st | 0.76 | 0.12 s | – | 1 | OK |
| 10 | kalle | 0% | – | 2.65 | 92 Hz | 4.7 st | 0.79 | 0.28 s | – | 2 | OK |
| 11 | byte | 0% | 19,70 ✓ | 2.25 | 190 Hz | 3.1 st | 0.78 | 0.21 s | – | 1 | OK |
| 12 | kalle | 0% | 18 ✓ | 2.65 | 106 Hz | 5.1 st | 0.72 | 0.13 s | – | 1 | OK |
| 13 | byte | 0% | 40 ✓, 2.000 ✓ | 2.70 | 212 Hz | 2.9 st | 0.70 | 0.24 s | – | 1 | OK |
| 14 | kalle | 0% | – | 2.38 | 87 Hz | 2.0 st | 0.60 | 0.10 s | – | 1 | OK |

## Hinweise

- Modell `eleven_multilingual_v2` (Vorgabe). Wort-Timing der Untertitel aus dem Endpoint `/with-timestamps`
- Stille am Zeilenanfang/-ende wird weggeschnitten, Pausen zwischen Wörtern werden auf 0,14–0,30 s begrenzt. Tempo: zuerst über den API-Parameter `speed`, Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %; Zeile 8 als kurzer Ausruf bewusst −21 %). Rubberband wurde ersetzt, weil es bei kurzen Ausrufen die Sprachmelodie messbar verflachte.
- Tonhöhe gemessen mit pYIN auf 48 kHz (85-ms-Fenster); bei 16 kHz wurden kurze Ausrufe fälschlich als stimmlos/monoton gewertet.
- Zeile 8 („Des gibt's doch net!“): aus allen erzeugten Varianten die lebendigste mit sauber erkanntem „net“ gewählt (Feinabstimmung in `engine/voices.json`). Das ElevenLabs-Kontingent ist erschöpft (Stand: 12 Credits); weitere Stimmen-Castings waren deshalb nicht möglich.
- Schwäbische Wörter (net, i, des, verschlamp) dürfen in der Rücktranskription abweichen; Zahlwörter, „Code“ und „Marketing“ müssen exakt erkannt werden („Code“ würde bei falscher Aussprache als „Kot“ transkribiert).
- Schreibweisen nur für die Sprachausgabe: siehe „Sprechtext“ je Zeile. Die Untertitel zeigen exakt den Episoden-Text.
- Tonhöhe: keine Verschiebung; Byte (Laura) und Kalle (Brian) sind von Natur aus klar verschieden.

## Details pro Zeile

**1. kalle:** „24 Euro für en Sack Mehl?! Die spinnet doch!“  
Sprechtext: „vierundzwanzig Euro für 'n Sack Mehl?! Die spinnet doch!“  
Whisper: „24 Euro für einen Sack Mehl? Die spinnet doch!“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 1.0}`, Seed 4217, Tempo-Stretch x0.88  
- Versuch 1: Stabilität 0.4, Seed 5101, Stretch x0.88, WER 11%, 2.67 W/s, Schreibweise {'en': "'n"}, Fehler: WER 11% > 10 % – „24 Euro für einen Sack Mehl? Die spinne doch!“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.88, WER 0%, 2.84 W/s, Schreibweise {'en': "'n"}, Fehler: Tempo 2,84 W/s ausserhalb 2,0–2,8 – „24 Euro für einen Sack Mehl? Die spinnet doch!“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x1.06, WER 22%, 2.15 W/s, Schreibweise {'en': "'n"}, Fehler: WER 22% > 10 % – „24 Euro für ein Sack Mehl? Die Spinne doch!“

**2. byte:** „Ich telefonier das mal schnell weg.“  
Sprechtext: „Ich telefonier das mal schnell weg.“  
Whisper: „Ich telefonier' das mal schnell weg.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.88, WER 0%, 3.12 W/s, Schreibweise –, Fehler: Tempo 3,12 W/s ausserhalb 2,0–2,8 – „Ich telefoniere das mal schnell weg.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.00, WER 0%, 2.45 W/s, Schreibweise –, Fehler: keine – „Ich telefonier' das mal schnell weg.“

**3. kalle:** „Du? Telefonieren? Du hast doch net mal Ohren!“  
Sprechtext: „Du? Telefonieren? Du hast doch net mal Ohren!“  
Whisper: „Du, telefonieren, du hast doch net mal Ohren.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.97  

**4. byte:** „Brauch ich nicht. Ich hab drei Hörer.“  
Sprechtext: „Brauch ich nicht. Ich hab drei Hörer.“  
Whisper: „Brauche ich nicht. Ich habe drei Hörer.“  
Einstellungen: `{"stability": 0.45, "similarity_boost": 0.75, "style": 0.1, "use_speaker_boost": true, "speed": 0.7}`, Seed 4234, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.88, WER 0%, 2.83 W/s, Schreibweise –, Fehler: Tempo 2,83 W/s ausserhalb 2,0–2,8 – „Brauche ich nicht, ich habe drei Hörer.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.00, WER 0%, 2.58 W/s, Schreibweise –, Fehler: monoton (Tonhoehen-Streuung 0.9 Halbtoene) – „Brauche ich nicht. Ich habe drei Hörer.“
- Versuch 3: Stabilität 0.45, Seed 4234, Stretch x1.00, WER 0%, 2.40 W/s, Schreibweise –, Fehler: keine – „Brauche ich nicht. Ich habe drei Hörer.“

**5. byte:** „Hallo! Hier ist Byte, die KI der Bäckerei Kalle!“  
Sprechtext: „Hallo! Hier ist Byte, die KI der Bäckerei Kalle!“  
Whisper: „Hallo, hier ist Byte, die KI der Bäckerei Kalle.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.94  

**6. byte:** „23. 21. 22 Euro. Drei Angebote in vierzig Sekunden.“  
Sprechtext: „dreiundzwanzig. einundzwanzig. zweiundzwanzig Euro. Drei Angebote in vierzig Sekunden.“  
Whisper: „23, 21, 22 Euro. Drei Angebote in 40 Sekunden.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 1.2}`, Seed 4217, Tempo-Stretch x1.10  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x1.15, WER 0%, 1.68 W/s, Schreibweise –, Fehler: Tempo 1,68 W/s ausserhalb 2,0–2,8 – „23, 21, 22 Euro. Drei Angebote in 40 Sekunden.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.10, WER 0%, 2.25 W/s, Schreibweise –, Fehler: keine – „23, 21, 22 Euro. Drei Angebote in 40 Sekunden.“

**7. kalle:** „Zack, die 21! Bestell!“  
Sprechtext: „Zack, die einundzwanzig! Bestell!“  
Whisper: „Zack, die 21. Bestell!“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4217, Tempo-Stretch x1.15  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x1.08, WER 25%, 2.15 W/s, Schreibweise –, Fehler: WER 25% > 10 % – „Sag die 21. Bestell!“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.15, WER 0%, 2.01 W/s, Schreibweise –, Fehler: monoton (Tonhoehen-Streuung 1.3 Halbtoene) – „Zack, die 21. Bestell!“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x1.15, WER 0%, 2.11 W/s, Schreibweise –, Fehler: monoton (Tonhoehen-Streuung 0.9 Halbtoene) – „Zack, die 21. Bestell!“

**8. byte:** „Moment. Jetzt wird's spannend.“  
Sprechtext: „Moment. Jetzt wird's spannend.“  
Whisper: „Moment, jetzt wird's spannend.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**9. byte:** „Die Konkurrenz macht 21. Und Sie?“  
Sprechtext: „Die Konkurrenz macht einundzwanzig. Und Sie?“  
Whisper: „Die Konkurrenz macht 21 und Sie?“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**10. kalle:** „Byte! Des isch mein Müller, der kennt mi!“  
Sprechtext: „Byte! Des isch mein Müller, der kennt mi!“  
Whisper: „Byte, das ist mein Müller, der kennt mich.“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4217, Tempo-Stretch x0.98  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 12%, 2.65 W/s, Schreibweise –, Fehler: WER 12% > 10 % – „Das ist mein Müller, der kennt mich.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.98, WER 0%, 2.65 W/s, Schreibweise –, Fehler: keine – „Byte, das ist mein Müller, der kennt mich.“

**11. byte:** „Eben. Darum macht er's jetzt für 19,70.“  
Sprechtext: „Eben. Darum macht er's jetzt für neunzehn Euro siebzig.“  
Whisper: „Eben. Darum macht er es jetzt für 19,70 Euro.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.09  

**12. kalle:** „Das sind ja 18 Prozent!“  
Sprechtext: „Das sind ja achtzehn Prozent!“  
Whisper: „Das sind ja 18 Prozent.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.95  

**13. byte:** „Bei 40 Säcken im Monat: über 2.000 Euro im Jahr.“  
Sprechtext: „Bei vierzig Säcken im Monat: über zweitausend Euro im Jahr.“  
Whisper: „Bei 40 Säcken im Monat, über 2000 Euro im Jahr.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.96  

**14. kalle:** „Und i hab jahrelang einfach bezahlt…“  
Sprechtext: „Und ich hab jahrelang einfach bezahlt…“  
Whisper: „Und ich hab jahrelang einfach bezahlt.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

