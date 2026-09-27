## Користувач
Порівняй тренд "Pyhton programming" між англійською та німецькою Wikipedia.

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:Python" \
  --query "en:Python (programming language)" \
  --targets en,de \
  --user-message "Порівняй тренд \"Pyhton programming\" між англійською та німецькою Wikipedia." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/14/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/14/basket.json \
  --last 24 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/14/views.json

python3 scripts/analyze_trend.py \
  --views /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/14/views.json \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/14/analysis.json
```

## Відповідь агента
Я виправив опечатку: "Pyhton" → "Python".

Тема: «Python» (Q28865).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю останні 12 місяців (вересень 2025 — серпень 2026) з попередніми 12 (вересень 2024 — серпень 2025) — так сезонні коливання не спотворюють висновок.

- Англійська Wikipedia (en): без явної зміни, −6 % (1 495 211 переглядів проти 1 589 227). Довіра: висока.
  - Уся en.wikipedia за той самий час: −7 %; з поправкою на це зміна теми +1 %.
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.
- Німецька Wikipedia (de): інтерес падає, −22 % (129 707 переглядів проти 165 478). Довіра: висока.
  - Уся de.wikipedia за той самий час: −7 %; з поправкою на це зміна теми −15 %.
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.

Порівняння мов (за відносною зміною з поправкою на загальну відвідуваність кожного розділу, не за абсолютними числами — розділи мають дуже різну аудиторію):
- en +1 %, de −15 %.
- Відносно найшвидше зростає інтерес — Англійська Wikipedia (en), довіра: висока.

Графік: /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/14/views.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.
