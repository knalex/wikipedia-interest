## Користувач
Is interest in ChatGPT growing faster in the German or the French Wikipedia?

## Команди агента
```bash
cd <skill> && WIKIPEDIA_RESOLVER_CONTACT=you@example.com python3 scripts/resolve_topic.py \
  --query "en:ChatGPT" \
  --targets de,fr \
  --user-message "Is interest in ChatGPT growing faster in the German or the French Wikipedia?" \
  --out <tmp>/x/20_3/basket.json

cd <skill> && WIKIPEDIA_RESOLVER_CONTACT=you@example.com python3 scripts/fetch_pageviews.py \
  --basket <tmp>/x/20_3/basket.json \
  --last 24 \
  --out <tmp>/x/20_3/views.json
```

## Відповідь агента
Я зібрав дані про перегляди статті ChatGPT у німецькій та французькій Вікіпедії за останні 24 місяці (вересень 2024 — серпень 2026).

**Німецька Вікіпедія (de.wikipedia):**
- Загалом переглядів: 7 083 614
- Статті: 2 (основна стаття + 1 перенаправлення)

**Французька Вікіпедія (fr.wikipedia):**
- Загалом переглядів: 4 973 618
- Статті: 3 (основна стаття + 2 перенаправлення)

**Важливе зауваження:** Я не можу порівнювати абсолютні числа переглядів між мовними розділами як міру інтересу, оскільки вони мають дуже різну аудиторію. Для коректного порівняння того, в якій мові зростає інтерес швидше, потрібна аналізація трендів (етап 3), яка ще розробляється.

Повні дані про помісячні перегляди зберігаються у файлі views.json.
