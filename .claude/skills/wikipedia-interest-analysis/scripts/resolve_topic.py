#!/usr/bin/env python3
"""
resolve_topic.py — перетворює тему користувача на «кошик теми»: одне основне
поняття Wikidata і точні статті Вікіпедії (разом із перенаправленнями), які
представляють його в кожному цільовому мовному розділі. Результат готовий для
Pageviews API.

Етапи:
  1. пошук        — кожен --query (МОВА:ТЕКСТ) шукається у Wikidata
                    (wbsearchentities, повнотекстовий пошук як запасний варіант).
  2. вибір        — перемагає кандидат, якого знайшло більше формулювань; далі
                    точна назва > точний синонім > збіг за початком. Нічию
                    розв'язує лише перевага в DOMINANCE_RATIO разів за кількістю
                    мовних розділів зі статтею, інакше результат «ambiguous».
  3. розширення   — перелічуються ширші поняття (P279/P361 основного) і вужчі
                    (ті, чиї P279/P31/P361 вказують на основне). Мовчки вони не
                    додаються: --scope extended додає вужчі, що є в усіх цільових
                    розділах, --include додає вибрані QID.
  4. перенаправлення — для кожної включеної статті збираються перенаправлення,
                    бо Pageviews рахує перегляди перенаправлення під його назвою.
  5. запасний пошук — для розділів, де в основного поняття немає пов'язаної
                    статті, шукаються сторінки з точно такою назвою і згадки
                    фрази. Знахідки — лише докази для користувача, у кошик не йдуть.

Використовується тільки стандартна бібліотека Python. Мережеві запити йдуть
на www.wikidata.org і <мова>.wikipedia.org.
"""

import argparse
import difflib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
# Політика User-Agent Wikimedia вимагає контакт; він береться зі змінної
# середовища, щоб ніколи не потрапити в код навички.
CONTACT_ENV_VAR = "WIKIPEDIA_RESOLVER_CONTACT"
USER_AGENT_TEMPLATE = "wikipedia-interest-analysis/0.3 (skill; contact: {contact})"

# Аудиторія навички україномовна, хоч би якою мовою була введена тема.
REPLY_LANGUAGE = "uk"
LABEL_LANGS = ["uk", "en"]

SEARCH_LIMIT = 10
FULLTEXT_LIMIT = 5
RELATED_SEARCH_LIMIT = 50
RELATED_STDOUT_LIMIT = 15
AMBIGUOUS_LIMIT = 5
DOMINANCE_RATIO = 3
BATCH = 50
MIN_FALLBACK_PHRASE_LEN = 3
# Нижче цього порогу назва вибраного поняття не схожа на слова користувача
# («електромобілі» / «електротранспорт» = 0.55; відмінки й опечатки дають >= 0.8).
LABEL_MATCH_MIN = 0.75

NAME_CLASSES = {
    "Q101352": "прізвище", "Q202444": "ім'я", "Q12308941": "чоловіче ім'я",
    "Q11879590": "жіноче ім'я", "Q4167410": "сторінка неоднозначності",
}
NAME_ITEM_MAX_ARTICLES = 60  # елементи-імена невеликі; великим сутностям claims не завантажуємо
NARROWER_PROPS = ("P279", "P31", "P361")
BROADER_PROPS = ("P279", "P361")
NON_WIKIPEDIA_SITES = {
    "commonswiki", "specieswiki", "metawiki", "mediawikiwiki", "wikidatawiki",
    "sourceswiki", "wikimaniawiki", "outreachwiki", "incubatorwiki",
    "wikifunctionswiki", "foundationwiki",
}
QUERY_RE = re.compile(r"^([a-z][a-z0-9-]{1,11}):(.+)$", re.S)
QID_RE = re.compile(r"^Q[1-9][0-9]*$")


class ResolverError(Exception):
    pass


class WikimediaClient:
    def __init__(self, user_agent: str, retries: int = 2):
        self.user_agent = user_agent
        self.retries = retries

    def get_json(self, url: str, params: dict) -> dict:
        full_url = request_key(url, params)
        req = urllib.request.Request(full_url, headers={"User-Agent": self.user_agent})
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code in (429, 502, 503, 504) and attempt < self.retries:
                    time.sleep(_retry_delay(e.headers.get("Retry-After"), attempt))
                    continue
                raise ResolverError(f"HTTP {e.code} для {full_url}") from e
            except urllib.error.URLError as e:
                raise ResolverError(f"Не вдалося з'єднатися з {url}: {e.reason}") from e
            if "error" in data:
                raise ResolverError(f"Помилка API для {full_url}: {data['error'].get('info', data['error'])}")
            return data
        raise ResolverError(f"Вичерпано спроби для {full_url}")


