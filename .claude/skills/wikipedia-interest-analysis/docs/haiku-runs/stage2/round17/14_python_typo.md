## Користувач
Порівняй тренд "Pyhton programming" між англійською та німецькою Wikipedia.

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:Python programming" \
  --query "en:Python programming" \
  --targets en,de \
  --user-message "Порівняй тренд \"Pyhton programming\" між англійською та німецькою Wikipedia." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/z/14/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/z/14/basket.json \
  --last 24 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/z/14/views.json
```

## Відповідь агента
Виправив опечатку: «Pyhton» → «Python».

Тема: «Python» (Q28865).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.

- Англійська Wikipedia (en): 3 084 438 переглядів за період (стаття «Python (programming language)» і 50 перенаправлень).
- Німецька Wikipedia (de): 295 185 переглядів за період (стаття «Python (Programmiersprache)» і 5 перенаправлень).

Це лише суми переглядів. Чи зростає інтерес, як він змінювався в часі й наскільки цьому можна довіряти, покаже аналіз тренду (етап 3), який ще в розробці; тоді ж з'являться графіки й рекомендації. Абсолютні числа різних мовних розділів не можна порівнювати як міру інтересу: розділи мають дуже різну аудиторію, коректне порівняння (відносні зміни) буде на етапі 3.
