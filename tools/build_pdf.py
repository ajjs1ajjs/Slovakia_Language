#!/usr/bin/env python3
"""PDF з клікабельним аудіо: текст лекції + аудіо-дошка в кінці.
Кожна фраза на дошці: текст + QR (телефон) + клікабельна зона Play
(Movie-анотація з вбудованим MP3 — грає по кліку в Adobe Acrobat/Reader;
у браузерних переглядачах — скануй QR).
MP3 зберігається ОДИН раз і ділиться між вкладенням (панель Acrobat)
та кнопкою Play.
  python tools/build_pdf.py --lesson 001
  python tools/build_pdf.py --all
Вивід: build/pdf/<ID>.pdf
"""
import argparse, json, re, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdf"
TMP = ROOT / "build" / "tmp"
ARIAL = Path(r"C:\Windows\Fonts\arial.ttf")
ARIAL_B = Path(r"C:\Windows\Fonts\arialbd.ttf")

# --- текстова частина (platypus), без QR-звалища ---
def build_story(lines, W):
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    st = {
        "h1": ParagraphStyle("h1", fontName="Arial-B", fontSize=16, leading=20, spaceAfter=8),
        "h2": ParagraphStyle("h2", fontName="Arial-B", fontSize=13, leading=16, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Arial", fontSize=10, leading=14, spaceAfter=4),
        "cell": ParagraphStyle("cell", fontName="Arial", fontSize=9, leading=12),
        "cellH": ParagraphStyle("cellH", fontName="Arial-B", fontSize=9, leading=12),
    }
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    story, tbl, first = [], [], True
    def flush_tbl():
        nonlocal tbl, first
        if not tbl:
            return
        rows = [[Paragraph(f"<b>{esc(c)}</b>" if first or i == 0 else esc(c),
                           st["cellH"] if (first or i == 0) else st["cell"]) for c in r] for i, r in
                enumerate([[c.strip() for c in re.sub(r"^\||\|$", "", t).split("|")] for t in tbl])]
        if len(rows[0]) > 4:
            rows = [r[:4] for r in rows]
        t = Table(rows, colWidths=[W * x for x in ([0.18, 0.24, 0.28, 0.30][:len(rows[0])])], repeatRows=1)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                               ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0fb")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(t)
        story.append(Spacer(1, 6))
        tbl, first = [], True
    for ln in lines:
        s = ln.strip()
        if s.startswith("# "):
            flush_tbl(); story.append(Paragraph(esc(s[2:]), st["h1"])); continue
        if s.startswith("## ") or re.match(r"^\d+\.\s+[A-ZÁ-ŽІ-Ї]", s) and len(s) < 60 and not s.startswith(("1. —", "2. —", "3. —")):
            flush_tbl(); story.append(Paragraph(esc(re.sub(r"^#*\s*|\d+\.\s*", "", s)), st["h2"])); continue
        if re.match(r"^\|.*\|$", s):
            if re.match(r"^\|[\s:\-|]+\|$", s):
                first = False; continue
            tbl.append(s); continue
        flush_tbl()
        if not s:
            continue
        if s.startswith("---"):
            story.append(HRFlowable(width="100%")); continue
        if re.match(r"^([-*]|\d+\.)\s", s):
            s = "• " + re.sub(r"^([-*]|\d+\.)\s*", "", s)
        story.append(Paragraph(esc(s), st["body"]))
    flush_tbl()
    return story, st

# --- аудіо-дошка (canvas, фіксовані координати для зон Play) ---
CELL_H, COLS, ROWS, M = 170, 2, 4, 42
def build_board(lid, items, qrdir):
    """Малює сторінки дошки. Повертає (шлях, placements[(board_page, rect, fname)])."""
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    try:
        pdfmetrics.registerFont(TTFont("Arial", str(ARIAL)))
        pdfmetrics.registerFont(TTFont("Arial-B", str(ARIAL_B)))
    except Exception:
        pass
    W, H = A4
    cw = (W - 2 * M - 12) / COLS
    TMP.mkdir(parents=True, exist_ok=True)
    path = TMP / f"board-{lid}.pdf"
    c = Canvas(str(path), pagesize=A4)
    placements, idx = [], 0
    total = len(items)
    while idx < total or (idx == 0 and total == 0):
        c.setFont("Arial-B", 14)
        c.drawString(M, H - M, "AUDIÓGRAMA — натисни ▶ Play (Adobe Acrobat Reader)")
        c.setFont("Arial", 9)
        c.setFillGray(0.4)
        c.drawString(M, H - M - 16, "Klikni na bunku = prehrat. QR = mobil. / Клік по клітинці = звук. QR = телефон.")
        c.setFillGray(0)
        for r in range(ROWS):
            for col in range(COLS):
                if idx >= total:
                    break
                tag, e = items[idx]
                x0 = M + col * (cw + 12)
                y1 = H - M - 30 - r * (CELL_H + 8)
                y0 = y1 - CELL_H
                x1 = x0 + cw
                c.setStrokeGray(0.6)
                c.rect(x0, y0, x1 - x0, CELL_H, stroke=1, fill=0)
                c.setFont("Arial-B", 11)
                c.drawString(x0 + 8, y1 - 18, f"▶ Play [{tag}]")
                c.setFont("Arial", 10)
                for j, wl in enumerate(textwrap.wrap(e["text"][:140], 40)[:4]):
                    c.drawString(x0 + 8, y1 - 36 - j * 14, wl)
                c.setFont("Arial", 8)
                c.setFillGray(0.45)
                c.drawString(x0 + 8, y0 + 8, e["file"])
                c.setFillGray(0)
                p = qrdir / (Path(e["file"]).stem + ".png")
                if p.exists():
                    c.drawImage(str(p), x1 - 72, y0 + 24, width=64, height=64)
                placements.append((0, (x0, y0, x1, y1), e["file"]))
                idx += 1
            if idx >= total:
                break
        c.showPage()
        if idx >= total:
            break
    # номер сторінки дошки = кількість showPage-1; перерахуємо placements по факту
    c.save()
    from pypdf import PdfReader
    nb = len(PdfReader(str(path)).pages)
    per = COLS * ROWS
    fixed = [((i // per), rect, fn) for i, (_, rect, fn) in enumerate(placements)]
    assert len(fixed) == total and (nb == (total + per - 1) // per or total == 0)
    return path, fixed

def lesson_pdf(lid: str, md_path: Path):
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (DictionaryObject, NameObject, TextStringObject,
                               ArrayObject, NumberObject, BooleanObject, DecodedStreamObject)
    pdfmetrics.registerFont(TTFont("Arial", str(ARIAL)))
    pdfmetrics.registerFont(TTFont("Arial-B", str(ARIAL_B)))
    idx_path = ROOT / "assets" / "audio" / lid / "index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"slow": [], "normal": []}
    items = [("SLOW", e) for e in index["slow"]] + [("DIALÓG", e) for e in index["normal"]]
    lines = md_path.read_text(encoding="utf-8").splitlines()
    W, H = A4
    story, st = build_story(lines, W - 84)
    TMP.mkdir(parents=True, exist_ok=True)
    content_path = TMP / f"content-{lid}.pdf"
    doc = BaseDocTemplate(str(content_path), pagesize=A4, leftMargin=42, rightMargin=42,
                          topMargin=42, bottomMargin=42, title=f"Lekcia {lid}", author="Slovenčina 0→B2")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame],
        onPage=lambda c, d: (c.setFont("Arial", 8), c.drawCentredString(W / 2, 24, f"{d.page}")))])
    doc.build(story)
    n_content = len(PdfReader(str(content_path)).pages)

    w = PdfWriter()
    w.append(PdfReader(str(content_path)))
    adir = ROOT / "assets" / "audio" / lid
    qrdir = ROOT / "assets" / "qr" / lid
    specs = {}  # fname -> filespec ref (один потік MP3 на всі використання)
    if items:
        board_path, placements = build_board(lid, items, qrdir)
        w.append(PdfReader(str(board_path)))
        for f in adir.glob("*.mp3"):
            stream = DecodedStreamObject()
            stream.set_data(f.read_bytes())
            stream.update({NameObject("/Type"): NameObject("/EmbeddedFile")})
            sref = w._add_object(stream)
            fs = DictionaryObject({
                NameObject("/Type"): NameObject("/Filespec"),
                NameObject("/F"): TextStringObject(f"{lid}/{f.name}"),
                NameObject("/EF"): DictionaryObject({NameObject("/F"): sref}),
            })
            specs[f.name] = w._add_object(fs)
        # дерево вкладень (панель Acrobat)
        names = ArrayObject()
        for fn in sorted(specs):
            names += [TextStringObject(f"{lid}/{fn}"), specs[fn]]
        w._root_object[NameObject("/Names")] = DictionaryObject({
            NameObject("/EmbeddedFiles"): DictionaryObject({NameObject("/Names"): names})})
        # клікабельні зони Play (Movie-анотації)
        nplay = 0
        for bpage, rect, fn in placements:
            if fn not in specs:
                continue
            x0, y0, x1, y1 = rect
            ann = DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Movie"),
                NameObject("/Rect"): ArrayObject([NumberObject(int(x0)), NumberObject(int(y0)),
                                                 NumberObject(int(x1)), NumberObject(int(y1))]),
                NameObject("/Border"): ArrayObject([NumberObject(0)] * 3),
                NameObject("/T"): TextStringObject(f"Play: {fn}"),
                NameObject("/Movie"): DictionaryObject({
                    NameObject("/F"): specs[fn],
                    NameObject("/Poster"): BooleanObject(True)}),
            })
            w.add_annotation(n_content + bpage, ann)
            nplay += 1
    else:
        nplay = 0
    out = OUT / f"{lid}.pdf"
    OUT.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as fh:
        w.write(fh)
    back = PdfReader(str(out))
    got = len(getattr(back, "attachments", {}) or {})
    movies = sum(1 for p in back.pages for a in (p.get("/Annots") or [])
                 if str(a.get_object().get("/Subtype")) == "/Movie")
    print(f"[{lid}] pdf={out.stat().st_size//1024}KB mp3={len(specs)} play={nplay} back_attach={got} back_play={movies}")
    assert got == len(specs), f"[{lid}] attachments mismatch!"
    assert movies == nplay, f"[{lid}] movie annots mismatch!"

def collect():
    out = []
    for d in sorted(ROOT.glob("0*")):
        if d.is_dir():
            for f in sorted(d.glob("*.md")):
                m = re.match(r"(\d+)", f.name)
                if m:
                    out.append((m.group(1), f))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    lessons = collect()
    if a.lesson:
        lessons = [x for x in lessons if x[0] == a.lesson] or sys.exit("нема лекції")
    elif not a.all:
        sys.exit("вкажи --lesson 001 або --all")
    for lid, path in lessons:
        lesson_pdf(lid, path)
    print(f"OK lessons={len(lessons)}")
