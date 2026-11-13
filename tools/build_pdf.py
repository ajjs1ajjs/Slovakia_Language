#!/usr/bin/env python3
"""Гарний PDF курсу: текст + фото + аудіо-дошка з динаміками (PCM 22050Hz 16-bit, клік = голос).
  python tools/build_pdf.py --lesson 001   # одна лекція
  python tools/build_pdf.py --all          # всі лекції
  python tools/build_pdf.py --full         # + обкладинка, зміст, закладки, весь курс одним файлом
Вивід: build/pdf/<ID>.pdf, build/Slovak-0-B2-full.pdf
"""
import argparse, json, re, sys, textwrap
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "pdf"
TMP = ROOT / "build" / "tmp"
FOTO = ROOT / "assets" / "foto"
BLUE = "#0b4ea2"


def find_font(is_bold: bool):
    filename = "arialbd.ttf" if is_bold else "arial.ttf"
    dejavu = "DejaVuSans-Bold.ttf" if is_bold else "DejaVuSans.ttf"
    liberation = "LiberationSans-Bold.ttf" if is_bold else "LiberationSans-Regular.ttf"
    freesans = "FreeSansBold.ttf" if is_bold else "FreeSans.ttf"

    candidates = [
        ROOT / "assets" / "fonts" / dejavu,
        ROOT / "assets" / "fonts" / filename,
        ROOT / "assets" / "fonts" / liberation,
        Path(f"/usr/share/fonts/truetype/dejavu/{dejavu}"),
        Path(f"/usr/share/fonts/dejavu/{dejavu}"),
        Path(r"C:\Windows\Fonts") / filename,
        Path(f"/usr/share/fonts/truetype/msttcorefonts/{filename}"),
        Path(f"/usr/share/fonts/truetype/liberation/{liberation}"),
        Path(f"/usr/share/fonts/liberation-sans/{liberation}"),
        Path(f"/usr/share/fonts/truetype/freefont/{freesans}"),
        Path(f"/System/Library/Fonts/Supplemental/{filename}"),
        Path(f"/Library/Fonts/{filename}"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def register_fonts() -> None:
    """Register Arial pair or compatible free font (cross-platform)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    reg = find_font(is_bold=False)
    bold = find_font(is_bold=True)
    if not reg or not bold:
        raise FileNotFoundError(
            "Шрифт не знайдено (Arial або LiberationSans/DejaVuSans). "
            "Встановіть шрифти або покладіть arial.ttf та arialbd.ttf у assets/fonts/"
        )
    pdfmetrics.registerFont(TTFont("Arial", str(reg)))
    pdfmetrics.registerFont(TTFont("Arial-B", str(bold)))

LEVELS = {"00_A0-Zaklady-vymova": ("A0", "Основи вимови"),
          "01_A1-Prezitie": ("A1", "Виживання"),
          "02_A2-Kazdodenny-zivot": ("A2", "Щоденне життя"),
          "03_B1-Nezavislost": ("B1", "Незалежність"),
          "04_B2-Sloboda": ("B2", "Вільне спілкування")}

# окремі рядки-сміття (джерела фото, заглушки) — пропускаємо цілком
JUNK_LINE = re.compile(r"^(Поки фото|Unsplash|Джерело:)", re.I)
# заголовок QR-секції (вона завжди остання — далі пропускаємо все)
QR_HEAD = re.compile(r"^#{1,4}\s*(\d+\.\s*)?QR\b", re.I)
# рядки всередині QR-секції
QR_TAIL = re.compile(r"QR\s*(→|->|до|к\s*MP3)|кнопка Play|Play \(Adobe\)|для телефона|скани QR", re.I)


def md_inline(s: str) -> str:
    s = re.sub(r"\\([*_`#>\[\]()!\\-])", r"\1", s)  # \* -> *
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"`([^`]+)`", r'<font backColor="#eef1f6">\1</font>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"<i>\1</i>", s)
    return s


def styles():
    from reportlab.lib.styles import ParagraphStyle
    return {
        "h1": ParagraphStyle("h1", fontName="Arial-B", fontSize=18, leading=22,
                             textColor=BLUE, spaceAfter=2),
        "info": ParagraphStyle("info", fontName="Arial", fontSize=10, leading=14,
                               textColor="#0b4ea2", backColor="#eaf0fb",
                               borderPadding=(6, 6, 6), spaceAfter=8),
        "h2": ParagraphStyle("h2", fontName="Arial-B", fontSize=13, leading=16,
                             textColor="#ffffff", backColor=BLUE,
                             borderPadding=(5, 6, 5), spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Arial", fontSize=10, leading=14, spaceAfter=4),
        "dialog": ParagraphStyle("dialog", fontName="Arial", fontSize=10, leading=14,
                                 spaceAfter=4, leftIndent=8, borderPadding=5,
                                 backColor="#f2f7ff"),
        "quote": ParagraphStyle("quote", fontName="Arial", fontSize=10, leading=14,
                                spaceAfter=4, leftIndent=12, textColor="#475467",
                                borderPadding=(0, 0, 0, 8), borderColor=BLUE),
        "warn": ParagraphStyle("warn", fontName="Arial", fontSize=10, leading=14,
                               spaceAfter=4, leftIndent=12, textColor="#664d03",
                               backColor="#fff7e0", borderPadding=(6, 6, 6)),
        "bullet": ParagraphStyle("bullet", fontName="Arial", fontSize=10, leading=14,
                                 spaceAfter=3, leftIndent=16, firstLineIndent=0),
        "keyH": ParagraphStyle("keyH", fontName="Arial-B", fontSize=11, leading=14,
                               textColor="#166534", spaceBefore=8, spaceAfter=4),
        "key": ParagraphStyle("key", fontName="Arial", fontSize=10, leading=14,
                              spaceAfter=3, leftIndent=16, textColor="#14532d",
                              backColor="#eef7ee", borderPadding=(4, 4, 4)),
        "note": ParagraphStyle("note", fontName="Arial", fontSize=9, leading=12,
                               textColor="#667085", spaceAfter=4, leftIndent=8),
        "foot": ParagraphStyle("foot", fontName="Arial", fontSize=9, leading=12,
                               textColor="#667085", spaceAfter=4),
        "caption": ParagraphStyle("caption", fontName="Arial", fontSize=9, leading=12,
                                  textColor="#475467", alignment=1, spaceAfter=8),
        "cell": ParagraphStyle("cell", fontName="Arial", fontSize=9, leading=12),
        "cellH": ParagraphStyle("cellH", fontName="Arial-B", fontSize=9, leading=12,
                                textColor="#ffffff"),
        "cellS": ParagraphStyle("cellS", fontName="Arial", fontSize=8, leading=10),
        "cellSH": ParagraphStyle("cellSH", fontName="Arial-B", fontSize=8, leading=10,
                                 textColor="#ffffff"),
    }


def foto_flowable(fname: str, W):
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.utils import ImageReader
    p = FOTO / fname
    if not p.exists():
        return None
    try:
        iw, ih = ImageReader(str(p)).getSize()
    except Exception:
        return None
    w = min(W, 340)
    h = w * ih / iw
    if h > 250:
        h = 250
        w = h * iw / ih
    img = RLImage(str(p), width=w, height=h)
    img.hAlign = "CENTER"
    return img


def clean_caption(cap: str) -> str:
    cap = re.sub(r"Джерело:.*$", "", cap).strip()
    cap = re.sub(r"Unsplash[^.!\n]*[.!\n]?", "", cap).strip()
    cap = re.sub(r"або згенерувати AI\.?", "", cap).strip()
    cap = re.sub(r"\s{2,}", " ", cap).strip(" —–- ,.")
    return cap


def col_widths(ncols: int, header, W):
    if ncols == 2:
        return [W * 0.30, W * 0.70]
    if ncols == 3:
        return [W * 0.20, W * 0.35, W * 0.45]
    if ncols == 4:
        if header and header[0].strip().upper() == "SK":
            return [W * 0.20, W * 0.24, W * 0.26, W * 0.30]
        return [W * 0.16, W * 0.28, W * 0.28, W * 0.28]
    if ncols == 5:
        return [W * 0.14, W * 0.24, W * 0.18, W * 0.22, W * 0.22]
    return [W * 0.12, W * 0.22, W * 0.14, W * 0.18, W * 0.16, W * 0.18][:ncols]


def build_story(lines, W):
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib import colors
    st = styles()
    story, tbl = [], []
    blue = colors.HexColor(BLUE)
    skip_qr, in_key = False, False

    def flush_tbl():
        nonlocal tbl
        if not tbl:
            return
        data = []
        for t in tbl:
            cells = [c.strip() for c in re.sub(r"^\||\|$", "", t).split("|")]
            if re.match(r"^:?-{2,}:?$", cells[0].replace(" ", "")) and all(
                    re.match(r"^:?-{2,}:?$", c.replace(" ", "")) for c in cells):
                continue  # рядок-розділювач --- не дані
            data.append(cells)
        tbl = []
        if not data:
            return
        hdr, rows = data[0], data[1:]
        n = len(hdr)
        # 5-та колонка Audio/QR у словниках — звук живе на аудіо-дошці, колонку ховаємо
        if n == 5 and re.search(r"audio|QR|▶|слухай", hdr[4], re.I):
            hdr, rows = hdr[:4], [r[:4] for r in rows]
            n = 4
        small = n > 4
        cs, ch = (st["cellS"], st["cellSH"]) if small else (st["cell"], st["cellH"])
        prow = [[Paragraph("<b>" + md_inline(c) + "</b>", ch) for c in hdr]]
        for r in rows:
            r = (r + [""] * n)[:n]
            prow.append([Paragraph(md_inline(c), cs) for c in r])
        t = Table(prow, colWidths=col_widths(n, hdr, W), repeatRows=1)
        style = [("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                 ("BACKGROUND", (0, 0), (-1, 0), blue),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LEFTPADDING", (0, 0), (-1, -1), 6),
                 ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                 ("TOPPADDING", (0, 0), (-1, -1), 4),
                 ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                 ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                  [colors.white, colors.HexColor("#f6f9ff")])]
        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 6))

    for ln in lines:
        s = ln.strip()
        if skip_qr:
            continue
        if QR_HEAD.search(s) or s.startswith("[QR") or QR_TAIL.search(s):
            if QR_HEAD.search(s):
                skip_qr = True  # QR-секція завжди остання
            continue
        if "<details" in s or "<summary" in s:
            flush_tbl()
            story.append(Paragraph("KĽÚČ / Ключі — перевір себе", st["keyH"]))
            in_key = True
            continue
        if "</details>" in s:
            in_key = False
            continue
        if JUNK_LINE.match(s):
            continue
        if s.startswith("# "):
            flush_tbl()
            story.append(Paragraph(md_inline(s[2:]), st["h1"]))
            story.append(HRFlowable(width="100%", thickness=2, color=blue, spaceAfter=6))
            continue
        if re.match(r"^#{2,4}\s+", s):
            flush_tbl()
            in_key = False
            story.append(Paragraph(md_inline(re.sub(r"^#{2,4}\s*", "", s)), st["h2"]))
            continue
        if re.match(r"^\d+\.\s+[A-ZÁ-ŽІ-Ї]", s) and len(s) < 60 and "—" not in s[:20]:
            flush_tbl()
            story.append(Paragraph(md_inline(re.sub(r"^\d+\.\s*", "", s)), st["h2"]))
            continue
        if re.match(r"^\|.*\|$", s):
            tbl.append(s)
            continue
        flush_tbl()
        if not s:
            continue
        if s.startswith("---"):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=6))
            continue
        if re.match(r"^\*\*Úroveň:\*\*|^Úroveň:", s):
            story.append(Paragraph(md_inline(s), st["info"]))
            continue
        if re.match(r"^\*\*Kľúč", s):
            story.append(Paragraph("KĽÚČ / Ключі — перевір себе", st["keyH"]))
            rest = re.sub(r"^\*\*Kľúč[^*]*\*\*\s*", "", s).strip()
            if rest:
                t = re.sub(r"^([-*]|\d+\.)\s*", "", rest)
                story.append(Paragraph("✓  " + md_inline(t), st["key"]))
            in_key = True
            continue
        if "assets/foto/" in s:
            m = re.search(r"assets/foto/([A-Za-z0-9_.\-]+\.jpg)", s)
            if m:
                img = foto_flowable(m.group(1), W)
                if img:
                    story.append(img)
                else:
                    story.append(Paragraph("FOTO: " + m.group(1), st["note"]))
                cap = clean_caption(re.sub(r"`?assets/foto/[A-Za-z0-9_.\-]+\.jpg`?\s*[—–-]?\s*", "", s).strip())
                if cap:
                    story.append(Paragraph(md_inline(cap), st["caption"]))
                continue
        if "audio-scripts/" in s:
            story.append(Paragraph(
                "Аудіо до цієї лекції — в кінці лекції (аудіо-дошка): "
                "клік по динаміку в Adobe Reader.", st["note"]))
            continue
        if s.startswith("&gt;") or ln.strip().startswith(">"):
            txt = re.sub(r"^&gt;|^>", "", s).strip()
            story.append(Paragraph(md_inline(txt),
                                   st["warn"] if txt.startswith("Увага") else st["quote"]))
            continue
        if re.match(r"^[—–]\s", s) or re.match(r"^\d+\.\s+[—–]", s) or re.match(r"^\d+\.\s+\*\*[^*:]+:\*\*", s):
            t = re.sub(r"^\d+\.\s*", "", s)
            story.append(Paragraph(md_inline(t), st["dialog"]))
            continue
        if in_key:
            t = re.sub(r"^([-*]|\d+\.)\s*", "", s)
            story.append(Paragraph("✓  " + md_inline(t), st["key"]))
            continue
        if re.match(r"^(\\?[*\-]|\d+\.)\s", s):
            m_num = re.match(r"^(\d+\.)\s+(.*)$", s)
            if m_num:
                story.append(Paragraph(f"<b>{m_num.group(1)}</b>  " + md_inline(m_num.group(2)), st["bullet"]))
            else:
                t = re.sub(r"^\\?[*\-]\s*", "", s)
                if s.startswith("\\"):
                    story.append(Paragraph(md_inline(t), st["foot"]))
                else:
                    story.append(Paragraph("•  " + md_inline(t), st["bullet"]))
            continue
        story.append(Paragraph(md_inline(s), st["body"]))
    flush_tbl()
    return story, st

# --- аудіо-дошка ---
# УВАГА: SPK_W/SPK_H — єдине джерело розміру динаміка.
# І малюнок, і клікабельна Sound-зона беруться звідси — рухати тільки разом.
CELL_H, COLS, ROWS, M = 170, 2, 4, 42
SPK_W, SPK_H = 44, 26


def build_board(lid, items):
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as _colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    try:
        register_fonts()
    except Exception:
        pass
    W, H = A4
    blue = _colors.HexColor(BLUE)
    cw = (W - 2 * M - 12) / COLS
    TMP.mkdir(parents=True, exist_ok=True)
    path = TMP / f"board-{lid}.pdf"
    c = Canvas(str(path), pagesize=A4)
    placements, idx, total, bp = [], 0, len(items), 0
    while idx < total:
        bp += 1
        c.setFont("Arial-B", 14)
        c.setFillColor(blue)
        c.drawString(M, H - M, f"AUDIÓGRAMA {lid} — klikni na reproduktor = zvuk")
        c.setFillGray(0)
        c.setFont("Arial", 9)
        c.setFillGray(0.4)
        c.drawString(M, H - M - 16, "Pocuvaj v Adobe Acrobat Reader: klik na ikonu reproduktora.")
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
                c.setStrokeColor(_colors.HexColor("#8aa4c8"))
                c.rect(x0, y0, x1 - x0, CELL_H, stroke=1, fill=0)
                c.setFillColor(blue)
                c.rect(x0, y0 + CELL_H - 26, 76, 26, stroke=0, fill=1)
                c.setFillColor(_colors.white)
                c.setFont("Arial-B", 11)
                c.drawString(x0 + 8, y0 + CELL_H - 19, tag)
                c.setFillColor(_colors.black)
                c.setFont("Arial", 10)
                for j, wl in enumerate(textwrap.wrap(e["text"][:160], 44)[:3]):
                    c.drawString(x0 + 8, y1 - 36 - j * 14, wl)
                sx0, sy0 = x0 + 8, y0 + 30
                # намальованого динаміка нема навмисно: єдиний візуал — /AP
                # анотації (той самий прямокутник), щоб не було подвоєння
                c.setFont("Arial", 9)
                c.setFillGray(0.35)
                c.drawString(sx0 + 52, sy0 + 9, "hrať / слухай")
                assert sx0 + SPK_W <= x1 and sy0 + SPK_H <= y1, "динамік виліз за клітинку"
                placements.append((0, (sx0, sy0, sx0 + SPK_W, sy0 + SPK_H), e["file"]))
                c.setFont("Arial", 8)
                c.setFillGray(0.45)
                c.drawString(x0 + 8, y0 + 8, e["file"])
                c.setFillGray(0)
                idx += 1
            if idx >= total:
                break
        c.setFont("Arial", 8)
        c.setFillGray(0.5)
        c.drawCentredString(W / 2, 24, f"Lekcia {lid} · audiodoska · {bp}")
        c.setFillGray(0)
        c.showPage()
        if idx >= total:
            break
    c.save()
    per = COLS * ROWS
    fixed = [((i // per), rect, fn) for i, (_, rect, fn) in enumerate(placements)]
    assert len(fixed) == total
    return path, fixed


def lesson_title(md_path: Path) -> str:
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return md_path.stem


def lesson_pdf(lid: str, md_path: Path):
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as _colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (DictionaryObject, NameObject, TextStringObject,
                               ArrayObject, NumberObject, DecodedStreamObject)
    register_fonts()
    idx_path = ROOT / "assets" / "audio" / lid / "index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"slow": [], "normal": []}
    items = [("SLOW", e) for e in index["slow"]] + [("DIALÓG", e) for e in index["normal"]]
    lines = md_path.read_text(encoding="utf-8").splitlines()
    W, H = A4
    title = lesson_title(md_path)
    story, st = build_story(lines, W - 84)
    TMP.mkdir(parents=True, exist_ok=True)
    content_path = TMP / f"content-{lid}.pdf"
    blue = _colors.HexColor(BLUE)

    def on_page(canv, doc):
        canv.saveState()
        canv.setFont("Arial", 8)
        canv.setFillGray(0.5)
        canv.drawString(42, H - 30, f"Slovenčina 0 → B2 · {lid}")
        canv.setStrokeColor(blue)
        canv.setLineWidth(0.7)
        canv.line(42, H - 35, W - 42, H - 35)
        canv.setFillGray(0)
        canv.setFont("Arial", 8)
        canv.drawCentredString(W / 2, 24, f"Lekcia {lid}  ·  {doc.page}")
        canv.restoreState()

    doc = BaseDocTemplate(str(content_path), pagesize=A4, leftMargin=42, rightMargin=42,
                          topMargin=52, bottomMargin=42, title=f"Lekcia {lid} — {title}",
                          author="Slovenčina 0→B2")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])
    doc.build(story)
    n_content = len(PdfReader(str(content_path)).pages)

    w = PdfWriter()
    w.append(PdfReader(str(content_path)))
    udir = ROOT / "build" / "wav22050" / lid
    if items and not udir.exists():
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "tools" / "make_pcm.py"),
                        "--lesson", lid], check=True)
    nplay = 0
    missing = []
    if items:
        board_path, placements = build_board(lid, items)
        w.append(PdfReader(str(board_path)))
        # власний вигляд динаміка (/AP): Acrobat показує наш значок,
        # не підміняє своїм і не "бруднить" файл (не питає збереження)
        ap_content = (f"0.918 0.941 0.984 rg 0 0 {SPK_W} {SPK_H} re f\n"
                      f"0.541 0.643 0.784 RG 1 w 0.5 0.5 {SPK_W - 1} {SPK_H - 1} re S\n"
                      "0.043 0.306 0.635 rg 9 6 m 9 20 l 21 13 l h f\n"
                      "0.043 0.306 0.635 RG 1.4 w 24 9 m 28 13 l 24 17 l S\n"
                      "26 6 m 32 13 l 26 20 l S\n").encode("ascii")
        ap = DecodedStreamObject()
        ap.set_data(ap_content)
        ap.update({NameObject("/Type"): NameObject("/XObject"),
                   NameObject("/Subtype"): NameObject("/Form"),
                   NameObject("/BBox"): ArrayObject([NumberObject(0), NumberObject(0),
                                                    NumberObject(SPK_W), NumberObject(SPK_H)]),
                   NameObject("/Resources"): DictionaryObject()})
        ap_ref = w._add_object(ap)
        for bpage, rect, fn in placements:
            u = udir / (fn + ".pcm")
            if not u.exists():
                missing.append(fn)
                continue
            stream = DecodedStreamObject()
            stream.set_data(u.read_bytes())
            stream.update({NameObject("/Type"): NameObject("/Sound"),
                           NameObject("/R"): NumberObject(22050),
                           NameObject("/C"): NumberObject(1),
                           NameObject("/B"): NumberObject(16),
                           NameObject("/E"): NameObject("/Signed")})
            sref = w._add_object(stream)
            x0, y0, x1, y1 = rect
            w.add_annotation(n_content + bpage, DictionaryObject({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Sound"),
                # Locked=128: грати можна, рухати/видаляти — ні (інакше файл "брудниться")
                NameObject("/F"): NumberObject(128),
                NameObject("/Rect"): ArrayObject([NumberObject(int(x0)), NumberObject(int(y0)),
                                                  NumberObject(int(x1)), NumberObject(int(y1))]),
                NameObject("/T"): TextStringObject(f"Zvuk: {fn}"),
                NameObject("/AP"): DictionaryObject({NameObject("/N"): ap_ref}),
                NameObject("/Sound"): sref}))
            nplay += 1
    if missing:
        raise RuntimeError(f"[{lid}] без PCM лишились {len(missing)} записів: {', '.join(missing[:5])}"
                           f" — перезапусти tools/make_pcm.py --lesson {lid}")
    out = OUT / f"{lid}.pdf"
    OUT.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as fh:
        w.write(fh)
    back = PdfReader(str(out))
    sounds = sum(1 for p in back.pages for a in (p.get("/Annots") or [])
                 if str(a.get_object().get("/Subtype")) == "/Sound")
    print(f"[{lid}] pdf={out.stat().st_size//1024}KB zvukov={nplay} back={sounds}")
    assert sounds == nplay, f"[{lid}] sound annots mismatch!"


def collect():
    out = []
    for d, (lv, _) in LEVELS.items():
        dd = ROOT / d
        if not dd.is_dir():
            continue
        for f in sorted(dd.glob("*.md")):
            m = re.match(r"(\d+)", f.name)
            if not m:
                continue
            out.append({"id": m.group(1), "title": lesson_title(f), "level": lv,
                        "dir": d, "path": f})
    return out


def course_stats(meta):
    n_audio = 0
    for m in meta:
        idx = ROOT / "assets" / "audio" / m["id"] / "index.json"
        if idx.exists():
            try:
                j = json.loads(idx.read_text(encoding="utf-8"))
                n_audio += len(j.get("slow", [])) + len(j.get("normal", []))
            except Exception:
                pass
    n_foto = len(list((ROOT / "assets" / "foto").glob("*.jpg")))
    return len(meta), n_audio, n_foto


def expected_sounds(meta):
    _, n_audio, _ = course_stats(meta)
    return n_audio


def build_front(meta, starts):
    """Обкладинка + зміст. Повертає (шлях, toc_links) для клікабельних посилань у змісті."""
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                    Spacer, Table, TableStyle, HRFlowable, PageBreak, Flowable)
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    register_fonts()
    st = styles()
    blue = colors.HexColor(BLUE)
    toc_links = []

    class TocRow(Flowable):
        def __init__(self, tbl, lid):
            super().__init__()
            self.tbl = tbl
            self.lid = lid
            self.w = self.h = 0

        def wrap(self, aw, ah):
            self.w, self.h = self.tbl.wrap(aw, ah)
            return self.w, self.h

        def draw(self):
            self.tbl.drawOn(self.canv, 0, 0)
            x0, y0 = self.canv.absolutePosition(0, 0)
            toc_links.append((self.canv.getPageNumber() - 1, (x0, y0, x0 + self.w, y0 + self.h), self.lid))

    story = []
    story.append(Spacer(1, 90))
    story.append(Paragraph("Slovenčina 0 → B2", ParagraphStyle("cov",
        parent=st["h1"], fontSize=34, leading=40, alignment=1)))
    story.append(Paragraph("Словацька з нуля до вільного спілкування", ParagraphStyle("cov2",
        parent=st["body"], fontSize=14, leading=18, alignment=1, textColor="#344054")))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="30%", thickness=3, color=blue, spaceAfter=12, hAlign="CENTER"))
    nl, na, nf = course_stats(meta)
    story.append(Paragraph(f"{nl} lekcií  •  ~3000 slov  •  {na} nahrávok  •  {nf} fotografií",
        ParagraphStyle("cov3", parent=st["body"], fontSize=11, leading=15, alignment=1)))
    story.append(Spacer(1, 24))
    story.append(Paragraph("Ako používať / Як користуватись", ParagraphStyle(
        "covh", parent=st["h2"], fontSize=14, alignment=1)))
    for t in ("<b>1.</b> Відкрий у безкоштовному <b>Adobe Acrobat Reader</b> і клікай по <b>динаміку</b> біля фрази — звук грає у файлі.",
              "<b>2.</b> Слухай по черзі: спочатку повільно (<b>SLOW</b>), потім діалог (<b>DIALÓG</b>).",
              "<b>3.</b> Кожна лекція: словник з транскрипцією → граматика → діалог → вимова → вправи з ключами."):
        story.append(Paragraph("•  " + t, ParagraphStyle("covb",
            parent=st["bullet"], fontSize=11, leading=16, leftIndent=60, rightIndent=40)))
    story.append(Spacer(1, 24))
    # таблиця рівнів
    rows = [[Paragraph("<b>Рівень</b>", st["cellH"]), Paragraph("<b>Що вмієш</b>", st["cellH"]),
             Paragraph("<b>Лекції</b>", st["cellH"])]]
    descs = {"A0": "Читати і вітатися", "A1": "Виживання: магазин, місто, готель",
             "A2": "Щоденне життя: лікар, банк, установа", "B1": "Незалежність: робота, думки, дебати",
             "B2": "Свобода: аргументи, ідіоми, презентації"}
    for lv in ["A0", "A1", "A2", "B1", "B2"]:
        ids = [m["id"] for m in meta if m["level"] == lv]
        nm = dict(LEVELS.values())[lv]
        rows.append([Paragraph(f"<b>{lv}</b>", st["cell"]),
                     Paragraph(f"{nm}. {descs[lv]}", st["cell"]),
                     Paragraph(f"{ids[0]}–{ids[-1]}", st["cell"])])
    t = Table(rows, colWidths=[70, 330, 110])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                           ("BACKGROUND", (0, 0), (-1, 0), blue),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                            [colors.white, colors.HexColor("#f6f9ff")])]))
    story.append(t)
    story.append(PageBreak())
    story.append(Paragraph("OBSAH / Зміст", ParagraphStyle("toc",
        parent=st["h1"], fontSize=20, alignment=1)))
    story.append(Spacer(1, 8))
    pg_style = ParagraphStyle("pg", parent=st["cell"], alignment=2)
    row_style = TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 2),
                            ("TOPPADDING", (0, 0), (-1, -1), 1),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2)])
    for lv in ["A0", "A1", "A2", "B1", "B2"]:
        nm = dict(LEVELS.values())[lv]
        story.append(Paragraph(f"{lv} · {nm}", ParagraphStyle("toch",
            parent=st["h2"], fontSize=12)))
        for m in [x for x in meta if x["level"] == lv]:
            short = m["title"][:72]
            tt = Table([[Paragraph(f"<b>{m['id']}</b>  {md_inline(short)}", st["cell"]),
                         Paragraph(f"{starts[m['id']]}", pg_style)]], colWidths=[440, 70])
            tt.setStyle(row_style)
            story.append(TocRow(tt, m["id"]))
        story.append(Spacer(1, 6))
    path = TMP / "front.pdf"
    TMP.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=42, rightMargin=42,
                          topMargin=42, bottomMargin=42, title="Slovenčina 0→B2")
    doc.addPageTemplates([PageTemplate(id="p", frames=[
        Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")])])
    doc.build(story)
    return path, toc_links


def build_credits():
    """Сторінка атрибуції фото з assets/foto/SOURCES_*.md для фінального PDF."""
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    register_fonts()
    st = styles()
    blue = colors.HexColor(BLUE)
    story = [
        Paragraph("Атрибуція фотоматеріалів / Photo Credits", st["h1"]),
        Paragraph(
            "Усі 111 фотографій у курсі взято з Wikimedia Commons під вільними ліцензіями "
            "(CC BY, CC BY-SA, CC0, Public Domain). Нижче наведено джерела та авторів.",
            st["body"],
        ),
        Spacer(1, 6),
    ]
    rows = [[Paragraph("<b>Файл</b>", st["cellSH"]), Paragraph("<b>Лекція</b>", st["cellSH"]),
             Paragraph("<b>Ліцензія та автор</b>", st["cellSH"])]]
    for src in sorted(FOTO.glob("SOURCES_*.md")):
        for line in src.read_text(encoding="utf-8").splitlines():
            if line.startswith("|") and not line.startswith("| file") and not line.startswith("|---"):
                cols = [c.strip() for c in line.strip("|").split("|")]
                if len(cols) >= 4:
                    rows.append([
                        Paragraph(md_inline(cols[0]), st["cellS"]),
                        Paragraph(md_inline(cols[1][:45]), st["cellS"]),
                        Paragraph(md_inline(cols[3]), st["cellS"]),
                    ])
    t = Table(rows, colWidths=[80, 210, 220], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), blue),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f9ff")]),
    ]))
    story.append(t)
    path = TMP / "credits.pdf"
    TMP.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=42, rightMargin=42,
                          topMargin=42, bottomMargin=42, title="Photo Credits")
    doc.addPageTemplates([PageTemplate(id="p", frames=[
        Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")])])
    doc.build(story)
    return path


def build_full(lessons):
    from pypdf import PdfReader as R, PdfWriter
    from pypdf.annotations import Link
    for m in lessons:
        p = OUT / f"{m['id']}.pdf"
        if not p.exists():
            sys.exit(f"нема {p} — спочатку --all")
        m["npages"] = len(R(str(p)).pages)
    # прохід 1: дізнатись кількість сторінок front
    dummy = {m["id"]: 0 for m in lessons}
    f1, _ = build_front(lessons, dummy)
    F = len(R(str(f1)).pages)
    # прохід 2: справжні номери сторінок (1-based)
    starts, acc = {}, F + 1
    for m in lessons:
        starts[m["id"]] = acc
        acc += m["npages"]
    f2, toc_links = build_front(lessons, starts)
    assert len(R(str(f2)).pages) == F, "front reflow!"
    credits_pdf = build_credits()
    w = PdfWriter()
    w.append(R(str(f2)))
    for m in lessons:
        w.append(R(str(OUT / f"{m['id']}.pdf")))
    credits_start = acc - 1
    w.append(R(str(credits_pdf)))
    # клікабельні посилання в змісті
    for pno, rect, lid in toc_links:
        w.add_annotation(page_number=pno, annotation=Link(rect=rect, target_page_index=starts[lid] - 1))
    # закладки
    parents = {}
    for lv in ["A0", "A1", "A2", "B1", "B2"]:
        ms = [m for m in lessons if m["level"] == lv]
        nm = dict(LEVELS.values())[lv]
        parents[lv] = w.add_outline_item(f"{lv} · {nm}", starts[ms[0]["id"]] - 1, parent=None)
        for m in ms:
            w.add_outline_item(f"{m['id']} {m['title'][:60]}", starts[m["id"]] - 1, parent=parents[lv])
    w.add_outline_item("Атрибуція фото / Photo Credits", credits_start, parent=None)
    out = ROOT / "build" / "Slovak-0-B2-full.pdf"
    with open(out, "wb") as fh:
        w.write(fh)
    back = R(str(out))
    sounds = sum(1 for p in back.pages for a in (p.get("/Annots") or [])
                 if str(a.get_object().get("/Subtype")) == "/Sound")
    exp = expected_sounds(lessons)
    print(f"[FULL] pages={len(back.pages)} speakers={sounds} size={out.stat().st_size//1024//1024}MB")
    assert sounds == exp, f"speakers {sounds} != {exp}"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args()
    lessons = collect()
    if a.lesson:
        sel = [x for x in lessons if x["id"] == a.lesson] or sys.exit("нема лекції")
        for x in sel:
            lesson_pdf(x["id"], x["path"])
    elif a.full:
        build_full(collect())
    elif a.all:
        for x in lessons:
            lesson_pdf(x["id"], x["path"])
        print(f"OK lessons={len(lessons)}")
    else:
        sys.exit("вкажи --lesson 001, --all або --full")
