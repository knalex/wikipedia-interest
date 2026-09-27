"""Офлайн-тести етапу 2 (fetch_pageviews.py): записані відповіді Pageviews API
і синтетичні ряди для граничних випадків."""
import contextlib
import datetime as dt
import io
import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import fetch_pageviews as fp  # noqa: E402
import resolve_topic as rt  # noqa: E402
from cases import CASES, STAGE2_CASES, STAGE2_TODAY  # noqa: E402
from test_resolve_topic import NoNetworkClient, ReplayClient, run  # noqa: E402

TODAY = dt.date.fromisoformat(STAGE2_TODAY)


def basket_for(stage1_case):
    _, _, full = run(CASES[stage1_case], ReplayClient(stage1_case))
    return full


def run_stage2(argv, client, basket):
    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
        path = Path(tmp) / "basket.json"
        path.write_text(json.dumps(basket, ensure_ascii=False), encoding="utf-8")
        views = Path(tmp) / "views.json"
        code = fp.main(argv + ["--basket", str(path), "--today", STAGE2_TODAY, "--out", str(views)], client=client)
        full = json.loads(views.read_text(encoding="utf-8")) if views.exists() else None
    return code, json.loads(out.getvalue()), full


def run_case(name):
    stage1, argv = STAGE2_CASES[name]
    return run_stage2(argv, ReplayClient(name), basket_for(stage1))


def codes(result):
    return {w["code"] for w in result.get("warnings", [])}


class FakePageviews:
    """Віддає задані ряди за назвою статті; для відсутніх — 404."""

    def __init__(self, series_by_title):
        self.series = series_by_title
        self.calls = 0

    def get_json(self, url, params):
        self.calls += 1
        title = urllib.parse.unquote(url.split("/user/")[1].split("/")[0])
        if title not in self.series:
            raise rt.ResolverError("HTTP 404", status=404)
        return {"items": [{"timestamp": ts + "00", "views": v} for ts, v in self.series[title].items()]}


def fake_basket(titles):
    return {"status": "resolved", "targets": ["uk"], "core": {"entity_id": "Q1", "label": "тест"},
            "warnings": [],
            "articles": [{"lang": "uk", "project": "uk.wikipedia", "title": t, "kind": kind, "entity_id": "Q1",
                          "role": "core"} for t, kind in titles]}


class RecordedCases(unittest.TestCase):
    def test_partial_basket_keeps_missing_language(self):
        code, view, full = run_case("pv_if_last24")
        self.assertEqual((code, view["status"]), (0, "partial"))
        self.assertEqual(view["period"]["used"], {"start": "2024-09", "end": "2026-08"})
        self.assertEqual(len(full["languages"]["cs"]["series"]), 24)
        self.assertGreater(full["languages"]["cs"]["total_views"], 0)
        self.assertEqual(full["languages"]["pl"]["total_views"], 0)
        self.assertIn("no_articles_for_language", codes(view))
        self.assertIn("asymmetric_basket", codes(view))  # перенесено з етапу 1

    def test_period_before_2015_is_clipped(self):
        _, view, full = run_case("pv_bitcoin_before_2015")
        self.assertIn("period_before_data", codes(view))
        self.assertEqual(view["period"]["requested"]["start"], "2010-01")
        self.assertEqual(view["period"]["used"], {"start": "2015-07", "end": "2015-12"})
        en = full["languages"]["en"]
        self.assertEqual(en["articles_count"], 48)
        self.assertEqual(sum(p["views"] for p in en["series"]), en["total_views"])  # сума з перенаправленнями
        self.assertIn("липня 2015", view["summary_uk"])

    def test_summary_is_ready_text_and_stdout_has_no_series(self):
        _, view, full = run_case("pv_if_last24")
        summary = view["summary_uk"]
        self.assertEqual(summary, full["summary_uk"])
        self.assertIn("вересень 2024 — серпень 2026 (24 місяці)", summary)
        self.assertIn("Польська Wikipedia (pl): окремої статті на цю тему немає", summary)
        self.assertIn(f"{fp.number(full['languages']['cs']['total_views'])} переглядів", summary)
        self.assertIn("не можна порівнювати", summary)  # дві мови
        self.assertNotIn("series", view["languages"]["cs"])
        self.assertIn("series", full["languages"]["cs"])
        self.assertTrue(any("analyze_trend.py" in s for s in view["next_steps"]))  # далі — етап 3
        self.assertIsNotNone(full["languages"]["cs"]["project_series"])  # загальна відвідуваність розділу
        self.assertNotIn("project_series", view["languages"]["cs"])


