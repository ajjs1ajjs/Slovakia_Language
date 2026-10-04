#!/usr/bin/env python3
"""ТЕСТ-2: чистий WAV (правильний парсинг data-чанка) + великі цілі + варіант D.
  C: Sound-анотація (динамік праворуч, текст ліворуч — без накладання)
  D: FileAttachment-анотація (скріпка) з вбудованим MP3
  E: повтор A (Movie, голе ім'я) з великою ціллю
"""
import json, struct, subprocess
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (DictionaryObject, NameObject, TextStringObject,
                           ArrayObject, NumberObject, BooleanObject, DecodedStreamObject)

ROOT = Path(__file__).resolve().parent.parent
LID = "001"
ADIR = ROOT / "assets" / "audio" / LID
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()

def mp3_to_pcm(mp3: Path):
    out = ROOT / "build" / "tmp" / (mp3.stem + "-c2.wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([FF, "-y", "-v", "error", "-i", str(mp3),
                    "-ar", "22050", "-ac", "1", "-sample_fmt", "s16", str(out)], check=True)
    raw = out.read_bytes()
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WAVE", "не WAV"
    # йдемо по чанках до 'data' (ffmpeg може вставити fact/LIST)
    pos, fmt = 12, None
    while pos + 8 <= len(raw):
        cid, size = raw[pos:pos + 4], struct.unpack("<I", raw[pos + 4:pos + 8])[0]
        if cid == b"fmt ":
            fmt = raw[pos + 8:pos + 8 + size]
        if cid == b"data":
            pcm = raw[pos + 8:pos + 8 + size]
            break
        pos += 8 + size + (size & 1)
    else:
        raise ValueError("нема data-чанка")
    audio_fmt, channels, rate, _, _, bits = struct.unpack("<HHIIHH", fmt[:16])
    assert (audio_fmt, channels, rate, bits) == (1, 1, 22050, 16), f"fmt={audio_fmt,channels,rate,bits}"
    assert len(pcm) == size and size % 2 == 0
    return pcm

def filespec(w, arcname, data):
    s = DecodedStreamObject()
    s.set_data(data)
    s.update({NameObject("/Type"): NameObject("/EmbeddedFile")})
    sref = w._add_object(s)
    fs = DictionaryObject({NameObject("/Type"): NameObject("/Filespec"),
                           NameObject("/F"): TextStringObject(arcname),
                           NameObject("/EF"): DictionaryObject({NameObject("/F"): sref})})
    return w._add_object(fs)

def rect_ann(subtype, rect, title, extra):
    x0, y0, x1, y1 = [NumberObject(int(v)) for v in rect]
    d = DictionaryObject({NameObject("/Type"): NameObject("/Annot"),
                          NameObject("/Subtype"): NameObject(subtype),
                          NameObject("/Rect"): ArrayObject([x0, y0, x1, y1]),
                          NameObject("/T"): TextStringObject(title)})
    d.update(extra)
    return d

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
    tmp = ROOT / "build" / "tmp" / "test2-base.pdf"
    c = Canvas(str(tmp), pagesize=A4)
    c.setFont("Arial-B", 13)
    c.drawString(42, H - 60, "TEST-2: клік по значку ПРАВОРУЧ від тексту")
    c.setFont("Arial", 10)
    c.setFillGray(0.4)
    c.drawString(42, H - 78, "Якщо зверху жовта смуга про multimedia/blocked — натисни Allow / Дозволити.")
    c.setFillGray(0)
    targets = {}
    y = H - 130
    for i, (fn, text) in enumerate(phrases):
        c.setFont("Arial-B", 12)
        c.drawString(42, y, f"{i+1}. {text}")
        y -= 30
        for var, hint in (("C", "динамік = звук WAV всередині"),
                          ("D", "скріпка = відкрити MP3 всередині"),
                          ("E", "плівка = Movie (повтор A)")):
            c.setFont("Arial", 11)
            c.drawString(60, y + 4, f"[{var}] {hint}  >>> значок тут:")
            targets[(var, fn)] = (300, y - 4, 340, y + 20)
            y -= 40
        y -= 16
    c.save()

    w = PdfWriter()
    w.append(PdfReader(str(tmp)))
    for (var, fn), rect in targets.items():
        if var == "C":
            pcm = mp3_to_pcm(ADIR / fn)
            s = DecodedStreamObject()
            s.set_data(pcm)
            s.update({NameObject("/R"): NumberObject(22050), NameObject("/C"): NumberObject(1),
                      NameObject("/B"): NumberObject(16), NameObject("/E"): NameObject("/Signed")})
            sref = w._add_object(s)
            w.add_annotation(0, rect_ann("/Sound", rect, f"C {fn}", {NameObject("/Sound"): sref}))
        elif var == "D":
            fs = filespec(w, fn, (ADIR / fn).read_bytes())
            w.add_annotation(0, rect_ann("/FileAttachment", rect, f"D {fn}",
                                         {NameObject("/FS"): fs, NameObject("/Name"): NameObject("/Paperclip")}))
        else:
            fs = filespec(w, fn, (ADIR / fn).read_bytes())
            w.add_annotation(0, rect_ann("/Movie", rect, f"E {fn}",
                                         {NameObject("/Movie"): DictionaryObject(
                                             {NameObject("/F"): fs,
                                              NameObject("/Poster"): BooleanObject(False)})}))
    out = ROOT / "build" / "TEST2-play.pdf"
    with open(out, "wb") as fh:
        w.write(fh)
    r = PdfReader(str(out))
    kinds = {}
    for p in r.pages:
        for a in (p.get("/Annots") or []):
            k = str(a.get_object().get("/Subtype"))
            kinds[k] = kinds.get(k, 0) + 1
    print(f"TEST2 OK: {out.stat().st_size//1024}KB annots={kinds}")

if __name__ == "__main__":
    main()
