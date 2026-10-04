#!/usr/bin/env python3
"""Індекс лекцій для PWA: сканує 0*_*/**.md -> pwa/lessons.json [{id, level, title, path}]."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEVEL = {"00_A0-Zaklady-vymova": "A0", "01_A1-Prezitie": "A1",
         "02_A2-Kazdodenny-zivot": "A2", "03_B1-Nezavislost": "B1", "04_B2-Sloboda": "B2"}
out = []
for d, lv in LEVEL.items():
    for f in sorted((ROOT / d).glob("*.md")):
        m = re.match(r"(\d+)", f.name)
        title = f.name
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        out.append({"id": m.group(1), "level": lv, "title": title, "path": f"{d}/{f.name}"})
(ROOT / "pwa" / "lessons.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"lessons: {len(out)}")
