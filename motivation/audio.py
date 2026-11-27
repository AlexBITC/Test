"""Ton: Stimme (-16 LUFS), selbst synthetisierte Musik und Soundeffekte, Ducking, Endmix -14 LUFS,
True Peak < -1 dBTP. Alles wird zirkulaer gemischt (Hall-Fahnen laufen ueber den Loop-Punkt).

  python3 -m motivation.audio  -> out/motivation/mix.wav (+ stems)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "motivation"
SR = 48000
TL = json.loads((OUT / "timeline.json").read_text())
EV = json.loads((OUT / "events.json").read_text())
FPS, N = TL["fps"], TL["n_frames"]
T = N / FPS
NS = int(round(T * SR))
rng = np.random.default_rng(7)
SENT = {s["id"]: s for s in TL["sentences"]}


def sec(frame):
    return frame / FPS


def word_t(sid, word):
    for w in SENT[sid]["words"]:
        if w["w"].lower().strip(".,?!") == word:
            return w["start"]
    raise KeyError(word)


def add(buf, x, t0, gain=1.0):
    """zirkulaer addieren (mono x in mono/stereo buf)"""
    i0 = int(round(t0 * SR)) % NS
    n = len(x)
    idx = (np.arange(n) + i0) % NS
    if buf.ndim == 2 and x.ndim == 1:
        np.add.at(buf, (idx, slice(None)), (x * gain)[:, None])
    else:
        np.add.at(buf, idx, x * gain)


def env_adsr(n, a, r, sr=SR):
    e = np.ones(n, np.float32)
    na, nr = max(1, int(a * sr)), max(1, int(r * sr))
    e[:na] = np.linspace(0, 1, na) ** 1.5
    e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x, axis=0)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x, axis=0)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x, axis=0)


def circ_reverb(x, rt=2.6, mix=0.3, pre=0.02, seed=1):
    """Faltungshall mit synthetischer Impulsantwort, zirkulaer per FFT (Loop-faehig). x stereo."""
    r = np.random.default_rng(seed)
    n = int(rt * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(x.shape[1]):
        ir = r.standard_normal(n) * np.exp(-6.9 * t / rt)
        ir = lp(ir, 5000)
        ir[: int(pre * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        irf = np.zeros(NS)
        irf[:n] = ir[:NS]
        out[:, ch] = np.real(np.fft.ifft(np.fft.fft(x[:, ch]) * np.fft.fft(irf)))
    return x * (1 - mix) + out * mix * 1.6


# ------------------------------------------------------------------ Musik
CH = {"Am": [45, 52, 57, 60, 64], "F": [41, 48, 53, 57, 60], "C": [48, 55, 60, 64, 67], "G": [43, 50, 55, 59, 62],
      "Em": [40, 47, 52, 55, 59], "Fmaj7": [41, 48, 52, 57, 60]}
s = lambda i: SENT[i]["start"]
CHORDS = [  # (Startzeit, Akkord)
    (0.0, "Am"), (s(2) - 0.1, "F"), (s(3) - 0.1, "C"), (word_t(3, "dangerous"), "G"),
    (s(4) - 0.1, "Am"), (word_t(4, "mountain"), "F"), (s(5) - 0.1, "C"), (word_t(5, "never"), "G"),
    (s(6) - 0.1, "Am"), (word_t(6, "that's"), "F"), (s(7) - 0.1, "C"), (word_t(7, "just"), "G"),
    (s(8) - 0.3, "Fmaj7"), (word_t(8, "tomorrow"), "Em"), (s(9) - 0.1, "F"), (word_t(9, "waiting"), "G"),
    (sec(EV["now"]), "C"), (sec(EV["loop0"]) - 0.4, "Am"),
]
MELODIC = False   # False: keine Akkordflaechen, kein Bass/Arpeggio, keine Gloeckchen (nur Puls + Effekte)
CEIL = -3.0   # dBTP vor AAC: der Encoder erzeugt bis ~1,5 dB Ueberschwinger
TEMPO = 84
BEAT = 60 / TEMPO


def pad_note(freq, dur, bright):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n)
    for det in (-0.0045, 0.0, 0.0052):
        f = freq * (1 + det)
        ph = rng.uniform(0, 6.28)
        for h in range(1, 14):
            if f * h > 9000:
                break
            amp = (1 / h) * math.exp(-h / (2.5 + 6 * bright))
            y += amp * np.sin(2 * math.pi * f * h * t + ph * h)
    vib = 1 + 0.06 * np.sin(2 * math.pi * 0.23 * t + rng.uniform(0, 6))
    return (y * vib).astype(np.float32)


def section_brightness(t):
    """0 dunkel .. 1 hell (Filter/Obertoene der Flaechen)"""
    if t < s(4):
        return 0.15
    if t < s(5):
        return 0.25 + 0.2 * (t - s(4)) / (s(5) - s(4))
    if t < s(8) - 0.3:
        return 0.45 + 0.4 * (t - s(5)) / (s(8) - s(5))
    if t < s(9):
        return 0.05
    if t < sec(EV["now"]):
        return 0.5
    return 1.0


def music():
    pad = np.zeros((NS, 2))
    for i, (t0, name) in enumerate(CHORDS):
        t1 = CHORDS[i + 1][0] if i + 1 < len(CHORDS) else T + CHORDS[0][0]
        dur = t1 - t0 + 1.2
        br = section_brightness(t0 + 0.1)
        level = 0.55 if t0 < s(8) - 0.5 else (0.35 if t0 < s(9) - 0.2 else 0.8)
        if t0 >= sec(EV["now"]) - 0.01 and name == "C":
            level = 1.1
        for k, m in enumerate(CH[name]):
            y = pad_note(mtof(m + 12 * (k > 2 and br > 0.6)), dur, br)
            y *= env_adsr(len(y), 0.5 if t0 > 0 else 0.02, 1.1)
            pan = (k / (len(CH[name]) - 1)) * 0.8 - 0.4
            st = np.stack([y * (1 - pan) , y * (1 + pan)], 1) * 0.5
            buf = np.zeros((NS, 2))
            i0 = int(t0 * SR)
            idx = (np.arange(len(y)) + i0) % NS
            np.add.at(buf, idx, st)
            pad += buf * level / len(CH[name])
    pad = lp(pad, 3200)
    # Bass (Grundton) ab Satz 4
    bass = np.zeros(NS)
    for i, (t0, name) in enumerate(CHORDS):
        if t0 < s(4) - 0.2 or (s(8) - 0.5 < t0 < s(9) - 0.2):
            continue
        t1 = CHORDS[i + 1][0] if i + 1 < len(CHORDS) else T
        n = int((t1 - t0 + 0.4) * SR)
        tt = np.arange(n) / SR
        f = mtof(CH[name][0] - 12 if CH[name][0] > 44 else CH[name][0])
        y = (np.sin(2 * math.pi * f * tt) + 0.25 * np.sin(4 * math.pi * f * tt)) * env_adsr(n, 0.08, 0.4)
        add(bass, y.astype(np.float32), t0, 0.22 if t0 < sec(EV["now"]) else 0.3)
    # Pluck-Arpeggio (8tel) von Satz 5 bis Satz 8, lauter werdend
    arp = np.zeros(NS)
    t = s(5) - 0.05
    k = 0
    while t < s(8) - 0.6:
        name = [c for c in CHORDS if c[0] <= t + 0.01][-1][1]
        notes = CH[name][1:] + [CH[name][2] + 12]
        m = notes[[0, 2, 1, 3, 2, 4, 3, 2][k % 8] % len(notes)] + 12
        n = int(0.5 * SR)
        tt = np.arange(n) / SR
        f = mtof(m)
        y = (np.sin(2 * math.pi * f * tt) + 0.3 * np.sin(4 * math.pi * f * tt) + 0.1 * np.sin(6 * math.pi * f * tt))
        y *= np.exp(-tt / 0.18) * (1 - np.exp(-tt / 0.003))
        g = 0.05 + 0.1 * (t - s(5)) / (s(8) - s(5))
        add(arp, y.astype(np.float32), t, g)
        t += BEAT / 2
        k += 1
    # weicher Herzschlag-Kick ab Satz 6 (Viertel), steigend
    kick = np.zeros(NS)
    t = s(6) - 0.05
    while t < s(8) - 0.6:
        add(kick, kick_sound(0.7), t, 0.18 + 0.17 * (t - s(6)) / (s(8) - s(6)))
        t += BEAT
    # Trommeln im Finale: 8tel, verdichtend bis "now"
    t = word_t(9, "stop") - 0.1
    while t < sec(EV["now"]) - 0.12:
        u = (t - word_t(9, "stop")) / (sec(EV["now"]) - word_t(9, "stop"))
        add(kick, kick_sound(0.5 + 0.4 * u), t, 0.2 + 0.3 * u)
        t += BEAT / (2 if u < 0.55 else 4)
    if not MELODIC:
        pad[:] = 0
        bass[:] = 0
        arp[:] = 0
    mus = pad + np.stack([bass + kick, bass + kick], 1) + np.stack([arp * 0.8, arp * 1.2], 1)
    return circ_reverb(mus, rt=2.8, mix=0.32)


def kick_sound(punch=1.0):
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    f = 46 + 70 * np.exp(-tt / 0.04) * punch
    ph = 2 * math.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-tt / 0.16) + 0.1 * rng.standard_normal(n) * np.exp(-tt / 0.008)).astype(np.float32)


# ------------------------------------------------------------------ Soundeffekte
def noise(d):
    return rng.standard_normal(int(d * SR)).astype(np.float32)


def page_flip():
    d = 0.16
    x = bp(noise(d), 900, 5200) * np.exp(-np.arange(int(d * SR)) / SR / 0.05)
    x2 = bp(noise(d), 200, 900) * np.exp(-np.arange(int(d * SR)) / SR / 0.03) * 0.6
    return (x + x2).astype(np.float32)


def whoosh(d=0.6, lo=300, hi=3000, rev=False):
    n = int(d * SR)
    x = noise(d)
    out = np.zeros(n, np.float32)
    seg = 1024
    for i in range(0, n, seg):
        u = i / n
        fc = lo + (hi - lo) * (u if not rev else u)
        b, a = signal.butter(2, [max(40, fc * 0.6) / (SR / 2), min(20000, fc * 1.4) / (SR / 2)], "band")
        out[i:i + seg] = signal.lfilter(b, a, x[i:i + seg])
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2 if not rev else np.linspace(0, 1, n) ** 3
    return out * e


def boom(d=1.6, f0=60, f1=30):
    n = int(d * SR)
    tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt / 0.25)
    y = np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-tt / (d / 3.2))
    y += lp(noise(d), 400) * np.exp(-tt / 0.12) * 0.5
    return y.astype(np.float32)


def chime(m, d=1.4, bright=1.0):
    n = int(d * SR)
    tt = np.arange(n) / SR
    f = mtof(m)
    y = np.zeros(n)
    for h, a, dec in ((1, 1, 1.0), (2.01, 0.35 * bright, 0.5), (3.0, 0.18 * bright, 0.3), (4.2, 0.08 * bright, 0.2)):
        y += a * np.sin(2 * math.pi * f * h * tt) * np.exp(-tt / (d * dec / 3))
    return (y * (1 - np.exp(-tt / 0.002))).astype(np.float32)


def shatter_snd():
    d = 1.4
    n = int(d * SR)
    tt = np.arange(n) / SR
    y = hp(noise(d), 2500) * np.exp(-tt / 0.09) * 0.8
    for _ in range(40):
        t0 = abs(rng.normal(0, 0.12))
        f = rng.uniform(2500, 8500)
        dd = rng.uniform(0.04, 0.35)
        m = int(dd * SR)
        p = np.sin(2 * math.pi * f * np.arange(m) / SR) * np.exp(-np.arange(m) / SR / (dd / 4)) * rng.uniform(0.1, 0.35)
        i0 = int(t0 * SR)
        y[i0:i0 + m] += p[: max(0, min(m, n - i0))]
    b = boom(0.8, 90, 40)
    y[:len(b)] += b * 0.5
    return y.astype(np.float32)


def crackle(d):
    n = int(d * SR)
    y = np.zeros(n, np.float32)
    for _ in range(int(d * 40)):
        i = rng.integers(0, n - 400)
        y[i:i + 400] += hp(noise(400 / SR), 1500) * np.exp(-np.arange(400) / 60) * rng.uniform(0.2, 0.7)
    return y


def rumble(d, g=1.0):
    n = int(d * SR)
    tt = np.arange(n) / SR
    y = lp(noise(d), 140, 4) * 3 + 0.5 * np.sin(2 * math.pi * 38 * tt)
    return (y * np.sin(np.pi * np.minimum(1, tt / d)) ** 0.7 * g).astype(np.float32)


def hum(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    y = sum(np.sin(2 * math.pi * 120 * h * tt) / h for h in (1, 2, 3, 5))
    fl = (rng.random(n // 800 + 1) > 0.3).repeat(800)[:n]
    e = env_adsr(n, 0.02, 0.3)
    return (y * fl * e * 0.4).astype(np.float32)


def tick():
    n = int(0.05 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * math.pi * 3200 * tt) * np.exp(-tt / 0.006) + hp(noise(0.05), 3000) * np.exp(-tt / 0.004) * 0.5).astype(np.float32)


def step_snd():
    n = int(0.18 * SR)
    tt = np.arange(n) / SR
    return (lp(noise(0.18), 300) * np.exp(-tt / 0.03) * 2 + np.sin(2 * math.pi * 70 * tt) * np.exp(-tt / 0.05)).astype(np.float32)


def riser(d):
    n = int(d * SR)
    tt = np.arange(n) / SR
    u = tt / d
    f = 180 * 2 ** (u * 2.5)
    y = np.sin(2 * math.pi * np.cumsum(f) / SR) * 0.4 + np.sin(2 * math.pi * np.cumsum(f * 1.5) / SR) * 0.2
    nz = whoosh(d, 400, 7000)
    return ((y + nz * 1.2) * u ** 2.2).astype(np.float32)


def add_tone(*a, **k):
    if MELODIC:
        add(*a, **k)


def sfx():
    S = np.zeros(NS)
    # Loop-Schnitt: Rueckwaerts-Schwell zum Blitz, Aufschlag bei Frame 0 (+ Wrap)
    add(S, whoosh(sec(EV["flash_peak"] - EV["loop0"]) + 0.3, 300, 6000, rev=True), sec(EV["loop0"]) - 0.3, 0.35)
    add(S, boom(1.4, 70, 34), sec(EV["flash_peak"]), 0.55)
    add_tone(S, chime(84, 1.6, 0.6), sec(EV["flash_peak"]), 0.06)
    # Goldkreis um die 1
    add(S, whoosh(sec(EV["circle"][1] - EV["circle"][0]) + 0.2, 2000, 7000), sec(EV["circle"][0]), 0.12)
    add_tone(S, chime(81, 1.5), sec(EV["circle"][1]) - 0.05, 0.07)
    # Blaetter
    for i, f in enumerate(EV["flips"]):
        add(S, page_flip(), sec(f), 0.32 + 0.1 * (i % 2))
    add(S, boom(0.6, 90, 50), sec(EV["flips"][-1]) + 0.35, 0.25)
    # TOMORROW: Neon an, Riss, Zerbrechen
    add(S, hum(0.7), sec(EV["tm_in"]), 0.06)
    add(S, crackle(sec(EV["crack"][1] - EV["crack"][0]) + 0.2), sec(EV["crack"][0]), 0.22)
    add(S, shatter_snd(), sec(EV["shatter"]), 0.42)
    # Berg waechst
    for i, f in enumerate(EV["grow"]):
        add(S, rumble(0.9 if i < 4 else 1.4, 1.0 if i < 4 else 1.6), sec(f), 0.12)
    add(S, boom(1.2, 55, 30), sec(EV["grow"][-1]), 0.35)
    add(S, whoosh(1.2, 2500, 300), sec(EV["shrink"][0]), 0.12)
    # Schritte + goldene Wegsegmente (Pentatonik aufwaerts)
    penta = [69, 72, 74, 76, 79, 81, 84, 86, 88, 91]
    for f in EV["walk_steps"]:
        add(S, step_snd(), sec(f), 0.10)
    for i, f in enumerate(EV["seg_hits"]):
        add_tone(S, chime(penta[min(i, len(penta) - 1)] if i < 10 else penta[(i % 5) + 4], 1.0, 0.7), sec(f), 0.045)
    add(S, whoosh(sec(EV["ring"][1] - EV["ring"][0]), 1200, 4000), sec(EV["ring"][0]), 0.06)
    add_tone(S, chime(88, 1.5), sec(EV["ring"][1]), 0.06)
    for m in (72, 76, 79, 84):
        add_tone(S, chime(m, 2.0), sec(EV["today"]), 0.05)
    # Sanduhr: Ticken, Rieseln, letztes Korn
    t = sec(EV["sand"][0])
    while t < sec(EV["sand"][1]):
        add(S, tick(), t, 0.10)
        t += 0.5
    sd = sec(EV["sand"][1] - EV["sand"][0])
    add(S, (bp(noise(sd), 3000, 9000) * env_adsr(int(sd * SR), 0.5, 0.4)).astype(np.float32), sec(EV["sand"][0]), 0.02)
    add_tone(S, chime(96, 1.8, 0.3), sec(EV["sand"][1]) + 0.35, 0.05)
    # Finale
    add(S, whoosh(0.5, 300, 1500), sec(EV["ready"]), 0.12)
    for f in EV["run_steps"]:
        add(S, step_snd(), sec(f), 0.2)
    rs = sec(EV["now"]) - word_t(9, "stop")
    add(S, riser(rs), word_t(9, "stop"), 0.18)
    add(S, boom(2.4, 75, 28), sec(EV["now"]), 0.85)
    add(S, (hp(noise(2.5), 4000) * np.exp(-np.arange(int(2.5 * SR)) / SR / 0.6)).astype(np.float32), sec(EV["now"]), 0.12)
    for m in (72, 76, 79, 84, 88):
        add_tone(S, chime(m, 3.0, 0.8), sec(EV["now"]), 0.04)
    # Szenenwechsel
    for k in ("B", "C", "D", "E", "F"):
        add(S, whoosh(0.5), sec(EV["scenes"][k][0]) - 0.25, 0.08)
    st = np.stack([S, S], 1)
    return circ_reverb(st, rt=1.8, mix=0.22, seed=3)


# ------------------------------------------------------------------ Stimme
def voice():
    meter = pyln.Meter(SR)
    v = np.zeros(NS)
    gains = {}
    rising = [i for i in SENT if SENT[i]["mood"] == "rising"]
    for i, snt in SENT.items():
        y, sr = sf.read(str(ROOT / snt["wav"]), dtype="float64")
        assert sr == SR
        y = hp(y, 70)
        L = meter.integrated_loudness(y) if len(y) > SR * 0.5 else meter.integrated_loudness(np.concatenate([y, y]))
        mood = snt["mood"]
        off = TL["mood_gain_db"][mood]
        if mood == "rising":
            off = 0.3 + 1.2 * rising.index(i) / max(1, len(rising) - 1)
        g = 10 ** ((-20 - L + off) / 20)
        gains[i] = round(20 * math.log10(g), 2)
        add(v, (y * g).astype(np.float32), snt["start"])
    L = meter.integrated_loudness(v)
    v *= 10 ** ((-16 - L) / 20)
    return v, gains


def true_peak_db(x):
    up = signal.resample_poly(x, 4, 1, axis=0)
    return 20 * math.log10(np.abs(up).max() + 1e-12)


def limiter(x, ceiling_db=-1.5):
    """Look-ahead-Limiter auf 4x-ueberabgetasteter Huellkurve (zirkulaer)."""
    c = 10 ** (ceiling_db / 20)
    up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = up.reshape(-1, 4).max(axis=1)[: len(x)]
    need = np.minimum(1.0, c / np.maximum(pk, 1e-9))
    la = int(0.003 * SR)
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(need, size=2 * la + 1, mode="wrap")
    # Release-Glaettung (zirkulaer, zwei Durchlaeufe)
    rel = math.exp(-1 / (0.08 * SR))
    for _ in range(2):
        cur = g[-1]
        out = np.empty_like(g)
        for i in range(len(g)):
            cur = min(g[i], cur + (1 - cur) * (1 - rel))
            out[i] = cur
        g = out
    att = np.convolve(np.concatenate([g[-la:], g]), np.ones(la) / la, "valid")[: len(g)]
    g = np.minimum(g, att)
    return x * g[:, None]


def main():
    v, gains = voice()
    m = music()
    fx = sfx()
    # Ducking: Musik unter der Stimme absenken (Huellkurve der Stimme)
    envv = np.sqrt(np.maximum(lp(v ** 2, 8), 0))
    envv = np.clip(envv / (np.percentile(envv[envv > 1e-4], 90) + 1e-9), 0, 1)
    duck = 1 - 0.5 * np.clip(envv * 1.6, 0, 1)        # bis -6 dB
    duck = lp(duck, 4)
    meter = pyln.Meter(SR)
    Lm = meter.integrated_loudness(m)
    m *= 10 ** (((-25.5 if MELODIC else -31.0) - Lm) / 20)   # nur Puls: deutlich leiser
    m *= duck[:, None]
    Lf = meter.integrated_loudness(fx)
    fx *= 10 ** ((-26 - Lf) / 20)
    fx *= (0.6 + 0.4 * (duck - 0.5) / 0.5)[:, None]   # bis -4,4 dB unter der Stimme
    vs = np.stack([v, v], 1)
    mix = vs + m + fx
    L = meter.integrated_loudness(mix)
    mix *= 10 ** ((-14 - L) / 20)
    pre = mix.copy()                 # Vorstufe; Verstaerkung so suchen, dass NACH dem Limiter -14 LUFS
    gain_db = 0.0
    for _ in range(6):
        mix = limiter(pre * 10 ** (gain_db / 20), CEIL)
        L = meter.integrated_loudness(mix)
        if abs(L + 14.0) < 0.03:
            break
        gain_db += -14.0 - L
    tp = true_peak_db(mix)
    L = meter.integrated_loudness(mix)
    Lv = meter.integrated_loudness(v)
    sf.write(str(OUT / "mix.wav"), mix.astype(np.float32), SR, subtype="PCM_24")
    sf.write(str(OUT / "stem_voice.wav"), v.astype(np.float32), SR, subtype="PCM_24")
    sf.write(str(OUT / "stem_music.wav"), m.astype(np.float32), SR, subtype="PCM_24")
    sf.write(str(OUT / "stem_sfx.wav"), fx.astype(np.float32), SR, subtype="PCM_24")
    rep = {"voice_lufs": round(Lv, 2), "mix_lufs": round(L, 2), "mix_true_peak_dbtp": round(tp, 2),
           "voice_gain_db": gains, "duration_s": T}
    (OUT / "audio_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
