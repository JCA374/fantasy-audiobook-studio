#!/usr/bin/env python3
"""Objective gate for one chapter in the manuscript-review loop: the checks that don't need judgement, the change
budget that keeps fixes from turning into rewrites, and a logged record that the loop ran.

    gate.py books/<slug> chNN            check, snapshot this round's text and log it (round 0 = the draft)
    gate.py books/<slug> chNN --dry      check only: no snapshot, no log (use while fixing)
    gate.py books/<slug> chNN --close    after the reviewer's last pass: log the chapter's final verdict

Hard checks (any failure fails the gate):
  words        within ±15% of the chapter's target in outline.md ("**N. Title** (1,900 words")
  dialogue     no speech-flow `clipped exchange`, `clipped-dialogue share` or `two-word-line share` hit
  budget       words changed since the previous round: ≤25% in round 1, ≤10% after (a fix, not a rewrite)
  rounds       at most 3 rounds after the draft
Reported for the reviewer, not failing: other speech-flow candidates, AI-ism word hits (Tier 1 of the vendored
avoid-ai-writing list plus fiction tics), total drift from the draft (warns above 35%), open must-fix issues in
review.md.

--close passes when the last round's gate passed, the chapter is unchanged since that snapshot and review.md has no
open must-fix issue for it. At round 3 with must-fix issues still open it logs `capped`: the loop stops and the
issues go to status.md for the author.

Snapshots live in BOOK/.review/chNN.rN.md (git-ignored). Exit code 0 = pass.
"""
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
sys.path.insert(0, str(SKILLS / "speech-flow" / "scripts"))
sys.path.insert(0, str(SKILLS / "fantasy-novella" / "scripts"))
import evidence  # noqa: E402
from scan import scan  # noqa: E402

STAGE = "manuscript-review"
TOLERANCE = 0.15
BUDGET = {1: 0.25}          # round -> max share of words changed since the previous round
LATER_BUDGET = 0.10
DRIFT_WARN = 0.35
MAX_ROUNDS = 3
DIALOGUE = ("clipped exchange", "clipped-dialogue share", "two-word-line share")
# fiction tics generated prose drifts into; counted, not failed (the reviewer judges them in context)
TICS = {"a breath … didn't know": r"a breath (?:s?he|they|I) didn'?t know", "something shifted": r"something shifted",
        "the weight of": r"the weight of (?:it|the|her|his|their)", "for a moment": r"for a (?:long )?moment",
        "couldn't help but": r"couldn'?t help but", "a flicker of": r"a flicker of",
        "the silence stretched/hung": r"the silence (?:stretched|hung)", "let out a breath": r"let out a (?:\w+ )?breath",
        "somehow": r"somehow"}


def tier1():
    """Tier 1 words from the vendored avoid-ai-writing table (read, never edited)."""
    md = (SKILLS / "avoid-ai-writing" / "SKILL.md").read_text(encoding="utf-8")
    block = md.split("#### Tier 1", 1)[-1].split("####", 1)[0]
    out = []
    for cell in re.findall(r"^\| ([^|]+?) \|", block, re.M):
        for w in cell.split(" / "):
            w = re.sub(r"\s*\(.*?\)", "", w).strip()
            if w and w not in ("Replace", "---") and "…" not in w and len(w.split()) <= 3:
                out.append(w.lower())
    return {w: re.escape(w) for w in out}


def words(text):
    return re.findall(r"[\w’']+", re.sub(r"^#.*$", "", text, flags=re.M))


def changed(a, b):
    """Share of words changed between two texts (0 = same, 1 = nothing in common)."""
    wa, wb = words(a), words(b)
    if not wa and not wb:
        return 0.0
    same = sum(m.size for m in difflib.SequenceMatcher(None, wa, wb, autojunk=False).get_matching_blocks())
    return 1 - same / max(len(wa), len(wb))


def target(book, ch):
    p = book / "outline.md"
    if not p.exists():
        return None
    m = re.search(rf"\*\*{int(ch[2:])}\. [^*]+\*\*\s*\(([\d,]+) words", p.read_text(encoding="utf-8"))
    return int(m.group(1).replace(",", "")) if m else None


def ledger(book, ch):
    """Rows of BOOK/review.md for this chapter: [{id, ch, rd, cat, sev, par, issue, status}]."""
    p = book / "review.md"
    if not p.exists():
        return []
    keys = ["id", "ch", "rd", "cat", "sev", "par", "issue", "status"]
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= len(keys) and cells[1] == ch:
            rows.append(dict(zip(keys, cells[:7] + ["|".join(cells[7:])])))
    return rows


def open_must(book, ch):
    return [r["id"] for r in ledger(book, ch) if r["sev"] == "must" and r["status"].startswith("open")]


def snapshots(book, ch):
    d = book / ".review"
    return sorted(d.glob(f"{ch}.r*.md"), key=lambda p: int(p.stem.split(".r")[-1])) if d.exists() else []


