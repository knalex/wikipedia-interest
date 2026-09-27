## Користувач
Як змінювався інтерес до теми "вегетаріанство" в німецькій Wikipedia за 3 роки?

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 .claude/skills/wikipedia-interest-analysis/scripts/resolve_topic.py \
  --query "uk:вегетаріанство" \
  --query "en:vegetarianism" \
  --targets de \
  --user-message "Як змінювався інтерес до теми \"вегетаріанство\" в німецькій Wikipedia за 3 роки?" \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_1/basket.json

cd /home/alex/Interest/wikipedia-interest && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 .claude/skills/wikipedia-interest-analysis/scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_1/basket.json \
  --last 36 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_1/views.json
```

## Відповідь агента
Я зібрав дані про перегляди статті про вегетаріанство в німецькій Wikipedia за останні 3 роки (вересень 2023 — серпень 2026).

**Стаття в німецькій Wikipedia:** Vegetarismus (включаючи 16 перенаправлень)

**Загальна кількість переглядів за період:** 173 359 переглядів

**Період даних:** вересень 2023 — серпень 2026 (36 місяців)

**Як змінювався інтерес:**
- **2023 р. (вересень-грудень):** середньо 6 245 переглядів на місяць
- **2024 р. (січень-грудень):** середньо 5 635 переглядів на місяць (зменшення порівняно з 2023)
- **2025 р. (січень-грудень):** середньо 4 006 переглядів на місяць (істотне зменшення)
- **2026 р. (січень-серпень):** середньо 3 564 переглядів на місяць (продовження тренду)

**Основна спостереження:** Інтерес до вегетаріанства в німецькій Wikipedia демонстрував тенденцію до зменшення протягом 3 років. Максимальні перегляди були на початку періоду (січень 2024 з 7 856 переглядів), а мінімальні — в липні 2025 (3 119 переглядів).

Більше за всього користувачів переглядали основну статтю "Vegetarismus" (160 883 переглядів), а також перенаправлення "Vegetarier" та "Vegetarisch".

Деталі зібрані в файли basket.json та views.json у папці /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_1/
