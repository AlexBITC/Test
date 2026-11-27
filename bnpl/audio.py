"""Ton fuer das BNPL-Video: Stimme -16 LUFS, leise selbst erzeugte Klangflaeche ohne Melodie
(28 dB unter der Stimme), dezente Klicks bei den Haekchen-Boxen, Endmix -14 LUFS,
True Peak vor AAC <= -3 dBTP (AAC erzeugt Ueberschwinger; Ziel in der MP4: unter -1 dBTP).
Zirkulaer gemischt: Hall und Flaeche laufen ueber den Loop-Punkt.

  python3 -m bnpl.audio -> out/bnpl/mix.wav
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal
from scipy.ndimage import minimum_filter1d

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "bnpl"
SR = 48000
TL = json.loads((OUT / "timeline.json").read_text())
EV = json.loads((OUT / "anchors.json").read_text())["events"]
FPS, N = TL["fps"], TL["n_frames"]
NS = int(round(N / FPS * SR))
CEIL = -3.0
MUSIC_BELOW_VOICE_DB = 28.0
rng = np.random.default_rng(11)


def add(buf, x, t0, gain=1.0):
    i0 = int(round(t0 * SR)) % NS
    idx = (np.arange(len(x)) + i0) % NS
    if buf.ndim == 2:
        np.add.at(buf, (idx, slice(None)), (x * gain)[:, None])
    else:
        np.add.at(buf, idx, x * gain)


def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "low")
    return signal.lfilter(b, a, x, axis=0)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x, axis=0)


def drone():
    """Ruhige, stehende Flaeche: Grundton A (55/110 Hz) + Quinte, langsam atmend, gefiltertes Rauschen.
    Keine Tonfolge, keine Melodie. Alle Frequenzen ganzzahlig pro Loop -> nahtlos."""
    t = np.arange(NS) / SR
    T = NS / SR

    def loopf(f):          # Frequenz so runden, dass genau ganze Perioden in den Loop passen
        return round(f * T) / T
    y = np.zeros((NS, 2))
    for f, a, pan in ((55, 0.5, 0.0), (110, 0.35, -0.3), (164.8, 0.18, 0.3), (220, 0.08, 0.0)):
        f = loopf(f)
        for ch, det in ((0, -0.0015), (1, 0.0015)):
            fd = loopf(f * (1 + det))
            y[:, ch] += a * (1 - pan if ch == 0 else 1 + pan) * np.sin(2 * math.pi * fd * t)
    breath = 0.75 + 0.25 * np.sin(2 * math.pi * loopf(0.07) * t)
    nz = lp(rng.standard_normal((NS, 2)), 600) * 0.6
    y = (y + nz) * breath[:, None]
    return lp(y, 900)


def tick():
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * math.pi * 2100 * tt) * np.exp(-tt / 0.008) * 0.6
            + hp(rng.standard_normal(n), 2500) * np.exp(-tt / 0.004) * 0.4).astype(np.float32)


def circ_reverb(x, rt=1.6, mix=0.18):
    n = int(rt * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    r = np.random.default_rng(3)
    for ch in range(x.shape[1]):
        ir = lp(r.standard_normal(n) * np.exp(-6.9 * t / rt), 5000)
        ir /= np.sqrt(np.sum(ir ** 2))
        irf = np.zeros(NS)
        irf[:n] = ir
        out[:, ch] = np.real(np.fft.ifft(np.fft.fft(x[:, ch]) * np.fft.fft(irf)))
    return x * (1 - mix) + out * mix * 1.5


def limiter(x, ceiling_db):
    c = 10 ** (ceiling_db / 20)
    up = np.abs(signal.resample_poly(x, 4, 1, axis=0)).max(axis=1)
    pk = up.reshape(-1, 4).max(axis=1)[: len(x)]
    need = np.minimum(1.0, c / np.maximum(pk, 1e-9))
    la = int(0.003 * SR)
    g = minimum_filter1d(need, size=2 * la + 1, mode="wrap")
    rel = 1 - math.exp(-1 / (0.08 * SR))
    for _ in range(2):
        cur = g[-1]
        out = np.empty_like(g)
        for i in range(len(g)):
            cur = min(g[i], cur + (1 - cur) * rel)
            out[i] = cur
        g = out
    return x * g[:, None]


def true_peak_db(x):
    return 20 * math.log10(np.abs(signal.resample_poly(x, 4, 1, axis=0)).max() + 1e-12)


def main():
    meter = pyln.Meter(SR)
    v = np.zeros(NS)
    for s in TL["sentences"]:
        y, sr = sf.read(str(ROOT / s["wav"]), dtype="float64")
        y = hp(y, 70)
        L = meter.integrated_loudness(y)
        add(v, (y * 10 ** ((-20 - L) / 20)).astype(np.float32), s["start"])   # Saetze gleich laut
    v *= 10 ** ((-16 - meter.integrated_loudness(v)) / 20)
    Lv = meter.integrated_loudness(v)
    vs = np.stack([v, v], 1)
    vs = circ_reverb(vs, rt=0.9, mix=0.06)                 # kaum Raum, nur Zusammenhalt
    vs *= 10 ** ((-16 - meter.integrated_loudness(vs)) / 20)
    m = drone()
    m *= 10 ** ((-16 - MUSIC_BELOW_VOICE_DB - meter.integrated_loudness(m)) / 20)
    fx = np.zeros((NS, 2))
    for t in EV["pay"]:
        add(fx, tick(), (t + 9) / FPS, 1.0)
    fx = circ_reverb(fx, rt=1.2, mix=0.25)
    fx *= 10 ** ((-36 - meter.integrated_loudness(fx)) / 20)
    pre = vs + m + fx
    gain_db = 0.0
    for _ in range(6):
        mix = limiter(pre * 10 ** (gain_db / 20), CEIL)
        L = meter.integrated_loudness(mix)
        if abs(L + 14) < 0.03:
            break
        gain_db += -14 - L
    sf.write(str(OUT / "mix.wav"), mix.astype(np.float32), SR, subtype="PCM_24")
    rep = {"voice_lufs": round(Lv, 2), "music_lufs": round(meter.integrated_loudness(m), 2),
           "music_below_voice_db": MUSIC_BELOW_VOICE_DB, "mix_lufs": round(L, 2), "mix_true_peak_dbtp": round(true_peak_db(mix), 2)}
    (OUT / "audio_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
