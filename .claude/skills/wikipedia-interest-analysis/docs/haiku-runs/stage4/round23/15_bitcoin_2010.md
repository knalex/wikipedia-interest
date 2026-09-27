## Користувач
Покажи тренд переглядів статті "Bitcoin" з 2010 по 2015 рік в англійській Wikipedia.

## Команди агента
```bash
—
```

## Відповідь агента
На жаль, тренд з 2010 по 2015 рік неможливо отримати. API переглядів Wikimedia має дані лише з **1 липня 2015 року** і не охоплює раніший період.

Можу запропонувати кілька варіантів:
1. **Тренд з липня 2015 по сьогодні** — показати, як змінювалась кількість переглядів статті «Bitcoin» на англійській Wikipedia за останні роки
2. **Іншу тему** — якщо вас цікавить інтерес до якоїсь іншої теми
3. **Інший період** — якщо вас цікавить період після липня 2015 року

Яку опцію ви виберете?

## Користувач
Добре, покажи з липня по грудень 2015.

## Команди агента
```bash
cd /home/alex/Interest/wikipedia-interest/.claude/skills/wikipedia-interest-analysis && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py --query "uk:Біткойн" --query "en:Bitcoin" --targets en --user-message "Покажи тренд переглядів статті \"Bitcoin\" з 2010 по 2015 рік в англійській Wikipedia." --user-message "Добре, покажи з липня по грудень 2015." --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/15/basket.json

WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py --basket /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/15/basket.json --start 2015-07 --end 2015-12 --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/15/views.json

python3 scripts/analyze_trend.py --views /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/15/views.json --out /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/15/analysis.json --chart /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/15/chart.svg
```

## Відповідь агента
Тема: «біткойн» (Q131723).
Період: липень 2015 — грудень 2015 (6 місяців). Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.
Порівнюю другу половину періоду (жовтень 2015 — грудень 2015) з першою (липень 2015 — вересень 2015).

- Англійська Wikipedia (en): без явної зміни, +7 % (888 198 переглядів проти 827 122). Довіра: середня.
  - Уся en.wikipedia за той самий час: −1 %; з поправкою на це зміна теми +8 %.
  - Період коротший за 2 роки, тож порівнюються дві його половини і сезонність не врахована.

Графік: /tmp/claude-1000/-home-alex-Interest-----/c7af1123-6abc-4b3d-9aa0-04efdd5b9d60/scratchpad/r/15/chart.svg
Поріг: зміна менша за ±10 % вважається «без явної зміни».
Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією мовою і залежать від пошукових систем, новин і назв статей.

Можу зробити з цього звіт на одну сторінку (PDF), яким зручно поділитися з командою.
