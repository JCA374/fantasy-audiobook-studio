#!/usr/bin/env python3
"""Check, stage by stage, that a book went through the pipeline: proof from the files and from the run log
(pipeline.log.jsonl, written by each stage's own script), not from anyone's summary.

    .venv/bin/python .claude/skills/fantasy-novella/scripts/verify.py books/<slug> [--json FILE]

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
for s in ("narration-prep", "listen-check", "kokoro-narrate"):
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


def verify(book):
    book = Path(book)
    chapters = sorted(book.glob("ch[0-9][0-9].md"))
    scripts = [book / "audio" / f"{md.stem}.txt" for md in chapters]
    status = (book / "status.md").read_text(encoding="utf-8") if (book / "status.md").exists() else ""
    rows = [
        files_stage(book, "0 seed", ["seed.md"]),
        files_stage(book, "1 story bible", ["story-bible.md", "glossary.md"]),
        files_stage(book, "2 structure", ["outline.md"]),
        ("3 draft", "MANUAL", f"{len(chapters)} chapters") if chapters else ("3 draft", "MISSING", "no chNN.md"),
        ("4 edit", "MANUAL", "judgement stage: no file proves an edit pass"),
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
    rows = verify(book)
    worst = evidence.report(rows, f"== {book.name}: pipeline evidence")
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(
            json.dumps([{"stage": s, "state": st, "detail": d} for s, st, d in rows], ensure_ascii=False, indent=1))
    sys.exit(0 if worst in ("PASS", "MANUAL") else 1)


if __name__ == "__main__":
    main()
