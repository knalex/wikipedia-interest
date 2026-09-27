## Користувач
Чи зростає інтерес до теми "квантова біологія" у шведській Wikipedia?

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:квантова біологія" \
  --query "en:quantum biology" \
  --targets sv \
  --user-message "Чи зростає інтерес до теми \"квантова біологія\" у шведській Wikipedia?" \
  --out <tmp>/w/18/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket <tmp>/w/18/basket.json \
  --last 24 \
  --out <tmp>/w/18/views.json

python3 scripts/analyze_trend.py \
  --views <tmp>/w/18/views.json \
  --out <tmp>/w/18/analysis.json
```

## Відповідь агента
Тема: «Квантова біологія» (Q1429339).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю останні 12 місяців (вересень 2025 — серпень 2026) з попередніми 12 (вересень 2024 — серпень 2025) — так сезонні коливання не спотворюють висновок.

- Шведська Wikipedia (sv): інтерес падає, −27 % (279 переглядів проти 381). Довіра: низька.
  - Уся sv.wikipedia за той самий час: −2 %; з поправкою на це зміна теми −25 %.
  - Мало переглядів (у середньому ~23 за місяць): випадкові коливання дають великі відсотки.

Графік: <tmp>/w/18/views.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.
