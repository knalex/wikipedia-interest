## Користувач
Порівняй тренд "Pyhton programming" між англійською та німецькою Wikipedia.

## Команди агента
```bash
cd <repo> && WIKIPEDIA_RESOLVER_CONTACT=you@example.com python3 .claude/skills/wikipedia-interest-analysis/scripts/resolve_topic.py \
  --query "en:Python programming" \
  --targets en,de \
  --user-message "Порівняй тренд \"Pyhton programming\" між англійською та німецькою Wikipedia." \
  --out <tmp>/x/14_3/basket.json

cd <repo> && WIKIPEDIA_RESOLVER_CONTACT=you@example.com python3 .claude/skills/wikipedia-interest-analysis/scripts/fetch_pageviews.py \
  --basket <tmp>/x/14_3/basket.json \
  --out <tmp>/x/14_3/views.json
```

## Відповідь агента
Я виправив опечатку "Pyhton" → "Python" і зібрав дані за останні 24 місяці (вересень 2024 — серпень 2026).

**Етап 1: Визначення теми** ✓ Знайдено
- Тема: Python (мова програмування загального призначення, Q28865)
- Англійська Wikipedia: "Python (programming language)"
- Німецька Wikipedia: "Python (Programmiersprache)"
- Поняття охоплене 122 мовними розділами

**Етап 2: Збір переглядів** ✓ Готово
Період не вказано; взято останні завершені місяці (24 місяці).

| Мова | Проект | Переглядів за період | Статей у кошику |
|---|---|---|---|
| Англійська | en.wikipedia | 3,084,438 | 51 |
| Німецька | de.wikipedia | 295,185 | 6 |

**Важливо**: Не порівнюй абсолютні числа між мовами як міру інтересу — мовні розділи мають дуже різну аудиторію. Коректне порівняння тренду (відносні зміни, чи інтерес зростає чи падає) буде на етапі 3, який ще в розробці.

Дані збережено в `<tmp>/x/14_3/views.json` для подальшого аналізу.
