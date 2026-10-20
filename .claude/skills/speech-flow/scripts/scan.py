#!/usr/bin/env python3
"""Flag spots in a manuscript chapter that may trip a TTS narrator or a listener.

Mechanical first pass for the speech-flow skill. Every hit is a *candidate*: judge it
by ear (read it aloud in your head, as the listener) before proposing a change.

usage: scan.py books/<slug>/ch01.md [more chapters...]

The dialogue checks (bare short line, clipped dialogue) are for fiction. A work dir whose book.yaml says
`kind: prose` or `kind: voiceover` (voice-text skill) skips them; every other check runs for all kinds.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "fantasy-novella" / "scripts"))
import evidence  # noqa: E402  (pipeline.log.jsonl: proof this stage ran)

LONG = 35          # words; writing-for-the-ear says prefer < ~30
BARE_LINE = 6      # words; a lone quoted line this short gets an emotion beat
CLIPPED = 3        # words; a spoken line whose every sentence is this short is "clipped" (case 07)
CLIPPED_SHARE = 0.15  # more clipped lines than this per chapter reads as lazy (about 1 in 7 is fine)
CLIPPED_MIN = 12   # only judge the share when a chapter has at least this many spoken lines
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


def spoken(par):
    """The words a character says in a paragraph (all quoted parts joined), or None if nobody speaks."""
    qs = re.findall(r'"([^"]+)"|“([^”]+)”', par)
    return " ".join(a or b for a, b in qs) or None


def clipped(speech):
    """True if every sentence of the speech is CLIPPED words or fewer: "No.", "Off where?", "Yes. Fine. Go." """
    parts = [p for p in re.split(r"[.!?…]+", speech) if words(p)]
    return bool(parts) and max(words(p) for p in parts) <= CLIPPED


def kind_of(book):
    """fiction (the default), prose or voiceover, from BOOK/book.yaml."""
    p = Path(book) / "book.yaml"
    if not p.exists():
        return "fiction"
    import yaml
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("kind", "fiction")


def scan(path):
    return scan_text(path.read_text(encoding="utf-8"), kind_of(path.parent))


def scan_text(text, kind="fiction"):
    """Return [(paragraph number, check name, excerpt)] for a chapter or a snippet."""
    fiction = kind == "fiction"
    hits = []
    pars = [p for p in re.split(r"\n\s*\n", text) if p.strip() and not p.startswith("#")]
    lines = []  # (¶, speech, clipped) for every paragraph with dialogue
    for n, par in enumerate(pars, 1):
        par = " ".join(par.split())
        if (sp := spoken(par)) is not None:
            lines.append((n, sp, clipped(sp)))

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
        # a bare short line of dialogue on its own: no tag, no beat, so the listener gets no emotion (cases 01, 05)
        if fiction and re.fullmatch(r'["“][^"”]+["”]', par) and words(par) <= BARE_LINE:
            hit("bare short line (add an emotion beat)" + (" + short question" if par.rstrip('"”').endswith("?") else ""), par)
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
    # clipped dialogue (case 07): a few terse lines land hard; many of them read as lazy writing
    if not fiction:
        lines = []
    run = []
    for i, (n, sp, c) in enumerate(lines):
        prev_n = lines[i - 1][0] if i else None
        if c and run and prev_n == n - 1:
            run.append((n, sp))
        else:
            if len(run) >= 2:
                hits.append((run[0][0], f"clipped exchange ({len(run)} terse lines in a row)", " / ".join(x for _, x in run)))
            run = [(n, sp)] if c else []
    if len(run) >= 2:
        hits.append((run[0][0], f"clipped exchange ({len(run)} terse lines in a row)", " / ".join(x for _, x in run)))
    n_clip = sum(c for _, _, c in lines)
    if len(lines) >= CLIPPED_MIN and n_clip / len(lines) > CLIPPED_SHARE:
        hits.append((0, f"clipped-dialogue share {n_clip}/{len(lines)} = {n_clip / len(lines):.0%} (> {CLIPPED_SHARE:.0%})",
                     "¶" + " ¶".join(str(n) for n, _, c in lines if c)))
    return sorted(hits, key=lambda h: h[0])


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    found = {}
    for arg in sys.argv[1:]:
        p = Path(arg)
        hits = scan(p)
        found[p] = len(hits)
        print(f"== {p}  ({len(hits)} candidates; ¶ = paragraph number, heading excluded)")
        for n, check, ex in hits:
            print(f"¶{n:<3} {check:<44} {ex}")
    for book in {p.parent for p in found if (p.parent / "book.yaml").exists()}:   # a book's chapters: log the run
        chapters = [p for p in found if p.parent == book]
        evidence.log(book, "speech-flow", chapters, candidates={p.stem: found[p] for p in chapters})


if __name__ == "__main__":
    main()
