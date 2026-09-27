## Користувач
Як змінювався інтерес до теми "вегетаріанство" в німецькій Wikipedia за 3 роки?

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 .claude/skills/wikipedia-interest-analysis/scripts/resolve_topic.py --query "uk:вегетаріанство" --query "en:vegetarianism" --query "de:Vegetarismus" --targets de --user-message "Як змінювався інтерес до теми \"вегетаріанство\" в німецькій Wikipedia за 3 роки?" --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/13/basket.json
cd /home/alex/Interest/wikipedia-interest && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 .claude/skills/wikipedia-interest-analysis/scripts/fetch_pageviews.py --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/13/basket.json --last 36 --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/13/views.json
cd /home/alex/Interest/wikipedia-interest && python3 .claude/skills/wikipedia-interest-analysis/scripts/analyze_trend.py --views /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/13/views.json --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/13/analysis.json --chart /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/13/chart.svg
```

## Відповідь агента
Тема: «вегетаріанство» (Q83364).
Період: вересень 2023 — серпень 2026 (36 місяців). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю останні 12 місяців (вересень 2025 — серпень 2026) з попередніми 12 (вересень 2024 — серпень 2025) — так сезонні коливання не спотворюють висновок.

- Німецька Wikipedia (de): інтерес падає, −25 % (43 432 перегляди проти 58 074). Довіра: висока.
  - Уся de.wikipedia за той самий час: −7 %; з поправкою на це зміна теми −19 %.
  - За весь період: перші 12 місяців (вересень 2023 — серпень 2024) → останні 12: −40 % (43 432 проти 71 853).
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.

Графік: /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/13/chart.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.

Можу зробити з цього звіт на одну сторінку (PDF), яким зручно поділитися з командою.
