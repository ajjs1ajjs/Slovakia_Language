#!/usr/bin/env python3
"""PDF з інтегрованим аудіо: один PDF на лекцію (текст + QR + MP3-attachments).
MP3 вкладаються у PDF як attachments (Acrobat/Reader: панель вкладень -> Play),
а QR-коди поруч із фразами відкривають ті самі MP3 з телефона.
  python tools/build_pdf.py --lesson 001
  python tools/build_pdf.py --all
Вивід: build/pdf/<ID>.pdf
"""
import argparse, io, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdf"
ARIAL = Path(r"C:\Windows\Fonts\arial.ttf")
ARIAL_B = Path(r"C:\Windows\Fonts\arialbd.ttf")

def build_story(lines, W):
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
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
        # прибрати колонку Audio (остання), якщо є
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

def lesson_pdf(lid: str, md_path: Path):
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                    Spacer, Image as RLImage)
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Arial", str(ARIAL)))
    pdfmetrics.registerFont(TTFont("Arial-B", str(ARIAL_B)))
    idx_path = ROOT / "assets" / "audio" / lid / "index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"slow": [], "normal": []}
    lines = md_path.read_text(encoding="utf-8").splitlines()
    W, H = A4
    story, st = build_story(lines, W - 84)
    # QR-блок: кожна аудіо-фраза + її QR
    qrdir = ROOT / "assets" / "qr" / lid
    items = [("SLOW", e) for e in index["slow"]] + [("DIALÓG", e) for e in index["normal"]]
    if items:
        story.append(Paragraph("AUDIÓGRAMA / Аудіо з QR (скануй телефоном)", st["h2"]))
        for tag, e in items:
            p = qrdir / (Path(e["file"]).stem + ".png")
            if p.exists():
                story.append(RLImage(str(p), width=42, height=42))
            story.append(Paragraph(f"[{tag}] {e['file']}", st["body"]))
    out = OUT / f"{lid}.pdf"
    OUT.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(out), pagesize=A4, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42,
                          title=f"Lekcia {lid}", author="Slovenčina 0→B2")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame],
        onPage=lambda c, d: (c.setFont("Arial", 8), c.drawCentredString(W / 2, 24, f"{d.page}")))])
    doc.build(story)
    # вкласти MP3 як attachments (pypdf)
    from pypdf import PdfReader, PdfWriter
    r, w = PdfReader(str(out)), PdfWriter()
    w.append(r)
    adir = ROOT / "assets" / "audio" / lid
    n = 0
    for tag, e in items:
        f = adir / e["file"]
        if f.exists():
            w.add_attachment(e["file"], f.read_bytes())
            n += 1
    with open(out, "wb") as fh:
        w.write(fh)
    # перевірка назад
    back = PdfReader(str(out))
    got = len(getattr(back, "attachments", {}) or {})
    print(f"[{lid}] pdf={out.stat().st_size//1024}KB mp3_in={n} attached_back={got}" + ("" if n else " (без аудіо: тест)"))
    assert got == n, f"[{lid}] attachments mismatch!"

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
