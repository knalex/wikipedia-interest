## Користувач
Is interest in ChatGPT growing faster in the German or the French Wikipedia?

## Команди агента
```bash
cd <skill> && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/resolve_topic.py \
  --query "en:ChatGPT" \
  --targets de,fr \
  --user-message "Is interest in ChatGPT growing faster in the German or the French Wikipedia?" \
  --out <tmp>/s2r/20/basket.json

cd <skill> && WIKIPEDIA_RESOLVER_CONTACT="you@example.com" python3 scripts/fetch_pageviews.py \
  --basket <tmp>/s2r/20/basket.json \
  --last 24 \
  --out <tmp>/s2r/20/views.json
```

## Відповідь агента
Я зібрав дані про перегляди статей про ChatGPT за останні 24 місяці (вересень 2024 — серпень 2026) в німецьких та французьких розділах Вікіпедії.

**Німецька Вікіпедія (de.wikipedia):**
- Всього переглядів за період: 7 083 614
- Статей в кошику: 2 (основна стаття ChatGPT + перенаправлення ChatGPT Plus)

**Французька Вікіпедія (fr.wikipedia):**
- Всього переглядів за період: 4 973 618
- Статей в кошику: 3 (основна стаття ChatGPT + перенаправлення Chatgpt та Chat gpt)

Дані показують, що в немецькомовному розділі Вікіпедії статті про ChatGPT мали більше переглядів в абсолютних цифрах. Однак я не можу робити висновків про темп росту інтересу — цей аналіз належить до етапу 3 (аналіз трендів), який ще знаходиться в розробці.

Для коректного порівняння потрібно враховувати різницю в аудиторіях мовних розділів Вікіпедії, що буде зроблено на наступному етапі.
