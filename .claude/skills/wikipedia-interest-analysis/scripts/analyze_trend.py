#!/usr/bin/env python3
"""
analyze_trend.py — етап 3: за рядами переглядів етапу 2 (views.json з
fetch_pageviews.py) визначає тренд у кожному мовному розділі, оцінює, наскільки
йому можна довіряти, порівнює мови за відносною зміною і малює графік (SVG).

- Тренд: для місячних рядів від 24 точок — останні 12 місяців проти
  попередніх 12 (рік до року, тож сезонність не спотворює висновок); інакше —
  друга половина періоду проти першої.
- Довіра знижується через: мало переглядів, статтю, що з'явилася посеред
  періоду, висновок, що тримається на одному сплеску, різкий і стійкий злам
  рівня (часто це перейменування чи перенаправлення статті), розбіжність між
  зміною й загальним нахилом ряду, короткий період без урахування сезонності.
- Мови порівнюються лише за відносною зміною, не за абсолютними числами.
- Готову відповідь користувачу (summary_uk) агент переказує дослівно.

Використовується тільки стандартна бібліотека Python.
"""

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_pageviews import (  # noqa: E402
    REPLY_LANGUAGE, edition_name, human_period, number, plural, sentence,
)

GROWTH_THRESHOLD = 10.0          # %, менша зміна — «без явної зміни»
LOW_VOLUME = {"monthly": 100, "daily": 10}   # середньо переглядів за період
MIN_POINTS = {"monthly": 6, "daily": 14}
SPIKE_FACTOR = 4.0               # сплеск — у стільки разів вище за медіану
BREAK_WINDOW = {"monthly": 3, "daily": 7}
BREAK_RATIO = 2.5                # різка зміна медіани сусідніх вікон
BREAK_PERSIST = 1.8              # і стійка: медіана всього «після» проти «до»
PERIODS_PER_YEAR = {"monthly": 12, "daily": 365}
CONFIDENCE_ORDER = ["висока", "середня", "низька"]
TREND_WORDS = {"growing": "інтерес зростає", "declining": "інтерес падає", "flat": "без явної зміни",
               "new": "перегляди з'явилися лише посеред періоду", "none": "даних для висновку замало"}
UNIT_GEN = {"monthly": ("місяць", "місяці", "місяців"), "daily": ("день", "дні", "днів")}
MONTHS_LOC = ["січні", "лютому", "березні", "квітні", "травні", "червні",
              "липні", "серпні", "вересні", "жовтні", "листопаді", "грудні"]
MONTHS_GEN = ["січня", "лютого", "березня", "квітня", "травня", "червня",
              "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2", "#17becf"]


def in_period(text: str, granularity: str) -> str:
    """«у квітні 2025» / «2026-07-31»."""
    if granularity == "daily":
        return text
    year, month = text.split("-")
    return f"у {MONTHS_LOC[int(month) - 1]} {year}"


def from_period(text: str, granularity: str) -> str:
    """«з травня 2025» / «з 2026-07-31»."""
    if granularity == "daily":
        return f"з {text}"
    year, month = text.split("-")
    return f"з {MONTHS_GEN[int(month) - 1]} {year}"


def views_word(n: int) -> str:
    return plural(n, "перегляд", "перегляди", "переглядів")


def pct(x: float) -> str:
    return f"{x:+.0f} %".replace("-", "−")


# ---------- розрахунки ----------

def windows(n: int, granularity: str) -> tuple:
    """(before, after, method) — зрізи індексів для порівняння."""
    if granularity == "monthly" and n >= 24:
        return slice(n - 24, n - 12), slice(n - 12, n), "yoy"
    half = n // 2
    return slice(n - 2 * half, n - half), slice(n - half, n), "halves"


def pct_change(before: list, after: list):
    b, a = sum(before), sum(after)
    return None if b == 0 else (a / b - 1) * 100


