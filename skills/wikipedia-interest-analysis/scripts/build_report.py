#!/usr/bin/env python3
"""
build_report.py — етап 4: звіт на одну сторінку (PDF) за результатом етапу 3.

Бере повний аналіз (файл --out з analyze_trend.py) і ряди етапу 2
(views.json) і складає сторінку A4: головний висновок, таблиця по мовах,
графік, причини рівня довіри, що з цього випливає для рішення, припущення й
обмеження. Усі числа й формулювання беруться з аналізу — звіт нічого не
рахує заново, тож збігається з відповіддю агента.

Використовується тільки стандартна бібліотека Python; шрифт DejaVu Sans
(кирилиця) лежить в assets/fonts і вбудовується підмножиною.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_trend import PALETTE, REPORT_OFFER, TREND_WORDS, nice_step, pct, period_phrase  # noqa: E402
from fetch_pageviews import REPLY_LANGUAGE, number, sentence  # noqa: E402
from output_files import FILES_HEADING, display, files_block, run_dir_for  # noqa: E402
from pdf_writer import Page, TrueTypeFont  # noqa: E402

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
MARGIN = 42
GREY, DARK, LIGHT, ACCENT = "#666666", "#222222", "#f2f2f2", "#1f4e79"
CONF_COLOR = {"висока": "#2e7d32", "середня": "#b26a00", "низька": "#c62828"}
# Від повного до стислого: якщо сторінка не вміщує, беремо наступний варіант.
LAYOUTS = [
    {"body": 9, "reasons": 3, "chart": 190},
    {"body": 8.5, "reasons": 2, "chart": 160},
    {"body": 8, "reasons": 1, "chart": 140},
    {"body": 7.5, "reasons": 1, "chart": 120},
]


def load_fonts() -> dict:
    return {"regular": TrueTypeFont(str(FONT_DIR / "DejaVuSans.ttf")),
            "bold": TrueTypeFont(str(FONT_DIR / "DejaVuSans-Bold.ttf"))}


# ---------- зміст ----------

def measure(r: dict):
    return r.get("adjusted_change_pct", r.get("change_pct"))


def verdict(r: dict) -> str:
    return r.get("adjusted_trend") or r["trend"]


def headline(a: dict) -> str:
    cmp, langs = a["comparison"], a["languages"]
    by_lang = {x["lang"]: x for x in cmp.get("ranking", [])}
    adj = " з поправкою на розділ" if cmp.get("measure") == "adjusted_change_pct" else ""
    if len(by_lang) >= 2:
        top = langs[cmp["ranking"][0]["lang"]]
        ranked = ", ".join(f"{x['lang']} {pct(x['change_pct'])}" for x in cmp["ranking"])
        if cmp["verdict"] == "similar":
            return (f"Динаміка мов практично однакова (різниця менша за {a['threshold']:g} п. п.){adj}: "
                    f"{ranked}.")
        if cmp["verdict"] == "close_leaders":
            editions = [langs[l]["edition"] for l in cmp["leaders"]]
            names = ", ".join(editions[:-1]) + " і " + editions[-1]
            return (f"Найкраща відносна динаміка — {names} (між ними менше {a['threshold']:g} п. п.){adj}; "
                    f"усі мови: {ranked}.")
        if cmp["verdict"] == "leader_unreliable":
            return (f"Найкраща відносна динаміка — {top['edition']} ({pct(measure(top))}{adj}), але довіра до "
                    f"неї низька; усі мови: {ranked}.")
        best = cmp["ranking"][0]["change_pct"]
        what = ("Найшвидше зростає інтерес" if best > a["threshold"] else
                "Найменше падіння інтересу" if best < -a["threshold"] else "Найкраща відносна динаміка")
        return f"{what} — {top['edition']} ({pct(best)}{adj}, довіра {top['confidence']}); усі мови: {ranked}."
    with_data = [r for r in langs.values() if r["change_pct"] is not None]
    if not with_data:
        return "Для жодного з мовних розділів немає даних для висновку про тренд."
    r = with_data[0]
    extra = f", з поправкою на розділ {pct(r['adjusted_change_pct'])}" if "adjusted_change_pct" in r else ""
    return f"{r['edition']}: {TREND_WORDS[r['trend']]}, {pct(r['change_pct'])}{extra}; довіра {r['confidence']}."


def implications(a: dict) -> list:
    out = []
    for r in a["languages"].values():
        m = measure(r)
        if r["change_pct"] is None and r["trend"] != "new":
            out.append(f"Не виміряно — {r['edition']}: окремої статті немає або немає переглядів, тож інтерес цим "
                       f"методом оцінити не можна; потрібні інші джерела.")
        elif r["confidence"] == "низька":
            why = r["reasons"][0]["detail"] if r["reasons"] else "мало даних"
            out.append(f"Потрібна перевірка — {r['edition']}: довіра низька ({why}).")
        elif verdict(r) == "growing":
            out.append(f"Кандидат для дослідження — {r['edition']}: інтерес зростає ({pct(m)}), довіра "
                       f"{r['confidence']}.")
        elif verdict(r) == "flat":
            out.append(f"Стабільний інтерес — {r['edition']}: без явної зміни ({pct(m)}), довіра {r['confidence']}.")
        else:
            out.append(f"Не пріоритет за цими даними — {r['edition']}: інтерес падає ({pct(m)}), довіра "
                       f"{r['confidence']}.")
    return out


def limitations(a: dict) -> list:
    g = a["granularity"]
    first = next((r for r in a["languages"].values() if r.get("method")), None)
    out = []
    if first:
        b, af = first["before"], first["after"]
        how = "рік до року" if first["method"] == "yoy" else "друга половина періоду проти першої"
        out.append(f"Метод: {how} — {period_phrase(af['start'], af['end'], g)} проти "
                   f"{period_phrase(b['start'], b['end'], g)}.")
    if any("adjusted_change_pct" in r for r in a["languages"].values()):
        out.append("Поправка на розділ: зміну теми поділено на зміну загальної відвідуваності того самого розділу "
                   "Wikipedia за той самий час.")
    out.append(f"Поріг: зміна менша за ±{a['threshold']:g} % вважається «без явної зміни».")
    out += [sentence(w["detail"]) for w in a.get("stage2_warnings", [])
            if w["code"] not in ("series_starts_late", "article_without_views", "no_articles_for_language",
                                 "core_missing")]
    out.append("Перегляди Wikipedia — непрямий показник інтересу: лише читачі Wikipedia цією мовою; залежать від "
               "пошукових систем, новин і назв статей. Рішення варто підтвердити іншими джерелами.")
    return out


# ---------- верстка ----------

class Writer:
    def __init__(self, page: Page, body: float):
        self.p, self.body, self.y = page, body, MARGIN
        self.x, self.w = MARGIN, page.width - 2 * MARGIN

    def wrap(self, text: str, width: float, size: float, font="regular") -> list:
        lines, line = [], ""
        for word in text.split():
            cand = f"{line} {word}".strip()
            if self.p.text_width(cand, size, font) <= width or not line:
                line = cand
            else:
                lines.append(line)
                line = word
        return lines + ([line] if line else [])

    def para(self, text, size=None, font="regular", color=DARK, indent=0.0, gap=3.0, x=None, width=None):
        size = size or self.body
        x = (x if x is not None else self.x) + indent
        width = (width or self.w) - indent
        for line in self.wrap(text, width, size, font):
            self.y += size * 1.3
            self.p.text(x, self.y, line, size, font, color)
        self.y += gap

    def bullet(self, text, size=None, color=DARK, marker="•"):
        size = size or self.body
        lines = self.wrap(text, self.w - 12, size)
        for i, line in enumerate(lines):
            self.y += size * 1.3
            if i == 0:
                self.p.text(self.x + 2, self.y, marker, size, "regular", ACCENT)
            self.p.text(self.x + 12, self.y, line, size, "regular", color)
        self.y += 1.5

    def heading(self, text):
        self.y += 7
        self.para(text, self.body + 2, "bold", ACCENT, gap=1)


def draw_table(wr: Writer, a: dict):
    cols = [("Мовний розділ", 0.30), ("Перегляди", 0.20), ("Зміна", 0.14), ("З поправкою", 0.17), ("Довіра", 0.19)]
    size, row_h = wr.body, wr.body * 1.9
    x0, w = wr.x, wr.w
    wr.p.rect(x0, wr.y + 2, w, row_h, fill=LIGHT)
    xs, x = [], x0
    for _, frac in cols:
        xs.append(x + 5)
        x += w * frac
    for (label, _), cx in zip(cols, xs):
        wr.p.text(cx, wr.y + 2 + row_h * 0.68, label, size, "bold", DARK)
    wr.y += 2 + row_h
    for r in a["languages"].values():
        after = r.get("after", {}).get("views")
        cells = [r["edition"],
                 "—" if after is None else number(after),
                 "—" if r["change_pct"] is None else pct(r["change_pct"]),
                 pct(r["adjusted_change_pct"]) if "adjusted_change_pct" in r else "—",
                 "—" if r["change_pct"] is None and r["trend"] != "new" else r["confidence"]]
        for i, (cell, cx) in enumerate(zip(cells, xs)):
            color = CONF_COLOR.get(cell, DARK) if i == 4 else DARK
            wr.p.text(cx, wr.y + row_h * 0.68, cell, size, "bold" if i == 4 else "regular", color)
        wr.p.line(x0, wr.y + row_h, x0 + w, wr.y + row_h, "#dddddd", 0.5)
        wr.y += row_h
    first = next((r for r in a["languages"].values() if r.get("after")), None)
    if first:
        wr.para(f"Перегляди — за період порівняння ({period_phrase(first['after']['start'], first['after']['end'], a['granularity'])}); "
                f"зміна — проти попереднього періоду такої ж довжини.", wr.body - 1.5, color=GREY, gap=2)


def draw_chart(wr: Writer, a: dict, views: dict, height: float):
    langs = [l for l, r in a["languages"].items() if r.get("before") and r["before"]["views"] > 0]
    if not langs:
        return
    periods = [p["period"] for p in views["languages"][langs[0]]["series"]]
    indexed = len(langs) > 1
    series = {}
    for lang in langs:
        r = a["languages"][lang]
        values = [p["views"] for p in views["languages"][lang]["series"]]
        if indexed:
            n_before = len([p for p in periods if r["before"]["start"] <= p <= r["before"]["end"]])
            base = r["before"]["views"] / n_before
            values = [v / base * 100 for v in values]
        series[lang] = values
    size = wr.body - 1
    title = ("Індекс переглядів (попередній період = 100)" if indexed else
             f"Перегляди за {'місяць' if a['granularity'] == 'monthly' else 'день'}")
    wr.para(title, wr.body, "bold", DARK, gap=4)
    top_y, left, right = wr.y, wr.x + 34, wr.x + wr.w
    bottom = top_y + height
    vmax = max(max(v) for v in series.values()) * 1.08 or 1
    step = nice_step(vmax)
    vmax = -(-vmax // step) * step
    n = len(periods)
    X = (lambda i: left + (right - left) * i / (n - 1)) if n > 1 else (lambda i: (left + right) / 2)
    Y = lambda v: bottom - height * v / vmax  # noqa: E731
    first = a["languages"][langs[0]]
    a0 = periods.index(first["after"]["start"])
    wr.p.rect(X(a0), top_y, X(n - 1) - X(a0), height, fill=LIGHT)
    wr.p.text(X(a0) + 3, top_y + size + 2, "період порівняння", size - 0.5, "regular", GREY)
    v = 0.0
    while v <= vmax + 1e-9:
        wr.p.line(left, Y(v), right, Y(v), "#e0e0e0", 0.5)
        label = number(round(v))
        wr.p.text(left - 4 - wr.p.text_width(label, size - 0.5), Y(v) + 2.5, label, size - 0.5, "regular", GREY)
        v += step
    if indexed:
        wr.p.line(left, Y(100), right, Y(100), "#999999", 0.6, dash=(3, 2))
    wr.p.line(left, bottom, right, bottom, "#555555", 0.6)
    every = max(1, round(n / 8))
    for i in range(0, n, every):
        label = periods[i]
        wr.p.text(X(i) - wr.p.text_width(label, size - 0.5) / 2, bottom + size + 3, label, size - 0.5, "regular", GREY)
    legend_x = left
    for idx, lang in enumerate(langs):
        color = PALETTE[idx % len(PALETTE)]
        wr.p.polyline([(X(i), Y(v)) for i, v in enumerate(series[lang])], color, 1.6)
        r = a["languages"][lang]
        if r.get("break"):
            k = periods.index(r["break"]["period"])
            wr.p.line(X(k), top_y, X(k), bottom, color, 0.8, dash=(4, 3))
        if r.get("spike"):
            k = periods.index(r["spike"]["period"])
            wr.p.circle(X(k), Y(series[lang][k]), 4, color, 1.1)
        label = lang + ("" if r["change_pct"] is None else f" {pct(r['change_pct'])}")
        wr.p.rect(legend_x, bottom + 2 * size + 8, 10, 3, fill=color)
        wr.p.text(legend_x + 13, bottom + 2 * size + 11, label, size, "regular", DARK)
        legend_x += wr.p.text_width(label, size) + 30
    wr.y = bottom + 2 * size + 14
    wr.para("Кружок — разовий сплеск, пунктир — злам рівня.", size - 0.5, color=GREY, gap=2)


def layout(a: dict, views: dict, question, fonts: dict, opts: dict, today: dt.date):
    page = Page(fonts)
    wr = Writer(page, opts["body"])
    topic = a["topic"]
    wr.para(f"Інтерес до теми «{topic['label']}» у Wikipedia", 16, "bold", DARK, gap=2)
    used = a["period"]["used"]
    langs = ", ".join(a["languages"])
    wr.para(f"Період: {period_phrase(used['start'], used['end'], a['granularity'])} · Мовні розділи: {langs} · "
            f"Wikidata: {topic['entity_id']} · Звіт від {today.isoformat()}", wr.body - 0.5, color=GREY, gap=2)
    if question and fonts["regular"].supports(question):
        wr.para(f"Питання: «{question}»", wr.body - 0.5, color=GREY, gap=2)
    wr.p.line(wr.x, wr.y + 3, wr.x + wr.w, wr.y + 3, ACCENT, 1.2)
    wr.y += 5
    wr.heading("Головне")
    wr.para(headline(a), wr.body + 1, "bold", DARK)
    draw_table(wr, a)
    wr.y += 4
    draw_chart(wr, a, views, opts["chart"])
    wr.heading("Чому така довіра")
    steady = [r["lang"] for r in a["languages"].values() if not r["reasons"]]
    if steady:
        wr.bullet(f"{', '.join(steady)}: зміна стійка — переглядів достатньо, без зламів і сплесків, нахил ряду в "
                  f"той самий бік.")
    for r in a["languages"].values():
        for x in r["reasons"][:opts["reasons"]]:
            wr.bullet(f"{r['lang']}: {sentence(x['detail'])}")
    wr.heading("Що з цього випливає")
    for text in implications(a):
        wr.bullet(text)
    wr.heading("Припущення й обмеження")
    for text in limitations(a):
        wr.bullet(text, wr.body - 0.5, GREY)
    footer_y = page.height - MARGIN + 14
    fits = wr.y <= footer_y - 10
    page.text(MARGIN, footer_y, "Дані: Wikimedia Pageviews API (agent=user) і Wikidata. Звіт згенеровано навичкою "
              "wikipedia-interest-analysis; розрахунки — у файлі аналізу етапу 3.", 6.5, "regular", GREY)
    return page, fits


def build(a: dict, views: dict, question, today: dt.date):
    fonts = load_fonts()
    for i, opts in enumerate(LAYOUTS):
        page, fits = layout(a, views, question, fonts, opts, today)
        if fits:
            return page, i
    return page, len(LAYOUTS) - 1  # найстисліший варіант, навіть якщо щось не вмістилося


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--analysis", required=True, help="Повний аналіз етапу 3 (файл --out з analyze_trend.py).")
    parser.add_argument("--views", required=True, help="Ряди етапу 2 (файл --out з fetch_pageviews.py).")
    parser.add_argument("--out", help="Куди записати PDF (типово — report.pdf у теці аналізу).")
    parser.add_argument("--question", help="Питання користувача дослівно — для шапки звіту.")
    parser.add_argument("--today", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    def emit(result):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "ok" else 1

    try:
        a = json.loads(Path(args.analysis).read_text(encoding="utf-8"))
        views = json.loads(Path(args.views).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return emit({"status": "error", "reason": f"input_unreadable: {e}"})
    if "languages" not in a or "comparison" not in a:
        return emit({"status": "error", "reason": "analysis_not_ready: потрібен файл --out з analyze_trend.py",
                     "next_steps": ["Спершу запусти етап 3 з `--out` і передай цей файл як --analysis."]})
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    page, variant = build(a, views, args.question, today)
    out = Path(args.out) if args.out else run_dir_for(args.analysis, a["topic"]["entity_id"]) / "report.pdf"
    out.write_bytes(page.to_pdf(f"Інтерес до теми «{a['topic']['label']}» у Wikipedia"))
    summary = a.get("summary_uk", "").split("\n\n" + FILES_HEADING)[0].replace(REPORT_OFFER, "").rstrip()
    reply = (summary + "\n\n" if summary else "") + f"Звіт на одну сторінку (PDF): {display(out)}"
    files = files_block(out.parent, will_create=[out.name])
    if files:
        reply += "\n\n" + files
    return emit({
        "status": "ok",
        "reply_uk": reply,
        "report": display(out),
        "pages": 1,
        "layout_variant": variant,
        "reply_language": REPLY_LANGUAGE,
        "next_steps": [
            "Відповідай користувачу українською.",
            "Перекажи користувачу `reply_uk` дослівно — це вся відповідь: висновки аналізу й шлях до звіту. Перед "
            "ним можна додати лише те, що стосується етапу 1 (як ти виправив опечатку, що уточнив).",
            "Нікуди не публікуй і не завантажуй звіт; не додавай власних висновків понад `reply_uk`.",
        ],
    })


if __name__ == "__main__":
    sys.exit(main())
