"""Офлайн-тести етапу 4 (build_report.py і pdf_writer.py): коректний PDF на одну
сторінку з кирилицею і зміст, узятий з аналізу етапу 3."""
import contextlib
import datetime as dt
import io
import json
import re
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import analyze_trend as at  # noqa: E402
import build_report as br  # noqa: E402
import pdf_writer as pw  # noqa: E402
from test_analyze_trend import make_views  # noqa: E402

TODAY = dt.date(2026, 9, 27)


def analysis_for(views):
    return at.run(views, at.GROWTH_THRESHOLD)


def pdf_text(pdf: bytes) -> str:
    """Текст сторінки через ToUnicode: без зовнішніх інструментів."""
    streams = [m.group(1) for m in re.finditer(rb"stream\n(.*?)\nendstream", pdf, re.S)]
    maps, content = {}, ""
    for raw in streams:
        try:
            data = zlib.decompress(raw)
        except zlib.error:
            data = raw
        text = data.decode("latin-1")
        if "beginbfchar" in text:
            for g, u in re.findall(r"<([0-9A-F]{4})> <([0-9A-F]+)>", text):
                maps.setdefault(g, bytes.fromhex(u).decode("utf-16-be"))
        elif " Tj " in text:
            content = text
    out = []
    for hexs in re.findall(r"<([0-9A-F]+)> Tj", content):
        out.append("".join(maps.get(hexs[i:i + 4], "?") for i in range(0, len(hexs), 4)))
    return "\n".join(out)


class PdfWriter(unittest.TestCase):
    def test_single_page_with_cyrillic_subset(self):
        fonts = br.load_fonts()
        page = pw.Page(fonts)
        page.text(40, 60, "Інтерес до «їжака»: ґанок −60 %", 12, "bold")
        pdf = page.to_pdf("Тест")
        self.assertTrue(pdf.startswith(b"%PDF-1.7"))
        self.assertEqual(len(re.findall(rb"/Type /Page\b", pdf)), 1)
        self.assertLess(len(pdf), 60_000)  # шрифт вбудовано підмножиною, не цілком
        self.assertIn("Інтерес до «їжака»: ґанок −60 %", pdf_text(pdf))

    def test_unsupported_script_is_detected(self):
        self.assertFalse(br.load_fonts()["regular"].supports("電気自動車"))
        self.assertTrue(br.load_fonts()["regular"].supports("Přerušovaný půst"))


class Content(unittest.TestCase):
    def test_growth_leader_and_implications(self):
        a = analysis_for(make_views({"de": [1000] * 12 + [1400] * 12, "fr": [1000] * 12 + [800] * 12}))
        self.assertTrue(br.headline(a).startswith("Найшвидше зростає інтерес — Німецька Wikipedia (de)"))
        imp = br.implications(a)
        self.assertTrue(imp[0].startswith("Кандидат для дослідження — Німецька"))
        self.assertTrue(imp[1].startswith("Не пріоритет за цими даними — Французька"))

    def test_missing_article_and_low_confidence(self):
        a = analysis_for(make_views({"pl": None, "sv": [20] * 12 + [30] * 12}))
        imp = br.implications(a)
        self.assertTrue(imp[0].startswith("Не виміряно — Польська"))
        self.assertTrue(imp[1].startswith("Потрібна перевірка — Шведська"))

    def test_limitations_name_method_and_threshold(self):
        text = " ".join(br.limitations(analysis_for(make_views({"uk": [1000] * 24}))))
        self.assertIn("рік до року", text)
        self.assertIn("±10 %", text)


class Report(unittest.TestCase):
    def build(self, series, question=None):
        views = make_views(series)
        page, variant = br.build(analysis_for(views), views, question, TODAY)
        return page.to_pdf("тест"), variant

    def test_many_languages_still_fit_one_page(self):
        series = {l: [1000 + 50 * i for i in range(24)] for l in ("en", "de", "fr", "ja", "es", "it", "pl", "uk")}
        pdf, variant = self.build(series, "Порівняй інтерес у восьми мовних розділах Wikipedia.")
        self.assertEqual(len(re.findall(rb"/Type /Page\b", pdf)), 1)
        self.assertLess(variant, len(br.LAYOUTS))

    def test_report_text_matches_analysis(self):
        pdf, _ = self.build({"uk": [1000] * 12 + [300] * 12}, "Чи зростає інтерес до астрономії?")
        text = pdf_text(pdf)
        for part in ("Інтерес до теми «тест» у Wikipedia", "Головне", "−70 %", "Чому така довіра",
                     "Що з цього випливає", "Припущення й обмеження", "Питання: «Чи зростає інтерес до астрономії?»"):
            self.assertIn(part, text)

    def test_cli(self):
        views = make_views({"uk": [1000] * 12 + [1300] * 12})
        a = analysis_for(views)
        a["summary_uk"] = at.summary_uk(a, None)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
            ap, vp, pdf = Path(tmp) / "a.json", Path(tmp) / "v.json", Path(tmp) / "r.pdf"
            ap.write_text(json.dumps(a, ensure_ascii=False), encoding="utf-8")
            vp.write_text(json.dumps(views, ensure_ascii=False), encoding="utf-8")
            code = br.main(["--analysis", str(ap), "--views", str(vp), "--out", str(pdf), "--today", "2026-09-27"])
            self.assertTrue(pdf.exists())
        result = json.loads(out.getvalue())
        self.assertEqual((code, result["status"], result["pages"]), (0, "ok", 1))
        self.assertTrue(any("Нікуди не публікуй" in s for s in result["next_steps"]))
        self.assertTrue(result["reply_uk"].endswith(f"Звіт на одну сторінку (PDF): {pdf}"))
        self.assertIn("інтерес зростає", result["reply_uk"])
        self.assertNotIn(at.REPORT_OFFER, result["reply_uk"])

    def test_rejects_stage2_file_as_analysis(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
            vp = Path(tmp) / "v.json"
            vp.write_text(json.dumps(make_views({"uk": [1] * 24})), encoding="utf-8")
            code = br.main(["--analysis", str(vp), "--views", str(vp), "--out", str(Path(tmp) / "r.pdf")])
        self.assertEqual((code, json.loads(out.getvalue())["status"]), (1, "error"))


if __name__ == "__main__":
    unittest.main()
