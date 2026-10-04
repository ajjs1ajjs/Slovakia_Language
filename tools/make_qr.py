#!/usr/bin/env python3
"""Перегенерація ТІЛЬКИ QR-PNG (без TTS) з новим base-url для хостингу.
  python tools/make_qr.py --base-url https://USER.github.io/REPO/audio
Без --base-url QR кодують відносний шлях audio/<ID>/<file>."""
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="")
    a = ap.parse_args()
    import qrcode
    n = 0
    for idx in sorted((ROOT / "assets" / "audio").glob("*/index.json")):
        lid = idx.parent.name
        for e in sum(([x for x in json.loads(idx.read_text(encoding="utf-8")).values()], []):
            url = f"{a.base_url.rstrip('/')}/{lid}/{e['file']}" if a.base_url else f"audio/{lid}/{e['file']}"
            out = ROOT / "assets" / "qr" / lid / (Path(e["file"]).stem + ".png")
            out.parent.mkdir(parents=True, exist_ok=True)
            qrcode.make(url).save(str(out))
            n += 1
    print(f"QR regenerated: {n}")
