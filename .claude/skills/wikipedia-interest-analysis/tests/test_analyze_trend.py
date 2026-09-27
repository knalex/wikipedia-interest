"""Офлайн-тести етапу 3 (analyze_trend.py): синтетичні ряди для кожного правила довіри
і повний ланцюжок на записаних відповідях етапу 2."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import analyze_trend as at  # noqa: E402
from test_fetch_pageviews import run_case  # noqa: E402


def months(start: str, n: int) -> list:
    y, m = map(int, start.split("-"))
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def make_views(series_by_lang: dict, project_by_lang=None, granularity="monthly", start="2024-09",
               warnings=None) -> dict:
    languages = {}
    for lang, values in series_by_lang.items():
        n = len(values) if values else 24
        periods = months(start, n) if granularity == "monthly" else [
            f"2026-07-{d:02d}" if d <= 31 else f"2026-08-{d - 31:02d}" for d in range(1, n + 1)]
        project = (project_by_lang or {}).get(lang)
        languages[lang] = {
            "project": f"{lang}.wikipedia", "articles_count": 0 if values is None else 1,
            "total_views": sum(values or []),
            "series": [{"period": p, "views": v} for p, v in zip(periods, values or [0] * 24)],
            "project_series": None if project is None else [{"period": p, "views": v}
                                                            for p, v in zip(periods, project)],
            "articles": []}
    first = next(iter(languages.values()))["series"]
    return {"status": "ok", "topic": {"entity_id": "Q1", "label": "тест"}, "granularity": granularity,
            "period": {"used": {"start": first[0]["period"], "end": first[-1]["period"]}, "points": len(first)},
            "languages": languages, "warnings": warnings or []}


def analyze(views, threshold=at.GROWTH_THRESHOLD):
    return at.run(views, threshold)


def codes(result):
    return {r["code"] for r in result["reasons"]}


class TrendAndConfidence(unittest.TestCase):
    def test_steady_growth_is_high_confidence(self):
        r = analyze(make_views({"uk": [1000] * 12 + [1300] * 12}))["languages"]["uk"]
        self.assertEqual((r["trend"], r["change_pct"], r["confidence"], r["method"]), ("growing", 30.0, "висока", "yoy"))
        self.assertEqual(codes(r), set())

    def test_small_change_is_flat(self):
        r = analyze(make_views({"uk": [1000] * 12 + [1050] * 12}))["languages"]["uk"]
        self.assertEqual(r["trend"], "flat")

    def test_growth_carried_by_one_spike_is_low(self):
        values = [1000] * 12 + [1000] * 5 + [5000] + [1000] * 6
        r = analyze(make_views({"uk": values}))["languages"]["uk"]
        self.assertEqual(r["trend"], "growing")
        self.assertIn("spike_driven", codes(r))
        self.assertEqual(r["confidence"], "низька")

    def test_spike_that_does_not_change_verdict_keeps_confidence(self):
        values = [1000] * 12 + [2000] * 5 + [9000] + [2000] * 6
        r = analyze(make_views({"uk": values}))["languages"]["uk"]
        self.assertIn("spike", codes(r))
        self.assertEqual(r["confidence"], "висока")

    def test_level_break_lowers_confidence_and_names_the_month(self):
        r = analyze(make_views({"uk": [1000] * 12 + [300] * 12}))["languages"]["uk"]
        self.assertEqual(r["trend"], "declining")
        self.assertIn("level_break", codes(r))
        self.assertEqual((r["confidence"], r["break"]["period"]), ("середня", "2025-09"))

    def test_low_volume_is_low_confidence(self):
        r = analyze(make_views({"sv": [20] * 12 + [30] * 12}))["languages"]["sv"]
        self.assertIn("low_volume", codes(r))
        self.assertEqual(r["confidence"], "низька")

    def test_article_created_mid_period(self):
        r = analyze(make_views({"uk": [0] * 6 + [500] * 18}))["languages"]["uk"]
        self.assertIn("series_starts_late", codes(r))
        self.assertEqual(r["confidence"], "низька")

    def test_long_period_reports_whole_span(self):
        r = analyze(make_views({"uk": [1000] * 12 + [1500] * 12 + [2000] * 12}, start="2023-09"))["languages"]["uk"]
        self.assertEqual(r["full_period"]["change_pct"], 100.0)
        self.assertIn("За весь період", "\n".join(at.language_block(r)))

    def test_break_in_short_period_mentions_seasonality(self):
        r = analyze(make_views({"cs": [2500] * 9 + [900] * 3}))["languages"]["cs"]
        detail = next(x["detail"] for x in r["reasons"] if x["code"] == "level_break")
        self.assertIn("сезонність", detail)

    def test_short_period_compares_halves(self):
        r = analyze(make_views({"uk": [1000] * 6 + [1500] * 6}))["languages"]["uk"]
        self.assertEqual((r["method"], r["trend"]), ("halves", "growing"))
        self.assertIn("short_period", codes(r))
        self.assertEqual(r["confidence"], "середня")

    def test_daily_series(self):
        r = analyze(make_views({"en": [100] * 30 + [200] * 30}, granularity="daily"))["languages"]["en"]
        self.assertEqual((r["method"], r["trend"]), ("halves", "growing"))

    def test_missing_article_gives_no_trend(self):
        a = analyze(make_views({"pl": None, "cs": [1000] * 24}))
        self.assertEqual(a["languages"]["pl"]["trend"], "none")
        self.assertIn("no_data", codes(a["languages"]["pl"]))
        self.assertEqual(a["status"], "partial")
        self.assertEqual(a["comparison"]["excluded"], ["pl"])


class ProjectAdjustmentAndComparison(unittest.TestCase):
    def test_whole_wikipedia_decline_is_separated(self):
        views = make_views({"pl": [1000] * 12 + [820] * 12}, {"pl": [10**6] * 12 + [910000] * 12})
        r = analyze(views)["languages"]["pl"]
        self.assertEqual((r["trend"], r["project_change_pct"], r["adjusted_change_pct"]), ("declining", -9.0, -9.9))
        self.assertEqual(r["adjusted_trend"], "flat")

    def test_comparison_uses_relative_adjusted_change(self):
        views = make_views({"de": [1000] * 12 + [1400] * 12, "fr": [50000] * 12 + [52000] * 12},
                           {"de": [10**6] * 24, "fr": [10**6] * 24})
        a = analyze(views)
        cmp = a["comparison"]
        self.assertEqual((cmp["measure"], cmp["verdict"], cmp["ranking"][0]["lang"]),
                         ("adjusted_change_pct", "leader", "de"))
        text = at.summary_uk(a, None)
        self.assertIn("найшвидше зростає інтерес — Німецька Wikipedia (de)", text)
        self.assertIn("не за абсолютними числами", text)

    def test_similar_changes_are_not_ranked(self):
        a = analyze(make_views({"de": [1000] * 12 + [1200] * 12, "fr": [1000] * 12 + [1150] * 12}))
        self.assertEqual(a["comparison"]["verdict"], "similar")

    def test_flat_leader_is_not_called_growing(self):
        a = analyze(make_views({"en": [1000] * 12 + [1010] * 12, "de": [1000] * 12 + [800] * 12}))
        text = at.summary_uk(a, None)
        self.assertIn("Найкраща відносна динаміка (сама по собі — без явної зміни) — Англійська", text)
        self.assertNotIn("найшвидше зростає", text)

    def test_threshold_is_configurable(self):
        r = analyze(make_views({"uk": [1000] * 12 + [1300] * 12}), threshold=50)["languages"]["uk"]
        self.assertEqual(r["trend"], "flat")


class Text(unittest.TestCase):
    def test_month_cases(self):
        self.assertEqual(at.in_period("2025-04", "monthly"), "у квітні 2025")
        self.assertEqual(at.from_period("2025-05", "monthly"), "з травня 2025")
        self.assertEqual(at.pct(-45.4), "−45 %")

    def test_stage2_warnings_are_carried(self):
        warn = [{"code": "period_defaulted", "detail": "період не названо, тому взято типовий"}]
        a = analyze(make_views({"uk": [1000] * 24}, warnings=warn))
        self.assertIn("Період не названо, тому взято типовий.", at.summary_uk(a, None))


class Cli(unittest.TestCase):
    def run_main(self, views, extra=()):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
            path = Path(tmp) / "views.json"
            path.write_text(json.dumps(views, ensure_ascii=False), encoding="utf-8")
            code = at.main(["--views", str(path), *extra])
            svg = path.with_suffix(".svg")
            svg_text = svg.read_text(encoding="utf-8") if svg.exists() else None
        return code, json.loads(out.getvalue()), svg_text

    def test_chart_summary_and_order(self):
        code, result, svg = self.run_main(make_views({"de": [1000] * 12 + [1400] * 12, "fr": [900] * 24}))
        self.assertEqual(code, 0)
        self.assertEqual(list(result)[:3], ["status", "summary_uk", "next_steps"])
        xml.dom.minidom.parseString(svg)  # коректний SVG
        self.assertIn("Індекс переглядів", svg)
        self.assertIn(f"Графік: {result['chart']}", result["summary_uk"])
        self.assertTrue(any("дослівно" in s for s in result["next_steps"]))

    def test_bad_input(self):
        code, result, _ = self.run_main({"status": "error"})
        self.assertEqual((code, result["status"]), (1, "error"))


class RecordedChain(unittest.TestCase):
    def test_stage2_output_feeds_stage3(self):
        _, _, full = run_case("pv_if_last24")
        a = at.run(full, at.GROWTH_THRESHOLD)
        self.assertEqual(a["languages"]["pl"]["trend"], "none")
        cs = a["languages"]["cs"]
        self.assertEqual(cs["method"], "yoy")
        self.assertIn("adjusted_change_pct", cs)
        self.assertIsNotNone(cs["change_pct"])


if __name__ == "__main__":
    unittest.main()