def label_for(change, threshold: float) -> str:
    if change is None:
        return "none"
    if change > threshold:
        return "growing"
    if change < -threshold:
        return "declining"
    return "flat"


def theil_sen_pct_per_year(values: list, granularity: str):
    """Стійкий до викидів нахил (медіана попарних нахилів) у % від середнього за рік."""
    mean = statistics.fmean(values) if values else 0
    if len(values) < 3 or mean == 0:
        return None
    slopes = [(values[j] - values[i]) / (j - i) for i in range(len(values)) for j in range(i + 1, len(values))]
    return statistics.median(slopes) * PERIODS_PER_YEAR[granularity] / mean * 100


def find_spike(values: list):
    med = statistics.median(values) if values else 0
    if med <= 0:
        return None
    i = max(range(len(values)), key=lambda k: values[k])
    return (i, values[i] / med, med) if values[i] > SPIKE_FACTOR * med else None


def find_break(values: list, granularity: str, floor: float):
    """Найсильніша різка й стійка зміна рівня: (індекс, медіана до, медіана після) або None."""
    w, best = BREAK_WINDOW[granularity], None
    for k in range(w, len(values) - w + 1):
        b, a = statistics.median(values[k - w:k]), statistics.median(values[k:k + w])
        if b <= 0 or a <= 0 or max(a, b) < floor:
            continue
        ratio = a / b
        if BREAK_RATIO > ratio > 1 / BREAK_RATIO:
            continue
        persist = statistics.median(values[k:]) / max(statistics.median(values[:k]), 1e-9)
        if BREAK_PERSIST > persist > 1 / BREAK_PERSIST or (persist > 1) != (ratio > 1):
            continue
        # Сила — за середніми вікон: так точка зламу припадає саме на перший період нового рівня.
        strength = abs(math.log(statistics.fmean(values[k:k + w]) / statistics.fmean(values[k - w:k])))
        if best is None or strength > best[0]:
            best = (strength, k, b, a)
    return None if best is None else best[1:]


