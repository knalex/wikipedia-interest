## Користувач
Як змінювався інтерес до теми "вегетаріанство" в німецькій Wikipedia за 3 роки?

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 skills/wikipedia-interest-analysis/scripts/resolve_topic.py --query "uk:вегетаріанство" --query "en:vegetarianism" --targets de --user-message "Як змінювався інтерес до теми \"вегетаріанство\" в німецькій Wikipedia за 3 роки?"
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 skills/wikipedia-interest-analysis/scripts/fetch_pageviews.py --basket wikipedia-interest-output/20260927-152104-Q83364/basket.json --last 36
python3 skills/wikipedia-interest-analysis/scripts/analyze_trend.py --views wikipedia-interest-output/20260927-152104-Q83364/views.json
```

## Відповідь агента
Тема: «вегетаріанство» (Q83364).
Період: вересень 2023 — серпень 2026 (36 місяців). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю останні 12 місяців (вересень 2025 — серпень 2026) з попередніми 12 (вересень 2024 — серпень 2025) — так сезонні коливання не спотворюють висновок.

- Німецька Wikipedia (de): інтерес падає, −25 % (43 432 перегляди проти 58 074). Довіра: висока.
  - Уся de.wikipedia за той самий час: −7 %; з поправкою на це зміна теми −19 %.
  - За весь період: перші 12 місяців (вересень 2023 — серпень 2024) → останні 12: −40 % (43 432 проти 71 853).
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.

Графік: wikipedia-interest-output/20260927-152104-Q83364/views.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.

Створено теку з результатами: <repo>/wikipedia-interest-output/20260927-152104-Q83364/
У ній:
- basket.json — кошик статей (етап 1)
- views.json — перегляди по місяцях чи днях (етап 2)
- analysis.json — аналіз тренду й довіри (етап 3)
- views.svg — графік (етап 3)
(Тека wikipedia-interest-output/ має власний .gitignore, тож у git ці файли не потрапляють.)

Можу зробити з цього звіт на одну сторінку (PDF), яким зручно поділитися з командою.
