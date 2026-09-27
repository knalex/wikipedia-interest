## Користувач
Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки.

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:інтервальне голодування" \
  --query "en:intermittent fasting" \
  --query "pl:post przerywany" \
  --targets pl,cs \
  --user-message "Порівняй зростання інтересу до інтервального голодування в польськомовній та чеськомовній Wikipedia за останні два роки." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/s2r/01/basket.json
```

## Відповідь агента
У чеській Вікіпедії є стаття про інтервальне голодування ("Přerušovaný půst"), але у польській не має. Фраза "post przerywany" згадується тільки в 3 інших статтях (про опір інсуліну, надвагу та моржування).

Це означає, що порівняння буде асиметричним — ми вимірюватимемо різні набори статей. Виберіть, як далі:
1. Порівнювати тільки по чеській Вікіпедії
2. Додати для польської рубрику "Post" (піст у широкому розумінні) — але це інша тема
3. Відмовитися від порівняння

---

## Користувач
Варіант 1 — дивимось тільки чеську Вікіпедію.

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/s2r/01/basket.json \
  --last 24 \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/s2r/01/views.json
```

## Відповідь агента
Зібрав дані переглядів для чеської Вікіпедії за останні 24 місяці (вересень 2024 – серпень 2026):

**Статті про інтервальне голодування в чеській Вікіпедії:**
- Стаття: "Přerušovaný půst"
- Всього переглядів за період: **6,939**

**Розподіл переглядів по місяцях:**
- Найвищий: квітень 2025 (958 переглядів)
- Найнижчий: липень 2026 (91 перегляд)
- Діапазон: від 91 до 958 переглядів на місяць

**Обмеження:** Аналіз тренду та графіки (етап 3) ще в розробці. Наразі я можу лише назвати суми переглядів, але не робити висновків про те, чи зростає інтерес до теми.
