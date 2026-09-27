## Користувач
Порівняй тренд \"Pyhton programming\" між англійською та німецькою Wikipedia.

## Команди агента
```bash
cd <skill> && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "en:Python programming" \
  --query "en:Python programming" \
  --targets en,de \
  --user-message "Порівняй тренд \"Pyhton programming\" між англійською та німецькою Wikipedia." \
  --out <tmp>/x/14_1/basket.json
cd <skill> && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket <tmp>/x/14_1/basket.json \
  --out <tmp>/x/14_1/views.json
```

## Відповідь агента
Я виправив опечатку у вашому запиті: "Pyhton" → "Python". Тема ідентифікована в обох мовних розділах Вікіпедії:
- **Англійська Wikipedia**: "Python (programming language)"
- **Німецька Wikipedia**: "Python (Programmiersprache)"

Дані зібрані за останні 24 місяці (вересень 2024 – серпень 2026), оскільки період не вказано.

**Загальні перегляди за період:**
- **Англійська Wikipedia**: 3 084 438 переглядів (51 статтю/перенаправлення)
- **Німецька Wikipedia**: 295 185 переглядів (6 статей/перенаправлень)

Детальні дані за кожен місяць зібрані в файли basket.json та views.json.

**Важливо:** Аналіз тренду, графіки й висновки про зростання чи падіння інтересу будуть доступні на етапі 3, який ще в розробці. На цьому етапі можна назвати суми переглядів, але не порівнювати абсолютні числа між мовами як міру інтересу, оскільки мовні розділи мають дуже різну аудиторію.

