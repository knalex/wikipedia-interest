"""Офлайн-тести теки результатів (output_files.py): усі файли запуску — в одній підтеці
wikipedia-interest-output/, там же .gitignore, а відповідь закінчується переліком файлів."""
import contextlib
import datetime as dt
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import analyze_trend as at  # noqa: E402
import build_report as br  # noqa: E402
import fetch_pageviews as fp  # noqa: E402
import output_files as of  # noqa: E402
import resolve_topic as rt  # noqa: E402
from cases import CASES, STAGE2_CASES, STAGE2_TODAY  # noqa: E402
from test_resolve_topic import ReplayClient  # noqa: E402


def call(main, argv, **kw):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        code = main(argv, **kw)
    return code, json.loads(out.getvalue())


class OutputRoot(unittest.TestCase):
    def test_env_override_and_gitignore(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {of.OUTPUT_ENV_VAR: tmp + "/out"}):
            run = of.new_run_dir("Q333", now=dt.datetime(2026, 9, 27, 14, 52, 10))
            self.assertEqual(run.name, "20260927-145210-Q333")
            self.assertEqual((Path(tmp) / "out" / ".gitignore").read_text(encoding="utf-8").splitlines()[-1], "*")
            again = of.new_run_dir("Q333", now=dt.datetime(2026, 9, 27, 14, 52, 10))
            self.assertEqual(again.name, "20260927-145210-Q333-2")  # не перезаписує попередній запуск

    def test_run_from_skill_dir_does_not_write_next_to_code(self):
        with mock.patch.dict(os.environ, {of.OUTPUT_ENV_VAR: ""}), mock.patch.object(Path, "cwd",
                                                                                     return_value=of.SKILL_DIR):
            root = of.output_root()
        self.assertNotIn(of.SKILL_DIR, [root, *root.parents])


class FullChain(unittest.TestCase):
    def test_all_stages_write_into_one_run_dir(self):
        stage1, argv2 = STAGE2_CASES["pv_if_last24"]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {of.OUTPUT_ENV_VAR: tmp}):
            _, s1 = call(rt.main, CASES[stage1], client=ReplayClient(stage1))
            basket = Path(s1["full_basket_file"])
            self.assertEqual((basket.name, basket.parent.parent), ("basket.json", Path(tmp).resolve()))
            self.assertIn("fetch_pageviews.py --basket", s1["next_command"])
            self.assertTrue(any(s1["next_command"] in s for s in s1["next_steps"]))

            _, s2 = call(fp.main, argv2 + ["--basket", str(basket), "--today", STAGE2_TODAY],
                         client=ReplayClient("pv_if_last24"))
            self.assertEqual(Path(s2["full_views_file"]).resolve().parent, basket.parent)

            _, s3 = call(at.main, ["--views", s2["full_views_file"]])
            self.assertEqual(Path(s3["full_analysis_file"]).resolve().parent, basket.parent)
            self.assertIn("Створені файли — тека", s3["summary_uk"])

            _, s4 = call(br.main, ["--analysis", s3["full_analysis_file"], "--views", s2["full_views_file"],
                                   "--today", STAGE2_TODAY])
            files = sorted(p.name for p in basket.parent.iterdir())
            self.assertEqual(files, ["analysis.json", "basket.json", "report.pdf", "views.json", "views.svg"])
            reply = s4["reply_uk"]
            for name in files:
                self.assertIn(f"- {name} — ", reply)
            self.assertEqual(reply.count("Створені файли — тека"), 1)
            self.assertNotIn(at.REPORT_OFFER, reply)


if __name__ == "__main__":
    unittest.main()
