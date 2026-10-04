#!/usr/bin/env python3
"""Кеш muLaw 8000Hz mono для всіх MP3 (для Sound-анотацій у PDF).
  python tools/make_ulaw.py --all | --lesson 001
Вивід: build/wav8000/<ID>/<file>.ulaw (сирі muLaw-байти без заголовка).
"""
import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
OUT = ROOT / "build" / "wav8000"

def conv(mp3: Path, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 0:
        return "skip"
    subprocess.run([FF, "-y", "-v", "error", "-i", str(mp3),
                    "-ar", "8000", "-ac", "1", "-f", "mulaw", str(out)], check=True)
    return "ok"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    dirs = [ROOT / "assets" / "audio" / a.lesson] if a.lesson else sorted((ROOT / "assets" / "audio").glob("[0-9]*"))
    if not dirs:
        sys.exit("вкажи --lesson 001 або --all")
    n = ok = 0
    for d in dirs:
        for mp3 in sorted(d.glob("*.mp3")):
            r = conv(mp3, OUT / d.name / (mp3.name + ".ulaw"))
            n += 1
            ok += r == "ok"
    total = sum(f.stat().st_size for f in OUT.rglob("*.ulaw"))
    print(f"ulaw: files={n} new={ok} total={total//1024}KB")
