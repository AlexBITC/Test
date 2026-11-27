# Stimmen-Check: Byte macht Kalle viral

**Ergebnis:** nicht alle Zeilen bestanden (siehe unten)  
**Modell:** `eleven_multilingual_v2`  
**Kalle:** Brian - Deep, Resonant and Comforting (`nPczCjzI2devNBz1zQrb`)  
**Byte:** Laura - Enthusiast, Quirky Attitude (`FGY2WhTYpPnrIDTdsKH5`)  
**Stimmabstand:** Median-F0 Kalle 106 Hz, Byte 196 Hz → 10.8 Halbtöne (klar unterschiedlich)  
**Whisper:** faster-whisper `medium` (int8, CPU), Sprache de  
**Natürlichkeit (UTMOS22 strong):** nicht verfügbar (Modellcode müsste per torch.hub von GitHub geladen werden; das ist in dieser Umgebung blockiert: HTTPError: HTTP Error 403: Forbidden)

Grenzwerte: WER ≤ 10 %, Zahlen und Fachbegriff exakt, 2,0–2,8 Wörter/s, Tonhöhen-Streuung ≥ 1,5 Halbtöne, kein Clipping, Ende nicht abgeschnitten, keine Pause > 0,7 s (nach „…“ 1,0 s), UTMOS ≥ 3,5.

| # | Sprecher | WER | Zahlen/Begriff | W/s | F0 Median | F0 Streuung | Peak | längste Pause | UTMOS | Versuche | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | byte | 0% | – | 2.44 | 299 Hz | 1.9 st | 0.55 | 0.12 s | – | 2 | OK |
| 2 | kalle | 17% | – | 2.49 | 92 Hz | 3.8 st | 0.56 | 0.08 s | – | 3 | FAIL: WER 17% > 10 % |
| 3 | byte | 0% | – | 2.70 | 200 Hz | 3.9 st | 0.76 | 0.23 s | – | 2 | OK |
| 4 | kalle | 0% | eine ✓ | 2.65 | 130 Hz | 5.3 st | 0.57 | 0.14 s | – | 2 | OK |
| 5 | byte | 0% | drei ✓ | 2.43 | 219 Hz | 2.5 st | 0.77 | 0.17 s | – | 1 | OK |
| 6 | byte | 0% | acht ✓ | 2.70 | 169 Hz | 3.1 st | 0.76 | 0.11 s | – | 1 | OK |
| 7 | byte | 0% | – | 2.07 | 228 Hz | 3.7 st | 0.78 | 0.23 s | – | 1 | OK |
| 8 | kalle | 0% | – | 2.65 | 106 Hz | 3.8 st | 0.72 | 0.23 s | – | 2 | OK |
| 9 | byte | 0% | – | 2.64 | 181 Hz | 2.2 st | 0.62 | 0.18 s | – | 2 | OK |
| 10 | byte | 0% | 18 ✓ | 2.57 | 196 Hz | 3.3 st | 0.64 | 0.23 s | – | 1 | OK |
| 11 | byte | 0% | 12.000 ✓ | 2.30 | 195 Hz | 3.9 st | 0.75 | 0.19 s | – | 2 | OK |
| 12 | kalle | 0% | – | 2.65 | 145 Hz | 6.1 st | 0.48 | 0.12 s | – | 2 | OK |
| 13 | byte | 0% | Reichweite ✓ | 2.68 | 176 Hz | 1.6 st | 0.79 | 0.29 s | – | 1 | OK |
| 14 | kalle | 0% | – | 2.54 | 91 Hz | 3.9 st | 0.48 | 0.47 s | – | 2 | OK |

## Hinweise

