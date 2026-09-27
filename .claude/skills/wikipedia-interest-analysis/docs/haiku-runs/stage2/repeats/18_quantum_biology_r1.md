## Користувач
Чи зростає інтерес до теми "квантова біологія" у шведській Wikipedia?

## Команди агента
```bash
cd <skill> && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:квантова біологія" \
  --query "en:quantum biology" \
  --targets sv \
  --user-message "Чи зростає інтерес до теми \"квантова біологія\" у шведській Wikipedia?" \
  --out <tmp>/x/18_1/basket.json

cd <skill> && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket <tmp>/x/18_1/basket.json \
  --last 24 \
  --out <tmp>/x/18_1/views.json
```

## Відповідь агента
Дані про "квантову біологію" зібрані для шведської Wikipedia.

Статтю "Kvantbiologi" (квантова біологія) переглядали 660 разів за останні 24 місяці (вересень 2024 — серпень 2026).

Місячні дані показують:
- Найменше переглядів: 12 (лютий і березень 2026)
- Найбільше переглядів: 50 (квітень 2025)
- Всього: 660 переглядів за період

Дані зібрані через Wikimedia Pageviews API. Аналіз тренду та висновків про зростання чи падіння інтересу (етап 3) ще розробляється.

