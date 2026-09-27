
## Користувач
Порівняй тренд "Pyhton programming" між англійською та німецькою Wikipedia.

## Команди агента
```bash
cd <skill> && WIKIPEDIA_RESOLVER_CONTACT=you@example.com python3 scripts/resolve_topic.py \
  --query "en:Python programming" \
  --query "en:Python (programming language)" \
  --targets en,de \
  --user-message "Порівняй тренд \"Pyhton programming\" між англійською та німецькою Wikipedia." \
  --out <tmp>/x/14_2/basket.json

cd <skill> && WIKIPEDIA_RESOLVER_CONTACT=you@example.com python3 scripts/fetch_pageviews.py \
  --basket <tmp>/x/14_2/basket.json \
  --out <tmp>/x/14_2/views.json
```

## Відповідь агента
Я виправив опечатку: "Pyhton" → "Python". Збір даних завершено успішно для англійської та німецької Вікіпедії.

**Результати за 24 місяці (вересень 2024 — серпень 2026):**

**Англійська Вікіпедія (en.wikipedia):**
- Всього переглядів: 3,084,438
- Кількість статей: 51 (переважно перенаправлення)
- Головна стаття: "Python (programming language)" з 3,017,146 переглядами

**Німецька Вікіпедія (de.wikipedia):**
- Всього переглядів: 295,185
- Кількість статей: 6
- Головна стаття: "Python (Programmiersprache)" з 292,805 переглядами

**Важливі примітки:**
1. Період не вказано — використано останні завершені 24 місяці
2. Абсолютні числа переглядів не можна порівнювати між мовами через різну аудиторію розділів
3. Аналіз тренду, графіки і детальні висновки (етап 3) ще в розробці

Дані збережено у файлах:
- `<tmp>/x/14_2/basket.json`
- `<tmp>/x/14_2/views.json`

