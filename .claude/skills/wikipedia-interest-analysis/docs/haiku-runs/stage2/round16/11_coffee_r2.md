## Користувач
Порівняй інтерес до кави в польській і чеській Wikipedia за останні 3 роки.

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:кава" \
  --query "en:coffee" \
  --query "pl:kawa" \
  --query "cs:káva" \
  --targets pl,cs \
  --user-message "Порівняй інтерес до кави в польській і чеській Wikipedia за останні 3 роки." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/11_2/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/11_2/basket.json \
  --last 36 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/11_2/views.json
```

## Відповідь агента
Тема: «кава» (Q8486).
Період: вересень 2023 — серпень 2026 (36 місяців). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.

- Польська Wikipedia (pl): 121 763 перегляди за період (стаття «Kawa»).
- Чеська Wikipedia (cs): 49 875 переглядів за період (стаття «Káva» і 4 перенаправлення).

Це лише суми переглядів. Чи зростає інтерес, як він змінювався в часі й наскільки цьому можна довіряти, покаже аналіз тренду (етап 3), який ще в розробці; тоді ж з'являться графіки й рекомендації. Абсолютні числа різних мовних розділів не можна порівнювати як міру інтересу: розділи мають дуже різну аудиторію, коректне порівняння (відносні зміни) буде на етапі 3.

## Користувач
Додай ще словацьку Wikipedia до порівняння.

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:кава" \
  --query "en:coffee" \
  --query "pl:kawa" \
  --query "cs:káva" \
  --query "sk:kava" \
  --targets pl,cs,sk \
  --user-message "Порівняй інтерес до кави в польській і чеській Wikipedia за останні 3 роки." \
  --user-message "Додай ще словацьку Wikipedia до порівняння." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/11_2/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/11_2/basket.json \
  --last 36 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/11_2/views.json
```

## Відповідь агента
Тема: «кава» (Q8486).
Період: вересень 2023 — серпень 2026 (36 місяців). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.

- Польська Wikipedia (pl): 121 763 перегляди за період (стаття «Kawa»).
- Чеська Wikipedia (cs): 49 875 переглядів за період (стаття «Káva» і 4 перенаправлення).
- Словацька Wikipedia (sk): 18 494 перегляди за період (стаття «Káva»).

Це лише суми переглядів. Чи зростає інтерес, як він змінювався в часі й наскільки цьому можна довіряти, покаже аналіз тренду (етап 3), який ще в розробці; тоді ж з'являться графіки й рекомендації. Абсолютні числа різних мовних розділів не можна порівнювати як міру інтересу: розділи мають дуже різну аудиторію, коректне порівняння (відносні зміни) буде на етапі 3.