def analyze_language(lang: str, entry: dict, granularity: str, threshold: float) -> dict:
    periods = [p["period"] for p in entry["series"]]
    values = [p["views"] for p in entry["series"]]
    unit = UNIT_GEN[granularity]
    result = {"lang": lang, "edition": edition_name(lang), "total_views": entry["total_views"],
              "articles_count": entry["articles_count"], "reasons": [], "trend": "none", "change_pct": None,
              "confidence": "низька"}
    if not entry["articles_count"] or not any(values):
        result["reasons"].append({"code": "no_data", "detail": "статті на цю тему в розділі немає або в неї "
                                                               "немає переглядів, тож тренд визначити не можна"})
        return result
    if len(values) < MIN_POINTS[granularity]:
        result["reasons"].append({"code": "too_few_points",
                                  "detail": f"у періоді лише {len(values)} {plural(len(values), *unit)}, а для "
                                            f"висновку потрібно щонайменше {MIN_POINTS[granularity]}"})
        return result

    before, after, method = windows(len(values), granularity)
    change = pct_change(values[before], values[after])
    result.update({
        "method": method,
        "before": {"start": periods[before][0], "end": periods[before][-1], "views": sum(values[before])},
        "after": {"start": periods[after][0], "end": periods[after][-1], "views": sum(values[after])},
        "change_pct": None if change is None else round(change, 1),
        "slope_pct_per_year": None,
    })
    reasons, levels = result["reasons"], ["висока"]

    first = next(i for i, v in enumerate(values) if v)
    if first > 0:
        result["trend"] = "new" if change is None else label_for(change, threshold)
        reasons.append({"code": "series_starts_late",
                        "detail": f"перегляди є лише {from_period(periods[first], granularity)}; стаття, "
                                  f"ймовірно, новіша за період, тож ріст від нуля не означає зростання інтересу"})
        levels.append("низька")
    else:
        result["trend"] = label_for(change, threshold)

    mean_after = statistics.fmean(values[after])
    if mean_after < LOW_VOLUME[granularity]:
        reasons.append({"code": "low_volume",
                        "detail": f"мало переглядів (у середньому ~{number(round(mean_after))} на {unit[0]}): "
                                  f"випадкові коливання дають великі відсотки"})
        levels.append("низька")

    spike = find_spike(values)
    if spike and change is not None:
        i, factor, med = spike
        cleaned = values[:i] + [med] + values[i + 1:]
        cleaned_change = pct_change(cleaned[before], cleaned[after])
        same = label_for(cleaned_change, threshold) == result["trend"]
        detail = (f"разовий сплеск {in_period(periods[i], granularity)}: {number(values[i])} "
                  f"{views_word(values[i])}, у {factor:.1f} раза вище за медіану".replace(".", ","))
        if same:
            detail += f"; без нього висновок той самий ({pct(cleaned_change)})"
            reasons.append({"code": "spike", "detail": detail})
        else:
            detail += f"; без нього зміна {pct(cleaned_change)}, тож висновок тримається на одному сплеску"
            reasons.append({"code": "spike_driven", "detail": detail})
            levels.append("низька")
        result["spike"] = {"period": periods[i], "views": values[i], "times_median": round(factor, 1)}

    brk = find_break(values, granularity, LOW_VOLUME[granularity])
    if brk:
        k, b, a = brk
        reasons.append({"code": "level_break",
                        "detail": f"різка й стійка зміна рівня {from_period(periods[k], granularity)}: з ~"
                                  f"{number(round(b))} до ~{number(round(a))} на {unit[0]}. Таке часто "
                                  f"спричиняють зміни в самій статті (перейменування, об'єднання, "
                                  f"перенаправлення) або зовнішні події"
                                  + ("" if method == "yoy" else ", а за період коротший за 2 роки — і сезонність")
                                  + ", тож варто перевірити історію статті"})
        levels.append("середня")
        result["break"] = {"period": periods[k], "median_before": round(b), "median_after": round(a)}

    if granularity == "monthly" and len(values) >= 36:
        first12, last12 = values[:12], values[-12:]
        full = pct_change(first12, last12)
        if full is not None:
            result["full_period"] = {"first": {"start": periods[0], "end": periods[11], "views": sum(first12)},
                                     "last": {"start": periods[-12], "end": periods[-1], "views": sum(last12)},
                                     "change_pct": round(full, 1)}

    project = entry.get("project_series")
    if project and change is not None:
        pvalues = [p["views"] for p in project]
        pchange = pct_change(pvalues[before], pvalues[after])
        if pchange is not None:
            adjusted = ((1 + change / 100) / (1 + pchange / 100) - 1) * 100
            result["project_change_pct"] = round(pchange, 1)
            result["adjusted_change_pct"] = round(adjusted, 1)
            result["adjusted_trend"] = label_for(adjusted, threshold)

    slope = theil_sen_pct_per_year(values, granularity)
    result["slope_pct_per_year"] = None if slope is None else round(slope, 1)
    if (slope is not None and change is not None and abs(change) > threshold
            and abs(slope) > threshold and (slope > 0) != (change > 0)):
        reasons.append({"code": "inconsistent_direction",
                        "detail": "порівняння періодів і загальний нахил ряду вказують у різні боки — ряд "
                                  "нестабільний"})
        levels.append("середня")

    if method == "halves":
        reasons.append({"code": "short_period",
                        "detail": "період коротший за 2 роки, тож порівнюються дві його половини і сезонність не "
                                  "врахована" if granularity == "monthly" else
                                  "денні дані за короткий період: порівнюються дві половини, сезонність і "
                                  "новинні піки не відокремлено"})
        levels.append("середня")

    result["confidence"] = max(levels, key=CONFIDENCE_ORDER.index)
    return result