class Periods(unittest.TestCase):
    def test_default_is_last_24_complete_months(self):
        start, end, warnings, _ = fp.resolve_period("monthly", None, None, None, TODAY)
        self.assertEqual((start, end), (dt.date(2024, 9, 1), dt.date(2026, 8, 1)))
        self.assertIn("period_defaulted", {w["code"] for w in warnings})

    def test_current_month_is_excluded(self):
        _, end, warnings, _ = fp.resolve_period("monthly", None, "2026-01", "2026-12", TODAY)
        self.assertEqual(end, dt.date(2026, 8, 1))
        self.assertIn("incomplete_period_excluded", {w["code"] for w in warnings})

    def test_daily_default_ends_yesterday(self):
        start, end, _, _ = fp.resolve_period("daily", None, None, None, TODAY)
        self.assertEqual(end, dt.date(2026, 9, 26))
        self.assertEqual((end - start).days, 89)

    def test_period_entirely_before_data_is_an_error_without_network(self):
        basket = fake_basket([("Bitcoin", "article")])
        code, view, _ = run_stage2(["--start", "2010-01", "--end", "2014-12"], NoNetworkClient(), basket)
        self.assertEqual((code, view["status"]), (1, "error"))
        self.assertTrue(view["reason"].startswith("period_before_data"))

    def test_last_and_start_conflict(self):
        code, view, _ = run_stage2(["--last", "12", "--start", "2024-01"], NoNetworkClient(), fake_basket([]))
        self.assertTrue(view["reason"].startswith("conflicting_period"))


class SeriesAssembly(unittest.TestCase):
    def test_zero_fill_redirect_sum_and_late_start(self):
        pv = FakePageviews({
            "Нова_стаття": {"20260601": 50, "20260801": 70},   # липня немає → 0
            "Перенаправлення": {"20260801": 5},
        })
        basket = fake_basket([("Нова стаття", "article"), ("Перенаправлення", "redirect"), ("Пусте", "redirect")])
        code, view, full = run_stage2(["--start", "2026-05", "--end", "2026-08"], pv, basket)
        series = [p["views"] for p in full["languages"]["uk"]["series"]]
        self.assertEqual(series, [0, 50, 0, 75])
        self.assertIn("series_starts_late", codes(view))  # перегляди лише з 2026-06
        empty = next(a for a in full["languages"]["uk"]["articles"] if a["title"] == "Пусте")
        self.assertEqual((empty["views"], empty["first_period_with_views"]), (0, None))

    def test_article_without_views_is_flagged(self):
        code, view, _ = run_stage2(["--last", "3"], FakePageviews({}), fake_basket([("Нема", "article")]))
        self.assertIn("article_without_views", codes(view))

    def test_basket_from_ambiguous_stage1_is_rejected(self):
        code, view, _ = run_stage2(["--last", "3"], NoNetworkClient(), {"status": "ambiguous", "candidates": []})
        self.assertTrue(view["reason"].startswith("basket_not_ready"))


class Summary(unittest.TestCase):
    def test_plural_forms(self):
        forms = ("перегляд", "перегляди", "переглядів")
        self.assertEqual([fp.plural(n, *forms) for n in (1, 3, 5, 11, 12, 21, 22, 25, 111)],
                         ["перегляд", "перегляди", "переглядів", "переглядів", "переглядів",
                          "перегляд", "перегляди", "переглядів", "переглядів"])

    def test_single_language_has_no_cross_language_caveat(self):
        pv = FakePageviews({"A": {"20260801": 1}})
        _, view, _ = run_stage2(["--last", "1"], pv, fake_basket([("A", "article")]))
        self.assertIn("1 перегляд за період (стаття «A»)", view["summary_uk"])
        self.assertNotIn("не можна порівнювати", view["summary_uk"])


class Cache(unittest.TestCase):
    def test_repeat_requests_do_not_hit_network(self):
        inner = FakePageviews({"A": {"20260801": 1}})
        with tempfile.TemporaryDirectory() as tmp:
            client = fp.CachingClient(inner, Path(tmp))
            for _ in range(2):
                self.assertEqual(fp.fetch_series(client, "https://x/user/A/monthly/1/2"), {"20260801": 1})
                self.assertIsNone(fp.fetch_series(client, "https://x/user/B/monthly/1/2"))  # 404 теж кешується
        self.assertEqual(inner.calls, 2)
        self.assertEqual(client.hits, 2)


if __name__ == "__main__":
    unittest.main()
