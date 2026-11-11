#!/usr/bin/env python3
"""Контент-лінтер курсу: перевіряє структуру лекцій, посилання на фото/аудіо та ключі.

  python tools/check_course.py           # звіт + код виходу 1 при помилках
  python tools/check_course.py --strict  # попередження теж валять перевірку

Коди виходу: 0 — чисто, 1 — є помилки (або попередження у --strict).
Скрипт нічого не змінює: лише читає файли.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
FOTO = ROOT / "assets" / "foto"
AUDIO = ROOT / "assets" / "audio"
SCRIPTS = ROOT / "assets" / "audio-scripts"

# рівень -> очікувана кількість лекцій (див. KURIKULUM.md)
LEVELS = {
    "00_A0-Zaklady-vymova": 6,
    "01_A1-Prezitie": 20,
    "02_A2-Kazdodenny-zivot": 25,
    "03_B1-Nezavislost": 30,
    "04_B2-Sloboda": 30,
}

LESSON_RE = re.compile(r"^(\d{3})-(.+)\.md$")
# секції шаблону: шукаємо за ключовим словом, номер і діакритика не важливі
SECTIONS = {
    "FOTO": re.compile(r"(?m)^#{2,4}\s*\d*\.?\s*FOTO\b", re.I),
    "SLOVÍČKA": re.compile(r"(?m)^#{2,4}\s*\d*\.?\s*SLOV[IÍ][ČC]KA\b", re.I),
    "GRAMATIKA": re.compile(r"(?m)^#{2,4}\s*\d*\.?\s*GRAMATIKA\b", re.I),
    "VÝSLOVNOSŤ": re.compile(r"(?m)^#{2,4}\s*\d*\.?\s*V[ÝY]SLOVNOS[TŤ]\b", re.I),
    "CVIČENIA": re.compile(r"(?m)^#{2,4}\s*\d*\.?\s*CVI[ČC]ENIA\b", re.I),
}
KEY_RE = re.compile(r"(?i)K[ĽL]ÚČ|Kľúč|KĽÚČ")
PHOTO_REF_RE = re.compile(r"assets/foto/([A-Za-z0-9_.\-]+\.jpg)")
PLACEHOLDER_RE = re.compile(
    r"Поки фото|згенерувати AI|фото-заглушка|Unsplash-підказка|згенеруємо пізніше", re.I
)
LEGACY_QR_RE = re.compile(r"(?m)^#{1,4}\s*\d*\.?\s*QR\b")
LEGACY_ID_RE = re.compile(r"\bT\d{2,3}-\d{2}\b|\b\d{3}-(?:DIALOG|dialog)\.mp3\b")
SLOW_REF_RE = re.compile(r"(slow-\d{2}\.mp3)")
HEADING_RE = re.compile(r"(?m)^#{2,4}\s*\d*\.?\s*(SLOVICKA|VYSLOVNOST|CVICENIA|DIALOG)\b")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


def load_lessons(rep: Report) -> dict[str, Path]:
    lessons: dict[str, Path] = {}
    total = 0
    for level, expected in LEVELS.items():
        d = ROOT / level
        if not d.is_dir():
            rep.err(level, "немає каталогу рівня")
            continue
        found = 0
        for f in sorted(d.glob("*.md")):
            m = LESSON_RE.match(f.name)
            if not m:
                rep.warn(f.name, "файл не відповідає схемі NNN-nazov.md")
                continue
            lid = m.group(1)
            if lid in lessons:
                rep.err(f.name, f"дубль ID {lid} (вже є {lessons[lid].name})")
                continue
            lessons[lid] = f
            found += 1
        total += found
        if found != expected:
            rep.err(level, f"лекцій {found}, за курикулумом {expected}")
    return lessons


def check_lesson(lid: str, path: Path, rep: Report) -> None:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        rep.err(f"L{lid}", f"не UTF-8: {e}")
        return

    for name, rx in SECTIONS.items():
        if not rx.search(text):
            rep.err(f"L{lid}", f"немає секції {name}")

    if HEADING_RE.search(text):
        rep.err(f"L{lid}", "заголовок без діакритики (SLOVICKA/CVICENIA/...)")

    for m in PHOTO_REF_RE.finditer(text):
        if not (FOTO / m.group(1)).exists():
            rep.err(f"L{lid}", f"немає файлу фото {m.group(1)}")

    if PLACEHOLDER_RE.search(text):
        rep.err(f"L{lid}", "залишок заглушки/обіцянки («Поки фото», «згенеруємо пізніше»)")

    if LEGACY_QR_RE.search(text):
        rep.err(f"L{lid}", "секція QR лишилась від старої схеми (QR не використовується)")

    for m in LEGACY_ID_RE.finditer(text):
        rep.err(f"L{lid}", f"легасі-ідентифікатор аудіо «{m.group(0)}»")

    # ключі до вправ обов'язкові, якщо вправи є
    if SECTIONS["CVIČENIA"].search(text) and not KEY_RE.search(text):
        rep.err(f"L{lid}", "немає ключів до вправ")

    idx_path = AUDIO / lid / "index.json"
    if idx_path.exists():
        try:
            index = json.loads(idx_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            rep.err(f"L{lid}", f"index.json невалідний: {e}")
            return
        have_slow = {e["file"] for e in index.get("slow", [])}
        have_all = have_slow | {e["file"] for e in index.get("normal", [])}
        for ref in SLOW_REF_RE.findall(text):
            if ref not in have_slow:
                rep.err(f"L{lid}", f"посилання на {ref}, якого немає в index.json")
        for fn in sorted(have_all):
            if not (AUDIO / lid / fn).exists():
                rep.err(f"L{lid}", f"index.json вказує на відсутній {fn}")
        # порожній index.json — нормально для лекцій без озвучки (напр. тест A1),
        # але не тоді, коли текст посилається на slow-NN.mp3
        if not have_all and SLOW_REF_RE.search(text):
            rep.err(f"L{lid}", "текст посилається на аудіо, а index.json порожній")
    else:
        rep.warn(f"L{lid}", "немає assets/audio/<ID>/index.json")

    if not (SCRIPTS / f"{lid}.txt").exists():
        rep.warn(f"L{lid}", "немає audio-scripts/<ID>.txt")


def check_audio(lessons: dict[str, Path], rep: Report) -> None:
    if not AUDIO.is_dir():
        rep.err("assets/audio", "немає каталогу аудіо")
        return
    for d in sorted(p for p in AUDIO.iterdir() if p.is_dir()):
        if d.name not in lessons:
            rep.err(f"audio/{d.name}", "аудіо без лекції")
            continue
        idx = d / "index.json"
        if not idx.exists():
            rep.err(f"audio/{d.name}", "немає index.json")
            continue
        try:
            index = json.loads(idx.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            rep.err(f"audio/{d.name}", f"index.json невалідний: {e}")
            continue
        known = {e["file"] for e in index.get("slow", []) + index.get("normal", [])}
        for mp3 in sorted(d.glob("*.mp3")):
            if mp3.name not in known:
                rep.err(f"audio/{d.name}", f"{mp3.name} не згаданий в index.json")


def check_photos(lessons: dict[str, Path], rep: Report) -> None:
    if not FOTO.is_dir():
        rep.err("assets/foto", "немає каталогу фото")
        return
    sources = list(FOTO.glob("SOURCES_*.md"))
    if not sources:
        rep.err("assets/foto", "немає файлів атрибуції SOURCES_*.md")
        return
    attributed = set()
    for s in sources:
        for m in re.finditer(r"(?m)^\|\s*(\S+\.jpg)", s.read_text(encoding="utf-8", errors="replace")):
            attributed.add(m.group(1))
    for jpg in sorted(FOTO.glob("*.jpg")):
        if jpg.name not in attributed:
            rep.err("assets/foto", f"{jpg.name} без атрибуції в SOURCES_*.md")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="попередження теж вважати помилкою")
    a = ap.parse_args()

    rep = Report()
    lessons = load_lessons(rep)
    for lid, path in lessons.items():
        check_lesson(lid, path, rep)
    check_audio(lessons, rep)
    check_photos(lessons, rep)

    for w in rep.warnings:
        print(f"WARN  {w}")
    for e in rep.errors:
        print(f"ERROR {e}")

    n_err, n_warn = len(rep.errors), len(rep.warnings)
    print(f"\nлекцій: {len(lessons)} · помилок: {n_err} · попереджень: {n_warn}")
    if n_err or (a.strict and n_warn):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