def compare(results: list, threshold: float, stage2_codes: set) -> dict:
    usable = [r for r in results if r["change_pct"] is not None and r["trend"] != "new"]
    key = "adjusted_change_pct" if usable and all("adjusted_change_pct" in r for r in usable) else "change_pct"
    out = {"measure": key,
           "ranking": [{"lang": r["lang"], "change_pct": r[key], "confidence": r["confidence"]}
                       for r in sorted(usable, key=lambda r: -r[key])],
           "excluded": [r["lang"] for r in results if r not in usable]}
    if len(usable) < 2:
        out["verdict"] = "not_comparable"
        return out
    top, second = out["ranking"][0], out["ranking"][1]
    reliable = [r for r in out["ranking"] if r["confidence"] != "низька"]
    if top["change_pct"] - second["change_pct"] < threshold:
        out["verdict"] = "similar"
    elif top["confidence"] == "низька":
        out["verdict"] = "leader_unreliable"
    else:
        out["verdict"] = "leader"
    out["reliable_count"] = len(reliable)
    out["asymmetric"] = bool(stage2_codes & {"asymmetric_basket", "core_missing", "no_articles_for_language"})
    return out


# ---------- текст ----------

def period_phrase(start: str, end: str, granularity: str) -> str:
    return f"{human_period(start, granularity)} — {human_period(end, granularity)}"


def method_sentence(r: dict, granularity: str) -> str:
    b, a = r["before"], r["after"]
    if r["method"] == "yoy":
        return (f"Порівнюю останні 12 місяців ({period_phrase(a['start'], a['end'], granularity)}) з попередніми "
                f"12 ({period_phrase(b['start'], b['end'], granularity)}) — так сезонні коливання не спотворюють "
                f"висновок.")
    return (f"Порівнюю другу половину періоду ({period_phrase(a['start'], a['end'], granularity)}) з першою "
            f"({period_phrase(b['start'], b['end'], granularity)}).")


def language_block(r: dict) -> list:
    if r["change_pct"] is None and r["trend"] != "new":
        return [f"- {r['edition']}: {TREND_WORDS['none']}."] + [f"  - {sentence(x['detail'])}" for x in r["reasons"]]
    if r["trend"] == "new" or r["change_pct"] is None:
        head = f"- {r['edition']}: {TREND_WORDS['new']}."
    else:
        after = r["after"]["views"]
        head = (f"- {r['edition']}: {TREND_WORDS[r['trend']]}, {pct(r['change_pct'])} "
                f"({number(after)} {views_word(after)} проти {number(r['before']['views'])}).")
    lines = [head + f" Довіра: {r['confidence']}."]
    if "adjusted_change_pct" in r:
        line = (f"  - Уся {r['lang']}.wikipedia за той самий час: {pct(r['project_change_pct'])}; з поправкою на це "
                f"зміна теми {pct(r['adjusted_change_pct'])}")
        if r["adjusted_trend"] != r["trend"]:
            line += f" — відносно всього розділу {TREND_WORDS[r['adjusted_trend']]}"
        lines.append(line + ".")
    if r.get("full_period"):
        f = r["full_period"]
        lines.append(f"  - За весь період: перші 12 місяців ({period_phrase(f['first']['start'], f['first']['end'], 'monthly')}) "
                     f"→ останні 12: {pct(f['change_pct'])} ({number(f['last']['views'])} проти "
                     f"{number(f['first']['views'])}).")
    if r["reasons"]:
        lines += [f"  - {sentence(x['detail'])}" for x in r["reasons"]]
    else:
        lines.append("  - Зміна стійка: переглядів достатньо, без зламів і сплесків, нахил ряду в той самий бік.")
    return lines


