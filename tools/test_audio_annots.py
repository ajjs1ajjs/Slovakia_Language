#!/usr/bin/env python3
"""ТЕСТ: який варіант вбудованого аудіо грає в Acrobat.
Будує build/TEST-play.pdf: 3 фрази x 3 варіанти:
  A: Movie-анотація, /F голе ім'я файлу + /EF (MP3 всередині), Poster false
  B: Movie-анотація, /F з підпапкою + /EF (поточний варіант, контроль)
  C: Sound-анотація з WAV всередині (PCM, за спеком PDF)
Прямокутники малі (тільки зона [Play]), дизайн клітинки видно.
"""
import json, subprocess
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (DictionaryObject, NameObject, TextStringObject,
                           ArrayObject, NumberObject, BooleanObject, DecodedStreamObject)

ROOT = Path(__file__).resolve().parent.parent
LID = "001"
ADIR = ROOT / "assets" / "audio" / LID
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()

def mp3_to_wav(mp3: Path, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([FF, "-y", "-v", "error", "-i", str(mp3),
                    "-ar", "22050", "-ac", "1", "-sample_fmt", "s16", str(out)], check=True)
    raw = out.read_bytes()
    assert raw[:4] == b"RIFF", "не WAV"
    return raw[44:], len(raw) - 44  # PCM без заголовка, розмір

def filespec(w, arcname: str, data: bytes):
    s = DecodedStreamObject()
    s.set_data(data)
    s.update({NameObject("/Type"): NameObject("/EmbeddedFile")})
    sref = w._add_object(s)
    fs = DictionaryObject({
        NameObject("/Type"): NameObject("/Filespec"),
        NameObject("/F"): TextStringObject(arcname),
        NameObject("/EF"): DictionaryObject({NameObject("/F"): sref}),
    })
    return w._add_object(fs)

def movie_ann(fs_ref, rect, title, poster=False):
    x0, y0, x1, y1 = [NumberObject(int(v)) for v in rect]
    return DictionaryObject({
        NameObject("/Type"): NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Movie"),
        NameObject("/Rect"): ArrayObject([x0, y0, x1, y1]),
        NameObject("/Border"): ArrayObject([NumberObject(0)] * 3),
        NameObject("/T"): TextStringObject(title),
        NameObject("/Movie"): DictionaryObject({
            NameObject("/F"): fs_ref,
            NameObject("/Poster"): BooleanObject(poster)}),
    })

def sound_ann(w, pcm: bytes, rect, title):
    s = DecodedStreamObject()
    s.set_data(pcm)
    s.update({NameObject("/R"): NumberObject(22050), NameObject("/C"): NumberObject(1),
              NameObject("/B"): NumberObject(16), NameObject("/E"): NameObject("/Signed")})
    sref = w._add_object(s)
    x0, y0, x1, y1 = [NumberObject(int(v)) for v in rect]
    return DictionaryObject({
        NameObject("/Type"): NameObject("/Annot"),
        NameObject("/Subtype"): NameObject("/Sound"),
        NameObject("/Rect"): ArrayObject([x0, y0, x1, y1]),
        NameObject("/T"): TextStringObject(title),
        NameObject("/Sound"): sref,
    })

def main():
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Arial", r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-B", r"C:\Windows\Fonts\arialbd.ttf"))
    idx = json.loads((ADIR / "index.json").read_text(encoding="utf-8"))
    phrases = [(e["file"], e["text"]) for e in (idx["slow"][:2] + idx["normal"][:1])]
    W, H = A4
    tmp = ROOT / "build" / "tmp" / "test-base.pdf"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    c = Canvas(str(tmp), pagesize=A4)
    rects = {}  # (var, i) -> rect
    y = H - 80
    for i, (fn, text) in enumerate(phrases):
        c.setFont("Arial-B", 12)
        c.drawString(42, y, f"{i+1}. {text}")
        y -= 26
        for var in ("A", "B", "C"):
            label = {"A": "A: Movie, голе ім'я", "B": "B: Movie, з папкою (як було)",
                     "C": "C: Sound WAV"}[var]
            c.setFont("Arial", 11)
            c.drawString(60, y, f"[{var}] [ Play ]  {label}  <- клік сюди")
            rects[(var, fn)] = (60, y - 4, 140, y + 14)
            y -= 34
        y -= 14
    c.save()

    w = PdfWriter()
    w.append(PdfReader(str(tmp)))
    mp3 = {fn: (ADIR / fn).read_bytes() for fn, _ in phrases}
    wav = {}
    for fn, _ in phrases:
        pcm, _ = mp3_to_wav(ADIR / fn, ROOT / "build" / "tmp" / (fn + ".wav"))
        wav[fn] = pcm
    for (var, fn), rect in rects.items():
        if var == "A":
            fs = filespec(w, fn, mp3[fn])  # голе ім'я без папки
            w.add_annotation(0, movie_ann(fs, rect, f"A {fn}", poster=False))
        elif var == "B":
            fs = filespec(w, f"{LID}/{fn}", mp3[fn])
            w.add_annotation(0, movie_ann(fs, rect, f"B {fn}", poster=False))
        else:
            w.add_annotation(0, sound_ann(w, wav[fn], rect, f"C {fn}"))
    out = ROOT / "build" / "TEST-play.pdf"
    with open(out, "wb") as fh:
        w.write(fh)
    r = PdfReader(str(out))
    kinds = {}
    for p in r.pages:
        for a in (p.get("/Annots") or []):
            k = str(a.get_object().get("/Subtype"))
            kinds[k] = kinds.get(k, 0) + 1
    print(f"TEST pdf OK: {out.stat().st_size//1024}KB annots={kinds}")

if __name__ == "__main__":
    main()
