## Користувач
Покажи тренд переглядів статті "Bitcoin" з 2010 по 2015 рік в англійській Wikipedia.

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:Bitcoin" \
  --query "en:Bitcoin" \
  --targets en \
  --user-message "Покажи тренд переглядів статті \"Bitcoin\" з 2010 по 2015 рік в англійській Wikipedia." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/15_3/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/15_3/basket.json \
  --start 2010-01 \
  --end 2015-12 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/15_3/views.json
```

## Відповідь агента
Тема: «біткойн» (Q131723).
Період: липень 2015 — грудень 2015 (6 місяців). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.

- Англійська Wikipedia (en): 1 715 320 переглядів за період (стаття «Bitcoin» і 47 перенаправлень).

Зверніть увагу:
- Запитано з 2010-01, але Pageviews API має дані лише з 1 липня 2015 року; період обрізано до 2015-07 — 2015-12.

Це лише суми переглядів. Чи зростає інтерес, як він змінювався в часі й наскільки цьому можна довіряти, покаже аналіз тренду (етап 3), який ще в розробці; тоді ж з'являться графіки й рекомендації.

