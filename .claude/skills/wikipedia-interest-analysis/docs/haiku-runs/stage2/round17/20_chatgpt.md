## Користувач
Is interest in ChatGPT growing faster in the German or the French Wikipedia?

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "en:ChatGPT" \
  --targets de,fr \
  --user-message "Is interest in ChatGPT growing faster in the German or the French Wikipedia?" \
  --out "<tmp>/z/20/basket.json"

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket "<tmp>/z/20/basket.json" \
  --out "<tmp>/z/20/views.json"
```

## Відповідь агента
Тема: «Чат Джі Пі Ті» (Q115564437).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.

- Німецька Wikipedia (de): 7 083 614 переглядів за період (стаття «ChatGPT» і 1 перенаправлення).
- Французька Wikipedia (fr): 4 973 618 переглядів за період (стаття «ChatGPT» і 2 перенаправлення).

Зверніть увагу:
- Період не названо, тому взято типовий: 24 останні завершені місяці.

Це лише суми переглядів. Чи зростає інтерес, як він змінювався в часі й наскільки цьому можна довіряти, покаже аналіз тренду (етап 3), який ще в розробці; тоді ж з'являться графіки й рекомендації. Абсолютні числа різних мовних розділів не можна порівнювати як міру інтересу: розділи мають дуже різну аудиторію, коректне порівняння (відносні зміни) буде на етапі 3.
