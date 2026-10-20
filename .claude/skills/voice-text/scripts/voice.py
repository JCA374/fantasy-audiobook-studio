#!/usr/bin/env python3
"""Voice any text with the studio's audio pipeline, from any project: ear rewrites (speech-flow), Kokoro script
(narration-prep), render (kokoro-narrate), Whisper check (listen-check), packaging (audiobook-assemble).

Run it through the launcher next to this file, which picks the studio's Python:
    ~/.claude/skills/voice-text/scripts/voice.sh <command> ...

    new FILE... --kind prose|fiction|voiceover [--slug S] [--split] [--force]
                            make the work dir voice/<slug>/ in the current project (looks like a book dir)
    scan DIR                speech-flow candidates for every chapter
    g2p WORD... [--say T]   phonemes for glossary respellings (narration-prep §1)
    prep DIR                chNN.md -> audio/chNN.txt
    narrate DIR [args]      render (args as kokoro-narrate: --chapters, --voice, --sample ...)
    listen DIR [args]       Whisper check (args as listen-check: --chapters, --reuse, --clip ...)
    export DIR              assemble MP3s + .m4b; voiceover also gets audio/voiceover/ (unpadded MP3s + timings.json)
    status DIR              verify the audio stages from the evidence log (exit 0 = all PASS)
    test-rules              the studio's speech-flow rule tests

Nothing here re-implements a stage: each command calls the stage's own script, which logs its run to
DIR/pipeline.log.jsonl like it does for a book.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

SKILLS = Path(__file__).resolve().parents[2]
STUDIO = SKILLS.parents[1]
SCRIPTS = {
    "scan": SKILLS / "speech-flow/scripts/scan.py",
    "g2p": SKILLS / "narration-prep/scripts/g2p.py",
    "prep": SKILLS / "narration-prep/scripts/prep.py",
    "narrate": SKILLS / "kokoro-narrate/scripts/narrate.py",
    "listen": SKILLS / "listen-check/scripts/listen.py",
    "assemble": SKILLS / "audiobook-assemble/scripts/assemble.py",
    "status": SKILLS / "fantasy-novella/scripts/verify.py",
    "test-rules": SKILLS / "speech-flow/scripts/test_rules.py",
}
SPEED = {"prose": 0.95, "fiction": 0.95, "voiceover": 1.05}
SPLIT_WORDS = 3000   # a prose doc longer than this is split at its ## headings (with --split)
GLOSSARY = """# Pronunciation glossary

Invented or unusual names and words, with how they should sound (narration-prep §1).

