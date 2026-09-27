## Користувач
Сравни интерес к биткоину в польской и клингонской Википедии.

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && \
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "ru:биткоин" \
  --query "en:bitcoin" \
  --targets pl,tlh \
  --user-message "Сравни интерес к биткоину в польской и клингонской Википедии." \
  --out "/tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/09_3/basket.json"
```

## Відповідь агента
Розділу Вікіпедії клінґонською мовою (код tlh) не існує. Клінґонська — це вигаданий мовний конструкт із фантастичного серіалу Star Trek, і вона не має офіційного розділу на Вікіпедії.

Яку іншу мову ви хочете порівняти з польською? Наприклад, можна порівняти:
- **Англійську** (en)
- **Українську** (uk)  
- **Німецьку** (de)
- **Французьку** (fr)
- **Іспанську** (es)

Будь ласка, виберіть одну з цих мов, або назвіть іншу мову, яка вас цікавить.

## Користувач
Тогда английскую вместо клингонской.

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && \
WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "ru:биткоин" \
  --query "en:bitcoin" \
  --targets pl,en \
  --user-message "Сравни интерес к биткоину в польской и клингонской Википедии." \
  --user-message "Тогда английскую вместо клингонской." \
  --out "/tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/x/09_3/basket.json"
```

## Відповідь агента
Тема визначена. Буде проаналізовано статті про біткойн в польській та англійській Вікіпедії.

Який період вас цікавить? Наприклад:
- За останні 24 місяці (типово)
- За останні 12 місяців
- З конкретного року (напр., з 2023 року)
- За конкретний період (напр., з 2020 по 2024)

Якщо період не вкажете, буду вимірювати останні 24 місяці.
