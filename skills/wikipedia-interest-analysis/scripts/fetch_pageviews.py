#!/usr/bin/env python3
"""
fetch_pageviews.py — етап 2: збирає перегляди статей із кошика теми
(basket.json з resolve_topic.py) через Wikimedia Pageviews API і складає ряди
переглядів по кожному мовному розділу.

- Лише перегляди людей (agent=user, без ботів), усі платформи (all-access).
- Місячні (типово) або денні ряди. Поточний неповний місяць чи день
  відкидається: API повертає його частково, і графік хибно «падав» би в кінці.
- Даних немає до 1 липня 2015 року: період обрізається з попередженням.
- Періоди без переглядів API не повертає — вони заповнюються нулями.
- Перенаправлення підсумовуються з основною статтею.
- Відповіді за завершені періоди кешуються на диску, тож повторні й пов'язані
  запити (напр., додати ще одну мову) не ходять у мережу вдруге.

Використовується тільки стандартна бібліотека Python.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_topic import (  # noqa: E402
    CONTACT_ENV_VAR, REPLY_LANGUAGE, USER_AGENT_TEMPLATE, ResolverError, WikimediaClient, request_key,
)

PAGEVIEWS_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
AGGREGATE_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate"
DATA_START = dt.date(2015, 7, 1)
DEFAULT_LAST = {"monthly": 24, "daily": 90}
CACHE_ENV_VAR = "WIKIPEDIA_INTEREST_CACHE"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "wikipedia-interest-analysis"
# Дані за щойно завершений період API довантажує із запізненням; такі
# відповіді не кешуємо, щоб не закешувати неповні числа.
CACHE_SETTLE_DAYS = 3
TOP_ARTICLES_STDOUT = 5
UNIT = {"monthly": "місяць", "daily": "день"}
MONTHS_UK = ["січень", "лютий", "березень", "квітень", "травень", "червень",
             "липень", "серпень", "вересень", "жовтень", "листопад", "грудень"]
LANG_NAMES_UK = {
    "uk": "Українська", "en": "Англійська", "de": "Німецька", "fr": "Французька", "es": "Іспанська",
    "it": "Італійська", "pl": "Польська", "cs": "Чеська", "sk": "Словацька", "ja": "Японська",
    "sv": "Шведська", "ru": "Російська", "pt": "Португальська", "nl": "Нідерландська", "zh": "Китайська",
    "ko": "Корейська", "tr": "Турецька", "ar": "Арабська", "hu": "Угорська", "ro": "Румунська",
    "fi": "Фінська", "da": "Данська", "no": "Норвезька", "be": "Білоруська", "lt": "Литовська",
    "lv": "Латиська", "et": "Естонська", "bg": "Болгарська", "hr": "Хорватська", "sr": "Сербська",
    "el": "Грецька",
}
LANG_NOUNS_UK = {"he": "іврит", "hi": "гінді", "eo": "есперанто"}  # не узгоджуються як прикметник
# Попередження, які вже сказано в рядку мови або в рядку періоду summary_uk.
SUMMARY_SKIP = {"no_articles_for_language"}


class PeriodError(Exception):
    pass


# ---------- періоди ----------

def add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    return dt.date(d.year + y, m + 1, 1)


def month_end(d: dt.date) -> dt.date:
    return add_months(d, 1) - dt.timedelta(days=1)


def last_complete(granularity: str, today: dt.date) -> dt.date:
    if granularity == "monthly":
        return add_months(today.replace(day=1), -1)
    return today - dt.timedelta(days=1)


def step(d: dt.date, granularity: str, n: int = 1) -> dt.date:
    return add_months(d, n) if granularity == "monthly" else d + dt.timedelta(days=n)


def label(d: dt.date, granularity: str) -> str:
    return d.strftime("%Y-%m") if granularity == "monthly" else d.isoformat()


def parse_point(text: str, granularity: str) -> dt.date:
    fmt, hint = ("%Y-%m", "РРРР-ММ") if granularity == "monthly" else ("%Y-%m-%d", "РРРР-ММ-ДД")
    try:
        d = dt.datetime.strptime(text, fmt).date()
    except ValueError:
        raise PeriodError(f"bad_date: {text!r}, очікується {hint}") from None
    return d.replace(day=1) if granularity == "monthly" else d


def all_periods(start: dt.date, end: dt.date, granularity: str) -> list:
    out, d = [], start
    while d <= end:
        out.append(d)
        d = step(d, granularity)
    return out


def resolve_period(granularity: str, last, start_text, end_text, today: dt.date) -> tuple:
    """Повертає (start, end, warnings). Кидає PeriodError, якщо даних немає зовсім."""
    warnings = []
    newest = last_complete(granularity, today)
    first = DATA_START if granularity == "daily" else DATA_START.replace(day=1)
    if start_text:
        start = parse_point(start_text, granularity)
        end = parse_point(end_text, granularity) if end_text else newest
    else:
        if last is None:
            last = DEFAULT_LAST[granularity]
            warnings.append({"code": "period_defaulted",
                             "detail": f"період не названо, тому взято типовий: {last} " + (
                                 plural(last, "останній завершений місяць", "останні завершені місяці",
                                        "останніх завершених місяців") if granularity == "monthly" else
                                 plural(last, "останній день", "останні дні", "останніх днів"))})
        end = newest
        start = step(newest, granularity, -(last - 1))
    requested = (label(start, granularity), label(end, granularity))
    if start > end:
        raise PeriodError(f"bad_period: початок {requested[0]} пізніше за кінець {requested[1]}")
    if end > newest:
        end = newest
        warnings.append({"code": "incomplete_period_excluded",
                         "detail": f"поточний {UNIT[granularity]} ще не завершився, тому період закінчується "
                                   f"{label(newest, granularity)}"})
    if end < first:
        raise PeriodError(f"period_before_data: Pageviews API має дані лише з 1 липня 2015 року; "
                          f"за запитаний період {requested[0]} — {requested[1]} даних немає")
    if start < first:
        start = first
        warnings.append({"code": "period_before_data",
                         "detail": f"запитано з {requested[0]}, але Pageviews API має дані лише з 1 липня "
                                   f"2015 року; період обрізано до {label(start, granularity)} — "
                                   f"{label(end, granularity)}"})
    if start > end:
        raise PeriodError(f"period_before_data: після обрізання до липня 2015 року період порожній")
    return start, end, warnings, requested


# ---------- запити й кеш ----------

class CachingClient:
    """Кешує відповіді Pageviews (зокрема 404 «даних немає») у файлах на диску."""

    def __init__(self, inner, directory: Path):
        self.inner = inner
        self.directory = directory
        self.hits = 0

    def get_json(self, url: str, params: dict) -> dict:
        path = self.directory / (hashlib.sha256(request_key(url, params).encode()).hexdigest() + ".json")
        if path.exists():
            self.hits += 1
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("_not_found"):
                raise ResolverError(f"HTTP 404 (з кешу) для {url}", status=404)
            return cached
        try:
            data = self.inner.get_json(url, params)
        except ResolverError as e:
            if e.status == 404:
                self._write(path, {"_not_found": True})
            raise
        self._write(path, data)
        return data

    def _write(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def article_url(project: str, title: str, granularity: str, start: dt.date, end: dt.date) -> str:
    encoded = urllib.parse.quote(title.replace(" ", "_"), safe="")
    last_day = month_end(end) if granularity == "monthly" else end
    return (f"{PAGEVIEWS_API}/{project}/all-access/user/{encoded}/{granularity}/"
            f"{start.strftime('%Y%m%d')}00/{last_day.strftime('%Y%m%d')}00")


def project_url(project: str, granularity: str, start: dt.date, end: dt.date) -> str:
    last_day = month_end(end) if granularity == "monthly" else end
    return (f"{AGGREGATE_API}/{project}/all-access/user/{granularity}/"
            f"{start.strftime('%Y%m%d')}00/{last_day.strftime('%Y%m%d')}00")


def fetch_series(client, url: str):
    """{"РРРРММДД": перегляди} або None, якщо API не має даних (404)."""
    try:
        data = client.get_json(url, {})
    except ResolverError as e:
        if e.status == 404:
            return None
        raise
    return {item["timestamp"][:8]: item["views"] for item in data.get("items", [])}


# ---------- складання результату ----------

def collect(client, basket: dict, start: dt.date, end: dt.date, granularity: str) -> dict:
    keys = all_periods(start, end, granularity)
    languages = {}
    for lang in basket["targets"]:
        items = [a for a in basket.get("articles", []) if a["lang"] == lang]
        total_series = [0] * len(keys)
        details = []
        for a in items:
            series = fetch_series(client, article_url(a["project"], a["title"], granularity, start, end))
            values = [(series or {}).get(k.strftime("%Y%m%d"), 0) for k in keys]
            total_series = [x + y for x, y in zip(total_series, values)]
            with_views = [i for i, v in enumerate(values) if v]
            details.append({"title": a["title"], "kind": a["kind"], "entity_id": a["entity_id"], "role": a["role"],
                            "views": sum(values),
                            "first_period_with_views": label(keys[with_views[0]], granularity) if with_views else None})
        details.sort(key=lambda d: -d["views"])
        # Загальна відвідуваність розділу: етап 3 відокремлює зміну теми від зміни всієї Wikipedia.
        project = fetch_series(client, project_url(f"{lang}.wikipedia", granularity, start, end))
        languages[lang] = {"project": f"{lang}.wikipedia", "articles_count": len(items),
                           "project_series": None if project is None else [
                               {"period": label(k, granularity), "views": project.get(k.strftime("%Y%m%d"), 0)}
                               for k in keys],
                           "total_views": sum(total_series),
                           "series": [{"period": label(k, granularity), "views": v} for k, v in zip(keys, total_series)],
                           "articles": details}
    return languages


def data_warnings(languages: dict, start_label: str) -> list:
    warnings = []
    for lang, entry in languages.items():
        if not entry["articles_count"]:
            warnings.append({"code": "no_articles_for_language", "lang": lang,
                             "detail": f"у кошику немає статей для {lang}.wikipedia (на етапі 1 статтю не знайдено), "
                                       f"тому переглядів для цього розділу немає"})
            continue
        for a in entry["articles"]:
            if a["kind"] != "article":
                continue
            if a["first_period_with_views"] is None:
                warnings.append({"code": "article_without_views", "lang": lang,
                                 "detail": f"стаття «{a['title']}» у {lang}.wikipedia не має жодного перегляду за період"})
            elif a["first_period_with_views"] > start_label:
                warnings.append({"code": "series_starts_late", "lang": lang,
                                 "detail": f"стаття «{a['title']}» у {lang}.wikipedia має перегляди лише з "
                                           f"{a['first_period_with_views']}; раніше її, ймовірно, не існувало, тож ріст "
                                           f"від нуля на початку ряду не означає зростання інтересу"})
    return warnings


# ---------- готовий текст для користувача ----------

def plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def number(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def human_period(text: str, granularity: str) -> str:
    if granularity == "daily":
        return text
    year, month = text.split("-")
    return f"{MONTHS_UK[int(month) - 1]} {year}"


def edition_name(lang: str) -> str:
    if lang in LANG_NAMES_UK:
        return f"{LANG_NAMES_UK[lang]} Wikipedia ({lang})"
    if lang in LANG_NOUNS_UK:
        return f"Wikipedia мовою {LANG_NOUNS_UK[lang]} ({lang})"
    return f"{lang}.wikipedia"


def sentence(text: str) -> str:
    text = text.strip().rstrip(".")
    return text[:1].upper() + text[1:] + "."


def language_line(lang: str, entry: dict) -> str:
    name = edition_name(lang)
    if not entry["articles_count"]:
        return f"- {name}: окремої статті на цю тему немає, тому переглядів немає."
    articles = [a["title"] for a in entry["articles"] if a["kind"] == "article"]
    redirects = sum(1 for a in entry["articles"] if a["kind"] != "article")
    what = ", ".join(f"«{t}»" for t in articles[:3])
    if len(articles) > 3:
        what += f" та ще {len(articles) - 3}"
    what = ("стаття " if len(articles) == 1 else "статті ") + what
    if redirects:
        what += f" і {redirects} {plural(redirects, 'перенаправлення', 'перенаправлення', 'перенаправлень')}"
    total = entry["total_views"]
    return f"- {name}: {number(total)} {plural(total, 'перегляд', 'перегляди', 'переглядів')} за період ({what})."


def summary_uk(result: dict) -> str:
    g = result["granularity"]
    used, points = result["period"]["used"], result["period"]["points"]
    unit = (plural(points, "місяць", "місяці", "місяців") if g == "monthly"
            else plural(points, "день", "дні", "днів"))
    lines = [f"Тема: «{result['topic']['label']}» ({result['topic']['entity_id']}).",
             f"Період: {human_period(used['start'], g)} — {human_period(used['end'], g)} ({points} {unit}). "
             f"Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями.",
             ""]
    lines += [language_line(lang, entry) for lang, entry in result["languages"].items()]
    notes = [sentence(w["detail"]) for w in result["warnings"] if w["code"] not in SUMMARY_SKIP]
    if notes:
        lines += ["", "Зверніть увагу:"] + [f"- {n}" for n in notes]
    lines.append("")
    closing = ("Це лише суми переглядів. Чи зростає інтерес і наскільки цьому можна довіряти, показує аналіз "
               "тренду (етап 3).")
    if len(result["languages"]) > 1:
        closing += (" Абсолютні числа різних мовних розділів не можна порівнювати як міру інтересу: розділи "
                    "мають дуже різну аудиторію, коректне порівняння (відносні зміни) буде на етапі 3.")
    lines.append(closing)
    return "\n".join(lines)


def next_steps(result: dict) -> list:
    return [
        "Відповідай користувачу українською, навіть якщо він писав іншою мовою.",
        f"Одразу запусти етап 3: `python3 scripts/analyze_trend.py --views <файл --out цього запуску> "
        f"--out <шлях>.analysis.json` і перекажи користувачу його `summary_uk`. Цей `summary_uk` окремо не "
        f"показуй: він лише для випадку, коли етап 3 завершився помилкою.",
        "Нічого не додавай про зміни в часі від себе: не описуй перегляди по місяцях, не називай піків і спадів — "
        "це робить етап 3.",
        "Не читай `views.json`, щоб скласти відповідь: це вхід для етапу 3.",
    ]


def compact(result: dict, out_path: str) -> dict:
    """Без помісячного ряду: агент переказує summary_uk, а ряд потрібен лише етапу 3."""
    first = ("status", "summary_uk", "next_steps")
    view = {k: result[k] for k in first if k in result}
    view.update({k: v for k, v in result.items() if k not in first and k != "languages"})
    view["languages"] = {}
    for lang, entry in result["languages"].items():
        view["languages"][lang] = {**{k: v for k, v in entry.items()
                                      if k not in ("articles", "series", "project_series")},
                                   "top_articles": entry["articles"][:TOP_ARTICLES_STDOUT],
                                   "articles_total": len(entry["articles"])}
    view["full_views_file"] = out_path
    return view


def run(client, basket: dict, granularity: str, last, start_text, end_text, today: dt.date) -> dict:
    if basket.get("status") not in ("resolved", "partial") or "articles" not in basket:
        return {"status": "error", "reason": "basket_not_ready: потрібен повний кошик (basket.json) етапу 1 "
                                             "зі статусом resolved або partial",
                "next_steps": ["Спершу виконай етап 1 (resolve_topic.py) і передай його файл --out."]}
    try:
        start, end, warnings, requested = resolve_period(granularity, last, start_text, end_text, today)
    except PeriodError as e:
        return {"status": "error", "reason": str(e),
                "next_steps": [f"Відповідай користувачу українською. Скажи: {str(e).split(': ', 1)[-1]}. "
                               f"Запропонуй період від липня 2015 року."]}
    languages = collect(client, basket, start, end, granularity)
    start_label = label(start, granularity)
    stage1 = [{"code": w["code"], "detail": w["detail"]} for w in basket.get("warnings", [])
              if w["code"] in ("asymmetric_basket", "core_missing")]
    result = {
        "status": "ok" if all(e["articles_count"] for e in languages.values()) else "partial",
        "topic": {"entity_id": basket["core"]["entity_id"], "label": basket["core"]["label"]},
        "granularity": granularity,
        "period": {"requested": {"start": requested[0], "end": requested[1]},
                   "used": {"start": start_label, "end": label(end, granularity)},
                   "points": len(all_periods(start, end, granularity))},
        "source": "Wikimedia Pageviews API, agent=user, access=all-access",
        "languages": languages,
        "warnings": warnings + data_warnings(languages, start_label) + stage1,
        "reply_language": REPLY_LANGUAGE,
    }
    result["summary_uk"] = summary_uk(result)
    result["next_steps"] = next_steps(result)
    return result


def main(argv=None, client=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--basket", required=True, help="Повний кошик етапу 1 (файл --out з resolve_topic.py).")
    parser.add_argument("--granularity", choices=("monthly", "daily"), default="monthly")
    parser.add_argument("--last", type=int, help="Останні N завершених місяців (або днів для daily). "
                                                 "Типово: 24 місяці або 90 днів.")
    parser.add_argument("--start", help="Початок періоду: РРРР-ММ (monthly) або РРРР-ММ-ДД (daily).")
    parser.add_argument("--end", help="Кінець періоду; типово — останній завершений місяць/день.")
    parser.add_argument("--out", help="Записати сюди повний результат у JSON; тоді в stdout буде стислий вигляд.")
    parser.add_argument("--no-cache", action="store_true", help="Не читати й не писати дисковий кеш.")
    parser.add_argument("--today", help=argparse.SUPPRESS)  # для відтворюваних тестів
    args = parser.parse_args(argv)

    def emit(result):
        if args.out and "languages" in result:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            result = compact(result, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") in ("ok", "partial") else 1

    if args.last is not None and (args.start or args.end):
        return emit({"status": "error", "reason": "conflicting_period: передайте або --last, або --start/--end"})
    if args.last is not None and args.last < 1:
        return emit({"status": "error", "reason": "bad_period: --last має бути додатним"})
    try:
        basket = json.loads(Path(args.basket).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return emit({"status": "error", "reason": f"basket_unreadable: {e}"})
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()

    if client is None:
        contact = os.environ.get(CONTACT_ENV_VAR, "").strip()
        if not contact:
            return emit({"status": "error", "reason": f"contact_not_configured: задайте {CONTACT_ENV_VAR} — "
                                                      "email або URL для політики User-Agent Wikimedia"})
        client = WikimediaClient(USER_AGENT_TEMPLATE.format(contact=contact))
        newest_end = last_complete(args.granularity, today)
        settled = (today - (month_end(newest_end) if args.granularity == "monthly" else newest_end)).days
        if not args.no_cache and settled >= CACHE_SETTLE_DAYS:
            client = CachingClient(client, Path(os.environ.get(CACHE_ENV_VAR) or DEFAULT_CACHE_DIR) / "pageviews")

    try:
        result = run(client, basket, args.granularity, args.last, args.start, args.end, today)
    except ResolverError as e:
        result = {"status": "error", "reason": str(e),
                  "next_steps": ["Це помилка мережі чи API, а не відсутність інтересу: спробуй ще раз пізніше."]}
    return emit(result)


if __name__ == "__main__":
    sys.exit(main())