def request_key(url: str, params: dict) -> str:
    return f"{url}?{urllib.parse.urlencode(sorted((k, str(v)) for k, v in params.items()))}"


def _retry_delay(retry_after, attempt: int) -> float:
    try:
        return min(float(retry_after), 10.0)
    except (TypeError, ValueError):
        return 2.0 ** attempt


def wiki_api(lang: str) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"


def site_key(lang: str) -> str:
    return lang.replace("-", "_") + "wiki"


def wikipedia_sitelink_count(sitelinks: dict) -> int:
    return sum(1 for k in sitelinks if k.endswith("wiki") and k not in NON_WIKIPEDIA_SITES)


def parse_queries(raw: list) -> list:
    parsed = []
    for item in raw:
        m = QUERY_RE.match(item.strip())
        if not m or not m.group(2).strip():
            raise ValueError(f"bad_query_format: {item!r}, очікується МОВА:ТЕКСТ, напр. uk:астрономія")
        parsed.append((m.group(1), m.group(2).strip()))
    return parsed


# ---------- етапи 1-2: пошук і вибір основного поняття ----------

def match_rank(match: dict, text: str, lang: str) -> tuple:
    """Менше — краще: точна назва, точний синонім, назва за початком, синонім за
    початком, опис, повнотекстовий збіг; далі збіг мовою запиту кращий за інші."""
    kind = match.get("type")
    exact = match.get("text", "").casefold() == text.casefold()
    if kind == "label":
        rank = 0 if exact else 2
    elif kind == "alias":
        rank = 1 if exact else 3
    elif kind == "fulltext":
        rank = 5
    else:
        rank = 4
    return (rank, 0 if match.get("language") == lang else 1)


def search_candidates(client, queries: list) -> dict:
    """Повертає {qid: {"мова:текст": найкращий ранг збігу для цього запиту}}."""
    found = {}
    for lang, text in queries:
        hits = client.get_json(WIKIDATA_API, {
            "action": "wbsearchentities", "search": text, "language": lang,
            "uselang": "en", "type": "item", "limit": SEARCH_LIMIT, "format": "json",
        }).get("search", [])
        matches = [(h["id"], h.get("match", {})) for h in hits]
        if not matches:
            data = client.get_json(WIKIDATA_API, {
                "action": "query", "list": "search", "srsearch": text, "srnamespace": 0,
                "srlimit": FULLTEXT_LIMIT, "srprop": "", "format": "json",
            })
            matches = [(h["title"], {"type": "fulltext", "language": lang})
                       for h in data.get("query", {}).get("search", []) if QID_RE.match(h["title"])]
        qkey = f"{lang}:{text}"
        for qid, match in matches:
            rank = match_rank(match, text, lang)
            ranks = found.setdefault(qid, {})
            ranks[qkey] = min(ranks.get(qkey, rank), rank)
    return found


def get_entities(client, ids: list, props: str, languages=None, sitefilter=None) -> dict:
    out = {}
    for i in range(0, len(ids), BATCH):
        params = {"action": "wbgetentities", "ids": "|".join(ids[i:i + BATCH]),
                  "props": props, "format": "json"}
        if languages:
            params["languages"] = "|".join(languages)
        if sitefilter:
            params["sitefilter"] = "|".join(sitefilter)
        for qid, ent in client.get_json(WIKIDATA_API, params).get("entities", {}).items():
            if "missing" not in ent:
                out[qid] = ent
    return out


def en_text(ent: dict, field: str) -> str:
    return ent.get(field, {}).get("en", {}).get("value", "")


def ui_text(ent: dict, field: str) -> str:
    """Назва чи опис для показу: українською, якщо є, інакше англійською."""
    for lang in LABEL_LANGS:
        value = ent.get(field, {}).get(lang, {}).get("value")
        if value:
            return value
    return ""


def target_titles(ent: dict, targets: list) -> dict:
    links = ent.get("sitelinks", {})
    return {t: links[site_key(t)]["title"] for t in targets if site_key(t) in links}


