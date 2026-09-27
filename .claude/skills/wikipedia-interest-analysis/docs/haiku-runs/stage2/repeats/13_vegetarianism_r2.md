## Користувач
Як змінювався інтерес до теми "вегетаріанство" в німецькій Wikipedia за 3 роки?

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:вегетаріанство" \
  --query "en:vegetarianism" \
  --targets de \
  --user-message "Як змінювався інтерес до теми \"вегетаріанство\" в німецькій Wikipedia за 3 роки?" \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_2/basket.json

cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_2/basket.json \
  --last 36 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_2/views.json
```

## Відповідь агента
Розв'язав тему вегетаріанства. У німецькій Wikipedia це основна стаття «Vegetarismus» з 16 перенаправленнями.

За останні 3 роки (вересень 2023 — серпень 2026) сторінки про вегетаріанство переглядалися **173 359 разів** загалом.

Дані по місяцях:
- **Вересень 2023 — грудень 2023**: від 6018 до 6542 переглядів на місяць
- **Січень 2024 — серпень 2024**: спад із 7856 на початку до 4492 на кінець (найнижче значення літа)
- **Вересень 2024 — грудень 2024**: невеликий ріст до 6175 переглядів
- **Січень 2025 — серпень 2026**: поступовий спад від 6881 до біля 3500 переглядів на місяць

Найпопулярніша сторінка — основна стаття «Vegetarismus» (160 883 переглядів, 93% усіх переглядів). Решта переглядів розподіляються між перенаправленнями («Vegetarier», «Vegetarisch», «Ovo-Lacto-Vegetarismus» та іншими).

**Важливо:** Це дані про кількість переглядів. Аналіз тренду й висновків про те, чи справді зростає чи падає інтерес (етап 3), ще в розробці.

Дані збережено у файлах:
- `/tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_2/basket.json` (кошик статей)
- `/tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/13_2/views.json` (переглядів по місяцях)
