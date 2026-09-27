
## Користувач
Як змінювався інтерес до теми "вегетаріанство" в німецькій Wikipedia за 3 роки?

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py --query "uk:вегетаріанство" --query "en:vegetarianism" --targets de --user-message "Як змінювався інтерес до теми \"вегетаріанство\" в німецькій Wikipedia за 3 роки?" --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_3/basket.json
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_3/basket.json --last 36 --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_3/views.json
```

## Відповідь агента
Зібрав дані про перегляди статей на тему вегетаріанства в німецькій Wikipedia за 3 роки (вересень 2023 — серпень 2026).

**Знайдена тема:** Vegetarismus (Q83364) — основна стаття в німецькій Вікіпедії плюс 16 перенаправлень (Vegetarier, Vegetarisch, Ovo-Lacto-Vegetarismus та інші).

**Період:** 36 місяців, вересень 2023 — серпень 2026

**Загальна кількість переглядів:** 173,359 за весь період

**Статистика за рік:**
- вересень 2023 — серпень 2024: ~77,113 переглядів (перший рік)
- вересень 2024 — серпень 2025: ~57,308 переглядів (другий рік)
- вересень 2025 — серпень 2026: ~38,938 переглядів (третій рік)

**Основна стаття:** Vegetarismus отримала 160,883 переглядів за період.

Дані зібрано з Wikimedia Pageviews API (всі джерела доступу, агент=user).

Висновків про тренди і значущість змін (етап 3 аналізу) зробити не можу — це в розробці.