def rank_candidates(found: dict, ents: dict, only=None) -> list:
    """Спершу кандидати, яких знайшло більше запитів, далі — за найкращим рангом.
    З `only` ранжує так, ніби було передано лише цей запит."""
    ranked = []
    for qid, ranks in found.items():
        if only is not None:
            if only not in ranks:
                continue
            ranks = {only: ranks[only]}
        ent = ents.get(qid)
        count = wikipedia_sitelink_count(ent.get("sitelinks", {})) if ent else 0
        if count == 0:
            continue  # наукові статті, властивості Wikidata, заготовки без жодної статті
        best = min(ranks.values())
        ranked.append({"entity_id": qid, "entity": ent, "wiki_count": count,
                       "key": (-len(ranks), best[0], best[1])})
    ranked.sort(key=lambda c: (c["key"], -c["wiki_count"]))
    return ranked


def decide(ranked: list) -> tuple:
    """Повертає (статус, кандидати_з_нічиєю, переможений_суперник_або_None)."""
    if not ranked:
        return "not_found", [], None
    tied = [c for c in ranked if c["key"] == ranked[0]["key"]]
    if len(tied) == 1:
        return "resolved", tied, None
    if tied[0]["wiki_count"] >= DOMINANCE_RATIO * tied[1]["wiki_count"]:
        return "resolved", tied, tied[1]
    return "ambiguous", tied, None


def describe(c: dict) -> str:
    return (f"{c['entity_id']} ({ui_text(c['entity'], 'labels')}: {ui_text(c['entity'], 'descriptions')}; "
            f"статті в {c['wiki_count']} мовних розділах)")


def choose_core(client, queries: list, targets: list):
    """Повертає ("resolved", сутність, примітки) або ("ambiguous"/"not_found", дані, [])."""
    found = search_candidates(client, queries)
    if not found:
        return "not_found", {"reason": "no_wikidata_match"}, []
    ents = get_entities(client, list(found), "sitelinks|labels|descriptions", languages=LABEL_LANGS)
    status, tied, runner = decide(rank_candidates(found, ents))
    if status == "not_found":
        return "not_found", {"reason": "no_candidate_has_any_wikipedia_article",
                             "checked_candidates": sorted(found)}, []
    if status == "ambiguous":
        return "ambiguous", {"candidates": [
            {"entity_id": c["entity_id"], "label": ui_text(c["entity"], "labels"),
             "description": ui_text(c["entity"], "descriptions"),
             "language_editions_with_article": c["wiki_count"],
             "titles": target_titles(c["entity"], targets)}
            for c in tied[:AMBIGUOUS_LIMIT]]}, []
    winner, notes = tied[0], []
    winner_label = ui_text(winner["entity"], "labels")
    winner_desc = ui_text(winner["entity"], "descriptions")
    if runner:
        notes.append({"code": "resolved_by_dominance",
                      "detail": f"запит також збігся з {describe(runner)}; обрано значно поширеніше {describe(winner)}"})
    if len(queries) > 1:
        # Додаткові формулювання пише агент, а не користувач: позначаємо випадки,
        # коли значення визначили вони, а не слова користувача.
        own = f"{queries[0][0]}:{queries[0][1]}"
        own_text = queries[0][1]
        own_status, own_tied, _ = decide(rank_candidates(found, ents, only=own))
        # Елементи-імена зазвичай не мають статей, тож rank_candidates їх відкидає;
        # перевіряємо їх окремо: саме прізвище може означати багатьох людей.
        small = [qid for qid, ranks in found.items() if own in ranks and ranks[own][0] <= 1 and qid in ents
                 and wikipedia_sitelink_count(ents[qid].get("sitelinks", {})) <= NAME_ITEM_MAX_ARTICLES]
        typed = get_entities(client, small, "claims") if small else {}
        name_hits = [(qid, NAME_CLASSES[c]) for qid in small if qid in typed
                     for c in claim_ids(typed[qid], "P31") if c in NAME_CLASSES]
        if name_hits and winner["entity_id"] not in {q for q, _ in name_hits}:
            qid, kind = name_hits[0]
            notes.append({"code": "user_phrase_differs",
                          "detail": f"фраза користувача '{own}' — це {kind} ({qid}), вона може означати багатьох "
                                    f"різних людей або речі. Додаткові формулювання обрали {describe(winner)}",
                          "question": f"Під «{own_text}» ви маєте на увазі {winner_label} ({winner_desc}) "
                                      f"чи когось або щось інше?",
                          "alternatives": []})
        elif own_status == "ambiguous" or (own_status == "resolved" and own_tied[0]["entity_id"] != winner["entity_id"]):
            verb = "неоднозначна, підходять" if own_status == "ambiguous" else "вказує на"
            # Лише точний збіг назви чи синоніма робить фразу користувача справжнім
            # конкурентним прочитанням; збіги за початком чи в тексті — шум, вартий одного рядка.
            strong = own_tied[0]["key"][1] <= 1
            notes.append({"code": "user_phrase_differs" if strong else "user_phrase_weak_match",
                          "detail": f"фраза користувача '{own}' сама по собі {verb} "
                                    + "; ".join(describe(c) for c in own_tied[:AMBIGUOUS_LIMIT])
                                    + f". Додаткові формулювання обрали {describe(winner)}",
                          "question": f"Під «{own_text}» ви маєте на увазі {winner_label} ({winner_desc})?",
                          "alternatives": [c["entity_id"] for c in own_tied[:AMBIGUOUS_LIMIT]
                                           if c["entity_id"] != winner["entity_id"]]})
    if not any(n["code"] == "user_phrase_differs" for n in notes):
        note = label_mismatch_note(client, winner, queries[0][0], queries[0][1])
        if note:
            notes.append(note)
    return "resolved", winner["entity"], notes


