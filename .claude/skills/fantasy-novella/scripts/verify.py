#!/usr/bin/env python3
"""Check, stage by stage, that a book went through the pipeline: proof from the files and from the run log
(pipeline.log.jsonl, written by each stage's own script), not from anyone's summary.

    .venv/bin/python .claude/skills/fantasy-novella/scripts/verify.py books/<slug> [--json FILE] [--audio-only]

--audio-only checks only the audio stages 6-10: for a voice-text work dir (voice/<slug>/), which has no seed,
bible or outline because the text wasn't written here.

States, best to worst:
  PASS      proven: the stage's output matches the current input (by content hash, or re-derived)
  MANUAL    a judgement stage (seed, bible, outline, draft, edit, reader test): its files exist, but no script
            can prove the thinking happened
  UNLOGGED  the output exists and may be fine, but no logged run proves it (books made before the log existed)
  STALE     the output was made from an older input: re-run this stage (and the ones after it)
  MISSING   an output the stage should have written isn't there
  FAIL      the last logged run of this stage failed
Exit code 1 unless every stage is PASS or MANUAL.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
for s in ("narration-prep", "listen-check", "kokoro-narrate", "manuscript-review"):
    sys.path.insert(0, str(SKILLS / s / "scripts"))
sys.path.insert(0, str(HERE))
import evidence  # noqa: E402
from evidence import sha1  # noqa: E402


def rel(book, p):
    return str(Path(p).resolve().relative_to(book.resolve()))


def failed(book, stage):
    r = evidence.last(book, stage)
    return r if r and not r["ok"] else None


def files_stage(book, name, files):
    missing = [f for f in files if not (book / f).exists() or not (book / f).read_text(encoding="utf-8").strip()]
    if missing:
        return name, "MISSING", ", ".join(missing)
    return name, "MANUAL", ", ".join(files) + " present"


def bible_stage(book):
    """Stage 1 is judgement, but the world-rules skill leaves a shape to check: numbered rules and a reveal ladder."""
    name, state, detail = files_stage(book, "1 story bible", ["story-bible.md", "glossary.md"])
    if state != "MANUAL":
        return name, state, detail
    lines = (book / "story-bible.md").read_text(encoding="utf-8").splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"#+ .*(rules of the world|world rules)", l, re.I)), None)
    if start is None:
        return name, state, detail + "; no Rules of the World section (world-rules Build)"
    rules = 0
    for l in lines[start + 1:]:
        if re.match(r"#+ .*reveal ladder", l, re.I) or re.match(r"## ", l):
            break
        rules += bool(re.match(r"\d+\. ", l))
    ladder = any(re.match(r"#+ .*reveal ladder", l, re.I) for l in lines)
    return name, state, detail + (f"; {rules} numbered rules" if rules else "; rules not numbered") + \
        ("; reveal ladder" if ladder else "; no reveal ladder (world-rules Ladder)")


def review(book, chapters):
    """Stage 4: the manuscript-review loop's `gate.py --close` records. A chapter counts as reviewed when its last close
    passed and the chapter is unchanged since, or changed by at most 5% of its words (speech-flow edits come later)."""
    finals = [r for r in evidence.records(book, "manuscript-review") if r.get("final")]
    if not finals:
        return "4 edit", "MANUAL", "judgement stage: no manuscript-review loop logged"
    from gate import changed  # noqa: E402
    done, edited, stale, capped, todo = [], [], [], [], []
    for md in chapters:
        mine = [r for r in finals if r.get("chapter") == md.stem]
        if not mine:
            todo.append(md.stem)
            continue
        r = mine[-1]
        if not r["ok"]:
            (capped if r.get("capped") else todo).append(md.stem)
        elif r["inputs"].get(rel(book, md)) == sha1(md):
            done.append(md.stem)
        else:
            snap = book / ".review" / f"{md.stem}.r{r['round']}.md"
            if not snap.exists():
                edited.append(f"{md.stem} (Δ ?, snapshot not on this machine)")
                continue
            d = changed(snap.read_text(encoding="utf-8"), md.read_text(encoding="utf-8"))
            (edited if d <= 0.05 else stale).append(f"{md.stem} (Δ {d:.0%})")
    detail = "; ".join(x for x in [
        f"reviewed {len(done) + len(edited)}/{len(chapters)}",
        "edited since review: " + " ".join(edited) if edited else "",
        "changed >5% since review, re-run the loop: " + " ".join(stale) if stale else "",
        "capped with open issues (see status.md): " + " ".join(capped) if capped else "",
        "not reviewed: " + " ".join(todo) if todo else ""] if x)
    state = "STALE" if stale else "MANUAL" if (capped or todo or any("Δ ?" in e for e in edited)) else "PASS"
    return "4 edit", state, detail


def speech_flow(book, chapters):
    recs = evidence.records(book, "speech-flow")
    if not recs:
        return "UNLOGGED", "no scan.py run logged"
    stale, never = [], []
    for md in chapters:
        seen = [r["inputs"][rel(book, md)] for r in recs if rel(book, md) in r["inputs"]]
        if not seen:
            never.append(md.stem)
        elif seen[-1] != sha1(md):
            stale.append(md.stem)
    if stale or never:
        return "STALE", "; ".join(x for x in [f"edited since the last scan: {' '.join(stale)}" if stale else "",
                                               f"never scanned: {' '.join(never)}" if never else ""] if x)
    return "PASS", f"last scan of every chapter matches the manuscript ({len(chapters)} chapters)"


def narration_prep(book, chapters):
    import prep
    names = prep.glossary(book) if (book / "glossary.md").exists() else {}
    missing, stale = [], []
    for md in chapters:
        txt = book / "audio" / f"{md.stem}.txt"
        if not txt.exists():
            missing.append(md.stem)
        elif txt.read_text() != prep.convert(md, names):
            stale.append(md.stem)
    if missing:
        return "MISSING", "no script for " + " ".join(missing)
    if stale:
        return "STALE", "the script differs from what prep.py makes of the manuscript now: " + " ".join(stale)
    return "PASS", f"every audio/chNN.txt equals prep.py's output for the current manuscript ({len(chapters)})"


def narrate(book, scripts):
    from listen import cache_wav, load_cfg
    from narrate import parse
    cfg, cache = load_cfg(book), book / "audio" / ".cache"
    gaps = {}
    for s in scripts:
        items = [it for it in parse(s.read_text(encoding="utf-8")) if it[0] == "say"]
        n = sum(not cache_wav(it, cfg, cache).exists() for it in items)
        if n:
            gaps[s.stem] = n
    if gaps:
        return "STALE", "paragraphs not rendered: " + ", ".join(f"{k} ({v})" for k, v in gaps.items())
    r = evidence.last(book, "kokoro-narrate", ok=True)
    if not r:
        return "UNLOGGED", f"every paragraph of {len(scripts)} scripts has audio in the render cache; run not logged"
    old = [s.stem for s in scripts if r["inputs"].get(rel(book, s)) != sha1(s)]
    if old:
        return "STALE", f"last logged render ({r['time']}) used older scripts: {' '.join(old)}"
    return "PASS", f"rendered {r['time']} from the current scripts, every paragraph cached"


def listen_check(book, scripts):
    missing, unlogged, stale = [], [], []
    for s in scripts:
        rep = book / "audio" / f"{s.stem}.listen.json"
        if not rep.exists():
            missing.append(s.stem)
            continue
        r = json.loads(rep.read_text())
        audio = book / "audio" / r.get("audio", "")
        if "script_sha1" not in r:
            unlogged.append(s.stem)
        elif r["script_sha1"] != sha1(s) or (audio.exists() and r.get("audio_sha1") not in (None, sha1(audio))):
            stale.append(s.stem)
    if missing:
        return "MISSING", "no listen report for " + " ".join(missing)
    if stale:
        return "STALE", "script or audio changed since the listen check: " + " ".join(stale)
    if unlogged:
        return "UNLOGGED", f"reports exist but predate the evidence log ({len(unlogged)} chapters)"
    return "PASS", f"every report was made from the current script and audio ({len(scripts)})"


def assemble(book, scripts):
    audio = book / "audio"
    mp3s, m4bs = [audio / f"{s.stem}.mp3" for s in scripts], sorted(audio.glob("*.m4b"))
    missing = [p.name for p in mp3s if not p.exists()] + ([] if m4bs else [".m4b"])
    if missing:
        return "MISSING", " ".join(missing)
    r = evidence.last(book, "audiobook-assemble", ok=True)
    if not r:
        return "UNLOGGED", f"{len(mp3s)} MP3s and {m4bs[0].name} exist; assembly not logged"
    changed = [k for k, v in r["outputs"].items() if not (book / k).exists() or sha1(book / k) != v]
    old = [s.stem for s in scripts if r["inputs"].get(rel(book, s)) != sha1(s)]
    # chain: the WAVs it packaged must be the ones kokoro-narrate rendered
    rendered = {v for n in evidence.records(book, "kokoro-narrate") if n["ok"] for v in n["outputs"].values()}
    foreign = [Path(k).stem for k, v in r["inputs"].items() if k.endswith(".wav") and v not in rendered]
    if changed:
        return "STALE", "packaged files changed after the logged assembly: " + " ".join(changed)
    if old:
        return "STALE", f"assembled ({r['time']}) from older scripts: {' '.join(old)}"
    if foreign:
        return "STALE", "packaged WAVs that no logged render produced: " + " ".join(foreign)
    return "PASS", f"assembled {r['time']} from the current scripts' renders; MP3s and .m4b unchanged since"


def verify(book, audio_only=False):
    book = Path(book)
    chapters = sorted(book.glob("ch[0-9][0-9].md"))
    scripts = [book / "audio" / f"{md.stem}.txt" for md in chapters]
    status = (book / "status.md").read_text(encoding="utf-8") if (book / "status.md").exists() else ""
    rows = [] if audio_only else [
        files_stage(book, "0 seed", ["seed.md"]),
        bible_stage(book),
        files_stage(book, "2 structure", ["outline.md"]),
        ("3 draft", "MANUAL", f"{len(chapters)} chapters") if chapters else ("3 draft", "MISSING", "no chNN.md"),
        review(book, chapters),
        ("5 reader test", "MANUAL", "summary in status.md") if re.search(r"reader test", status, re.I)
        else ("5 reader test", "MISSING", "no reader-test summary in status.md"),
    ]
    later = [("6 speech flow", "speech-flow", speech_flow, chapters),
             ("7 audio prep", "narration-prep", narration_prep, chapters),
             ("8 narrate", "kokoro-narrate", narrate, scripts),
             ("9 listen check", "listen-check", listen_check, scripts),
             ("10 package", "audiobook-assemble", assemble, scripts)]
    for name, stage, check, arg in later:
        if f := failed(book, stage):
            rows.append((name, "FAIL", f"last run {f['time']} failed: {f.get('error', '?')}"))
        elif not chapters or (arg is scripts and not all(s.exists() for s in scripts) and stage != "narration-prep"):
            rows.append((name, "MISSING", "needs the previous stage's output"))
        else:
            rows.append((name, *check(book, arg)))
    return rows


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    book = Path(sys.argv[1])
    rows = verify(book, audio_only="--audio-only" in sys.argv)
    worst = evidence.report(rows, f"== {book.name}: pipeline evidence")
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(
            json.dumps([{"stage": s, "state": st, "detail": d} for s, st, d in rows], ensure_ascii=False, indent=1))
    sys.exit(0 if worst in ("PASS", "MANUAL") else 1)


if __name__ == "__main__":
    main()
