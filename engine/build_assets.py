"""Rendert die Asset-Bibliothek einmalig in Blender und legt sie als WebP ab.

  assets/clips/<name>/{in,loop}_NNNN.webp  + meta.json        Figuren-Clips (RGBA, loopbar)
  assets/clips/kalle_*/mund_{zu,halb,auf}/…  + boxes.json      Mund-Ausschnitte (Lippensynchron)
  assets/sets/<set>/bg.webp, fg.webp, meta.json                Set-Plates (Hinter-/Vordergrund, Anker)
  assets/manifest.json                                         Version (Hash) -> Szenen-Cache

Aufruf:  npm run assets [-- --only kalle_jubel,theke] [--force] [--jobs 2] [--samples 8]
Fertige Teile werden übersprungen (Ordner mit meta.json/boxes.json).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ENGINE = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
BLENDER = os.environ.get("BLENDER", "blender")
KALLE = ["neutral", "zweifel", "staunen", "schock", "jubel"]
BYTE = ["schweben", "sprechen"]
SETS = ["theke", "buero", "studio"]
VISEMES = ["zu", "halb", "auf"]
QUALITY = {"clip": 90, "mund": 94, "plate": 92}


def log(*a):
    print("[assets]", *a, flush=True)


def jobs(only=None):
    """Reihenfolge: zuerst das, womit compose schon arbeiten kann (Sets, neutral, Byte), dann der Rest."""
    out = [("plate", s, None, ASSETS / "sets" / s) for s in SETS]
    clip = lambda n, v=None: ("clip", n, v, ASSETS / "clips" / n)  # noqa: E731
    out += [clip("kalle_neutral")] + [clip(f"byte_{b}") for b in BYTE]
    out += [clip("kalle_neutral", v) for v in VISEMES]
    for k in KALLE[1:]:
        out += [clip(f"kalle_{k}")] + [clip(f"kalle_{k}", v) for v in VISEMES]
    if only:
        out = [j for j in out if j[1] in only or j[1].split("_", 1)[-1] in only]
    return out


def done(job) -> bool:
    kind, name, vis, d = job
    if vis:
        return (d / f"mund_{vis}" / "boxes.json").exists()
    return (d / "meta.json").exists()


def to_webp(folder: Path, quality: int):
    for p in sorted(folder.glob("*.png")):
        im = Image.open(p)
        im.save(p.with_suffix(".webp"), quality=quality, method=5, exact=False)
        p.unlink()


def run(job, samples, logdir: Path):
    kind, name, vis, d = job
    d.mkdir(parents=True, exist_ok=True)
    tag = f"{name}{'_' + vis if vis else ''}"
    cmd = [BLENDER, "-b", "--factory-startup", "--python", str(ENGINE / "assets_blender.py"), "--",
           kind, name, str(d), str(samples)] + ([vis] if vis else ([] if kind == "plate" else ["base"]))
    t0 = time.time()
    with open(logdir / f"{tag}.log", "w") as lf:
        p = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        raise RuntimeError(f"Blender-Fehler bei {tag}, siehe {logdir / (tag + '.log')}")
    if kind == "plate":
        to_webp(d, QUALITY["plate"])
    elif vis:
        to_webp(d / f"mund_{vis}", QUALITY["mund"])
    else:
        to_webp(d, QUALITY["clip"])
    return tag, time.time() - t0


def manifest():
    h = hashlib.sha256()
    entries = {}
    for p in sorted(ASSETS.rglob("*.json")):
        if p.name == "manifest.json":
            continue
        h.update(str(p.relative_to(ASSETS)).encode())
        h.update(p.read_bytes())
    for p in sorted(ASSETS.rglob("*.webp")):
        st = p.stat()
        h.update(f"{p.relative_to(ASSETS)}:{st.st_size}".encode())
    for d in sorted((ASSETS / "clips").glob("*")) + sorted((ASSETS / "sets").glob("*")):
        if d.is_dir():
            entries[str(d.relative_to(ASSETS))] = len(list(d.rglob("*.webp")))
    (ASSETS / "manifest.json").write_text(json.dumps(
        {"version": h.hexdigest()[:16], "built": time.strftime("%Y-%m-%d %H:%M"), "files": entries}, indent=1) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="Komma-Liste: kalle_jubel, byte_sprechen, theke …")
    ap.add_argument("--force", action="store_true", help="ausgewählte Teile neu rendern")
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("ASSET_JOBS", "2")))
    ap.add_argument("--samples", type=int, default=int(os.environ.get("ASSET_SAMPLES", "8")))
    args = ap.parse_args()
    if not shutil.which(BLENDER):
        sys.exit("Blender nicht gefunden (./setup.sh oder BLENDER=/pfad/zu/blender)")
    only = {x.strip() for x in args.only.split(",") if x.strip()} or None
    todo = jobs(only)
    if args.force:
        for kind, name, vis, d in todo:
            shutil.rmtree(d / f"mund_{vis}" if vis else d, ignore_errors=True)
    # Basis-Clips vor ihren Mund-Varianten (Varianten brauchen den fertigen Basis-Ordner nicht, aber
    # so ist die Bibliothek früh benutzbar)
    todo = [j for j in todo if not done(j)]
    logdir = ROOT / "out" / "work" / "assets"
    logdir.mkdir(parents=True, exist_ok=True)
    log(f"{len(todo)} Teile zu rendern, {args.jobs} parallel, {args.samples} Samples")
    t0 = time.time()
    with ThreadPoolExecutor(args.jobs) as ex:
        futs = [ex.submit(run, j, args.samples, logdir) for j in todo]
        for fu in as_completed(futs):
            tag, dt = fu.result()
            log(f"  fertig: {tag} ({dt / 60:.1f} min, gesamt {(time.time() - t0) / 60:.1f} min)")
    manifest()
    log("Manifest:", json.loads((ASSETS / "manifest.json").read_text())["version"])


if __name__ == "__main__":
    main()
