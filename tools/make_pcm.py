#!/usr/bin/env python3
"""Кеш PCM 22050Hz 16-bit mono big-endian для всіх MP3 (для Sound-анотацій у PDF).
PDF вимагає 16-біт семпли big-endian (s16be) — little-endian дає шипіння.
Якість помітно вища за muLaw 8000 (~5.5x розмір), Acrobat грає нормально.
  python tools/make_pcm.py --all | --lesson 001
Вивід: build/wav22050/<ID>/<file>.pcm (сирі s16be-байти без заголовка).
"""
import argparse, subprocess, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = ROOT / "build" / "wav22050"

def conv(mp3: Path, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 0:
        return "skip"
    subprocess.run([FF, "-y", "-v", "error", "-i", str(mp3),
                    "-ar", "22050", "-ac", "1", "-f", "s16be", str(out)], check=True)
    return "ok"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    dirs = [ROOT / "assets" / "audio" / a.lesson] if a.lesson else sorted((ROOT / "assets" / "audio").glob("[0-9]*"))
    if not dirs:
        raise SystemExit("вкажи --lesson 001 або --all")
    n = ok = 0
    for d in dirs:
        for mp3 in sorted(d.glob("*.mp3")):
            r = conv(mp3, OUT / d.name / (mp3.name + ".pcm"))
            n += 1
            ok += r == "ok"
    total = sum(f.stat().st_size for f in OUT.rglob("*.pcm"))
    print(f"pcm: files={n} new={ok} total={total//1024}KB")
