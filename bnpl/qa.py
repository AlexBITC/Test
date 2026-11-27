"""Pruefung der fertigen MP4: Format, Groesse, Lautheit/True Peak, leere Frames, Loop-Naht,
Kontaktbogen, Whisper-Abgleich des Endmixes mit dem Skript.

  python3 -m motivation.qa out/dont-wait-for-tomorrow.mp4
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "bnpl"


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def main():
    mp4 = Path(sys.argv[1])
    rep = {}
    pr = json.loads(sh(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(mp4)]).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
    rep["video"] = f"{v['codec_name']} {v.get('profile')} {v['width']}x{v['height']} {v['r_frame_rate']} fps {v['pix_fmt']}, {v['nb_frames']} Frames"
    rep["audio"] = f"{a['codec_name']} {a['sample_rate']} Hz {a['channels']} ch {int(a.get('bit_rate', 0)) // 1000} kbit/s"
    rep["dauer_s"] = round(float(pr["format"]["duration"]), 2)
    rep["groesse_mb"] = round(int(pr["format"]["size"]) / 1e6, 2)
    # Lautheit der fertigen Datei (AAC dekodiert)
    e = subprocess.run(["ffmpeg", "-nostats", "-i", str(mp4), "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    summ = e[e.rfind("Summary:"):]
    rep["lufs_integriert"] = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    rep["true_peak_dbtp"] = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    # Helligkeit pro Frame -> leere/schwarze Frames
    st = subprocess.run(["ffmpeg", "-i", str(mp4), "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    yavg = [float(x) for x in re.findall(r"YAVG=([\d.]+)", st)]
    rep["min_helligkeit"] = round(min(yavg), 2)
    rep["leere_frames"] = [i for i, y in enumerate(yavg) if y < 6]
    # Loop-Naht: erster vs. letzter Frame
    work = OUT / "qa"
    work.mkdir(exist_ok=True)
    n = int(v["nb_frames"])
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-vf", f"select='eq(n\\,0)+eq(n\\,{n - 1})+eq(n\\,{n - 2})'", "-vsync", "0", str(work / "loop_%d.png")])
    from PIL import Image
    f0 = np.asarray(Image.open(work / "loop_1.png"), np.float32)
    fl = np.asarray(Image.open(work / "loop_3.png"), np.float32)
    fl2 = np.asarray(Image.open(work / "loop_2.png"), np.float32)
    rep["loop_diff_letzter_zu_erstem"] = round(float(np.abs(f0 - fl).mean()), 2)
    rep["vergleich_vorletzter_zu_letztem"] = round(float(np.abs(fl2 - fl).mean()), 2)
    # Kontaktbogen: alle 0,5 s ein Bild (2 Boegen)
    for k, (t0, t1) in enumerate(((0, 18), (18, 36))):
        sh(["ffmpeg", "-y", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", str(mp4), "-vf",
            "fps=2,scale=216:384,drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:text='%{pts\\:hms}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=9x4",
            "-frames:v", "1", str(ROOT / "out" / f"bnpl_kontaktbogen_{k + 1}.png")])
    # Whisper auf dem fertigen Ton
    import librosa
    from faster_whisper import WhisperModel
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-ac", "1", "-ar", "16000", str(work / "final16.wav")])
    y = librosa.load(str(work / "final16.wav"), sr=16000)[0].astype(np.float32)
    m = WhisperModel("medium.en", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(y, language="en", beam_size=5)
    hyp = " ".join(s.text.strip() for s in segs)
    tl = json.loads((OUT / "timeline.json").read_text())
    ref = " ".join(s["text"] for s in tl["sentences"])
    def norm(t):
        t = re.sub(r"\$\s?(\d+(?:\.\d+)?)\s*(billion|million)", r"\1 \2 dollars", t.lower().replace("’", "'"))
        return [w.strip("'") for w in re.sub(r"[^a-z0-9' ]", " ", t).split() if w.strip("'")]
    rep["whisper_endmix"] = hyp
    rep["whisper_wortfehler"] = sum(1 for a_, b_ in zip(norm(ref), norm(hyp)) if a_ != b_) + abs(len(norm(ref)) - len(norm(hyp)))
    (OUT / "qa_report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
