## Користувач
Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:астрономія" \
  --query "en:astronomy" \
  --targets uk \
  --user-message "Ми думаємо додати курс з астрономії до освітнього застосунку. Чи зростає інтерес до цієї теми в україномовній Wikipedia, і наскільки цьому зростанню можна довіряти?" \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/03/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/03/basket.json \
  --last 24 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/03/views.json

python3 scripts/analyze_trend.py \
  --views /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/03/views.json \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/03/analysis.json
```

## Відповідь агента
Тема: «астрономія» (Q333).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю останні 12 місяців (вересень 2025 — серпень 2026) з попередніми 12 (вересень 2024 — серпень 2025) — так сезонні коливання не спотворюють висновок.

- Українська Wikipedia (uk): інтерес падає, −60 % (6 712 переглядів проти 16 614). Довіра: середня.
  - Уся uk.wikipedia за той самий час: −25 %; з поправкою на це зміна теми −46 %.
  - Разовий сплеск у вересні 2024: 4 687 переглядів, у 7,7 раза вище за медіану; без нього висновок той самий (−46 %).
  - Різка й стійка зміна рівня з червня 2025: з ~1 019 до ~361 на місяць. Таке часто спричиняють зміни в самій статті (перейменування, об'єднання, перенаправлення) або зовнішні події, тож варто перевірити історію статті.

Графік: /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/03/views.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.
