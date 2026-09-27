## Користувач
Сравни интерес к Меркурию в польской и чешской Википедии за последний год.

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 .claude/skills/wikipedia-interest-analysis/scripts/resolve_topic.py \
  --query "ru:Меркурий" \
  --query "en:Mercury" \
  --targets pl,cs \
  --user-message "Сравни интерес к Меркурию в польской и чешской Википедии за последний год." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/05_1/basket.json
```

## Відповідь агента
Знайдено три варіанти для "Меркурія":

1. **Меркурій (планета)** (Q308) — найближча до Сонця велика планета Сонячної системи
   - Польська Вікіпедія: *Merkury*
   - Чеська Вікіпедія: *Merkur (planeta)*

2. **Ртуть (хімічний елемент)** (Q925) — хімічний елемент з атомним номером 80
   - Польська Вікіпедія: *Rtęć*
   - Чеська Вікіпедія: *Rtuť*

3. **Меркурій (міфологія)** (Q1150) — римський бог торгівлі, купців, крадіїв і подорожей
   - Польська Вікіпедія: *Merkury (mitologia)*
   - Чеська Вікіпедія: *Merkur (mytologie)*

Очікую уточнення користувача щодо того, який з цих варіантів він має на увазі.

## Користувач (уточнення)
Планета, конечно.

## Команди агента
```bash
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 .claude/skills/wikipedia-interest-analysis/scripts/resolve_topic.py \
  --query "ru:Меркурий" \
  --query "en:Mercury" \
  --targets pl,cs \
  --user-message "Сравни интерес к Меркурию в польской и чешской Википедии за последний год." \
  --entity Q308 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/05_1/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 .claude/skills/wikipedia-interest-analysis/scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/05_1/basket.json \
  --last 12 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/05_1/views.json
```

## Відповідь агента
Чудово! Тема визначена — Меркурій як планета (Q308). Тепер збрані дані про перегляди за останній рік (вересень 2025 — серпень 2026):

**Польська Вікіпедія (pl.wikipedia):**
- Всього переглядів: **61 511**
- Статей у наборі: 3 (основна стаття *Merkury*, перенаправлення)
- Розподіл за місяцями: піки у жовтні (6 086) та квітні (8 478)

**Чеська Вікіпедія (cs.wikipedia):**
- Всього переглядів: **30 686**
- Статей у наборі: 3 (основна стаття *Merkur (planeta)*, перенаправлення)
- Розподіл за місяцями: піки у вересні-жовтні 2025 (3 655, 3 980)

**Важливе зауваження:** Не варто порівнювати абсолютні цифри переглядів між мовами як міру інтересу — мовні розділи мають дуже різну аудиторію (словацька, польська, чеська розділи різняться за кількістю читачів). Детальний аналіз тренду та коректне порівняння (відносні зміни) будуть доступні на етапі 3, який ще в розробці.