def check(book, ch, rnd):
    md = book / f"{ch}.md"
    text = md.read_text(encoding="utf-8")
    fails, notes, facts = [], [], {"round": rnd}
    n = len(words(text))
    facts["words"] = n
    if (t := target(book, ch)) and abs(n - t) > TOLERANCE * t:
        fails.append(f"words {n} outside ±15% of the outline's {t}")
    hits = scan(md)
    dlg = [h for h in hits if h[1].startswith(DIALOGUE)]
    fails += [f"¶{p} {c}: {ex}" for p, c, ex in dlg]
    facts["dialogue_hits"] = len(dlg)
    other = [h for h in hits if h not in dlg]
    facts["speech_flow_candidates"] = len(other)
    notes += [f"speech-flow ¶{p} {c}: {ex}" for p, c, ex in other]
    low = text.lower()
    ai = {name: len(re.findall(rf"\b{pat}\b", low)) for name, pat in {**tier1(), **TICS}.items()}
    ai = {k: v for k, v in ai.items() if v}
    facts["ai_hits"] = sum(ai.values())
    notes += [f"ai-ism '{k}' ×{v}" for k, v in sorted(ai.items(), key=lambda kv: -kv[1])]
    snaps = snapshots(book, ch)
    if rnd > 0 and snaps:
        prev = snaps[-1].read_text(encoding="utf-8")
        c = changed(prev, text)
        facts["change"] = round(c, 3)
        budget = BUDGET.get(rnd, LATER_BUDGET)
        if c > budget:
            fails.append(f"changed {c:.0%} of the words since round {rnd - 1} (budget {budget:.0%}): that is a "
                         "rewrite, not a fix. Restore the snapshot and apply only the ledger's fixes, or stop and ask")
        drift = changed(snaps[0].read_text(encoding="utf-8"), text)
        facts["drift"] = round(drift, 3)
        if drift > DRIFT_WARN:
            notes.insert(0, f"WARNING drift {drift:.0%} from the draft (> {DRIFT_WARN:.0%}): is the story still the outline's?")
    if rnd > MAX_ROUNDS:
        fails.append(f"round {rnd} > {MAX_ROUNDS}: the loop is capped. Close it and send open issues to status.md")
    om = open_must(book, ch)
    facts["open_must"] = len(om)
    if om:
        notes.insert(0, "open must-fix in review.md: " + " ".join(om))
    return fails, notes, facts


def close(book, ch):
    md = book / f"{ch}.md"
    snaps = snapshots(book, ch)
    recs = [r for r in evidence.records(book, STAGE) if r.get("chapter") == ch and not r.get("final")]
    if not snaps or not recs:
        sys.exit(f"{ch}: no logged gate round to close; run gate.py {book} {ch} first")
    last = recs[-1]
    rnd = last["round"]
    unchanged = evidence.sha1(md) == evidence.sha1(snaps[-1])
    om = open_must(book, ch)
    ok = last["ok"] and unchanged and not om and rnd >= 1
    capped = not ok and rnd >= MAX_ROUNDS
    why = [] if ok else [x for x in [
        "" if last["ok"] else "the last gate round failed",
        "" if unchanged else "edited since the last gate round: run the gate again",
        "" if not om else "open must-fix: " + " ".join(om),
        "" if rnd >= 1 else "no review round yet (round 0 is the draft)"] if x]
    evidence.log(book, STAGE, [md], ok=ok, chapter=ch, round=rnd, final=True, capped=capped, open_must=len(om),
                 reasons=why)
    verdict = "PASS" if ok else ("CAPPED: stop here; copy the open issues to status.md for the author" if capped else "NOT DONE")
    print(f"{ch} close after round {rnd}: {verdict}")
    for w in why:
        print(f"  - {w}")
    return ok or capped


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    book, ch = Path(args[0]), Path(args[1]).stem
    if not (book / f"{ch}.md").exists():
        sys.exit(f"no {book / ch}.md")
    if "--close" in sys.argv:
        sys.exit(0 if close(book, ch) else 1)
    dry = "--dry" in sys.argv
    rnd = len(snapshots(book, ch))
    fails, notes, facts = check(book, ch, rnd)
    ok = not fails
    print(f"== {ch} round {rnd}{' (dry run)' if dry else ''}: {'PASS' if ok else 'FAIL'}  "
          + json.dumps({k: v for k, v in facts.items() if k != 'round'}))
    for f in fails:
        print(f"  FAIL  {f}")
    for x in notes:
        print(f"  note  {x}")
    if not dry:
        snap = book / ".review" / f"{ch}.r{rnd}.md"
        snap.parent.mkdir(exist_ok=True)
        snap.write_text((book / f"{ch}.md").read_text(encoding="utf-8"), encoding="utf-8")
        evidence.log(book, STAGE, [book / f"{ch}.md"], ok=ok, chapter=ch, failures=fails, **facts)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
