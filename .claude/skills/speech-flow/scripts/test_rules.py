#!/usr/bin/env python3
"""Regression tests: every training case's lesson must still hold in the scanner.

For each test in training/rule-tests.yaml the scanner must flag `before` with the named check
and must not flag `after` with it. Exit code 1 if any test fails. Optional `before_kind` / `after_kind`
(fiction, prose, voiceover; default fiction) scan that side as that kind of text.

usage: test_rules.py [--json FILE]     --json: also write results (the website shows them)
"""
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from scan import scan_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
TESTS = ROOT / "training" / "rule-tests.yaml"


def run():
    results = []
    for t in yaml.safe_load(TESTS.read_text(encoding="utf-8")):
        flags = lambda text, kind: [c for _, c, _ in scan_text(text, kind) if t["check"] in c]
        caught = bool(flags(t["before"], t.get("before_kind", "fiction")))
        clean = not flags(t["after"], t.get("after_kind", "fiction"))
        results.append({**t, "caught": caught, "clean": clean, "ok": caught and clean})
    return results


def main():
    results = run()
    for r in results:
        why = "" if r["ok"] else ("  <- before NOT flagged" if not r["caught"] else "  <- after still flagged")
        print(f'{"PASS" if r["ok"] else "FAIL"}  case {r["case"]}  {r["check"]}{why}')
    failed = sum(not r["ok"] for r in results)
    print(f"{len(results) - failed}/{len(results)} passed")
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(results, ensure_ascii=False, indent=1))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
