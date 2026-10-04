# Slovensky od nuly po B2 / Словацька з нуля до B2
## Курс для вільного спілкування

**Мета:** 0 → B2 (CEFR), ~3000 слів, вільне побутове + робоче спілкування
**Формат кожної лекції:** текст + транскрипція (IPA + українська) + фото-асоціація + аудіо (MP3 + QR у PDF + HTML-плеєр)
**Про PDF з аудіо:** так, можливо. Робимо 2 варіанти:
1. Інтерактивний PDF з QR-кодами → скануєш телефоном → відкривається MP3 (працює всюди, рекомендовано)
2. PDF з вбудованим аудіо (кнопка Play прямо в PDF, працює тільки в Adobe Acrobat). Згенеруємо на фінальному етапі.

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
- `tools/build_index.py` — індекс лекцій для PWA (`pwa/lessons.json`)
- `pwa/` — застосунок: каталог 111 лекцій, 🔊 озвучка (MP3, fallback Web Speech sk-SK),
  офлайн (Service Worker), кнопка 🖨 PDF (друк), встановлення на телефон.
  Запуск: `python -m http.server 8080` → http://localhost:8080/pwa/

Шаблон лекції: див. `_SABLONA-LEKCIE.md`
Курикулум детально: див. `KURIKULUM.md`
