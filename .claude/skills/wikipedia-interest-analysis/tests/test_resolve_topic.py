"""Офлайн-тести: записані відповіді API (tests/fixtures) відтворюються через скрипт.

Запуск: python3 -m unittest discover -s tests
Після зміни запитів до API перезапишіть відповіді: python3 tests/record_fixtures.py
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import resolve_topic as rt  # noqa: E402
from cases import CASES  # noqa: E402


class ReplayClient:
    def __init__(self, name):
        self.responses = json.loads((HERE / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))

    def get_json(self, url, params):
        key = rt.request_key(url, params)
        if key not in self.responses:
            raise AssertionError(f"незаписаний запит (перезапустіть record_fixtures.py): {key}")
        data = self.responses[key]
        if "_http_error" in data:
            raise rt.ResolverError(f"HTTP {data['_http_error']} (запис)", status=data["_http_error"])
        return data


class NoNetworkClient:
    def get_json(self, url, params):
        raise AssertionError("мережу використовувати не можна")


def run(argv, client):
    with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
        path = Path(tmp) / "basket.json"
        code = rt.main(argv + ["--out", str(path)], client=client)
        full = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return code, json.loads(out.getvalue()), full


def run_case(name):
    return run(CASES[name], ReplayClient(name))


def codes(result):
    return {w["code"] for w in result.get("warnings", [])}


def titles(full, lang, kind="article"):
    return {a["title"] for a in full["articles"] if a["lang"] == lang and a["kind"] == kind}


class GoldenCases(unittest.TestCase):
    def test_intermittent_fasting_missing_in_polish(self):
        code, view, full = run_case("if_pl_cs")
        self.assertEqual(code, 0)
        self.assertEqual(view["status"], "partial")
        self.assertEqual(view["core"]["entity_id"], "Q1666254")
        self.assertEqual(view["coverage"]["cs"]["core_title"], "Přerušovaný půst")
        self.assertIsNone(view["coverage"]["pl"]["core_title"])
        self.assertIn("Q44602", [b["entity_id"] for b in view["coverage"]["pl"]["broader_with_article"]])
        self.assertIn("core_missing", codes(view))
        self.assertEqual(titles(full, "pl"), set())
        self.assertEqual(titles(full, "cs"), {"Přerušovaný půst"})
        # ширше поняття пропонується, але ніколи не додається мовчки
        self.assertFalse(any(m["included"] for m in full["members"] if m["role"] != "core"))

    def test_polish_phrase_finds_mentions_only(self):
        _, view, _ = run_case("if_pl_phrase")
        mentions = view["coverage"]["pl"]["fallback"]["mentions"]
        self.assertEqual(mentions[0]["phrase"], "post przerywany")
        self.assertGreater(mentions[0]["total_articles"], 0)
        self.assertEqual(view["coverage"]["pl"]["included_articles"], 0)

    def test_include_broader_is_flagged_asymmetric(self):
        _, view, full = run_case("if_include_broader")
        self.assertEqual(titles(full, "pl"), {"Post"})
        self.assertEqual(titles(full, "cs"), {"Přerušovaný půst", "Půst"})
        self.assertIn("asymmetric_basket", codes(view))

    def test_entity_skips_search(self):
        code, view, _ = run_case("if_entity_cs")
        self.assertEqual((code, view["status"]), (0, "resolved"))
        self.assertEqual(view["coverage"]["cs"]["core_title"], "Přerušovaný půst")

    def test_astronomy_beats_hogwarts_class(self):
        _, view, full = run_case("astronomy_uk")
        self.assertEqual(view["status"], "resolved")
        self.assertEqual(view["core"]["entity_id"], "Q333")
        self.assertIn("resolved_by_dominance", codes(view))
        self.assertEqual(titles(full, "uk"), {"Астрономія"})
        self.assertEqual(view["core"]["label"], "астрономія")  # назви показуються українською
        for r in (a for a in full["articles"] if a["kind"] == "redirect"):
            self.assertEqual(r["redirect_to"], "Астрономія")
        self.assertTrue(any(m["role"] == "narrower" for m in full["members"]))

    def test_english_learning_uses_consensus_not_first_hit(self):
        _, view, _ = run_case("english_learning")
        self.assertEqual(view["core"]["entity_id"], "Q130192")
        self.assertEqual(view["status"], "partial")
        self.assertEqual(view["coverage"]["de"]["core_title"], "Englisch als Zweitsprache")
        self.assertIsNone(view["coverage"]["uk"]["core_title"])
        # сама українська фраза знаходить «International Corpus of English» лише повнотекстовим пошуком
        self.assertIn("user_phrase_weak_match", codes(view))
        self.assertNotIn("user_phrase_differs", codes(view))
        cs_matches = view["coverage"]["cs"]["fallback"]["exact_title_matches"]
        self.assertNotIn("Evaluation Assurance Level", [m["title"] for m in cs_matches])

    def test_agent_qualifier_is_flagged(self):
        code, view, _ = run_case("mercury_agent_qualifier")
        self.assertEqual((code, view["core"]["entity_id"]), (0, "Q308"))
        warning = next(w for w in view["warnings"] if w["code"] == "user_phrase_differs")
        self.assertIn("Q1150", warning["alternatives"])  # римський бог
        self.assertEqual(view["reply_language"], "uk")  # україномовна аудиторія навіть для російського запиту
        self.assertIn("українською", view["next_steps"][0])
        self.assertTrue(view["next_steps"][2].startswith("СПОЧАТКУ"))

    def test_unknown_edition_is_not_a_network_error(self):
        code, view, _ = run_case("unknown_edition")
        self.assertEqual((code, view["status"]), (1, "error"))
        self.assertTrue(view["reason"].startswith("unknown_wikipedia_edition: tlh"))
        self.assertEqual(view["targets"], ["pl", "tlh"])
        self.assertEqual(view["input_queries"], ["ru:биткоин"])

    def test_bare_surname_asks_which_person(self):
        _, view, _ = run_case("surname_only")
        self.assertEqual(view["core"]["entity_id"], "Q134958")
        warning = next(w for w in view["warnings"] if w["code"] == "user_phrase_differs")
        self.assertIn("прізвище", warning["detail"])
        self.assertTrue(view["next_steps"][2].startswith("СПОЧАТКУ"))

    def test_broader_translation_asks_to_confirm(self):
        _, view, _ = run_case("ev_broad_translation")
        self.assertEqual(view["core"]["entity_id"], "Q13629441")  # електротранспорт
        self.assertIn("core_label_mismatch", codes(view))
        self.assertTrue(view["next_steps"][2].startswith("СПОЧАТКУ"))

    def test_exact_translation_needs_no_question(self):
        _, view, _ = run_case("ev_exact_translation")
        self.assertEqual(view["core"]["entity_id"], "Q193692")  # електромобіль
        self.assertNotIn("core_label_mismatch", codes(view))
        self.assertNotIn("user_phrase_differs", codes(view))

    def test_latin_name_in_ukrainian_query_is_not_a_mismatch(self):
        _, view, _ = run_case("bitcoin_latin")
        self.assertEqual(view["core"]["entity_id"], "Q131723")
        self.assertNotIn("core_label_mismatch", codes(view))

    def test_targets_are_echoed(self):
        _, view, _ = run_case("ev_exact_translation")
        self.assertIn("--targets (en, de)", view["next_steps"][1])

    def test_not_found_forbids_unasked_searches(self):
        code, view, _ = run_case("nonsense")
        self.assertEqual((code, view["status"]), (1, "not_found"))
        self.assertTrue(any("без його дозволу" in s for s in view["next_steps"]))

    def test_substituted_user_words_are_flagged(self):
        _, view, _ = run_case("english_substituted")
        self.assertEqual(view["core"]["entity_id"], "Q1860")  # англійська мова — ширше поняття
        self.assertIn("query_not_in_user_message", codes(view))
        self.assertTrue(view["next_steps"][2].startswith("СПОЧАТКУ виправ запит"))

    def test_users_own_words_are_not_flagged(self):
        for name in ("if_pl_cs", "english_learning", "ev_broad_translation", "bitcoin_latin", "mercury_agent_qualifier"):
            _, view, _ = run_case(name)
            self.assertNotIn("query_not_in_user_message", codes(view), name)

    def test_mercury_is_ambiguous(self):
        code, view, full = run_case("mercury_ambiguous")
        self.assertEqual((code, view["status"]), (0, "ambiguous"))
        self.assertIsNone(full)
        ids = [c["entity_id"] for c in view["candidates"]]
        self.assertIn("Q308", ids)
        self.assertIn("Q925", ids)


class ArgumentErrors(unittest.TestCase):
    def check_error(self, argv, reason_prefix):
        code, view, _ = run(argv, NoNetworkClient())
        self.assertEqual((code, view["status"]), (1, "error"))
        self.assertTrue(view["reason"].startswith(reason_prefix), view["reason"])

    def test_empty_targets(self):
        self.check_error(["--query", "en:x", "--targets", " , "], "no_targets_given")

    def test_query_without_language(self):
        self.check_error(["--query", "astronomy", "--targets", "uk"], "bad_query_format")

    def test_no_query(self):
        self.check_error(["--targets", "uk"], "no_query_given")

    def test_query_without_user_message(self):
        self.check_error(["--query", "uk:кава", "--targets", "pl"], "no_user_message")

    def test_bad_qid(self):
        self.check_error(["--entity", "333", "--targets", "uk"], "bad_qid")


class Ranking(unittest.TestCase):
    def test_exact_label_beats_prefix_and_alias(self):
        exact = rt.match_rank({"type": "label", "text": "Астрономія", "language": "uk"}, "астрономія", "uk")
        prefix = rt.match_rank({"type": "label", "text": "Астрономія у Китаї", "language": "uk"}, "астрономія", "uk")
        alias = rt.match_rank({"type": "alias", "text": "астрономія", "language": "uk"}, "астрономія", "uk")
        self.assertLess(exact, alias)
        self.assertLess(alias, prefix)

    def test_query_language_beats_fallback_language(self):
        own = rt.match_rank({"type": "label", "text": "x", "language": "uk"}, "x", "uk")
        other = rt.match_rank({"type": "label", "text": "x", "language": "mul"}, "x", "uk")
        self.assertLess(own, other)

    def test_acronyms(self):
        self.assertTrue(rt.is_acronym("EAL"))
        self.assertTrue(rt.is_acronym("E.S.L."))
        self.assertFalse(rt.is_acronym("Post"))


if __name__ == "__main__":
    unittest.main()
