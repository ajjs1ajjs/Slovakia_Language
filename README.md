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
- `build/pdf/<ID>.pdf` — PDF лекції: текст + QR + MP3 всередині (attachments: Acrobat/Reader → панель вкладень → Play). Збірка: `python tools/build_pdf.py --all`

## Хостинг PWA / телефон
- GitHub Pages на приватному репо безкоштовним планом НЕ дають (422) — тому так:
- ПК + телефон в одному Wi-Fi: `python -m http.server 8080` → на телефоні http://192.168.50.42:8080/pwa/ (читати, слухати, Web Speech — все працює; для кнопки «Встановити» потрібен HTTPS)
- HTTPS-варіант: Cloudflare Tunnel (`cloudflared tunnel --url http://localhost:8080`) — дає https-URL, PWA встановлюється. У цьому середовищі API trycloudflare недоступне — запустити з дому.
- Після появи стабільного URL: `python tools/make_qr.py --base-url https://HOST/audio` + `python tools/build_pdf.py --all` — QR у PDF вестимуть на хост.

Шаблон лекції: див. `_SABLONA-LEKCIE.md`
Курикулум детально: див. `KURIKULUM.md`