# ---------- етап 3: пов'язані поняття ----------

def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.casefold(), b.casefold()).ratio()


def label_mismatch_note(client, winner: dict, lang: str, text: str):
    """Перевіряє, чи схожа назва вибраного поняття мовою користувача на його слова.
    Ловить випадки, коли агент переклав тему ширшим чи іншим поняттям."""
    # Англійські назви теж рахуються: «Bitcoin» латиницею в українському запиті — не розбіжність.
    langs = list(dict.fromkeys([lang, "en"]))
    names = get_entities(client, [winner["entity_id"]], "labels|aliases", languages=langs).get(winner["entity_id"], {})
    local = [names.get("labels", {}).get(lang, {}).get("value")]
    local += [a["value"] for a in names.get("aliases", {}).get(lang, [])]
    local = [n for n in local if n]
    known = local + [names.get("labels", {}).get("en", {}).get("value")]
    known += [a["value"] for a in names.get("aliases", {}).get("en", [])]
    known = [n for n in known if n]
    if not local or max(similarity(text, n) for n in known) >= LABEL_MATCH_MIN:
        return None
    return {"code": "core_label_mismatch",
            "detail": f"слова користувача «{text}» не схожі на назву вибраного поняття мовою {lang}: "
                      f"«{local[0]}» — {describe(winner)}. Можливо, англійське формулювання передало "
                      f"ширше чи інше поняття",
            "question": f"Під «{text}» ви маєте на увазі «{local[0]}» ({ui_text(winner['entity'], 'descriptions')})?",
            "alternatives": []}


