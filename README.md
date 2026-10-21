# Slovensky od nuly po B2 / Словацька з нуля до B2
## Курс для вільного спілкування

**Мета:** 0 → B2 (CEFR), ~3000 слів, вільне побутове + робоче спілкування
**Готовий продукт — PDF:**
- 📥 **Скачати повний курс одним файлом:** [Slovak-0-B2-full.pdf](https://github.com/ajjs1ajjs/Slovakia_Language/releases/download/v1.1/Slovak-0-B2-full.pdf) (111 лекцій, 467 сторінок, звук всередині)
- `build/Slovak-0-B2-full.pdf` — те саме, збирається локально: `python tools/build_pdf.py --all && python tools/build_pdf.py --full` (у git не лежить через ліміт 100 МБ, бери з релізу вище).
  Як слухати: в кінці кожної лекції — аудіо-дошка: клік по **динаміку** біля фрази грає голос
  (потрібен безкоштовний Adobe Acrobat Reader).
- `build/pdf/<ID>.pdf` — окремі PDF по лекціях (текст + звук по кліку). Збірка: `python tools/build_pdf.py --all`

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
- `tools/generate_audio.py` — TTS: `python tools/generate_audio.py --lesson 001` або `--all`
- `tools/make_pcm.py` — конвертація MP3 → PCM 22050 Гц для вбудовування в PDF
- `tools/make_ulaw.py` — кеш muLaw 8000 Гц (альтернатива для сумісності)
- `build/pdf/<ID>.pdf` — окремі PDF по лекціях (текст + звук по кліку). Збірка: `python tools/build_pdf.py --all`

Шаблон лекції: див. `_SABLONA-LEKCIE.md`
Курикулум детально: див. `KURIKULUM.md`

## Ліцензія

Вихідний код та навчальні матеріали поширюються на умовах ліцензії MIT (див. `LICENSE`). Фотоматеріали взяті з відкритих джерел (Wikimedia Commons тощо) на умовах відповідних вільних ліцензій (CC BY, CC BY-SA, Public Domain), докладно зазначених у файлах `assets/foto/SOURCES_*.md`.