| Term | Sounds like | Phonemes | Notes |
|------|-------------|----------|-------|
"""
GITIGNORE = "*.wav\n*/audio/.cache/\n"


def run(name, *args):
    return subprocess.run([sys.executable, str(SCRIPTS[name]), *map(str, args)]).returncode


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "text"


def sha1(text):
    return hashlib.sha1(text.encode()).hexdigest()


# ------------------------------------------------------------------ new: any text -> a book-shaped work dir

def clean(md):
    """Markdown written for the eye -> paragraphs for the ear. Returns (text, [things dropped or flattened]).
    Mechanical only; what was dropped is listed so Claude can say it in words (speech-flow)."""
    notes, out = [], []
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)                       # front matter
    def fence(m):
        code = [ln for ln in m.group(0).strip().splitlines()[1:-1] if ln.strip()] or ["(empty)"]
        notes.append(f"code block dropped: {code[0].strip()[:60]} (describe it in words if it matters)")
        return "\n\n"
    md = re.sub(r"^(```|~~~).*?^\1[^\n]*$", fence, md, flags=re.S | re.M)
    for block in re.split(r"\n\s*\n", md):
        lines = [ln.rstrip() for ln in block.strip().splitlines()]
        if not lines:
            continue
        if all(ln.lstrip().startswith("|") for ln in lines):
            notes.append(f"table dropped: {lines[0][:60]} (say what it shows in a sentence or two)")
            continue
        if all(re.match(r"\s*([-*+]|\d+[.)])\s+", ln) or ln.startswith("  ") for ln in lines):
            items = [re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", ln).strip() for ln in lines]
            notes.append(f"list of {len(items)} read as one paragraph per item: {items[0][:50]}…")
            items = [it[:1].upper() + it[1:] for it in items if it]
            out += [it if it.endswith((".", "!", "?", ":")) else it + "." for it in items]
            continue
        par = " ".join(ln.strip() for ln in lines)
        if re.match(r"#{2,6}\s", par):                     # subheading -> its own short paragraph
            par = par.lstrip("#").strip()
            par = par if par.endswith((".", "!", "?")) else par + "."
        par = re.sub(r"^>\s?", "", par)
        par = re.sub(r"!\[([^\]]*)\]\([^)]*\)", "", par)    # images
        par = re.sub(r"\[([^\]]+)\]\((?!/)[^)]*\)", r"\1", par)   # links (not Kokoro phoneme markup)
        par = re.sub(r"`([^`]+)`", r"\1", par)
        if re.search(r"https?://", par):
            notes.append(f"bare URL in: {par[:60]}… (a listener can't use it: name the site instead)")
        if par.strip():
            out.append(par.strip())
    return "\n\n".join(out), notes


def sections(md):
    """Split at ## headings -> [(title, body)]. Text before the first ## goes with the first section."""
    parts = re.split(r"^##\s+(.+)$", md, flags=re.M)
    head, rest = parts[0], list(zip(parts[1::2], parts[2::2]))
    if not rest:
        return [(None, md)]
    first_title, first_body = rest[0]
    return [(first_title.strip(), head + "\n\n" + first_body)] + [(t.strip(), b) for t, b in rest[1:]]


def cmd_new(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="voice new")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--kind", required=True, choices=list(SPEED))
    ap.add_argument("--slug")
    ap.add_argument("--title")
    ap.add_argument("--split", action="store_true", help=f"split a prose doc over {SPLIT_WORDS} words at its ## headings")
    ap.add_argument("--force", action="store_true", help="rebuild chNN.md from the sources (keeps glossary and voice)")
    ap.add_argument("--root", type=Path, default=Path("voice"), help="parent folder for work dirs (default voice/)")
    a = ap.parse_args(argv)

    texts = [(f, f.read_text(encoding="utf-8")) for f in a.files]
    h1 = re.search(r"^#\s+(.+)$", texts[0][1], flags=re.M)
    title = a.title or (h1.group(1).strip() if h1 else a.files[0].stem.replace("-", " ").replace("_", " ").title())
    work = a.root / (a.slug or slugify(title))
    if work.exists() and any(work.glob("ch[0-9][0-9].md")) and not a.force:
        sys.exit(f"{work} already has chapters (maybe with approved ear rewrites). Use --force to rebuild them "
                 "from the sources, or work in the existing dir.")

    chapters = []   # (heading or None, body, source path, section title)
    for f, text in texts:
        own_h1 = re.search(r"^#\s+(.+)$", text, flags=re.M)
        body = re.sub(r"^#\s+.+$", "", text, count=1, flags=re.M) if own_h1 else text
        heading = own_h1.group(1).strip() if own_h1 else (f.stem.replace("-", " ").title() if a.kind == "prose" else None)
        if a.kind == "voiceover":                       # one chapter per ## scene, scene titles not spoken
            chapters += [(None, b, f, t) for t, b in sections(body) if b.strip()]
        elif a.kind == "prose" and a.split and len(text.split()) > SPLIT_WORDS:
            chapters += [(t or heading, b, f, t) for t, b in sections(body) if b.strip()]
        else:
            chapters.append((heading, body, f, None))
    if len(chapters) > 99:
        sys.exit(f"{len(chapters)} chapters: more than the chNN layout holds")

    work.mkdir(parents=True, exist_ok=True)
    (work / "audio").mkdir(exist_ok=True)
    gi = a.root / ".gitignore"
    if not gi.exists():
        gi.write_text(GITIGNORE)
    for old in work.glob("ch[0-9][0-9].md"):
        old.unlink()
    meta_path = work / "book.yaml"
    old_meta = (yaml.safe_load(meta_path.read_text()) or {}) if meta_path.exists() else {}
    titles, sources, all_notes = {}, {}, []
    for i, (heading, body, src, section) in enumerate(chapters, 1):
        stem = f"ch{i:02d}"
        if a.kind == "fiction":
            text, notes = body.strip(), []           # a manuscript: copied as written, speech-flow does the rest
        else:
            text, notes = clean(body)
        (work / f"{stem}.md").write_text((f"# {heading}\n\n" if heading else "") + text + "\n", encoding="utf-8")
        titles[stem] = heading or section or f"Part {i}"
        sources[stem] = {"path": str(src.resolve()), "sha1": sha1(src.read_text(encoding="utf-8")),
                         **({"section": section} if section else {})}
        all_notes += [f"{stem}: {n}" for n in notes]
    meta = {"title": title, "kind": a.kind, "author": old_meta.get("author", ""),
            "narrator": old_meta.get("narrator", "Kokoro TTS (af_heart)"),
            "narration": old_meta.get("narration") or {"narrator": "af_heart", "speed": SPEED[a.kind], "paragraph_pause": 0.6},
            "chapters": titles, "sources": sources}
    meta_path.write_text(yaml.safe_dump(meta, allow_unicode=True, sort_keys=False), encoding="utf-8")
    if not (work / "glossary.md").exists():
        (work / "glossary.md").write_text(GLOSSARY, encoding="utf-8")

    words = sum(len((work / f"{s}.md").read_text().split()) for s in titles)
    print(f"{work}: {len(titles)} chapter(s), {words:,} words, kind={a.kind}, about {f"{words / 150:.0f} min" if words >= 150 else f"{words / 2.5:.0f} s"} of audio")
    for n in all_notes:
        print("  rewrite:", n)
    print(f"next: fill {work}/glossary.md, then  voice.sh scan {work}")


