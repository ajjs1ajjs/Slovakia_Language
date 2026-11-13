#!/usr/bin/env python3
"""Генерація автономного інтерактивного веб-курсу (HTML + аудіо в будь-якому браузері).

  python tools/build_web.py            # build/web/index.html (використовує ../../assets/)
  python tools/build_web.py --bundle   # копіює assets/foto та assets/audio у build/web/assets/
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "web"

LEVELS = [
    ("00_A0-Zaklady-vymova", "A0", "Основи вимови"),
    ("01_A1-Prezitie", "A1", "Виживання"),
    ("02_A2-Kazdodenny-zivot", "A2", "Щоденне життя"),
    ("03_B1-Nezavislost", "B1", "Незалежність"),
    ("04_B2-Sloboda", "B2", "Вільне спілкування"),
]


def load_sources() -> dict[str, tuple[str, str]]:
    info: dict[str, tuple[str, str]] = {}
    for src in sorted((ROOT / "assets" / "foto").glob("SOURCES_*.md")):
        for line in src.read_text(encoding="utf-8").splitlines():
            if line.startswith("|") and not line.startswith("| file") and not line.startswith("|---"):
                cols = [c.strip() for c in line.strip("|").split("|")]
                if len(cols) >= 4:
                    info[cols[0]] = (cols[2], cols[3])
    return info


def inline_html(s: str) -> str:
    s = re.sub(r"\\([*_`#>\[\]()!\\-])", r"\1", s)
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"<em>\1</em>", s)
    return s


def audio_btn(src: str, label: str = "▶") -> str:
    esc = html.escape(src, quote=True)
    return f'<button type="button" class="play-btn" data-src="{esc}" title="{esc}">{label}</button>'


def render_lesson_html(lid: str, md_path: Path, asset_prefix: str, sources: dict[str, tuple[str, str]]) -> dict:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), md_path.stem)
    idx_path = ROOT / "assets" / "audio" / lid / "index.json"
    audio_idx = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"slow": [], "normal": []}
    norm_files = [e["file"] for e in audio_idx.get("normal", [])]

    parts: list[str] = []
    tbl: list[str] = []
    in_key = False
    in_list = False
    list_tag = "ul"
    dialog_idx = 0
    in_dialog = False

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append(f"</{list_tag}>")
            in_list = False

    def flush_tbl():
        nonlocal tbl
        if not tbl:
            return
        rows = []
        for t in tbl:
            cells = [c.strip() for c in re.sub(r"^\||\|$", "", t).split("|")]
            if all(re.match(r"^:?-{2,}:?$", c.replace(" ", "")) for c in cells):
                continue
            rows.append(cells)
        tbl = []
        if not rows:
            return
        hdr, body = rows[0], rows[1:]
        is_audio_col = len(hdr) >= 5 and re.search(r"audio|▶|слухай", hdr[4], re.I)
        parts.append("<div class='tbl-wrap'><table><thead><tr>")
        for h in hdr:
            parts.append(f"<th>{inline_html(h)}</th>")
        parts.append("</tr></thead><tbody>")
        for r in body:
            r = (r + [""] * len(hdr))[: len(hdr)]
            parts.append("<tr>")
            for ci, c in enumerate(r):
                if is_audio_col and ci == 4:
                    btns = [audio_btn(f"{asset_prefix}/audio/{lid}/{fn}") for fn in re.findall(r"(?:slow|dialog)-\d{2}\.mp3", c)]
                    parts.append("<td>" + (" ".join(btns) if btns else "—") + "</td>")
                else:
                    parts.append(f"<td>{inline_html(c)}</td>")
            parts.append("</tr>")
        parts.append("</tbody></table></div>")

    for raw in lines:
        s = raw.strip()
        if s.startswith("# "):
            continue
        if "<details" in s or "<summary" in s:
            flush_tbl(); close_list()
            if not in_key:
                parts.append("<details class='key-box'><summary>KĽÚČ / Ключі — перевірити себе</summary>")
                in_key = True
            continue
        if "</details>" in s:
            close_list()
            if in_key:
                parts.append("</details>")
                in_key = False
            continue
        if re.match(r"^#{2,4}\s+", s):
            flush_tbl(); close_list()
            if in_key:
                parts.append("</details>"); in_key = False
            hd = re.sub(r"^#{2,4}\s*", "", s)
            in_dialog = bool(re.search(r"DIAL[OÓ]G", hd, re.I))
            parts.append(f"<h3>{inline_html(hd)}</h3>")
            continue
        if re.match(r"^\|.*\|$", s):
            close_list()
            tbl.append(s)
            continue
        flush_tbl()
        if not s:
            close_list()
            continue
        if s.startswith("---"):
            close_list()
            parts.append("<hr>")
            continue
        if re.match(r"^\*\*Úroveň:\*\*|^Úroveň:", s):
            close_list()
            parts.append(f"<div class='meta-bar'>{inline_html(s)}</div>")
            continue
        if re.match(r"^\*\*Kľúč", s):
            close_list()
            if not in_key:
                parts.append("<details class='key-box'><summary>KĽÚČ / Ключі — перевірити себе</summary>")
                in_key = True
            rest = re.sub(r"^\*\*Kľúč[^*]*\*\*\s*:?\s*", "", s).strip()
            if rest:
                parts.append(f"<p>{inline_html(rest)}</p>")
            continue
        if "assets/foto/" in s:
            close_list()
            m = re.search(r"assets/foto/([A-Za-z0-9_.\-]+\.jpg)", s)
            if m:
                fn = m.group(1)
                cap = re.sub(r"`?assets/foto/[A-Za-z0-9_.\-]+\.jpg`?\s*[—–-]?\s*", "", s).strip()
                url, lic = sources.get(fn, ("", ""))
                credit = f" · <a href='{html.escape(url)}' target='_blank' rel='noopener'>{html.escape(lic)}</a>" if url else ""
                parts.append(
                    f"<figure><img src='{asset_prefix}/foto/{fn}' loading='lazy' alt='{html.escape(title)}'>"
                    f"<figcaption>{inline_html(cap)}{credit}</figcaption></figure>"
                )
            continue
        if "audio-scripts/" in s or s.startswith("Джерело: Wikimedia Commons"):
            continue
        if s.startswith(">"):
            close_list()
            parts.append(f"<blockquote>{inline_html(s.lstrip('> ').strip())}</blockquote>")
            continue
        if in_dialog and (re.match(r"^[—–]\s", s) or re.match(r"^\d+\.\s+[—–]", s) or re.match(r"^\d+\.\s+\*\*[^*:]+:\*\*", s)):
            close_list()
            btn = ""
            if dialog_idx < len(norm_files):
                btn = audio_btn(f"{asset_prefix}/audio/{lid}/{norm_files[dialog_idx]}", "▶")
                dialog_idx += 1
            parts.append(f"<div class='dialog-line'>{btn}<span>{inline_html(s)}</span></div>")
            continue
        m_num = re.match(r"^(\d+)\.\s+(.*)$", s)
        m_bul = re.match(r"^\\?[*\-]\s+(.*)$", s)
        if m_num or m_bul:
            want = "ol" if m_num else "ul"
            if not in_list or list_tag != want:
                close_list()
                list_tag = want
                parts.append(f"<{list_tag}>")
                in_list = True
            txt = m_num.group(2) if m_num else m_bul.group(1)
            parts.append(f"<li>{inline_html(txt)}</li>")
            continue
        close_list()
        parts.append(f"<p>{inline_html(s)}</p>")

    flush_tbl(); close_list()
    if in_key:
        parts.append("</details>")

    # Додаткова аудіо-дошка для тренувань
    board_btns = []
    for tag, arr in (("SLOW", audio_idx.get("slow", [])), ("DIALÓG", audio_idx.get("normal", []))):
        for e in arr:
            fn = e["file"]
            board_btns.append(
                f"<div class='board-item'><span class='tag'>{tag}</span>"
                f"{audio_btn(f'{asset_prefix}/audio/{lid}/{fn}', '▶')} "
                f"<span>{html.escape(e['text'])}</span></div>"
            )
    if board_btns:
        parts.append("<details class='board-box'><summary>Повна аудіо-дошка лекції</summary><div class='board-grid'>" + "".join(board_btns) + "</div></details>")

    return {"id": lid, "title": title, "html": "\n".join(parts)}


def build_web(bundle: bool) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if bundle:
        asset_prefix = "assets"
        for sub in ("foto", "audio"):
            dst = OUT / "assets" / sub
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(ROOT / "assets" / sub, dst)
        for src in (OUT / "assets" / "foto").glob("SOURCES_*.md"):
            src.unlink()
    else:
        asset_prefix = "../../assets"

    sources = load_sources()
    lessons = []
    for folder, lv, lv_name in LEVELS:
        dd = ROOT / folder
        if not dd.is_dir():
            continue
        for md in sorted(dd.glob("*.md")):
            m = re.match(r"^(\d{3})-(.+)\.md$", md.name)
            if not m:
                continue
            item = render_lesson_html(m.group(1), md, asset_prefix, sources)
            item["level"] = lv
            item["level_name"] = lv_name
            lessons.append(item)

    data_json = json.dumps(lessons, ensure_ascii=False).replace("</", "<\\/")
    template = f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Slovenčina 0 → B2 — Інтерактивний курс</title>
<style>
:root {{ --blue:#0b4ea2; --bg:#f8fafc; --card:#ffffff; --border:#e2e8f0; --text:#0f172a; --muted:#64748b; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif; background:var(--bg); color:var(--text); display:flex; min-height:100vh; }}
aside {{ width:300px; background:#fff; border-right:1px solid var(--border); display:flex; flex-direction:column; position:sticky; top:0; height:100vh; }}
.brand {{ padding:14px 16px; background:var(--blue); color:#fff; font-weight:700; font-size:16px; }}
.brand small {{ display:block; font-weight:400; opacity:.85; font-size:12px; margin-top:2px; }}
.controls {{ padding:10px; border-bottom:1px solid var(--border); display:flex; flex-direction:column; gap:8px; }}
.controls input {{ width:100%; padding:7px 10px; border:1px solid var(--border); border-radius:6px; font-size:13px; }}
.lvl-tabs {{ display:flex; gap:4px; flex-wrap:wrap; }}
.lvl-tabs button {{ flex:1; border:1px solid var(--border); background:#f1f5f9; border-radius:6px; padding:4px 6px; font-size:12px; cursor:pointer; }}
.lvl-tabs button.active {{ background:var(--blue); color:#fff; border-color:var(--blue); }}
.nav-list {{ overflow-y:auto; flex:1; padding:6px; }}
.nav-item {{ display:flex; align-items:center; gap:6px; width:100%; text-align:left; border:0; background:transparent; padding:7px 8px; border-radius:6px; cursor:pointer; font-size:13px; color:var(--text); }}
.nav-item:hover {{ background:#f1f5f9; }}
.nav-item.active {{ background:#e0ecff; color:var(--blue); font-weight:600; }}
.nav-item .lid {{ font-weight:700; font-size:11px; color:var(--blue); min-width:28px; }}
.nav-item .done {{ margin-left:auto; color:#16a34a; font-size:12px; }}
main {{ flex:1; padding:24px 32px; max-width:960px; margin:0 auto; width:100%; }}
.topbar {{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:16px; flex-wrap:wrap; }}
.topbar h1 {{ margin:0; font-size:24px; color:var(--blue); }}
.done-btn {{ padding:7px 12px; border-radius:8px; border:1px solid var(--border); background:#fff; cursor:pointer; font-size:13px; }}
.done-btn.checked {{ background:#dcfce7; border-color:#16a34a; color:#166534; font-weight:600; }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:22px; box-shadow:0 1px 3px rgba(0,0,0,.04); }}
.meta-bar {{ background:#eaf0fb; color:var(--blue); padding:8px 12px; border-radius:8px; margin-bottom:14px; font-size:14px; }}
h3 {{ background:var(--blue); color:#fff; padding:6px 12px; border-radius:6px; font-size:15px; margin:20px 0 10px; }}
figure {{ margin:10px 0 16px; text-align:center; }}
figure img {{ max-width:100%; max-height:320px; border-radius:8px; object-fit:contain; }}
figcaption {{ font-size:12px; color:var(--muted); margin-top:6px; }}
.tbl-wrap {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; margin:8px 0 14px; font-size:14px; }}
th, td {{ border:1px solid var(--border); padding:7px 9px; text-align:left; vertical-align:top; }}
th {{ background:var(--blue); color:#fff; }}
tr:nth-child(even) td {{ background:#f8fbff; }}
code {{ background:#eef1f6; padding:1px 5px; border-radius:4px; font-size:90%; }}
.dialog-line {{ display:flex; align-items:flex-start; gap:8px; background:#f2f7ff; padding:8px 10px; border-radius:8px; margin:6px 0; }}
.play-btn {{ background:var(--blue); color:#fff; border:0; border-radius:6px; padding:3px 9px; cursor:pointer; font-size:12px; flex-shrink:0; }}
.play-btn.playing {{ background:#16a34a; }}
.key-box, .board-box {{ margin-top:14px; border:1px solid #bbf7d0; background:#f0fdf4; border-radius:8px; padding:10px 12px; }}
.board-box {{ border-color:var(--border); background:#f8fafc; }}
.key-box summary, .board-box summary {{ cursor:pointer; font-weight:600; color:#166534; }}
.board-box summary {{ color:var(--blue); }}
.board-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:8px; margin-top:10px; }}
.board-item {{ background:#fff; border:1px solid var(--border); border-radius:6px; padding:8px; font-size:13px; display:flex; align-items:center; gap:6px; }}
.tag {{ background:var(--blue); color:#fff; font-size:10px; font-weight:700; padding:2px 5px; border-radius:4px; }}
.pager {{ display:flex; justify-content:space-between; margin-top:16px; }}
.pager button {{ padding:8px 14px; border-radius:8px; border:1px solid var(--border); background:#fff; cursor:pointer; font-size:14px; }}
blockquote {{ border-left:4px solid var(--blue); margin:8px 0; padding:4px 12px; color:#334155; background:#f8fafc; }}
@media (max-width: 820px) {{ body {{ flex-direction:column; }} aside {{ width:100%; height:auto; position:static; max-height:42vh; }} main {{ padding:14px; }} }}
</style>
</head>
<body>
<aside>
  <div class="brand">Slovenčina 0 → B2 <small id="progressText">Прогрес: 0 / 111</small></div>
  <div class="controls">
    <input id="search" type="search" placeholder="Пошук лекції чи теми...">
    <div class="lvl-tabs" id="lvlTabs"></div>
  </div>
  <div class="nav-list" id="navList"></div>
</aside>
<main>
  <div class="topbar">
    <h1 id="lessonTitle"></h1>
    <button class="done-btn" id="doneBtn"></button>
  </div>
  <article class="card" id="lessonBody"></article>
  <div class="pager">
    <button id="prevBtn">← Попередня</button>
    <button id="nextBtn">Наступна →</button>
  </div>
</main>
<script>
const LESSONS = {data_json};
let activeLevel = 'ALL', query = '', currentIdx = 0;
let doneSet = new Set(JSON.parse(localStorage.getItem('sk_done') || '[]'));
const player = new Audio();
let activeBtn = null;

function stopBtn() {{ if (activeBtn) {{ activeBtn.classList.remove('playing'); activeBtn.textContent = '▶'; activeBtn = null; }} }}
player.addEventListener('ended', stopBtn);
document.addEventListener('click', (e) => {{
  const b = e.target.closest('.play-btn');
  if (!b) return;
  if (activeBtn === b && !player.paused) {{ player.pause(); stopBtn(); return; }}
  stopBtn();
  activeBtn = b;
  b.classList.add('playing');
  b.textContent = '■';
  player.src = b.dataset.src;
  player.play().catch(() => stopBtn());
}});

function renderTabs() {{
  const lvls = ['ALL', 'A0', 'A1', 'A2', 'B1', 'B2'];
  document.getElementById('lvlTabs').innerHTML = lvls.map(l =>
    `<button class="${{l===activeLevel?'active':''}}" onclick="setLvl('${{l}}')">${{l==='ALL'?'Усі':l}}</button>`
  ).join('');
}}
window.setLvl = (l) => {{ activeLevel = l; renderTabs(); renderNav(); }};

function renderNav() {{
  const q = query.toLowerCase();
  const filtered = LESSONS.filter(x => (activeLevel==='ALL' || x.level===activeLevel) && (!q || x.title.toLowerCase().includes(q) || x.id.includes(q)));
  document.getElementById('navList').innerHTML = filtered.map(x => {{
    const idx = LESSONS.indexOf(x);
    return `<button class="nav-item ${{idx===currentIdx?'active':''}}" onclick="openLesson(${{idx}})">
      <span class="lid">${{x.id}}</span><span>${{x.title.replace(/^\\d+\\s*/, '')}}</span>
      ${{doneSet.has(x.id)?'<span class="done">✓</span>':''}}
    </button>`;
  }}).join('');
  document.getElementById('progressText').textContent = `Прогрес: ${{doneSet.size}} / ${{LESSONS.length}}`;
}}

window.openLesson = (idx) => {{
  currentIdx = Math.max(0, Math.min(LESSONS.length - 1, idx));
  const L = LESSONS[currentIdx];
  location.hash = L.id;
  document.getElementById('lessonTitle').textContent = L.title;
  document.getElementById('lessonBody').innerHTML = L.html;
  const db = document.getElementById('doneBtn');
  const isDone = doneSet.has(L.id);
  db.className = 'done-btn' + (isDone ? ' checked' : '');
  db.textContent = isDone ? '✓ Пройдено' : 'Позначити пройденою';
  document.getElementById('prevBtn').disabled = currentIdx === 0;
  document.getElementById('nextBtn').disabled = currentIdx === LESSONS.length - 1;
  renderNav();
  window.scrollTo(0, 0);
}};

document.getElementById('doneBtn').onclick = () => {{
  const id = LESSONS[currentIdx].id;
  if (doneSet.has(id)) doneSet.delete(id); else doneSet.add(id);
  localStorage.setItem('sk_done', JSON.stringify([...doneSet]));
  openLesson(currentIdx);
}};
document.getElementById('prevBtn').onclick = () => openLesson(currentIdx - 1);
document.getElementById('nextBtn').onclick = () => openLesson(currentIdx + 1);
document.getElementById('search').oninput = (e) => {{ query = e.target.value; renderNav(); }};

const hashId = location.hash.replace('#', '');
const startIdx = Math.max(0, LESSONS.findIndex(x => x.id === hashId));
renderTabs();
openLesson(startIdx);
</script>
</body>
</html>
"""
    (OUT / "index.html").write_text(template, encoding="utf-8")
    print(f"WEB OK: {OUT / 'index.html'} (lessons={len(lessons)}, bundle={bundle})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", action="store_true", help="скопіювати фото та MP3 у build/web/assets")
    a = ap.parse_args()
    build_web(a.bundle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
