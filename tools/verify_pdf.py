#!/usr/bin/env python3
"""Перевірка зібраного PDF: сторінки + кількість вбудованих Sound-анотацій.

  python tools/verify_pdf.py build/pdf/004.pdf --expect-audio 004

Якщо --expect-audio задано, очікувана кількість звуків береться з
assets/audio/<ID>/index.json. Код виходу 1 — розбіжність.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "assets" / "audio"


def count_sounds(reader) -> int:
    total = 0
    for page in reader.pages:
        for annot in page.get("/Annots") or []:
            if str(annot.get_object().get("/Subtype")) == "/Sound":
                total += 1
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--expect-audio", default=None, metavar="LESSON_ID",
                    help="звірити кількість звуків з assets/audio/<ID>/index.json")
    a = ap.parse_args()

    from pypdf import PdfReader

    path = Path(a.pdf)
    if not path.exists():
        print(f"ERROR немає файлу {path}")
        return 1
    reader = PdfReader(str(path))
    sounds = count_sounds(reader)
    print(f"{path}: сторінок={len(reader.pages)} звуків={sounds}")

    if a.expect_audio:
        idx_path = AUDIO / a.expect_audio / "index.json"
        if not idx_path.exists():
            print(f"ERROR немає {idx_path}")
            return 1
        index = json.loads(idx_path.read_text(encoding="utf-8"))
        expected = len(index.get("slow", [])) + len(index.get("normal", []))
        print(f"очікувано з index.json: {expected}")
        if sounds != expected:
            print(f"ERROR звуків {sounds}, очікували {expected}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
