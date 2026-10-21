#!/usr/bin/env python3
"""Генерація MP3 + QR для курсу Slovakia_Language.
Парсить assets/audio-scripts/*.txt ([SLOW]/[NORMAL]), озвучує edge-tts (sk-SK),
кладe в assets/audio/<ID>/ + QR в assets/qr/<ID>/.

Використання:
  python tools/generate_audio.py --lesson 001            # одна лекція (демо)
  python tools/generate_audio.py --all                   # всі 111 (довго!)
  python tools/generate_audio.py --all --base-url https://USER.github.io/REPO/audio
Голоси: SLOW — ViktoriaNeural -20%, NORMAL — діалог по черзі Anton/Viktoria.
Без інтернету скрипт тільки друкує план (dry-run).
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
QRS = ROOT / "assets" / "qr"
FEMALE = "sk-SK-ViktoriaNeural"
MALE = "sk-SK-LukasNeural"

SKIP_PREFIX = ("LEKCIA", "LEKCI", "Інструкція", "Голос", "Файли", "Інструкц")

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
        # прибрати маркер паузи, розбити на фрази, почистити тире діалогу
        parts = [p.strip(" —–- \t") for p in re.split(r"\[пауза\]", line)]
        for p in parts:
            p = p.strip()
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

def make_qr(text, out: Path):
    import qrcode
    out.parent.mkdir(parents=True, exist_ok=True)
    qrcode.make(text).save(str(out))

async def build_lesson(lid: str, base_url: str, only_plan=False):
    src = SCRIPTS / f"{lid}.txt"
    if not src.exists():
        print(f"[{lid}] нема скрипта, пропуск")
        return
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
    # індекс + QR
    adir = AUDIO / lid
    adir.mkdir(parents=True, exist_ok=True)
    (adir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    if not only_plan:
        for entry in index["slow"] + index["normal"]:
            url = f"{base_url}/{lid}/{entry['file']}" if base_url else f"audio/{lid}/{entry['file']}"
            make_qr(url, QRS / lid / (Path(entry["file"]).stem + ".png"))
    print(f"[{lid}] OK: {AUDIO/lid} + {QRS/lid}")

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--base-url", default="")
    ap.add_argument("--plan", action="store_true", help="тільки розпарсити, без TTS")
    a = ap.parse_args()
    ids = ([a.lesson] if a.lesson else sorted(p.stem for p in SCRIPTS.glob("*.txt"))) if (a.lesson or a.all) else []
    if not ids:
        print("вкажи --lesson 001 або --all"); sys.exit(1)
    for lid in ids:
        try:
            await build_lesson(lid, a.base_url.rstrip("/"), only_plan=a.plan)
        except Exception as e:
            print(f"[{lid}] ПОМИЛКА: {e}")

if __name__ == "__main__":
    asyncio.run(main())
