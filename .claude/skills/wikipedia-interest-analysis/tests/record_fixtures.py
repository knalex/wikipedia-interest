#!/usr/bin/env python3
"""Перезаписує відповіді API для запитів із tests/cases.py (жива мережа).

Використання: WIKIPEDIA_RESOLVER_CONTACT=you@example.com python3 tests/record_fixtures.py [запит ...]
"""
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import fetch_pageviews as fp  # noqa: E402
import resolve_topic as rt  # noqa: E402
from cases import CASES, STAGE2_CASES, STAGE2_TODAY  # noqa: E402


class ReplayClient:
    def __init__(self, name):
        self.responses = json.loads((HERE / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))

    def get_json(self, url, params):
        data = self.responses[rt.request_key(url, params)]
        if "_http_error" in data:
            raise rt.ResolverError(f"HTTP {data['_http_error']} (запис)", status=data["_http_error"])
        return data


class RecordingClient:
    def __init__(self, inner):
        self.inner, self.log = inner, {}

    def get_json(self, url, params):
        try:
            data = self.inner.get_json(url, params)
        except rt.ResolverError as e:
            if e.status is None:
                raise
            self.log[rt.request_key(url, params)] = {"_http_error": e.status}
            raise
        self.log[rt.request_key(url, params)] = data
        return data


def main():
    contact = os.environ.get(rt.CONTACT_ENV_VAR, "").strip()
    if not contact:
        sys.exit(f"спершу задайте {rt.CONTACT_ENV_VAR}")
    real = rt.WikimediaClient(rt.USER_AGENT_TEMPLATE.format(contact=contact))
    for name in sys.argv[1:] or list(CASES) + list(STAGE2_CASES):
        client = RecordingClient(real)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            if name in STAGE2_CASES:
                stage1, argv = STAGE2_CASES[name]
                rt.main(CASES[stage1] + ["--out", f"{tmp}/basket.json"], client=ReplayClient(stage1))
                code = fp.main(argv + ["--basket", f"{tmp}/basket.json", "--today", STAGE2_TODAY,
                                       "--out", f"{tmp}/views.json"], client=client)
            else:
                code = rt.main(CASES[name] + ["--out", f"{tmp}/basket.json"], client=client)
        (HERE / "fixtures" / f"{name}.json").write_text(
            json.dumps(client.log, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        print(f"{name}: код виходу {code}, відповідей: {len(client.log)}")


if __name__ == "__main__":
    main()