# ------------------------------------------------------------------ export

def cmd_export(argv):
    work = Path(argv[0])
    rc = run("assemble", work, *argv[1:])
    if rc:
        return rc
    meta = yaml.safe_load((work / "book.yaml").read_text()) or {}
    if meta.get("kind") != "voiceover":
        return 0
    # a video editor wants each scene's speech with no lead-in or tail, and its exact length
    sys.path.insert(0, str(SCRIPTS["assemble"].parent))
    import assemble
    assemble.HEAD = assemble.TAIL = 0
    out = work / "audio" / "voiceover"
    out.mkdir(exist_ok=True)
    timings = []
    for wav in sorted(w for w in (work / "audio").glob("ch*.wav") if re.fullmatch(r"ch\d+", w.stem)):
        mastered = out / f"{wav.stem}.master.wav"
        assemble.master(wav, mastered)
        assemble.ff("-i", str(mastered), "-c:a", "libmp3lame", "-b:a", "96k", str(out / f"{wav.stem}.mp3"))
        timings.append({"scene": wav.stem, "title": (meta.get("chapters") or {}).get(wav.stem, wav.stem),
                        "file": f"{wav.stem}.mp3", "seconds": round(assemble.duration(out / f"{wav.stem}.mp3"), 3)})
        mastered.unlink()
    (out / "timings.json").write_text(json.dumps(timings, ensure_ascii=False, indent=1))
    print(f"voiceover: {len(timings)} scene MP3s + timings.json in {out} "
          f"({sum(t['seconds'] for t in timings):.1f} s in all)")
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        sys.exit(__doc__)
    cmd, argv = sys.argv[1], sys.argv[2:]
    if cmd == "new":
        return cmd_new(argv)
    if cmd == "export":
        return cmd_export(argv)
    if cmd == "scan":
        return run("scan", *sorted(Path(argv[0]).glob("ch[0-9][0-9].md")), *argv[1:])
    if cmd == "status":
        return run("status", argv[0], "--audio-only", *argv[1:])
    if cmd in SCRIPTS:
        return run(cmd, *argv)
    sys.exit(f"unknown command {cmd!r}\n{__doc__}")


if __name__ == "__main__":
    sys.exit(main() or 0)
