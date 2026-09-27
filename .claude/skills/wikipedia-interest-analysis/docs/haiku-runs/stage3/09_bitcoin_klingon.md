## Користувач
Сравни интерес к биткоину в польской и клингонской Википедии.

## Команди агента
```bash
# Stage 1: Resolve Bitcoin topic — FAILED, tlh edition does not exist
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "ru:биткоин" \
  --query "en:Bitcoin" \
  --targets pl,tlh \
  --user-message "Сравни интерес к биткоину в польской и клингонской Википедии." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/09/basket.json
```

## Відповідь агента
Розділу Вікіпедії для клингонської мови (tlh) немає. Яку мову Вікіпедії Ви мали на увазі? (Наприклад: англійська, німецька, французька, іспанська, українська, чеська). Будь ласка, вкажіть, яка саме мова Вікіпедії вас цікавить, і я почну аналіз.

## Користувач (уточнення)
Тогда английскую вместо клингонской.

## Команди агента
```bash
# Stage 1: Resolve Bitcoin topic in Polish and English Wikipedia
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "ru:биткоин" \
  --query "en:Bitcoin" \
  --targets pl,en \
  --user-message "Сравни интерес к биткоину в польской и клингонской Википедии." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/09/basket.json

# Stage 2: Fetch pageviews for Bitcoin in Polish and English Wikipedia
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/09/basket.json \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/09/views.json

# Stage 3: Analyze trend and generate comparison chart
python3 scripts/analyze_trend.py \
  --views /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/09/views.json \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/09/analysis.json
```

## Відповідь агента
Тема: «біткойн» (Q131723).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю останні 12 місяців (вересень 2025 — серпень 2026) з попередніми 12 (вересень 2024 — серпень 2025) — так сезонні коливання не спотворюють висновок.

- Польська Wikipedia (pl): інтерес падає, −39 % (90 966 переглядів проти 148 649). Довіра: висока.
  - Уся pl.wikipedia за той самий час: −9 %; з поправкою на це зміна теми −33 %.
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.
- Англійська Wikipedia (en): інтерес падає, −41 % (1 428 900 переглядів проти 2 427 040). Довіра: висока.
  - Уся en.wikipedia за той самий час: −7 %; з поправкою на це зміна теми −37 %.
  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.

Порівняння мов (за відносною зміною з поправкою на загальну відвідуваність кожного розділу, не за абсолютними числами — розділи мають дуже різну аудиторію):
- pl −33 %, en −37 %.
- Різниця між першими двома менша за 10 п. п. — вважайте динаміку однаковою.

Зверніть увагу:
- Період не названо, тому взято типовий: 24 останні завершені місяці.

Графік: /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/w/09/views.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.
