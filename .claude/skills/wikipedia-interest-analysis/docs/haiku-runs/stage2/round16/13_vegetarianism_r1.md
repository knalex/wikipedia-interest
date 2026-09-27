## Користувач
Як змінювався інтерес до теми "вегетаріанство" в німецькій Wikipedia за 3 роки?

## Команди агента
```bash
cd "/home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis" && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py --query "uk:вегетаріанство" --query "en:vegetarianism" --targets "de" --user-message "Як змінювався інтерес до теми \"вегетаріанство\" в німецькій Wikipedia за 3 роки?" --out "/tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/13_1/basket.json"

cd "/home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis" && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py --basket "/tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/13_1/basket.json" --last 36 --out "/tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/13_1/views.json"
```

## Відповідь агента
Тема: «вегетаріанство» (Q83364).
Період: вересень 2023 — серпень 2026 (36 місяців). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.

- Німецька Wikipedia (de): 173 359 переглядів за період (стаття «Vegetarismus» і 16 перенаправлень).

Це лише суми переглядів. Чи зростає інтерес, як він змінювався в часі й наскільки цьому можна довіряти, покаже аналіз тренду (етап 3), який ще в розробці; тоді ж з'являться графіки й рекомендації.
