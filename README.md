# Slovensky od nuly po B2 / Словацька з нуля до B2
## Курс для вільного спілкування

**Мета:** 0 → B2 (CEFR), ~3000 слів, вільне побутове + робоче спілкування

> 🆓 **Курс безкоштовний і відкритий.** Тексти лекцій, аудіоскрипти й генератор PDF — у цьому
> репозиторії під MIT. Усі 111 фото — під перевіреними вільними ліцензіями
> (CC BY, CC BY-SA, CC0, Public Domain) з атрибуцією в `assets/foto/SOURCES_*.md`.

**Готові формати курсу:**
- 📥 **Повний PDF одним файлом:** [Slovak-0-B2-full.pdf](https://github.com/ajjs1ajjs/Slovakia_Language/releases/download/v1.3.0/Slovak-0-B2-full.pdf) (111 лекцій, звук всередині, клікабельний зміст, атрибуція фото)
- 🃏 **Колода карток Anki:** [Slovak-0-B2.apkg](https://github.com/ajjs1ajjs/Slovakia_Language/releases/download/v1.3.0/Slovak-0-B2.apkg) (1300+ слів зі звуком та IPA)
- 🌐 **Автономний веб-плеєр:** [Slovak-0-B2-web.zip](https://github.com/ajjs1ajjs/Slovakia_Language/releases/download/v1.3.0/Slovak-0-B2-web.zip) — працює у будь-якому браузері (телефон, macOS, Linux, Windows) без Adobe Reader
- `build/Slovak-0-B2-full.pdf` — те саме, збирається локально (у git не лежить: збірки відтворюються з контенту, а готові артефакти роздаються через Releases).
  Як слухати в PDF: в кінці кожної лекції — аудіо-дошка: клік по **динаміку** біля фрази грає голос
  (потрібен безкоштовний Adobe Acrobat Reader; у браузерах і на мобільних зручніше відкрити веб-версію).
- `build/pdf/<ID>.pdf` — окремі PDF по лекціях (текст + звук по кліку). Збірка: `python tools/build_pdf.py --all`

## Швидкий старт (розробка)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; на Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python tools/check_course.py --strict        # лінтер контенту: структура, фото, аудіо, ключі
python tools/build_pdf.py --lesson 004       # одна лекція → build/pdf/004.pdf
python tools/build_pdf.py --all              # усі 111 PDF
python tools/build_pdf.py --full             # + обкладинка, клікабельний зміст, закладки, атрибуція
python tools/verify_pdf.py build/pdf/004.pdf --expect-audio 004   # звірити звуки з index.json
python tools/build_web.py --bundle           # інтерактивний веб-курс → build/web/index.html
python tools/build_anki.py                   # колода Anki → build/Slovak-0-B2.apkg
```

Потрібен **Python 3.9+** (перевірено на 3.12 / 3.14) і шрифт DejaVu Sans, Arial або Liberation Sans
(на Linux достатньо пакетів `fonts-dejavu-core` / `fonts-liberation`, на macOS — системний Arial).

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
- `tools/build_web.py` — генерація інтерактивного веб-курсу з аудіоплеєром у браузері
- `tools/build_anki.py` — експорт словникових карток зі звуком у колоду Anki (`.apkg`)

Шаблон лекції: див. `_SABLONA-LEKCIE.md`
Курикулум детально: див. `KURIKULUM.md`

## Перевірки

`python tools/check_course.py` запускається в CI на кожен push і PR. Він валить збірку, якщо:
- у лекції немає обов'язкової секції (FOTO / SLOVÍČKA / GRAMATIKA / VÝSLOVNOSŤ / CVIČENIA) або ключів до вправ;
- посилання на `assets/foto/*.jpg` або `slow-NN.mp3` не резолвиться;
- лишились заглушки («Поки фото», «згенеруємо пізніше») або легасі-ідентифікатори `T01-01`;
- фото без рядка атрибуції в `assets/foto/SOURCES_*.md`.

## Ліцензія

Вихідний код та навчальні матеріали поширюються на умовах ліцензії MIT (див. `LICENSE`). Фотоматеріали взяті з відкритих джерел (Wikimedia Commons тощо) на умовах відповідних вільних ліцензій (CC BY, CC BY-SA, CC0, Public Domain), докладно зазначених у файлах `assets/foto/SOURCES_*.md`.

Курс безкоштовний: жодних оплат, передплат чи реєстрації. Якщо хочеш підтримати проєкт — зірка на GitHub і повідомлення про помилку в лекціях.
