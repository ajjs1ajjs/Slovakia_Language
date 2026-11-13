#!/usr/bin/env python3
"""Генерація MP3 для курсу Slovakia_Language.

Парсить assets/audio-scripts/*.txt ([SLOW]/[NORMAL]), озвучує edge-tts (sk-SK)
і кладе MP3 + index.json у assets/audio/<ID>/.

Використання:
  python tools/generate_audio.py --lesson 001   # одна лекція
  python tools/generate_audio.py --all          # всі 111 (довго!)
  python tools/generate_audio.py --all --plan   # тільки розпарсити, без TTS

Будь-яка помилка TTS валить запуск з кодом 1: частково озвучений курс
не має вважатися успішною збіркою.
"""
import argparse, asyncio, json, re, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "assets" / "audio-scripts"
AUDIO = ROOT / "assets" / "audio"
FEMALE = "sk-SK-ViktoriaNeural"
MALE = "sk-SK-LukasNeural"

SKIP_PREFIX = ("LEKCIA", "LEKCI", "Інструкція", "Голос", "Файли", "Інструкц", "Voice", "Súbory")


def parse_script(path: Path):
    slow, normal, section = [], [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(SKIP_PREFIX):
            continue
        if line.startswith("[SLOW"):
            section = slow; continue
        if line.startswith("[NORMAL"):
            section = normal; continue
        if line.startswith("["):
            continue
        if section is None:
            continue
        # прибрати маркери паузи, ремарки у [квадратних дужках] та тире діалогу
        parts = [
            re.sub(r"\[[^\]]*\]", "", p).strip(" —–- \t")
            for p in re.split(r"\[(?:пауза|pauza)\]", line, flags=re.I)
        ]
        for p in parts:
            p = re.sub(r"\s{2,}", " ", p).strip()
            if p and not p.startswith(SKIP_PREFIX):
                section.append(p)
    # прибрати підряд-дублікати ("Dobrý deň. [пауза] Dobrý deň." → 1 фраза)
    def dedup(items):
        out = []
        for x in items:
            if not out or out[-1] != x:
                out.append(x)
        return out
    return dedup(slow), dedup(normal)


async def synth(text, voice, rate, out: Path):
    import edge_tts
    out.parent.mkdir(parents=True, exist_ok=True)
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(str(out))


async def build_lesson(lid: str, only_plan=False):
    src = SCRIPTS / f"{lid}.txt"
    if not src.exists():
        raise FileNotFoundError(f"нема скрипта {src}")
    slow, normal = parse_script(src)
    print(f"[{lid}] SLOW={len(slow)} NORMAL={len(normal)}")
    index = {"slow": [], "normal": []}
    tasks = []
    for i, phrase in enumerate(slow, 1):
        fn = f"slow-{i:02d}.mp3"
        index["slow"].append({"text": phrase, "file": fn})
        if not only_plan:
            tasks.append(synth(phrase, FEMALE, "-20%", AUDIO / lid / fn))
    for i, phrase in enumerate(normal, 1):
        fn = f"dialog-{i:02d}.mp3"
        voice = MALE if i % 2 == 1 else FEMALE
        index["normal"].append({"text": phrase, "file": fn, "voice": voice})
        if not only_plan:
            tasks.append(synth(phrase, voice, "+0%", AUDIO / lid / fn))
    if tasks:
        await asyncio.gather(*tasks)
    adir = AUDIO / lid
    adir.mkdir(parents=True, exist_ok=True)
    (adir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{lid}] OK: {adir} (slow={len(slow)}, dialog={len(normal)})")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--plan", action="store_true", help="тільки розпарсити, без TTS")
    a = ap.parse_args()
    ids = ([a.lesson] if a.lesson else sorted(p.stem for p in SCRIPTS.glob("*.txt"))) if (a.lesson or a.all) else []
    if not ids:
        print("вкажи --lesson 001 або --all"); sys.exit(1)
    failed = []
    for lid in ids:
        try:
            await build_lesson(lid, only_plan=a.plan)
        except Exception as e:
            print(f"[{lid}] ПОМИЛКА: {e}")
            failed.append(lid)
    if failed:
        print(f"\nЗБІЙ: {len(failed)} лекцій не озвучено: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
