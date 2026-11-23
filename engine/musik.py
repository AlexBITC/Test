"""Optionales Musikbett (Engine 2.4), komplett selbst erzeugt (Synthese, keine Dateien, keine Downloads).

Feld 'musik' pro Szene: hektisch | stille | neugierig | aufsteigend | warm. Ohne Feld in keiner Szene: keine Musik
(bisherige Folgen klingen unveraendert). Jede Stimmung laeuft als durchgehende Spur ueber die ganze Folge und wird
pro Szene mit 0,5-s-Rampen ein- und ausgeblendet (weiche Uebergaenge). Pegel: 20 dB unter dem Sprachpegel
(RMS der gesprochenen Abschnitte), also mindestens 18 dB darunter.

Klang: Pizzicato per Karplus-Strong (gezupfte Saite), Klavier per additiver Synthese mit Abklingen, weiches Pad.
  hektisch    - schnelle Pizzicato-Achtel (152 BPM), Moll, kurze Repetitionen
  stille      - keine Musik (blendet aus)
  neugierig   - tupfendes Pizzicato auf Zehenspitzen (100 BPM), grosse Sexten, Pausen
  aufsteigend - Klavier-Arpeggio, steigt Takt fuer Takt (108 BPM), dichter werdend
  warm        - ruhige Klavierakkorde (66 BPM) mit leisem Pad, I-vi-IV-V
"""
from __future__ import annotations

import numpy as np

SR = 48000
FPS = 30
STIMMUNGEN = ("hektisch", "stille", "neugierig", "aufsteigend", "warm")
UNTER_SPRACHE_DB = 20.0


def _hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _pizz(freq, dur, seed=0, hell=0.5):
    """Karplus-Strong: gezupfte Saite (Pizzicato)."""
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p).astype(np.float32)
    out = np.zeros(n, np.float32)
    decay = 0.996 - 0.004 * (1 - hell)
    for i in range(n):
        v = buf[i % p]
        out[i] = v
        buf[i % p] = decay * 0.5 * (v + buf[(i + 1) % p])
    env = np.exp(-np.arange(n) / SR * 9.0).astype(np.float32)
    return out * env


def _klavier(freq, dur, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for k, a in enumerate((1.0, 0.45, 0.22, 0.12, 0.06), start=1):
        s += a * np.sin(2 * np.pi * freq * k * t) * np.exp(-t * (1.6 + 0.9 * k))
    att = np.minimum(1.0, t / 0.006)
    return (vel * s * att).astype(np.float32)


def _pad(freqs, dur):
    t = np.arange(int(dur * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 0.5) for f in freqs)
    env = np.minimum(1.0, t / 0.8) * np.minimum(1.0, (dur - t) / 0.8)
    return (0.25 * s * env).astype(np.float32)


def _add(dst, src, at):
    a = int(at * SR)
    if a >= len(dst):
        return
    m = min(len(src), len(dst) - a)
    dst[a:a + m] += src[:m]


def _spur(stimmung, dauer):
    y = np.zeros(int(dauer * SR) + SR, np.float32)
    if stimmung == "hektisch":
        beat = 60 / 152 / 2
        muster = [57, 57, 60, 57, 64, 57, 60, 62, 57, 57, 60, 57, 65, 64, 62, 60]
        k = 0
        t = 0.0
        while t < dauer:
            m = muster[k % len(muster)] - (12 if (k // 16) % 2 else 0) * 0
            _add(y, _pizz(_hz(m), 0.25, seed=k, hell=0.7) * (0.9 if k % 2 == 0 else 0.6), t)
            if k % 4 == 0:
                _add(y, _pizz(_hz(45), 0.3, seed=500 + k, hell=0.3) * 0.8, t)
            k += 1
            t += beat
    elif stimmung == "neugierig":
        beat = 60 / 100 / 2
        muster = [72, None, 76, None, 74, 79, None, None, 72, None, 77, None, 76, 74, None, None]
        k, t = 0, 0.0
        while t < dauer:
            m = muster[k % len(muster)]
            if m:
                _add(y, _pizz(_hz(m), 0.3, seed=k, hell=0.8) * 0.7, t)
            if k % 8 == 0:
                _add(y, _pizz(_hz(48 + (0, 5, 7, 5)[(k // 8) % 4]), 0.5, seed=900 + k, hell=0.3) * 0.6, t)
            k += 1
            t += beat
    elif stimmung == "aufsteigend":
        beat = 60 / 108 / 2
        stufen = [(60, 64, 67, 72), (62, 65, 69, 74), (64, 67, 71, 76), (65, 69, 72, 77), (67, 71, 74, 79)]
        k, t = 0, 0.0
        while t < dauer:
            takt = (k // 8) % len(stufen)
            akk = stufen[takt]
            m = akk[k % 4] + (12 if (k % 8) >= 4 else 0)
            _add(y, _klavier(_hz(m), 1.2, vel=0.5 + 0.06 * takt), t)
            if k % 8 == 0:
                _add(y, _klavier(_hz(akk[0] - 12), 2.0, vel=0.6), t)
            k += 1
            t += beat
    elif stimmung == "warm":
        beat = 60 / 66
        folge = [(48, 60, 64, 67), (45, 57, 60, 64), (41, 57, 60, 65), (43, 55, 59, 62)]
        k, t = 0, 0.0
        while t < dauer:
            akk = folge[k % len(folge)]
            for j, m in enumerate(akk):
                _add(y, _klavier(_hz(m), 3.4, vel=0.55 if j else 0.7), t + 0.04 * j)
            _add(y, _pad([_hz(m) for m in akk[1:]], 4 * beat), t)
            k += 1
            t += 4 * beat * 0.5
    return y


def bett(tl, n, sprach_rms):
    """Musikspur (Mono, Laenge n Samples) fuer die Timeline. sprach_rms: RMS der gesprochenen Abschnitte."""
    sc = tl["scenes"]
    if not any(s.get("musik") for s in sc):
        return None
    dauer = n / SR
    out = np.zeros(n, np.float32)
    rampe = int(0.5 * SR)
    for st in sorted({s.get("musik") for s in sc if s.get("musik") and s.get("musik") != "stille"}):
        spur = _spur(st, dauer)[:n]
        rms = np.sqrt(np.mean(spur[spur != 0] ** 2)) + 1e-9
        spur = spur / rms
        env = np.zeros(n, np.float32)
        for s in sc:
            if s.get("musik") == st:
                a, b = int(s["f0"] / FPS * SR), int(s["f1"] / FPS * SR)
                env[a:b] = 1.0
        # weiche Uebergaenge (0,5 s): gleitender Mittelwert ueber die Huellkurve
        k = np.ones(rampe, np.float32) / rampe
        env = np.convolve(env, k, mode="same")
        out += spur * env
    ziel = sprach_rms * 10 ** (-UNTER_SPRACHE_DB / 20)
    return out * ziel