- Modell `eleven_multilingual_v2` (Vorgabe). Wort-Timing der Untertitel aus dem Endpoint `/with-timestamps`
- Stille am Zeilenanfang/-ende wird weggeschnitten, Pausen zwischen Wörtern werden auf 0,14–0,30 s begrenzt. Tempo: zuerst über den API-Parameter `speed`, Rest tonhöhenerhaltend per `atempo` (höchstens −12 % / +15 %; Zeile 8 als kurzer Ausruf bewusst −21 %). Rubberband wurde ersetzt, weil es bei kurzen Ausrufen die Sprachmelodie messbar verflachte.
- Tonhöhe gemessen mit pYIN auf 48 kHz (85-ms-Fenster); bei 16 kHz wurden kurze Ausrufe fälschlich als stimmlos/monoton gewertet.
- Zeile 8 („Des gibt's doch net!“): aus allen erzeugten Varianten die lebendigste mit sauber erkanntem „net“ gewählt (Feinabstimmung in `engine/voices.json`). Das ElevenLabs-Kontingent ist erschöpft (Stand: 12 Credits); weitere Stimmen-Castings waren deshalb nicht möglich.
- Schwäbische Wörter (net, i, des, verschlamp) dürfen in der Rücktranskription abweichen; Zahlwörter, „Code“ und „Marketing“ müssen exakt erkannt werden („Code“ würde bei falscher Aussprache als „Kot“ transkribiert).
- Schreibweisen nur für die Sprachausgabe: siehe „Sprechtext“ je Zeile. Die Untertitel zeigen exakt den Episoden-Text.
- Tonhöhe: keine Verschiebung; Byte (Laura) und Kalle (Brian) sind von Natur aus klar verschieden.

## Details pro Zeile

**1. byte:** „Kalle! Ich hab 'ne Idee. Wir drehen Videos!“  
Sprechtext: „Kalle! Ich hab 'ne Idee. Wir drehen Videos!“  
Whisper: „Kalle, ich hab ne Idee. Wir drehen Videos.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.88, WER 0%, 2.84 W/s, Schreibweise –, Fehler: Tempo 2,84 W/s ausserhalb 2,0–2,8 – „Kalle, ich hab ne Idee. Wir drehen Videos.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.00, WER 0%, 2.44 W/s, Schreibweise –, Fehler: keine – „Kalle, ich hab ne Idee. Wir drehen Videos.“

**2. kalle:** „Videos? I bin Bäcker, koi Influencer!“  
Sprechtext: „Videos? Ich bin Bäcker, koi Influencer!“  
Whisper: „Videos, ich bin Becker, Koi Influencer.“  
Einstellungen: `{"stability": 0.4, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x1.00, WER 17%, 2.49 W/s, Schreibweise {'I': 'Ich'}, Fehler: WER 17% > 10 % – „Videos, ich bin Becker, Koi Influencer.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.97, WER 17%, 2.65 W/s, Schreibweise {'I': 'Ich'}, Fehler: WER 17% > 10 % – „Videos, ich bin Becker, Koi Influencer.“
- Versuch 3: Stabilität 0.35, Seed 4234, Stretch x1.00, WER 33%, 2.34 W/s, Schreibweise {'I': 'Ich'}, Fehler: WER 33% > 10 % – „Videos, ich bin Bäcker, Koi-Influencer.“

**3. byte:** „Du musst nix können. Back einfach wie immer.“  
Sprechtext: „Du musst nix können. Back einfach wie immer.“  
Whisper: „Du musst nix können. Back einfach wie immer.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x0.96  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x0.88, WER 0%, 2.96 W/s, Schreibweise –, Fehler: Tempo 2,96 W/s ausserhalb 2,0–2,8 – „Du musst nix können, back einfach wie immer.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x0.96, WER 0%, 2.70 W/s, Schreibweise –, Fehler: keine – „Du musst nix können. Back einfach wie immer.“

**4. kalle:** „Na gut. Aber nur eine Brezel.“  
Sprechtext: „Na gut. Aber nur eine Brezel.“  
Whisper: „Na gut, aber nur eine Brezel.“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x0.90  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 0%, 3.77 W/s, Schreibweise –, Fehler: Tempo 3,77 W/s ausserhalb 2,0–2,8 – „Na gut, aber nur eine Brezel.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.90, WER 0%, 2.65 W/s, Schreibweise –, Fehler: keine – „Na gut, aber nur eine Brezel.“

**5. byte:** „Drei Minuten Material. Wackelig, dunkel, Mehl auf der Linse.“  
Sprechtext: „Drei Minuten Material. Wackelig, dunkel, Mehl auf der Linse.“  
Whisper: „Drei Minuten Material. Wackelig, dunkel, Mehl auf der Linse?“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**6. byte:** „Ich such die besten acht Sekunden.“  
Sprechtext: „Ich such die besten acht Sekunden.“  
Whisper: „Ich such die besten 8 Sekunden.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x0.98  

**7. byte:** „Zeitlupe beim Schlingen. Untertitel. Musik drauf.“  
Sprechtext: „Zeitlupe beim Schlingen. Untertitel. Musik drauf.“  
Whisper: „Zeitlupe beim Schlingen. Untertitel. Musik drauf.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.15  

**8. kalle:** „Des bin ja i! Des sieht aus wie im Fernsehen!“  
Sprechtext: „Des bin ja ich! Des sieht aus wie im Fernsehen!“  
Whisper: „Das bin ja ich. Das sieht aus wie im Fernsehen.“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x0.95  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 0%, 3.55 W/s, Schreibweise {'i!': 'ich!'}, Fehler: Tempo 3,55 W/s ausserhalb 2,0–2,8 – „Das bin ja ich. Das sieht aus wie im Fernsehen.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.95, WER 0%, 2.65 W/s, Schreibweise {'i!': 'ich!'}, Fehler: keine – „Das bin ja ich. Das sieht aus wie im Fernsehen.“

**9. byte:** „Und die erste Sekunde: Kalle schlingt mit geschlossenen Augen.“  
Sprechtext: „Und die erste Sekunde: Kalle schlingt mit geschlossenen Augen.“  
Whisper: „Und die erste Sekunde, Kalle schlingt mit geschlossenen Augen.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x1.00, WER 0%, 2.65 W/s, Schreibweise –, Fehler: monoton (Tonhoehen-Streuung 1.4 Halbtoene) – „Und die erste Sekunde. Kalle schlingt mit geschlossenen Augen.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.00, WER 0%, 2.64 W/s, Schreibweise –, Fehler: keine – „Und die erste Sekunde, Kalle schlingt mit geschlossenen Augen.“

**10. byte:** „Gepostet um 18 Uhr. Da sind deine Kunden online.“  
Sprechtext: „Gepostet um achtzehn Uhr. Da sind deine Kunden online.“  
Whisper: „Gepostet um 18 Uhr. Da sind deine Kunden online.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**11. byte:** „12.000 Aufrufe. Über Nacht.“  
Sprechtext: „zwölftausend Aufrufe. Über Nacht.“  
Whisper: „12.000 Aufrufe über Nacht.“  
Einstellungen: `{"stability": 0.75, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 1.2}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.5, Seed 4200, Stretch x1.15, WER 0%, 1.96 W/s, Schreibweise –, Fehler: Tempo 1,96 W/s ausserhalb 2,0–2,8 – „12.000 Aufrufe über Nacht.“
- Versuch 2: Stabilität 0.75, Seed 4217, Stretch x1.00, WER 0%, 2.30 W/s, Schreibweise –, Fehler: keine – „12.000 Aufrufe über Nacht.“

**12. kalle:** „Was isch denn hier los?!“  
Sprechtext: „Was isch denn hier los?!“  
Whisper: „Was ist denn hier los?“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.7}`, Seed 4217, Tempo-Stretch x0.90  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.88, WER 0%, 3.59 W/s, Schreibweise –, Fehler: Tempo 3,59 W/s ausserhalb 2,0–2,8 – „Was ist denn hier los?“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x0.90, WER 0%, 2.65 W/s, Schreibweise –, Fehler: keine – „Was ist denn hier los?“

**13. byte:** „Das ist Reichweite. Und alle wollen die blinde Brezel.“  
Sprechtext: „Das ist Reichweite. Und alle wollen die blinde Brezel.“  
Whisper: „Das ist Reichweite und alle wollen die blinde Brezel.“  
Einstellungen: `{"stability": 0.5, "similarity_boost": 0.75, "style": 0.25, "use_speaker_boost": true, "speed": 0.9}`, Seed 4200, Tempo-Stretch x1.00  

**14. kalle:** „Byte … i hätt da au no a Idee!“  
Sprechtext: „Byte … ich hätt da, au noch a Idee!“  
Whisper: „Byte. Ich hätte da auch noch eine Idee.“  
Einstellungen: `{"stability": 0.65, "similarity_boost": 0.75, "style": 0.35, "use_speaker_boost": true, "speed": 0.9}`, Seed 4217, Tempo-Stretch x1.00  
- Versuch 1: Stabilität 0.4, Seed 4200, Stretch x0.97, WER 12%, 2.65 W/s, Schreibweise {'i': 'ich', 'da': 'da,', 'no': 'noch'}, Fehler: WER 12% > 10 % – „Byte, ich hätte auch noch eine Idee.“
- Versuch 2: Stabilität 0.65, Seed 4217, Stretch x1.00, WER 0%, 2.54 W/s, Schreibweise {'i': 'ich', 'da': 'da,', 'no': 'noch'}, Fehler: keine – „Byte. Ich hätte da auch noch eine Idee.“