def comparison_lines(cmp: dict, results: dict, threshold: float) -> list:
    if not cmp.get("ranking") or len(results) < 2:
        return []
    measure = ("за відносною зміною з поправкою на загальну відвідуваність кожного розділу"
               if cmp.get("measure") == "adjusted_change_pct" else "за відносною зміною")
    lines = ["", f"Порівняння мов ({measure}, не за абсолютними числами — розділи мають дуже різну аудиторію):"]
    if cmp["verdict"] == "not_comparable":
        lines.append("- Порівняти не можна: відносну зміну вдалося визначити менш ніж для двох розділів.")
        return lines
    ranked = ", ".join(f"{r['lang']} {pct(r['change_pct'])}" for r in cmp["ranking"])
    lines.append(f"- {ranked}.")
    top = results[cmp["ranking"][0]["lang"]]
    if cmp["verdict"] == "similar":
        lines.append(f"- Різниця між першими двома менша за {GROWTH_THRESHOLD:.0f} п. п. — вважайте динаміку "
                     f"однаковою.")
    elif cmp["verdict"] == "leader_unreliable":
        lines.append(f"- Найкраща відносна динаміка — {top['edition']}, але довіра до неї низька, тож висновок про "
                     f"лідера ненадійний.")
    else:
        best = cmp["ranking"][0]["change_pct"]
        what = ("найшвидше зростає інтерес" if best > threshold else
                "найменше падіння інтересу" if best < -threshold else
                "найкраща динаміка (відносно розділу — без явної зміни)")
        lines.append(f"- Відносно {what} — {top['edition']}, довіра: {top['confidence']}.")
    if cmp["excluded"]:
        lines.append(f"- Не враховано (немає даних для відносної зміни): {', '.join(cmp['excluded'])}.")
    if cmp.get("asymmetric"):
        lines.append("- У різних мовах вимірюються різні набори статей, тож порівняння нерівноцінне.")
    return lines


def summary_uk(analysis: dict, chart_path) -> str:
    g = analysis["granularity"]
    used, points = analysis["period"]["used"], analysis["period"]["points"]
    lines = [f"Тема: «{analysis['topic']['label']}» ({analysis['topic']['entity_id']}).",
             f"Період: {period_phrase(used['start'], used['end'], g)} ({points} {plural(points, *UNIT_GEN[g])}). "
             f"Джерело: Wikimedia Pageviews API, лише перегляди людей (без ботів), разом із перенаправленнями."]
    with_method = next((r for r in analysis["languages"].values() if r.get("method")), None)
    if with_method:
        lines.append(method_sentence(with_method, g))
    lines.append("")
    for r in analysis["languages"].values():
        lines += language_block(r)
    lines += comparison_lines(analysis["comparison"], analysis["languages"], analysis["threshold"])
    notes = [sentence(w["detail"]) for w in analysis["stage2_warnings"]
             if w["code"] not in ("no_articles_for_language", "series_starts_late", "article_without_views")]
    if notes:
        lines += ["", "Зверніть увагу:"] + [f"- {n}" for n in notes]
    lines.append("")
    if chart_path:
        lines.append(f"Графік: {chart_path}")
    lines.append(f"Поріг: зміна менша за ±{GROWTH_THRESHOLD:.0f} % вважається «без явної зміни»." if
                 analysis["threshold"] == GROWTH_THRESHOLD else
                 f"Поріг: зміна менша за ±{analysis['threshold']:g} % вважається «без явної зміни».")
    lines.append("Перегляди Wikipedia — непрямий показник інтересу: вони враховують лише читачів Wikipedia цією "
                 "мовою і залежать від пошукових систем, новин і назв статей.")
    return "\n".join(lines)


