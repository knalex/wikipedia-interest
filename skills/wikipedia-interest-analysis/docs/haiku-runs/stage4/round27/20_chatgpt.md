## Користувач
Is interest in ChatGPT growing faster in the German or the French Wikipedia?

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 skills/wikipedia-interest-analysis/scripts/resolve_topic.py \
  --query "en:ChatGPT" \
  --targets de,fr \
  --user-message "Is interest in ChatGPT growing faster in the German or the French Wikipedia?"

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 skills/wikipedia-interest-analysis/scripts/fetch_pageviews.py --basket wikipedia-interest-output/20260927-152102-Q115564437/basket.json

python3 skills/wikipedia-interest-analysis/scripts/analyze_trend.py --views wikipedia-interest-output/20260927-152102-Q115564437/views.json
```

## Відповідь агента
Тема: «Чат Джі Пі Ті» (Q115564437).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю останні 12 місяців (вересень 2025 — серпень 2026) з попередніми 12 (вересень 2024 — серпень 2025) — так сезонні коливання не спотворюють висновок.

- Німецька Wikipedia (de): інтерес падає, −12 % (3 322 022 перегляди проти 3 761 592). Довіра: висока.
  - Уся de.wikipedia за той самий час: −7 %; з поправкою на це зміна теми −5 % — відносно всього розділу без явної зміни.
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.
- Французька Wikipedia (fr): інтерес падає, −12 % (2 335 064 перегляди проти 2 638 554). Довіра: висока.
  - Уся fr.wikipedia за той самий час: −11 %; з поправкою на це зміна теми −1 % — відносно всього розділу без явної зміни.
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.

Порівняння мов (за відносною зміною з поправкою на загальну відвідуваність кожного розділу, не за абсолютними числами — розділи мають дуже різну аудиторію):
- fr −1 %, de −5 %.
- Різниця між мовами менша за 10 п. п. — вважайте динаміку однаковою.

Зверніть увагу:
- Період не названо, тому взято типовий: 24 останні завершені місяці.

Графік: wikipedia-interest-output/20260927-152102-Q115564437/views.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.

Створено теку з результатами: <repo>/wikipedia-interest-output/20260927-152102-Q115564437/
У ній:
- basket.json — кошик статей (етап 1)
- views.json — перегляди по місяцях чи днях (етап 2)
- analysis.json — аналіз тренду й довіри (етап 3)
- views.svg — графік (етап 3)
(Тека wikipedia-interest-output/ має власний .gitignore, тож у git ці файли не потрапляють.)

Можу зробити з цього звіт на одну сторінку (PDF), яким зручно поділитися з командою.
