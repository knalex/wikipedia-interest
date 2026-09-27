## Користувач
Порівняй, як змінився інтерес до ШІ в українській і польській Wikipedia з 2023 року.

## Команди агента
```bash
mkdir -p /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/u/06
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:ШІ" \
  --query "uk:Штучний інтелект" \
  --query "en:Artificial intelligence" \
  --targets uk,pl \
  --user-message "Порівняй, як змінився інтерес до ШІ в українській і польській Wikipedia з 2023 року." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/u/06/basket.json
```

## Відповідь агента
Знайдено статтю про штучний інтелект в обох мовних розділах. Проте абревіатура «ШІ» може означати кілька речей. **Перед тим як збирати дані переглядів, мені потрібне уточнення:**

**Під «ШІ» ви маєте на увазі штучний інтелект (розділ інформатики)?**

Якщо так, я продовжу збір даних про перегляди сторінок "Штучний інтелект" в українській Вікіпедії та "Sztuczna inteligencja" в польській Вікіпедії з січня 2023 року.

Якщо ви мали на увазі щось інше — напишіть, і я перезапущу пошук з вашими уточненнями.

## Користувач
Так, ШІ — це штучний інтелект.

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/u/06/basket.json \
  --start 2023-01 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/u/06/views.json

cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && python3 scripts/analyze_trend.py \
  --views /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/u/06/views.json \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/u/06/analysis.json
```

## Відповідь агента
Тема: «штучний інтелект» (Q11660).
Період: січень 2023 — серпень 2026 (44 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю останні 12 місяців (вересень 2025 — серпень 2026) з попередніми 12 (вересень 2024 — серпень 2025) — так сезонні коливання не спотворюють висновок.

- Українська Wikipedia (uk): інтерес падає, −35 % (86 174 перегляди проти 132 725). Довіра: висока.
  - Уся uk.wikipedia за той самий час: −25 %; з поправкою на це зміна теми −14 %.
  - За весь період: перші 12 місяців (січень 2023 — грудень 2023) → останні 12: −45 % (86 174 проти 155 942).
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.
- Польська Wikipedia (pl): інтерес падає, −34 % (120 979 переглядів проти 184 328). Довіра: висока.
  - Уся pl.wikipedia за той самий час: −9 %; з поправкою на це зміна теми −28 %.
  - За весь період: перші 12 місяців (січень 2023 — грудень 2023) → останні 12: −50 % (120 979 проти 240 932).
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.

Порівняння мов (за відносною зміною з поправкою на загальну відвідуваність кожного розділу, не за абсолютними числами — розділи мають дуже різну аудиторію):
- uk −14 %, pl −28 %.
- Відносно найменше падіння інтересу — Українська Wikipedia (uk), довіра: висока.

Графік: /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/u/06/views.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.