def next_steps(analysis: dict) -> list:
    steps = [
        "Відповідай користувачу українською, навіть якщо він писав іншою мовою.",
        "Перекажи користувачу `summary_uk` дослівно — це вся відповідь про тренд. Перед ним можна додати лише те, "
        "що стосується етапу 1 (як ти виправив опечатку, що уточнив), а після — питання, якщо користувач мусить "
        "щось вирішити.",
        "Не додавай власних висновків, пояснень причин чи рекомендацій понад `summary_uk` і не порівнюй мови за "
        "абсолютними числами. Звіт на одну сторінку (етап 4) ще в розробці.",
    ]
    if analysis.get("chart"):
        steps.append(f"Графік уже створено: {analysis['chart']}. Дай користувачу цей шлях до файлу. Не малюй інших "
                     f"графіків, не пиши для цього коду і нікуди не публікуй та не завантажуй графік.")
    steps.append("Якщо користувач змінює припущення: інший період — перезапусти етап 2 з новим `--last`/`--start`, "
                 "потім цей скрипт; інший поріг «зростання» — лише цей скрипт з `--growth-threshold ЧИСЛО`.")
    return steps


# ---------- графік ----------

def nice_step(span: float) -> float:
    raw = span / 5 or 1
    mag = 10 ** math.floor(math.log10(raw))
    return next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)


