#!/usr/bin/env python3
"""Експорт словника курсу (111 лекцій) у колоду Anki (.apkg) зі звуком.

  python tools/build_anki.py
Вивід: build/Slovak-0-B2.apkg
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import tempfile
import time
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "Slovak-0-B2.apkg"

LEVELS = {
    "00_A0-Zaklady-vymova": "A0",
    "01_A1-Prezitie": "A1",
    "02_A2-Kazdodenny-zivot": "A2",
    "03_B1-Nezavislost": "B1",
    "04_B2-Sloboda": "B2",
}

SLOV_HDR = re.compile(r"(?m)^#{2,4}\s*\d*\.?\s*SLOV[IÍ][ČC]KA\b", re.I)
ANY_HDR = re.compile(r"^#{2,4}\s")
AUDIO_REF = re.compile(r"((?:slow|dialog)-\d{2}\.mp3)")


def stable_id(seed: str) -> int:
    return int(hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12], 16)


def parse_vocab() -> list[dict]:
    cards = []
    for folder, lv in LEVELS.items():
        dd = ROOT / folder
        if not dd.is_dir():
            continue
        for md in sorted(dd.glob("*.md")):
            m = re.match(r"^(\d{3})-(.+)\.md$", md.name)
            if not m:
                continue
            lid = m.group(1)
            lines = md.read_text(encoding="utf-8").splitlines()
            title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), md.stem)
            in_slov = False
            for ln in lines:
                if SLOV_HDR.match(ln):
                    in_slov = True
                    continue
                if in_slov and ANY_HDR.match(ln):
                    break
                if not in_slov or not ln.startswith("|"):
                    continue
                if ln.startswith("| SK") or re.match(r"^\|[\s\-:|]+\|$", ln):
                    continue
                cols = [c.strip() for c in ln.strip("|").split("|")]
                if len(cols) < 4 or not cols[0] or not cols[1]:
                    continue
                audio_col = cols[4] if len(cols) > 4 else ""
                m_aud = AUDIO_REF.search(audio_col)
                audio_path = None
                if m_aud:
                    cand = ROOT / "assets" / "audio" / lid / m_aud.group(1)
                    if cand.exists():
                        audio_path = cand
                cards.append({
                    "lid": lid,
                    "level": lv,
                    "title": title,
                    "sk": cols[0],
                    "ua": cols[1],
                    "ipa": cols[2],
                    "tr": cols[3],
                    "audio_path": audio_path,
                })
    return cards


def build_apkg(cards: list[dict], out_path: Path) -> None:
    now = int(time.time())
    model_id = 1710000001001
    deck_id = 1710000002001

    models = {
        str(model_id): {
            "id": model_id,
            "name": "Slovakia_Language_Vocab",
            "type": 0,
            "mod": now,
            "usn": -1,
            "sortf": 0,
            "did": deck_id,
            "tmpls": [
                {
                    "name": "SK -> UA",
                    "ord": 0,
                    "qfmt": (
                        "<div class='meta'>{{Level}} · {{Lesson}}</div>"
                        "<div class='sk'>{{SK}}</div>"
                        "<div class='aud'>{{Audio}}</div>"
                    ),
                    "afmt": (
                        "{{FrontSide}}<hr id='answer'>"
                        "<div class='ua'>{{UA}}</div>"
                        "<div class='ipa'>{{IPA}}</div>"
                        "<div class='tr'>{{Transcription}}</div>"
                    ),
                    "bqfmt": "",
                    "bafmt": "",
                    "did": None,
                    "bfont": "",
                    "bsize": 0,
                }
            ],
            "flds": [
                {"name": "SK", "ord": 0, "sticky": False, "rtl": False, "font": "Arial", "size": 20},
                {"name": "UA", "ord": 1, "sticky": False, "rtl": False, "font": "Arial", "size": 18},
                {"name": "IPA", "ord": 2, "sticky": False, "rtl": False, "font": "Arial", "size": 14},
                {"name": "Transcription", "ord": 3, "sticky": False, "rtl": False, "font": "Arial", "size": 15},
                {"name": "Audio", "ord": 4, "sticky": False, "rtl": False, "font": "Arial", "size": 12},
                {"name": "Level", "ord": 5, "sticky": False, "rtl": False, "font": "Arial", "size": 12},
                {"name": "Lesson", "ord": 6, "sticky": False, "rtl": False, "font": "Arial", "size": 12},
            ],
            "css": (
                ".card { font-family: Arial, sans-serif; text-align: center; color: #1e293b; background: #fff; padding: 18px; }\n"
                ".meta { font-size: 12px; color: #64748b; margin-bottom: 10px; }\n"
                ".sk { font-size: 26px; font-weight: bold; color: #0b4ea2; margin-bottom: 8px; }\n"
                ".ua { font-size: 21px; font-weight: 600; color: #0f172a; margin: 10px 0 6px; }\n"
                ".ipa { font-size: 14px; color: #475569; margin-bottom: 4px; }\n"
                ".tr { font-size: 15px; color: #166534; }\n"
            ),
            "latexPre": "",
            "latexPost": "",
            "req": [[0, "all", [0]]],
        }
    }
    decks = {
        str(deck_id): {
            "id": deck_id,
            "name": "Slovenčina 0 → B2",
            "mod": now,
            "usn": -1,
            "lrnToday": [0, 0],
            "revToday": [0, 0],
            "newToday": [0, 0],
            "timeToday": [0, 0],
            "collapsed": False,
            "browserCollapsed": False,
            "desc": "Курс словацької мови 0 → B2 (111 лекцій)",
            "dyn": 0,
            "conf": 1,
            "extendNew": 10,
            "extendRev": 50,
        }
    }
    dconf = {
        "1": {
            "id": 1,
            "name": "Default",
            "mod": 0,
            "usn": 0,
            "maxTaken": 60,
            "autoplay": True,
            "timer": 0,
            "replayq": True,
            "new": {"bury": True, "delays": [1, 10], "initialFactor": 2500, "ints": [1, 4, 7], "order": 1, "perDay": 20},
            "rev": {"bury": True, "ease4": 1.3, "fuzz": 0.05, "ivlFct": 1, "maxIvl": 36500, "minSpace": 1, "perDay": 200},
            "lapse": {"delays": [10], "leechAction": 0, "leechFails": 8, "minInt": 1, "mult": 0},
        }
    }
    conf = {
        "activeDecks": [deck_id],
        "curDeck": deck_id,
        "newSpread": 0,
        "collapseTime": 1200,
        "timeLim": 0,
        "estTimes": True,
        "dueCounts": True,
        "curModel": str(model_id),
        "nextPos": 1,
        "sortType": "noteFld",
        "sortBackwards": False,
        "addToCur": True,
    }

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "collection.anki2"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE col (
                id integer primary key, crt integer not null, mod integer not null,
                scm integer not null, ver integer not null, dty integer not null,
                usn integer not null, ls integer not null, conf text not null,
                models text not null, decks text not null, dconf text not null, tags text not null
            );
            CREATE TABLE notes (
                id integer primary key, guid text not null, mid integer not null,
                mod integer not null, usn integer not null, tags text not null,
                flds text not null, sfld text not null, csum integer not null,
                flags integer not null, data text not null
            );
            CREATE TABLE cards (
                id integer primary key, nid integer not null, did integer not null,
                ord integer not null, mod integer not null, usn integer not null,
                type integer not null, queue integer not null, due integer not null,
                ivl integer not null, factor integer not null, reps integer not null,
                lapses integer not null, left integer not null, odue integer not null,
                odid integer not null, flags integer not null, data text not null
            );
            CREATE TABLE revlog (
                id integer primary key, cid integer not null, usn integer not null,
                ease integer not null, ivl integer not null, lastIvl integer not null,
                factor integer not null, time integer not null, type integer not null
            );
            CREATE TABLE graves (usn integer not null, oid integer not null, type integer not null);
            """
        )
        cur.execute(
            "INSERT INTO col VALUES (1,?,?,?,?,0,0,0,?,?,?,?,?)",
            (now, now, now * 1000, 11, json.dumps(conf), json.dumps(models), json.dumps(decks), json.dumps(dconf), "{}"),
        )

        media_map = {}
        media_files = {}
        seen_media = {}

        for idx, c in enumerate(cards, 1):
            aud_tag = ""
            if c["audio_path"] is not None:
                mname = f"{c['lid']}-{c['audio_path'].name}"
                if mname not in seen_media:
                    midx = str(len(media_map))
                    media_map[midx] = mname
                    media_files[midx] = c["audio_path"]
                    seen_media[mname] = mname
                aud_tag = f"[sound:{mname}]"

            fields = [c["sk"], c["ua"], c["ipa"], c["tr"], aud_tag, c["level"], c["title"]]
            flds = "\x1f".join(fields)
            csum = int(hashlib.sha1(c["sk"].encode("utf-8")).hexdigest()[:8], 16)
            nid = 1710000100000 + idx
            cid = 1710000200000 + idx
            guid = hashlib.sha1(f"{c['lid']}:{idx}:{c['sk']}".encode("utf-8")).hexdigest()[:10]
            tags = f" Slovak_0_B2 {c['level']} L{c['lid']} "
            cur.execute(
                "INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,0,'')",
                (nid, guid, model_id, now, -1, tags, flds, c["sk"], csum),
            )
            cur.execute(
                "INSERT INTO cards VALUES (?,?,?,0,?,?,0,0,?,0,0,0,0,0,0,0,0,'')",
                (cid, nid, deck_id, now, -1, idx),
            )

        conn.commit()
        conn.close()

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_path, "collection.anki2")
            zf.writestr("media", json.dumps(media_map, ensure_ascii=False))
            for midx, mpath in media_files.items():
                zf.write(mpath, midx)

    print(f"ANKI OK: {out_path} (cards={len(cards)}, audio={len(media_files)}, size={out_path.stat().st_size // 1024}KB)")


def main() -> int:
    cards = parse_vocab()
    if not cards:
        print("ERROR: словникових карток не знайдено")
        return 1
    build_apkg(cards, OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