def claim_ids(ent: dict, prop: str) -> list:
    ids = []
    for claim in ent.get("claims", {}).get(prop, []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(value, dict) and value.get("id"):
            ids.append(value["id"])
    return ids


def find_narrower(client, qid: str) -> tuple:
    ids, truncated = [], False
    for prop in NARROWER_PROPS:
        data = client.get_json(WIKIDATA_API, {
            "action": "query", "list": "search", "srsearch": f"haswbstatement:{prop}={qid}",
            "srnamespace": 0, "srlimit": RELATED_SEARCH_LIMIT, "srprop": "", "format": "json",
        }).get("query", {})
        truncated |= data.get("searchinfo", {}).get("totalhits", 0) > RELATED_SEARCH_LIMIT
        ids += [h["title"] for h in data.get("search", []) if QID_RE.match(h["title"])]
    return list(dict.fromkeys(i for i in ids if i != qid)), truncated


def related_members(client, ids: list, role: str, targets: list) -> list:
    ents = get_entities(client, ids, "sitelinks|labels", languages=LABEL_LANGS,
                        sitefilter=[site_key(t) for t in targets])
    members = []
    for qid in ids:
        ent = ents.get(qid)
        if not ent:
            continue
        titles = target_titles(ent, targets)
        if not titles:
            continue
        members.append({"entity_id": qid, "label": ui_text(ent, "labels"), "role": role,
                        "titles": titles, "in_all_targets": len(titles) == len(targets)})
    members.sort(key=lambda m: (-len(m["titles"]), int(m["entity_id"][1:])))
    return members


# ---------- етапи 4-5: перенаправлення і запасний пошук у кожній Вікіпедії ----------

def fetch_redirects(client, lang: str, titles: list) -> dict:
    out = {t: [] for t in titles}
    for i in range(0, len(titles), BATCH):
        params = {"action": "query", "titles": "|".join(titles[i:i + BATCH]), "prop": "redirects",
                  "rdnamespace": 0, "rdlimit": "max", "format": "json", "formatversion": 2}
        while True:
            data = client.get_json(wiki_api(lang), params)
            for page in data.get("query", {}).get("pages", []):
                if page.get("title") in out:
                    out[page["title"]] += [r["title"] for r in page.get("redirects", [])]
            if "continue" not in data:
                break
            params = {**params, **data["continue"]}
    return out


def exact_title_matches(client, lang: str, phrases: list, core_qid: str) -> list:
    data = client.get_json(wiki_api(lang), {
        "action": "query", "titles": "|".join(phrases[:BATCH]), "redirects": 1,
        "prop": "pageprops", "ppprop": "wikibase_item", "format": "json", "formatversion": 2,
    }).get("query", {})
    redirected_from = {r["to"]: r["from"] for r in data.get("redirects", [])}
    matches = []
    for page in data.get("pages", []):
        if page.get("missing") or page.get("invalid") or page.get("ns") != 0:
            continue
        item = page.get("pageprops", {}).get("wikibase_item")
        matches.append({"title": page["title"], "via_redirect_from": redirected_from.get(page["title"]),
                        "wikibase_item": item, "same_concept": item == core_qid})
    return matches


def phrase_mentions(client, lang: str, phrase: str) -> dict:
    data = client.get_json(wiki_api(lang), {
        "action": "query", "list": "search", "srsearch": f'"{phrase}"', "srnamespace": 0,
        "srlimit": 3, "srprop": "", "format": "json",
    }).get("query", {})
    return {"phrase": phrase, "total_articles": data.get("searchinfo", {}).get("totalhits", 0),
            "sample_titles": [h["title"] for h in data.get("search", [])]}


def is_acronym(text: str) -> bool:
    # Англійські абревіатури (ESL, EAL) збігаються з непов'язаними сторінками в інших вікі.
    compact_text = text.replace(".", "").replace(" ", "")
    return len(compact_text) <= 6 and compact_text.isupper()


def fallback_for(client, lang: str, core: dict, queries: list) -> dict:
    local = [core.get("labels", {}).get(lang, {}).get("value")]
    local += [a["value"] for a in core.get("aliases", {}).get(lang, []) if not is_acronym(a["value"])]
    local += [text for qlang, text in queries if qlang == lang]
    local = [p for p in dict.fromkeys(local) if p and len(p) >= MIN_FALLBACK_PHRASE_LEN]
    english = [en_text(core, "labels")] + [a["value"] for a in core.get("aliases", {}).get("en", [])
                                           if not is_acronym(a["value"])]
    english += [text for qlang, text in queries if qlang == "en"]
    phrases = [p for p in dict.fromkeys(local + english) if p and len(p) >= MIN_FALLBACK_PHRASE_LEN]
    result = {"phrases_tried": phrases,
              "exact_title_matches": exact_title_matches(client, lang, phrases, core["id"]) if phrases else [],
              "mentions": [phrase_mentions(client, lang, p) for p in local]}
    if not local:
        result["note"] = (f"невідомо, як тема звучить мовою {lang}; додайте --query {lang}:<фраза>, "
                          f"щоб пошукати згадки")
    return result


# ---------- складання кошика ----------

def build_basket(client, core: dict, queries: list, targets: list, scope: str,
                 include: list, notes: list) -> dict:
    qid = core["id"]
    core_titles = target_titles(core, targets)
    warnings = list(notes)

    broader = related_members(client, list(dict.fromkeys(
        i for p in BROADER_PROPS for i in claim_ids(core, p))), "broader", targets)
    narrower_ids, truncated = find_narrower(client, qid)
    narrower = related_members(client, narrower_ids, "narrower", targets)
    if truncated:
        warnings.append({"code": "related_truncated",
                         "detail": f"понад {RELATED_SEARCH_LIMIT} вужчих понять на одну властивість; "
                                   f"перевірено лише перші"})

    known = {m["entity_id"]: m for m in broader + narrower}
    unknown = [i for i in include if i not in known and i != qid]
    for m in related_members(client, unknown, "user_added", targets):
        known[m["entity_id"]] = m
    for i in unknown:
        if i not in known:
            warnings.append({"code": "include_ignored",
                             "detail": f"{i} не має статті в жодному з розділів: {', '.join(targets)}"})

    members = [{"entity_id": qid, "label": ui_text(core, "labels"), "role": "core",
                "titles": core_titles, "in_all_targets": len(core_titles) == len(targets),
                "included": True}]
    for m in broader + narrower + [known[i] for i in unknown if i in known]:
        included = m["entity_id"] in include or (
            scope == "extended" and m["role"] == "narrower" and m["in_all_targets"])
        members.append({**m, "included": included})

    articles, coverage = [], {}
    for lang in targets:
        chosen = [(m, m["titles"][lang]) for m in members if m["included"] and lang in m["titles"]]
        redirects = fetch_redirects(client, lang, [t for _, t in chosen]) if chosen else {}
        for m, title in chosen:
            articles.append({"lang": lang, "project": f"{lang}.wikipedia", "title": title,
                             "kind": "article", "entity_id": m["entity_id"], "role": m["role"],
                             "source": "wikidata_sitelink"})
            articles += [{"lang": lang, "project": f"{lang}.wikipedia", "title": r, "kind": "redirect",
                          "redirect_to": title, "entity_id": m["entity_id"], "role": m["role"],
                          "source": "redirect"} for r in redirects.get(title, [])]
        entry = {"core_title": core_titles.get(lang),
                 "included_articles": len(chosen),
                 "included_redirects": sum(len(redirects.get(t, [])) for _, t in chosen)}
        if lang not in core_titles:
            entry["fallback"] = fallback_for(client, lang, core, queries)
            entry["broader_with_article"] = [
                {"entity_id": b["entity_id"], "label": b["label"], "title": b["titles"][lang]}
                for b in broader if lang in b["titles"]]
        coverage[lang] = entry

    missing = [t for t in targets if t not in core_titles]
    if missing:
        warnings.append({"code": "core_missing",
                         "detail": f"немає статті, пов'язаної з {qid}, у розділах: {', '.join(missing)}"})
    if any(e.get("fallback", {}).get("exact_title_matches") for e in coverage.values()):
        warnings.append({"code": "unverified_fallback_titles",
                         "detail": "знайдено сторінки з точно такою назвою поза зв'язками Wikidata; "
                                   "до кошика не включені, підтвердьте з користувачем"})
    included_sets = {lang: {a["entity_id"] for a in articles if a["lang"] == lang and a["kind"] == "article"}
                     for lang in targets}
    if len({frozenset(s) for s in included_sets.values()}) > 1:
        warnings.append({"code": "asymmetric_basket",
                         "detail": "у різних мовах вимірюються різні набори понять; "
                                   "порівняння між мовами нерівноцінне"})

    if not core_titles:
        status = "not_found"
    elif missing:
        status = "partial"
    else:
        status = "resolved"
    basket = {
        "status": status,
        "input_queries": [f"{l}:{t}" for l, t in queries],
        "targets": targets,
        "scope": scope,
        "core": {"entity_id": qid, "label": ui_text(core, "labels"),
                 "description": ui_text(core, "descriptions"),
                 "language_editions_with_article": wikipedia_sitelink_count(core.get("sitelinks", {}))},
        "coverage": coverage,
        "members": members,
        "articles": articles,
        "warnings": warnings,
    }
    if status == "not_found":
        basket["reason"] = "no_article_in_any_target"
    basket["next_steps"] = next_steps(basket)
    return basket


def next_steps(b: dict) -> list:
    steps = []
    qid = b["core"]["entity_id"]
    for w in b["warnings"]:
        if w["code"] in ("user_phrase_differs", "core_label_mismatch"):
            options = f" QID кандидатів: {', '.join(w['alternatives'])}." if w["alternatives"] else ""
            steps.append(f"СПОЧАТКУ постав користувачу питання: «{w['question']}» Зупинись і чекай відповіді. "
                         f"Причина: {w['detail']}. Якщо він має на увазі інше, перезапусти з його уточненим "
                         f"формулюванням або з --entity <QID>.{options}")
    for w in b["warnings"]:
        if w["code"] == "user_phrase_weak_match":
            steps.append(f"Згадай одним рядком, питати не треба: {w['detail']}.")
        elif w["code"] == "resolved_by_dominance":
            steps.append(f"Згадай одним рядком: {w['detail']}.")
    for lang, entry in b["coverage"].items():
        if entry["core_title"]:
            continue
        steps.append(f"Скажи користувачу: у {lang}.wikipedia немає статті про «{b['core']['label']}» ({qid}).")
        for m in entry["fallback"]["exact_title_matches"]:
            steps.append(f"Неперевірена сторінка «{m['title']}» у {lang}.wikipedia (елемент {m['wikibase_item']}) "
                         f"має відому назву теми; запитай користувача, перш ніж її використовувати, потім "
                         f"перезапусти з --include {m['wikibase_item']}.")
        for men in entry["fallback"]["mentions"]:
            if men["total_articles"]:
                steps.append(f"Фразу «{men['phrase']}» згадано в {men['total_articles']} статтях {lang}.wikipedia "
                             f"(напр., {', '.join(men['sample_titles'])}): тема є лише всередині інших статей.")
        if "note" in entry["fallback"]:
            steps.append(f"За бажанням переклади тему мовою {lang} і перезапусти, додавши --query {lang}:<фраза>.")
        for br in entry["broader_with_article"]:
            steps.append(f"Запропонуй ширше поняття {br['entity_id']} «{br['label']}» ({lang}: {br['title']}) "
                         f"через --include {br['entity_id']}; попередь, що воно ширше і це не та сама тема.")
    optional = [m for m in b["members"] if m["role"] == "narrower" and not m["included"] and m["in_all_targets"]]
    if optional:
        steps.append(f"Вужчих понять, що є в усіх вибраних розділах: {len(optional)} (напр., "
                     f"{', '.join(m['label'] or m['entity_id'] for m in optional[:3])}); запропонуй "
                     f"--scope extended або --include <QID>, щоб розширити тему.")
    if not steps:
        steps.append("Кошик готовий; передай його 'articles' на етап збору переглядів.")
    return steps


def compact(result: dict, out_path: str) -> dict:
    view = {k: v for k, v in result.items() if k not in ("articles", "members")}
    included = [m for m in result["members"] if m["included"]]
    optional = [m for m in result["members"] if not m["included"]]
    view["included_members"] = [{k: m[k] for k in ("entity_id", "label", "role", "titles")} for m in included]
    view["optional_members"] = [{k: m[k] for k in ("entity_id", "label", "role", "titles")}
                                for m in optional[:RELATED_STDOUT_LIMIT]]
    view["optional_members_total"] = len(optional)
    view["full_basket_file"] = out_path
    return view


def unknown_targets(client, targets: list) -> list:
    info = client.get_json(WIKIDATA_API, {"action": "paraminfo", "modules": "wbgetentities", "format": "json"})
    params = info["paraminfo"]["modules"][0]["parameters"]
    sites = set(next(x["type"] for x in params if x["name"] == "sites"))
    return [t for t in targets if site_key(t) not in sites]


def _resolve(client, queries: list, targets: list, scope: str, include: list, entity) -> dict:
    unknown = unknown_targets(client, targets)
    if unknown:
        codes = ", ".join(unknown)
        return {"status": "error",
                "input_queries": [f"{l}:{t}" for l, t in queries],
                "targets": targets,
                "reason": f"unknown_wikipedia_edition: {codes} (такого розділу Вікіпедії не існує або його закрито)",
                "next_steps": [f"Скажи користувачу, що розділу Вікіпедії {codes} немає, і запитай, який розділ "
                               f"узяти натомість. Це не проблема мережі."]}
    notes = []
    if entity:
        core_id = entity
    else:
        status, payload, found_notes = choose_core(client, queries, targets)
        if status != "resolved":
            return {"status": status, "input_queries": [f"{l}:{t}" for l, t in queries], **payload,
                    "next_steps": ["Покажи кандидатів користувачу і перезапусти з --entity <QID>."]
                    if status == "ambiguous" else
                    ["Скажи користувачу, що тему не знайдено. Не запускай інших пошуків (частин теми, схожих "
                     "тем) без його дозволу: можеш лише запропонувати їх і чекати відповіді.",
                     "Якщо користувач погодиться, спробуй інше формулювання, напр. додай --query en:<англійська фраза>."]}
        core_id = payload["id"]
        notes += found_notes
    langs = list(dict.fromkeys(LABEL_LANGS + targets + [l for l, _ in queries]))
    core = get_entities(client, [core_id], "sitelinks|labels|descriptions|aliases|claims",
                        languages=langs).get(core_id)
    if not core:
        return {"status": "not_found", "reason": "entity_not_found", "entity_id": core_id,
                "next_steps": ["Перевір QID разом із користувачем."]}
    return build_basket(client, core, queries, targets, scope, include, notes)


WORD_RE = re.compile(r"\w+")


WORD_MATCH_MIN = 0.65  # на одне слово: «кави»/«кава» = 0.75, «Pyhton»/«Python» = 0.67


def phrase_in_messages(text: str, messages: list) -> bool:
    """Чи стоять слова фрази в одному з повідомлень підряд і в тому ж порядку,
    кожне схоже на своє з допуском на відмінок чи опечатку. Порядок важливий:
    у «…вивчення англійської… вивчення мов» немає фрази «англійська мова»."""
    words = WORD_RE.findall(text.casefold())
    if not words:
        return False
    for message in messages:
        tokens = WORD_RE.findall(message.casefold())
        for i in range(len(tokens) - len(words) + 1):
            if all(similarity(w, t) >= WORD_MATCH_MIN for w, t in zip(words, tokens[i:i + len(words)])):
                return True
    return False


def query_source_note(queries: list, user_messages: list):
    """Перший --query має бути словами користувача. Агент міг замінити їх (напр.,
    «вивчення англійської» → «англійська мова») — тоді скрипт шукає інше поняття."""
    lang, text = queries[0]
    if phrase_in_messages(text, user_messages):
        return None
    return {"code": "query_not_in_user_message",
            "detail": f"перший запит «{text}» ({lang}) не знайдено в повідомленнях користувача; "
                      f"результат може стосуватися іншого поняття, ніж те, про яке він питав"}


def resolve(client, queries: list, targets: list, scope: str, include: list, entity,
            user_messages=()) -> dict:
    result = _resolve(client, queries, targets, scope, include, entity)
    result["reply_language"] = REPLY_LANGUAGE
    first = ["Відповідай користувачу українською, навіть якщо він писав іншою мовою.",
             f"Перевір, що --targets ({', '.join(targets)}) — це саме ті мовні розділи, які назвав "
             f"користувач, без пропусків; якщо чогось бракує, перезапусти з повним списком."]
    note = query_source_note(queries, list(user_messages)) if queries and user_messages else None
    if note:
        result.setdefault("warnings", []).insert(0, note)
        first.append(f"СПОЧАТКУ виправ запит: {note['detail']}. Перезапусти, давши першим --query "
                     f"слова користувача з його повідомлення без заміни (можна лише початкову форму). "
                     f"Якщо ти змінив їх навмисно, спершу спитай користувача, чи він має на увазі саме це.")
    result["next_steps"] = first + result.get("next_steps", [])
    return result


def main(argv=None, client=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--query", action="append", default=[],
                        help="МОВА:ТЕКСТ, можна кілька. Спершу слова користувача, далі, напр., англійське формулювання.")
    parser.add_argument("--entity", help="Пропустити пошук і взяти цей QID як основне поняття (після уточнення).")
    parser.add_argument("--targets", required=True, help="Коди мовних розділів через кому, напр. pl,cs.")
    parser.add_argument("--scope", choices=("core", "extended"), default="core",
                        help="core: лише основне поняття. extended: ще й вужчі поняття, що є в усіх розділах.")
    parser.add_argument("--include", default="", help="QID через кому, які треба додати до кошика (з дозволу користувача).")
    parser.add_argument("--out", help="Записати сюди повний кошик у JSON; тоді в stdout буде стислий вигляд.")
    parser.add_argument("--user-message", action="append", default=[],
                        help="Повідомлення користувача дослівно, можна кілька (початкове й уточнення про тему). "
                             "Обов'язкове разом з --query.")
    args = parser.parse_args(argv)

    def fail(reason):
        print(json.dumps({"status": "error", "reason": reason}, ensure_ascii=False))
        return 1

    targets = list(dict.fromkeys(t.strip() for t in args.targets.split(",") if t.strip()))
    include = [i.strip() for i in args.include.split(",") if i.strip()]
    if not targets:
        return fail("no_targets_given")
    if not args.query and not args.entity:
        return fail("no_query_given: передайте --query МОВА:ТЕКСТ або --entity QID")
    bad = [i for i in include + ([args.entity] if args.entity else []) if not QID_RE.match(i)]
    if bad:
        return fail(f"bad_qid: {', '.join(bad)}")
    try:
        queries = parse_queries(args.query)
    except ValueError as e:
        return fail(str(e))
    user_messages = [m for m in args.user_message if m.strip()]
    if queries and not user_messages:
        return fail("no_user_message: передайте --user-message з повідомленням користувача дослівно")
    if client is None:
        contact = os.environ.get(CONTACT_ENV_VAR, "").strip()
        if not contact:
            return fail(f"contact_not_configured: задайте {CONTACT_ENV_VAR} — email або URL "
                        "для політики User-Agent Wikimedia")
        client = WikimediaClient(USER_AGENT_TEMPLATE.format(contact=contact))

    try:
        result = resolve(client, queries, targets, args.scope, include, args.entity, user_messages)
    except ResolverError as e:
        result = {"status": "error", "reason": str(e)}

    if args.out and "articles" in result:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        result = compact(result, args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in ("resolved", "partial", "ambiguous") else 1


if __name__ == "__main__":
    sys.exit(main())
