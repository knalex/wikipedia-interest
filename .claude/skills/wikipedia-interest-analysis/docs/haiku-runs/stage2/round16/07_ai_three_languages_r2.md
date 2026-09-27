
## Користувач
Порівняй інтерес до "штучного інтелекту" в українській, польській та чеській Wikipedia.

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && \
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "uk:штучний інтелект" \
  --query "en:artificial intelligence" \
  --targets uk,pl,cs \
  --user-message "Порівняй інтерес до \"штучного інтелекту\" в українській, польській та чеській Wikipedia." \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/07_2/basket.json

cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && \
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/07_2/basket.json \
  --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/y/07_2/views.json
```

## Відповідь агента
Тема: «штучний інтелект» (Q11660).
Період: вересень 2024 — серпень 2026 (24 місяці). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.

- Українська Wikipedia (uk): 218 899 переглядів за період (стаття «Штучний інтелект» і 7 перенаправлень).
- Польська Wikipedia (pl): 305 307 переглядів за період (стаття «Sztuczna inteligencja»).
- Чеська Wikipedia (cs): 143 966 переглядів за період (стаття «Umělá inteligence» і 4 перенаправлення).

Зверніть увагу:
- Період не названо, тому взято типовий: 24 останні завершені місяці.

Це лише суми переглядів. Чи зростає інтерес, як він змінювався в часі й наскільки цьому можна довіряти, покаже аналіз тренду (етап 3), який ще в розробці; тоді ж з'являться графіки й рекомендації. Абсолютні числа різних мовних розділів не можна порівнювати як міру інтересу: розділи мають дуже різну аудиторію, коректне порівняння (відносні зміни) буде на етапі 3.
