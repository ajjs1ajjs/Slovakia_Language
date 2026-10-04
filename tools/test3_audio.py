#!/usr/bin/env python3
"""ТЕСТ-3: S1 = 22050/16/signed + /Type /Sound; S2 = 8000/muLaw (макс. сумісність)."""
import json, struct, subprocess
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (DictionaryObject, NameObject, TextStringObject,
                           ArrayObject, NumberObject, DecodedStreamObject)

ROOT = Path(__file__).resolve().parent.parent
LID = "001"
ADIR = ROOT / "assets" / "audio" / LID
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()

def wav_pcm(mp3: Path):
    out = ROOT / "build" / "tmp" / (mp3.stem + "-t3.wav")
    subprocess.run([FF, "-y", "-v", "error", "-i", str(mp3),
                    "-ar", "22050", "-ac", "1", "-sample_fmt", "s16", str(out)], check=True)
    raw = out.read_bytes()
    pos = 12
    while pos + 8 <= len(raw):
        cid, size = raw[pos:pos + 4], struct.unpack("<I", raw[pos + 4:pos + 8])[0]
        if cid == b"data":
            return raw[pos + 8:pos + 8 + size]
        pos += 8 + size + (size & 1)
    raise ValueError("no data")

def mulaw_pcm(mp3: Path):
    out = ROOT / "build" / "tmp" / (mp3.stem + "-t3.ulaw")
    subprocess.run([FF, "-y", "-v", "error", "-i", str(mp3),
                    "-ar", "8000", "-ac", "1", "-f", "mulaw", str(out)], check=True)
    return out.read_bytes()

def sound(w, data: bytes, r, ch, b, enc):
    s = DecodedStreamObject()
    s.set_data(data)
    s.update({NameObject("/Type"): NameObject("/Sound"),
              NameObject("/R"): NumberObject(r), NameObject("/C"): NumberObject(ch),
              NameObject("/B"): NumberObject(b), NameObject("/E"): NameObject(enc)})
    return w._add_object(s)

def main():
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-B", r"C:\Windows\Fonts\arialbd.ttf"))
    idx = json.loads((ADIR / "index.json").read_text(encoding="utf-8"))
    phrases = [(e["file"], e["text"]) for e in (idx["slow"][:2])]
    W, H = A4
    tmp = ROOT / "build" / "tmp" / "test3-base.pdf"
    c = Canvas(str(tmp), pagesize=A4)
    c.setFont("Arial-B", 13)
    c.drawString(42, H - 60, "TEST-3: клік по значку праворуч")
    targets, y = {}, H - 120
    for i, (fn, text) in enumerate(phrases):
        c.setFont("Arial-B", 12)
        c.drawString(42, y, f"{i+1}. {text}")
        y -= 30
        for var, hint in (("S1", "динамік = 22050Hz"), ("S2", "динамік = 8000 muLaw")):
            c.setFont("Arial", 11)
            c.drawString(60, y + 4, f"[{var}] {hint}  >>> значок тут:")
            targets[(var, fn)] = (300, y - 4, 340, y + 20)
            y -= 40
        y -= 16
    c.save()
    w = PdfWriter()
    w.append(PdfReader(str(tmp)))
    for (var, fn), rect in targets.items():
        x0, y0, x1, y1 = [NumberObject(int(v)) for v in rect]
        if var == "S1":
            sref = sound(w, wav_pcm(ADIR / fn), 22050, 1, 16, "/Signed")
        else:
            sref = sound(w, mulaw_pcm(ADIR / fn), 8000, 1, 8, "/muLaw")
        w.add_annotation(0, DictionaryObject({
            NameObject("/Type"): NameObject("/Annot"), NameObject("/Subtype"): NameObject("/Sound"),
            NameObject("/Rect"): ArrayObject([x0, y0, x1, y1]),
            NameObject("/T"): TextStringObject(f"{var} {fn}"),
            NameObject("/Sound"): sref}))
    out = ROOT / "build" / "TEST3-play.pdf"
    with open(out, "wb") as fh:
        w.write(fh)
    print(f"TEST3 OK: {out.stat().st_size//1024}KB")

if __name__ == "__main__":
    main()
