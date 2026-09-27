# Інтерес до тем у Вікіпедії — навичка для AI-агента

Навичка у форматі [Agent Skills](https://agentskills.io/specification): агент
аналізує статистику переглядів Вікіпедії, оцінює, наскільки можна довіряти
зростанню, порівнює мовні розділи, будує графіки й готує звіт на одну сторінку
PDF. Допомагає командам B2C-продуктів вирішити, які теми розвивати і якими
мовами запускатися.

Усе — в директорії навички
[`.claude/skills/wikipedia-interest-analysis/`](.claude/skills/wikipedia-interest-analysis/):

| Що | Де |
|---|---|
| Інструкції для агента | [`SKILL.md`](.claude/skills/wikipedia-interest-analysis/SKILL.md) |
| Код (етапи 1–4) | [`scripts/`](.claude/skills/wikipedia-interest-analysis/scripts/) |
| Хід роботи й перевірки | [`docs/process.md`](.claude/skills/wikipedia-interest-analysis/docs/process.md) |
| Опис завдання | [`docs/task.md`](.claude/skills/wikipedia-interest-analysis/docs/task.md) |
| Перевірка на Claude Haiku 4.5 | [`docs/haiku-evaluation.md`](.claude/skills/wikipedia-interest-analysis/docs/haiku-evaluation.md) |
| План розвитку | [`docs/roadmap.md`](.claude/skills/wikipedia-interest-analysis/docs/roadmap.md) |
| Приклади й PDF-звіти | [`examples/`](.claude/skills/wikipedia-interest-analysis/examples/README.md) |

Вимоги: Python 3.8+, лише стандартна бібліотека, мережа для Wikidata й
Wikimedia Pageviews API. Тести без мережі:

```bash
cd .claude/skills/wikipedia-interest-analysis
python3 -m unittest discover -s tests
```
