#!/usr/bin/env python3
"""Flag spots in a manuscript chapter that may trip a TTS narrator or a listener.

Mechanical first pass for the speech-flow skill. Every hit is a *candidate*: judge it
by ear (read it aloud in your head, as the listener) before proposing a change.

usage: scan.py books/<slug>/ch01.md [more chapters...]
"""
import re
import sys
from pathlib import Path

LONG = 35          # words; writing-for-the-ear says prefer < ~30
COMMAS = 6         # commas in one sentence -> choppy run of pauses
INTERRUPTERS = r"by all accounts|of course|in fact|after all|apparently|it seemed|at least|for once|for a moment|in the end"
CUES = r"(:|thought|read|said|says|wrote|written|stamped|whispered|meant|saying)\s*$"
SUBJECT = r"\b(?:I|he|she|they|we|you)\b"
# after a single dash, a new clause (not an appositive tail) means the aside never closes
CLAUSE = r"^\s*(?:I|he|she|they|we|you|it|people|everyone|nobody)\s+\w+|,\s+(?:and|but|or)\s+(?:[A-Z]\w*|I|he|she|they|we|you|it)\s+\w+"

SENT_RE = re.compile(r"(?<=[.!?…])[\"”*]?\s+(?=[\"“*]?[A-Z])")
HEDGES = r"exactly|really|quite|precisely|entirely|perhaps|necessarily|just|simply|only"


def sentences(par):
    return [s for s in SENT_RE.split(par) if s.strip()]


def words(s):
    return len(re.findall(r"[\w’']+", s))


def scan(path):
    hits = []
    text = path.read_text(encoding="utf-8")
    pars = [p for p in re.split(r"\n\s*\n", text) if p.strip() and not p.startswith("#")]
    for n, par in enumerate(pars, 1):
        par = " ".join(par.split())

        def hit(check, excerpt):
            hits.append((n, check, excerpt if len(excerpt) < 160 else excerpt[:157] + "…"))

        # italics: vanish in audio; fine only when the words already say what they are
        for m in re.finditer(r"\*([^*]+)\*", par):
            before = par[: m.start()]
            in_dialogue = (before.count('"') + before.count("“")) % 2 == 1
            if in_dialogue and words(m.group(1)) <= 2:
                continue  # spoken emphasis: lost in audio, harmless
            if not re.search(CUES, before, re.I):
                hit("italics-without-cue", f"…{before[-40:]}*{m.group(1)}*")
        # bare short questions in dialogue (fine when a beat or tag follows)
        for m in re.finditer(r'["“]([^"”]+\?)["”]', par):
            if words(m.group(1)) <= 3 and not par[m.end():].strip():
                hit("short-question", m.group(0))
        for s in sentences(par):
            w = words(s)
            if w > LONG:
                hit(f"long-sentence ({w} words)", s)
            if s.count(",") >= COMMAS:
                hit(f"comma-run ({s.count(',')} commas)", s)
            if s.count(";"):
                hit("semicolon", s)
            dashes = s.count("—") + s.count(" -- ")
            if dashes == 1:
                tail = s.split("—", 1)[-1]
                if re.search(CLAUSE, tail):
                    hit("unclosed-dash", s)
            # "She looked up, and allowed…": comma splitting one subject's two verbs
            for m in re.finditer(rf"{SUBJECT}\s+\w+[^,.;:—]{{0,60}},\s+and\s+(\w+)", s, re.I):
                nxt = m.group(1).lower()
                if not re.fullmatch(r"(i|he|she|they|we|you|it|the|a|an|her|his|their|my|then|there|that|this|for|when|so|now|in|on|at)", nxt) and nxt.endswith(("ed", "s")):
                    hit("comma-before-and (one subject, two verbs?)", m.group(0))
            # "so much of X that by the time…": the listener needs a breath before the result clause (case 03)
            for m in re.finditer(r"\bso\s+\w+\b[^,.;:!?—]{25,}?\s+that\b", s):
                hit("so…that without a breath before 'that'", m.group(0))
            # "not softness, exactly, but attention": tiny comma pauses around a one-word hedge break the contrast (case 04)
            for m in re.finditer(rf"\b\w+,\s+({HEDGES}),\s+(?:but|and|or|yet)\b", s, re.I):
                hit("hedge boxed in commas (choppy)", m.group(0))
            m = re.search(rf"\b(?:had|has|was|were|is|are|would|could)\s+({INTERRUPTERS})\s+\w+", s, re.I)
            if m:
                hit("interrupter-without-commas", m.group(0))
    return hits


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        p = Path(arg)
        hits = scan(p)
        print(f"== {p}  ({len(hits)} candidates; ¶ = paragraph number, heading excluded)")
        for n, check, ex in hits:
            print(f"¶{n:<3} {check:<44} {ex}")


if __name__ == "__main__":
    main()
