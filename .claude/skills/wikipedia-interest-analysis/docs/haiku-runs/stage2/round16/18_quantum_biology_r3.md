
## Користувач
Чи зростає інтерес до теми "квантова біологія" у шведській Wikipedia?

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:квантова біологія" \
  --query "en:quantum biology" \
  --targets sv \
  --user-message "Чи зростає інтерес до теми \"квантова біологія\" у шведській Wikipedia?" \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/18_3/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/18_3/basket.json \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/18_3/views.json
```

## Відповідь агента
Тема: «Квантова біологія» (Q1429339).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.

- Шведська Wikipedia (sv): 660 переглядів за період (стаття «Kvantbiologi»).

Зверніть увагу:
- Період не названо, тому взято типовий: 24 останні завершені місяці.

Це лише суми переглядів. Чи зростає інтерес, як він змінювався в часі й наскільки цьому можна довіряти, покаже аналіз тренду (етап 3), який ще в розробці; тоді ж з'являться графіки й рекомендації.