def render_svg(analysis: dict, views: dict) -> str:
    g = analysis["granularity"]
    langs = [lang for lang, r in analysis["languages"].items() if r.get("before") and r["before"]["views"] > 0]
    if not langs:
        return ""
    indexed = len(langs) > 1
    periods = [p["period"] for p in views["languages"][langs[0]]["series"]]
    series = {}
    for lang in langs:
        values = [p["views"] for p in views["languages"][lang]["series"]]
        r = analysis["languages"][lang]
        if indexed:
            n_before = len([p for p in periods if r["before"]["start"] <= p <= r["before"]["end"]])
            base = r["before"]["views"] / n_before
            values = [v / base * 100 for v in values]
        series[lang] = values

    W, H, L, R, T, B = 820, 420, 70, 20, 60, 60
    pw, ph = W - L - R, H - T - B
    top = max(max(v) for v in series.values()) * 1.08 or 1
    step = nice_step(top)
    top = math.ceil(top / step) * step
    n = len(periods)
    x = (lambda i: L + pw * i / (n - 1)) if n > 1 else (lambda i: L + pw / 2)
    y = lambda v: T + ph * (1 - v / top)  # noqa: E731

    title = (f"Індекс переглядів: «{analysis['topic']['label']}» (попередній період = 100)" if indexed
             else f"Перегляди: «{analysis['topic']['label']}», {edition_name(langs[0])}")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="sans-serif" font-size="12">',
           f"<title>{escape(title)}</title>",
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="{L}" y="24" font-size="15" font-weight="bold">{escape(title)}</text>']
    first = analysis["languages"][langs[0]]
    a0 = periods.index(first["after"]["start"])
    out.append(f'<rect x="{x(a0):.1f}" y="{T}" width="{x(n - 1) - x(a0):.1f}" height="{ph}" fill="#f2f2f2"/>')
    out.append(f'<text x="{x(a0) + 4:.1f}" y="{T + 14}" fill="#777">період порівняння</text>')
    v = 0.0
    while v <= top + 1e-9:
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#e0e0e0"/>')
        out.append(f'<text x="{L - 6}" y="{y(v) + 4:.1f}" text-anchor="end" fill="#555">{number(round(v))}</text>')
        v += step
    if indexed:
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y(100):.1f}" y2="{y(100):.1f}" stroke="#999" '
                   f'stroke-dasharray="4 3"/>')
    every = max(1, round(n / 8))
    for i in range(0, n, every):
        out.append(f'<text x="{x(i):.1f}" y="{H - B + 18}" text-anchor="middle" fill="#555">{periods[i]}</text>')
    out.append(f'<line x1="{L}" x2="{W - R}" y1="{T + ph}" y2="{T + ph}" stroke="#555"/>')
    for idx, lang in enumerate(langs):
        color = PALETTE[idx % len(PALETTE)]
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(series[lang]))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>')
        r = analysis["languages"][lang]
        if r.get("break"):
            k = periods.index(r["break"]["period"])
            out.append(f'<line x1="{x(k):.1f}" x2="{x(k):.1f}" y1="{T}" y2="{T + ph}" stroke="{color}" '
                       f'stroke-dasharray="6 4"/>')
            out.append(f'<text x="{x(k) + 4:.1f}" y="{T + 30}" fill="{color}">злам рівня</text>')
        if r.get("spike"):
            k = periods.index(r["spike"]["period"])
            out.append(f'<circle cx="{x(k):.1f}" cy="{y(series[lang][k]):.1f}" r="6" fill="none" '
                       f'stroke="{color}" stroke-width="2"/>')
        change = "" if r["change_pct"] is None else f" {pct(r['change_pct'])}, довіра: {r['confidence']}"
        lx = L + 10 + idx * (pw // max(len(langs), 1))
        out.append(f'<rect x="{lx}" y="36" width="14" height="4" fill="{color}"/>')
        out.append(f'<text x="{lx + 18}" y="42">{escape(lang + change)}</text>')
    out.append(f'<text x="{L}" y="{H - 12}" fill="#777" font-size="11">Джерело: Wikimedia Pageviews API, '
               f'agent=user. Кружок — разовий сплеск, пунктир — злам рівня.</text>')
    out.append("</svg>")
    return "\n".join(out)


# ---------- запуск ----------

def run(views: dict, threshold: float) -> dict:
    if "languages" not in views or "granularity" not in views:
        return {"status": "error", "reason": "views_not_ready: потрібен повний файл --out етапу 2 (views.json)",
                "next_steps": ["Спершу виконай етап 2 (fetch_pageviews.py) з `--out` і передай цей файл."]}
    g = views["granularity"]
    results = {lang: analyze_language(lang, entry, g, threshold) for lang, entry in views["languages"].items()}
    stage2 = views.get("warnings", [])
    analysis = {
        "status": "ok" if all(r["change_pct"] is not None for r in results.values()) else "partial",
        "topic": views["topic"], "granularity": g, "period": views["period"], "threshold": threshold,
        "languages": results,
        "comparison": compare(list(results.values()), threshold, {w["code"] for w in stage2}),
        "stage2_warnings": stage2,
        "reply_language": REPLY_LANGUAGE,
    }
    return analysis


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--views", required=True, help="Повний результат етапу 2 (файл --out з fetch_pageviews.py).")
    parser.add_argument("--out", help="Записати сюди повний аналіз у JSON.")
    parser.add_argument("--chart", help="Шлях до графіка SVG; типово — поруч із --views, з розширенням .svg.")
    parser.add_argument("--no-chart", action="store_true", help="Не малювати графік.")
    parser.add_argument("--growth-threshold", type=float, default=GROWTH_THRESHOLD,
                        help=f"Поріг зміни у %%, менше за який — «без явної зміни» (типово {GROWTH_THRESHOLD:g}).")
    args = parser.parse_args(argv)

    try:
        views = json.loads(Path(args.views).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"status": "error", "reason": f"views_unreadable: {e}"}, ensure_ascii=False, indent=2))
        return 1
    if args.growth_threshold <= 0:
        print(json.dumps({"status": "error", "reason": "bad_threshold: --growth-threshold має бути додатним"},
                         ensure_ascii=False, indent=2))
        return 1
    analysis = run(views, args.growth_threshold)
    if analysis["status"] == "error":
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
        return 1

    chart = None
    if not args.no_chart:
        svg = render_svg(analysis, views)
        if svg:
            chart = args.chart or str(Path(args.views).with_suffix(".svg"))
            Path(chart).write_text(svg, encoding="utf-8")
    analysis["chart"] = chart
    analysis["summary_uk"] = summary_uk(analysis, chart)
    analysis["next_steps"] = next_steps(analysis)
    ordered = {k: analysis[k] for k in ("status", "summary_uk", "next_steps")}
    ordered.update({k: v for k, v in analysis.items() if k not in ordered})
    if args.out:
        Path(args.out).write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
        ordered["full_analysis_file"] = args.out
    print(json.dumps(ordered, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
