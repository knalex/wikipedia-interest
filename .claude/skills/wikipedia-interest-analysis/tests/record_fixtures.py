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

import resolve_topic as rt  # noqa: E402
from cases import CASES  # noqa: E402


class RecordingClient:
    def __init__(self, inner):
        self.inner, self.log = inner, {}

    def get_json(self, url, params):
        data = self.inner.get_json(url, params)
        self.log[rt.request_key(url, params)] = data
        return data


def main():
    contact = os.environ.get(rt.CONTACT_ENV_VAR, "").strip()
    if not contact:
        sys.exit(f"спершу задайте {rt.CONTACT_ENV_VAR}")
    real = rt.WikimediaClient(rt.USER_AGENT_TEMPLATE.format(contact=contact))
    for name in sys.argv[1:] or CASES:
        client = RecordingClient(real)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            code = rt.main(CASES[name] + ["--out", f"{tmp}/basket.json"], client=client)
        (HERE / "fixtures" / f"{name}.json").write_text(
            json.dumps(client.log, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        print(f"{name}: код виходу {code}, відповідей: {len(client.log)}")


if __name__ == "__main__":
    main()
