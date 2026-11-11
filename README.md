# Slovensky od nuly po B2 / Словацька з нуля до B2
## Курс для вільного спілкування

**Мета:** 0 → B2 (CEFR), ~3000 слів, вільне побутове + робоче спілкування

**Готовий продукт — PDF:**
- 📥 **Скачати повний курс одним файлом:** [Slovak-0-B2-full.pdf](https://github.com/ajjs1ajjs/Slovakia_Language/releases/download/v1.2.1/Slovak-0-B2-full.pdf) (111 лекцій, 467 сторінок, звук всередині)
- `build/Slovak-0-B2-full.pdf` — те саме, збирається локально (у git не лежить: PDF відтворюються з контенту, а повний курс роздається через Releases).
  Як слухати: в кінці кожної лекції — аудіо-дошка: клік по **динаміку** біля фрази грає голос
  (потрібен безкоштовний Adobe Acrobat Reader).
- `build/pdf/<ID>.pdf` — окремі PDF по лекціях (текст + звук по кліку). Збірка: `python tools/build_pdf.py --all`

## Швидкий старт (розробка)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; на Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python tools/check_course.py                 # лінтер контенту: структура, фото, аудіо, ключі
python tools/build_pdf.py --lesson 004       # одна лекція → build/pdf/004.pdf
python tools/build_pdf.py --all              # усі 111 PDF
python tools/build_pdf.py --full             # + обкладинка, зміст, закладки, монолітний PDF
python tools/verify_pdf.py build/pdf/004.pdf --expect-audio 004   # звірити звуки з index.json
```

Потрібен **Python 3.9+** (перевірено на 3.14) і шрифт Arial або Liberation/DejaVu Sans
(на Linux достатньо пакета `fonts-liberation`, на macOS — системний Arial).

## Структура

- `00_A0-Zaklady-vymova/` — Розділ 0. Основи вимови (6 лекцій)
- `01_A1-Prezitie/` — Розділ 1. A1 Виживання (20 лекцій)
- `02_A2-Kazdodenny-zivot/` — Розділ 2. A2 Щоденне життя (25 лекцій)
- `03_B1-Nezavislost/` — Розділ 3. B1 Незалежність (30 лекцій)
- `04_B2-Sloboda/` — Розділ 4. B2 Свобода дискусії (30 лекцій)
- `assets/foto/` — фото-асоціації з атрибуцією джерел у `SOURCES_*.md`
- `assets/audio-scripts/` — тексти для озвучки (TTS / диктор)
- `assets/audio/<ID>/` — MP3: slow-XX (повільно, Viktoria) + dialog-XX (діалог, Lukáš/Viktoria) + index.json
- `tools/build_pdf.py` — генерація інтерактивних PDF (полекційних або монолітного повного курсу)
- `tools/check_course.py` — лінтер контенту (секції лекції, посилання на фото/MP3, ключі, атрибуція)
- `tools/verify_pdf.py` — перевірка зібраного PDF: сторінки та кількість Sound-анотацій
- `tools/generate_audio.py` — TTS: `python tools/generate_audio.py --lesson 001` або `--all`
- `tools/make_pcm.py` — конвертація MP3 → PCM 22050 Гц для вбудовування в PDF

Шаблон лекції: див. `_SABLONA-LEKCIE.md`
Курикулум детально: див. `KURIKULUM.md`

## Перевірки

`python tools/check_course.py` запускається в CI на кожен push і PR. Він валить збірку, якщо:
- у лекції немає обов'язкової секції (FOTO / SLOVÍČKA / GRAMATIKA / VÝSLOVNOSŤ / CVIČENIA) або ключів до вправ;
- посилання на `assets/foto/*.jpg` або `slow-NN.mp3` не резолвиться;
- лишились заглушки («Поки фото», «згенеруємо пізніше») або легасі-ідентифікатори `T01-01`;
- фото без рядка атрибуції в `assets/foto/SOURCES_*.md`.

## Ліцензія

Вихідний код та навчальні матеріали поширюються на умовах ліцензії MIT (див. `LICENSE`). Фотоматеріали взяті з відкритих джерел (Wikimedia Commons тощо) на умовах відповідних вільних ліцензій (CC BY, CC BY-SA, Public Domain), докладно зазначених у файлах `assets/foto/SOURCES_*.md`.
