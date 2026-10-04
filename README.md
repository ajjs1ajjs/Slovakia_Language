# Slovensky od nuly po B2 / Словацька з нуля до B2
## Курс для вільного спілкування

**Мета:** 0 → B2 (CEFR), ~3000 слів, вільне побутове + робоче спілкування
**Готовий продукт — PDF:**
- `build/Slovak-0-B2-full.pdf` — весь курс одним файлом: 450 сторінок, 1463 MP3 всередині.
  Як слухати: в кінці кожної лекції — аудіо-дошка: клік по клітинці **▶ Play грає звук прямо у файлі**
  (потрібен безкоштовний Adobe Acrobat Reader; у вбудованих переглядачах браузерів — скануй QR).
  Усі MP3 також у панелі вкладень Acrobat.
- `build/pdf/<ID>.pdf` — окремі PDF по лекціях (текст + QR + MP3). Збірка: `python tools/build_pdf.py --all`

## Структура

- `00_A0-Zaklady-vymova/` — Розділ 0. Основи вимови (6 лекцій)
- `01_A1-Prezitie/` — Розділ 1. A1 Виживання (20 лекцій)
- `02_A2-Kazdodenny-zivot/` — Розділ 2. A2 Щоденне життя (25 лекцій)
- `03_B1-Nezavislost/` — Розділ 3. B1 Незалежність (30 лекцій)
- `04_B2-Sloboda/` — Розділ 4. B2 Свобода дискусії (30 лекцій)
- `assets/foto/` — фото-асоціації
- `assets/audio-scripts/` — тексти для озвучки (TTS / диктор)
- `assets/audio/<ID>/` — MP3: slow-XX (повільно, Viktoria) + dialog-XX (діалог, Lukáš/Viktoria) + index.json
- `assets/qr/<ID>/` — QR-PNG до кожного MP3 (для друку/PDF; з `--base-url` кодують повний URL)
- `tools/generate_audio.py` — TTS: `python tools/generate_audio.py --lesson 001` або `--all [--base-url ...]`
- `tools/build_index.py` — службове (індекс лекцій)
- `build/pdf/<ID>.pdf` — окремі PDF по лекціях (текст + QR + MP3). Збірка: `python tools/build_pdf.py --all`

Шаблон лекції: див. `_SABLONA-LEKCIE.md`
Курикулум детально: див. `KURIKULUM.md`
