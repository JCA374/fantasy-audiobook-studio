#!/usr/bin/env python3
"""Build the project website into _site/ from the repository's own files.

  skills      .claude/skills/*/SKILL.md + site/content/skills.yaml
  books       books/<slug>/book.yaml, chNN.md, making-of files, audio/*.mp3 + .m4b (EPUB generated here)
  training    training/*.md, *.txt, *.mp3 (made from the local .wav by --audio)
  pages       site/content/pipeline.md

usage: build.py [--audio]     --audio: (local) convert training/*.wav to .mp3 first
"""
import datetime as dt
import html
import json
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
CONTENT = ROOT / "site" / "content"
SKILLS_DIR = ROOT / ".claude" / "skills"
BOOKS = ROOT / "books"
TRAINING = ROOT / "training"
VIDEO = ROOT / "site/video/how-it-works.mp4"
REPO_URL = "https://github.com/JCA374/fantasy-audiobook-studio"

STAGES = [  # n, name, group, skills, output
    (0, "Seed", "write", ["story-seed"], "seed.md"),
    (1, "Story bible", "write", ["fantasy-novella", "fiction-workshop"], "story-bible.md · glossary.md"),
    (2, "Structure", "write", ["story-structure"], "outline.md"),
    (3, "Draft", "write", ["fantasy-novella", "avoid-ai-writing"], "chNN.md"),
    (4, "Edit", "write", ["fiction-workshop", "character-archetypes", "prose-mechanics", "avoid-ai-writing"], "revised chapters"),
    (5, "Reader test", "write", ["fiction-workshop"], "fresh-reader report"),
    (6, "Speech flow", "voice", ["speech-flow"], "chapters fixed for the ear"),
    (7, "Narration prep", "voice", ["narration-prep"], "audio/chNN.txt"),
    (8, "Narrate", "voice", ["kokoro-narrate"], "audio/chNN.wav"),
    (9, "Listen check", "voice", ["listen-check"], "timestamps to listen to"),
    (10, "Assemble & publish", "ship", ["audiobook-assemble"], ".m4b · .mp3 · .epub · this site"),
]
GROUPS = {"write": "Writing", "voice": "Voice", "ship": "Package"}
MAKING_OF = ["story-bible", "outline", "continuity", "glossary", "status", "rewrite-notes"]


# ---------------------------------------------------------------- helpers

def md(text, root=""):
    """Markdown -> HTML; relative links are made relative to the site root."""
    out = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"], output_format="html")
    return re.sub(r'href="(?!https?:|#|mailto:|/)([^"]+)"', lambda m: f'href="{root}{m.group(1)}"', out)


def strip_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (yaml.safe_load(m.group(1)) or {}, text[m.end():]) if m else ({}, text)


def esc(s):
    return html.escape(str(s), quote=True)


def write(rel, body):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def copy(src, rel):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, p)


def duration(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def mmss(sec):
    if sec is None:
        return ""
    sec = int(round(sec))
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60}:{sec % 60:02d}"


def words(text):
    return len(re.findall(r"[\w’']+", re.sub(r"^#.*$", "", text, flags=re.M)))


def size_mb(p):
    return f"{p.stat().st_size / 1e6:.0f} MB"


def changelog(n=8):
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "log", f"-{n}", "--date=short", "--pretty=%ad\t%s"],
                           capture_output=True, text=True, timeout=10)
        return [line.split("\t", 1) for line in r.stdout.splitlines() if "\t" in line]
    except (OSError, subprocess.SubprocessError):
        return []


# ---------------------------------------------------------------- layout

NAV = [("index.html", "Overview"), ("pipeline.html", "Pipeline"), ("skills/index.html", "Skills"),
       ("improvements.html", "Improvements"), ("books/index.html", "Books")]


def page(rel, title, body, section="", subnav=""):
    root = "../" * rel.count("/")
    nav = "".join(
        f'<a href="{root}{href}"{" aria-current=page" if label == section else ""}>{label}</a>' for href, label in NAV)
    write(rel, f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Fantasy Audiobook Studio</title>
<meta name="description" content="Short fantasy novels written with Claude Code and narrated locally with Kokoro TTS: the process, the skills, the books.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;1,8..60,400&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='7' fill='%23b4532a'/><path d='M10 8v17M10 18h12M22 18v7M13 8h7v10' stroke='%23fff6ea' stroke-width='3' fill='none'/></svg>">
</head><body>
<header class="site"><div class="wrap bar">
<a class="brand" href="{root}index.html"><span class="mark">◆</span> Fantasy Audiobook Studio</a>
<nav>{nav}</nav></div>{subnav}</header>
<main class="wrap">{body}</main>
<footer class="wrap"><p>Built from the repository by <code>site/build.py</code> · {dt.date.today().isoformat()} ·
<a href="{REPO_URL}">source on GitHub</a></p></footer>
</body></html>
""")


def pipeline_strip(root, link_stage=True):
    cards = []
    for n, name, group, skills, out in STAGES:
        chips = "".join(f'<a class="chip" href="{root}skills/{s}.html">{s}</a>' for s in skills)
        title = f'<a href="{root}pipeline.html#stage-{n}">{name}</a>' if link_stage else name
        cards.append(f'<li class="stage g-{group}"><span class="n">{n}</span><h3>{title}</h3>'
                     f'<div class="chips">{chips}</div><p class="out">→ {esc(out)}</p></li>')
    legend = "".join(f'<span class="lg g-{g}">{label}</span>' for g, label in GROUPS.items())
    return f'<div class="legend">{legend}</div><ol class="pipeline">{"".join(cards)}</ol>'


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------------------------------------------------------------- skills

def load_skills():
    meta = yaml.safe_load((CONTENT / "skills.yaml").read_text(encoding="utf-8"))
    skills = []
    for name, m in meta.items():
        fm, body = strip_frontmatter((SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8"))
        files = sorted(p.relative_to(SKILLS_DIR / name).as_posix() for p in (SKILLS_DIR / name).rglob("*")
                       if p.is_file() and p.name != "SKILL.md" and "__pycache__" not in p.parts)
        skills.append({"name": name, "desc": fm.get("description", ""), "body": body, "files": files, **m})
    return skills


WHO = {"claude": ("Claude", "judgement: reads, writes, decides what to flag"),
       "script": ("Script", "mechanical: same input, same output, every time"),
       "author": ("Author", "creative decisions and approval")}


def who_chips(who):
    return "".join(f'<li class="who who-{k}"><b>{WHO[k][0]}</b> {esc(v)}</li>' for k, v in who.items())


def skill_group(name):
    return next((g for _, _, g, sk, _ in STAGES if name in sk), "write")


def stage_track(name, root):
    """The pipeline stages as a row, with the ones this skill works in highlighted."""
    cells = "".join(
        f'<li class="g-{g}{" on" if name in sk else ""}" title="{n}. {esc(nm)}"><span>{n}</span><em>{esc(nm)}</em></li>'
        for n, nm, g, sk, _ in STAGES)
    return f'<a class="track-link" href="{root}pipeline.html"><ol class="track">{cells}</ol></a>'


def build_skills(skills, cases):
    guide = yaml.safe_load((CONTENT / "skills-guide.yaml").read_text(encoding="utf-8"))

    def tabs(current):
        items = "".join(
            f'<a href="{s["name"]}.html"{" aria-current=page" if s["name"] == current else ""}>'
            f'<span class="tab-stage">{s["stage"]}</span>{s["name"]}</a>' for s in skills)
        return f'<div class="tabs wrap" role="tablist">{items}</div>'

    groups = []
    for g, label in GROUPS.items():
        cards = []
        for s in skills:
            if skill_group(s["name"]) != g:
                continue
            gd = guide.get(s["name"], {})
            who = "".join(f'<span class="whotag who-{k}">{WHO[k][0]}</span>' for k in gd.get("who", {}))
            cards.append(f"""<a class="skillcard g-{g}" href="{s["name"]}.html">
<p class="sc-top"><span class="sc-stage">Stage {s["stage"]}</span><span class="badge {s["origin"]}">{s["origin"]}</span></p>
<h3>{s["name"]}</h3><p>{esc(gd.get("plain", s["role"]))}</p>
<p class="io"><span>{esc(gd.get("input", ""))}</span><b>→</b><span>{esc(gd.get("output", ""))}</span></p>
<p class="whos">{who}</p></a>""")
        groups.append(f'<h2 class="grouphead g-{g}">{label}</h2><div class="skillgrid">{"".join(cards)}</div>')

    page("skills/index.html", "Skills", f"""
<h1>Skills</h1>
<p class="lede">A <b>skill</b> is a written instruction manual that Claude follows for one job, like "turn this
chapter into a narration script". Each one is a folder with a <code>SKILL.md</code> file (the instructions) and
sometimes a small program for the mechanical parts. Together, {len(skills)} skills cover the whole path from idea to audiobook.</p>
<h2>How a skill works</h2>
<ol class="howflow">
<li><b>You ask</b><span>"Check chapter 2 for speech flow."</span></li>
<li><b>Claude picks the skill</b><span>Every skill has a short description of when to use it. Claude matches your request to it.</span></li>
<li><b>It follows the steps</b><span>Claude does the parts that need judgement and runs scripts for the mechanical parts.</span></li>
<li><b>It stops and hands back</b><span>You see the result and decide. Nothing goes further without your OK.</span></li>
</ol>
<h2>Who does what</h2>
<ul class="wholegend">{who_chips({k: v[1] for k, v in WHO.items()})}</ul>
<p class="hint"><span class="badge ours">ours</span> written for this project ·
<span class="badge vendored">vendored</span> copied unchanged from
<a href="https://github.com/rhavekost/author-toolkit">rhavekost/author-toolkit</a> (MIT), so they can be updated from the original.</p>
{"".join(groups)}""", "Skills", tabs(""))

    for i, s in enumerate(skills):
        gd = guide.get(s["name"], {})
        g = skill_group(s["name"])
        my_cases = [c for c in cases if c["id"] in s.get("cases", [])]
        case_html = "".join(
            f'<li><a href="../improvements/{c["slug"]}.html"><b>Case {c["id"]}</b> · {esc(c["title"])}</a>'
            f' <span class="status {c["state"]}">{esc(c["status"])}</span></li>' for c in my_cases)
        files = "".join(f"<li><code>{esc(f)}</code></li>" for f in s["files"]) or "<li>(SKILL.md only)</li>"
        src = f"{REPO_URL}/tree/main/.claude/skills/{s['name']}"
        steps = "".join(f"<li>{esc(st)}</li>" for st in gd.get("steps", []))
        ex = gd.get("example")
        example = f"""<section class="example"><h2>Example</h2><div class="ba">
<div><span class="ba-label">Before</span><p>{esc(ex["before"])}</p></div><b class="ba-arrow">→</b>
<div class="after"><span class="ba-label">After</span><p>{esc(ex["after"])}</p></div></div>
<p class="hint">{esc(ex.get("note", ""))}</p></section>""" if ex else ""
        prev = skills[i - 1] if i else None
        nxt = skills[i + 1] if i + 1 < len(skills) else None
        pager = (f'<a href="{prev["name"]}.html">← {prev["name"]}</a>' if prev else "<span></span>") + \
                (f'<a href="{nxt["name"]}.html">{nxt["name"]} →</a>' if nxt else "<span></span>")
        page(f"skills/{s['name']}.html", s["name"], f"""
<p class="kicker">Stage {s["stage"]} · {GROUPS[g]} · <span class="badge {s["origin"]}">{s["origin"]}</span></p>
<h1>{s["name"]}</h1>
<p class="lede">{esc(gd.get("plain", s["role"]))}</p>
{stage_track(s["name"], "../")}
<div class="glance">
<div><h3>When it runs</h3><p>{esc(gd.get("when", ""))}</p></div>
<div><h3>What goes in</h3><p>{esc(gd.get("input", ""))}</p></div>
<div><h3>What comes out</h3><p>{esc(gd.get("output", ""))}</p></div>
<div><h3>Who does the work</h3><ul class="wholist">{who_chips(gd.get("who", {}))}</ul></div>
</div>
<div class="cols">
<section><h2>Step by step</h2><ol class="steps">{steps}</ol></section>
{example}
</div>
<h2>In this project</h2>
<div class="cols">
<section>{md(s.get("use", ""), "../")}</section>
<section class="aside"><h3>From the books</h3>{md(s.get("examples", ""), "../")}
{f'<h3>Training cases</h3><ul class="cases">{case_html}</ul>' if case_html else ""}</section>
</div>
<details class="skillfile"><summary>For the curious: the instructions Claude reads (<code>SKILL.md</code>)</summary>
<p class="trigger"><b>Claude uses this skill when:</b> {esc(s["desc"])}</p>
<div class="prose">{md(s["body"], "../")}</div>
<h3>Other files in the skill</h3><ul class="files">{files}</ul>
<p><a href="{src}">View the skill on GitHub →</a></p>
</details>
<nav class="pager wide">{pager}</nav>""", "Skills", tabs(s["name"]))


# ---------------------------------------------------------------- training

def script_html(line):
    """Show Kokoro markup readably: [Mira](/mˈiɹə/) -> dotted name with phonemes on hover, [Can](+2) -> stressed."""
    out = esc(line)
    out = re.sub(r"\[([^\]]+)\]\(/([^)]*)/\)", r'<abbr title="/\2/">\1</abbr>', out)
    return re.sub(r"\[([^\]]+)\]\(([+-]\d)\)", r'<b class="stress" title="stress \2">\1</b><sup>\2</sup>', out)


def load_cases():
    index = {}
    if (TRAINING / "cases.md").exists():
        for line in (TRAINING / "cases.md").read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and re.fullmatch(r"\d+", cells[0]):
                index[cells[0]] = cells
    cases = []
    for f in sorted(TRAINING.glob("[0-9][0-9]-*.md")):
        cid = f.name[:2]
        text = f.read_text(encoding="utf-8")
        title = re.sub(r"^#\s*\d+\s*·\s*", "", text.splitlines()[0]).strip()
        problem, rule, status = (index.get(cid) or ["", "", "", "open"])[1:]
        cases.append({"id": cid, "slug": f.stem, "title": title, "text": text, "problem": problem, "rule": rule,
                      "status": status, "state": "fixed" if status.startswith("fixed") else "open"})
    return cases


def wav_to_mp3():
    for w in TRAINING.glob("*.wav"):
        mp3 = w.with_suffix(".mp3")
        if not mp3.exists() or mp3.stat().st_mtime < w.stat().st_mtime:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-ac", "1", "-b:a", "64k", str(mp3)], check=True)
            print("  mp3:", mp3.name)


def rule_tests():
    sys.path.insert(0, str(SKILLS_DIR / "speech-flow" / "scripts"))
    from test_rules import run
    return run()


def on_site(d):
    """A book folder is published unless its book.yaml says `site: false`."""
    y = d / "book.yaml"
    return y.exists() and (yaml.safe_load(y.read_text(encoding="utf-8")) or {}).get("site", True)


def listen_reports():
    out = []
    for f in sorted(BOOKS.glob("*/audio/ch*.listen.json")):
        if not on_site(f.parent.parent):
            continue
        out.append((f.parent.parent.name, json.loads(f.read_text(encoding="utf-8"))))
    return out


def slug_for(cases, cid):
    return next((c["slug"] for c in cases if c["id"] == cid), "")


def build_training(cases, skills):
    owner = {cid: s["name"] for s in skills for cid in s.get("cases", [])}
    cards = "".join(f"""<a class="case" href="improvements/{c["slug"]}.html">
<span class="cid">{c["id"]}</span><div><h3>{esc(c["title"])}</h3>
<p>{md(c["problem"])}</p><p class="rule"><b>Rule:</b> {md(c["rule"])}</p></div>
<span class="status {c["state"]}">{esc(c["status"])}</span></a>""" for c in reversed(cases))
    tests = rule_tests()
    passed = sum(t["ok"] for t in tests)
    test_rows = "".join(
        f'<tr><td>{"✅" if t["ok"] else "❌"}</td><td><a href="improvements/{slug_for(cases, t["case"])}.html">case {t["case"]}</a></td>'
        f'<td><code>{esc(t["check"])}</code></td><td class="q">{esc(t["before"])}</td><td class="q">{esc(t["after"])}</td></tr>'
        for t in tests)
    reports = listen_reports()
    rep_rows = []
    for book, r in reports:
        flags = [f'<li><b>{mmss(w["time"])}</b> {esc(w["kind"])}: expected “{esc(w["expected"]) or "–"}”, heard “{esc(w["heard"]) or "–"}”</li>' for w in r["words"]]
        flags += [f'<li><b>¶{p["para"]}</b> pace {esc(p["kind"])}: {p["wps"]} words/s (chapter {p["median"]})</li>' for p in r["pace"]]
        flags += [f'<li><b>¶{x["para"]}</b> flat short line: {esc(x["text"])}</li>' for x in r["stress"]]
        n = len(flags)
        rep_rows.append(f'<tr><td><a href="books/{book}/{r["chapter"]}.html">{r["chapter"]}</a></td><td>{mmss(r["duration"])}</td>'
                        f'<td>{r["checked"]}</td><td><span class="status {"fixed" if not n else "open"}">{n or "clean"}{" to check" if n else ""}</span>'
                        f'{f" <span class=hint>{len(r.get(chr(100) + "ismissed", []))} dismissed by the second model</span>" if r.get("dismissed") else ""}'
                        f'{"<ul class=flags>" + "".join(flags) + "</ul>" if n else ""}</td></tr>')
    proposals = TRAINING / "proposals.md"
    prop_html = md(re.sub(r"^#.*\n", "", proposals.read_text(encoding="utf-8"), count=1)) if proposals.exists() else ""
    page("improvements.html", "Improvements", f"""
<h1>Improvements</h1>
<p class="lede">The skills get better in four ways. Two depend on the author's ear, and two are automatic. Every lesson ends
up as a rule in a skill, so the next book starts with it already in place.</p>
<ol class="howflow improve">
<li><b>The author reports</b><span>"This sounds wrong." It becomes a training case with before/after audio; the author picks the fix.</span></li>
<li><b>The automatic listener</b><span>Speech recognition transcribes every chapter and compares it with the script, and turns up problems nobody reported.</span></li>
<li><b>Rule tests</b><span>Every rule has a before/after test that must pass before publishing, so a new rule can't undo an old fix.</span></li>
<li><b>Rule proposals</b><span>When a pattern repeats, Claude drafts the rule; the author approves it. Taste stays with the author.</span></li>
</ol>
<h2 id="cases">1 · Training cases</h2>
<p>The original text, what was heard, why it happened, and audio of the <i>before</i> and each attempted fix. Newest first.</p>
<div class="caselist">{cards or "<p>No cases yet.</p>"}</div>
<h2 id="listener">2 · Automatic listener</h2>
<p>The latest <a href="skills/listen-check.html">listen-check</a> report for each chapter. A flag means "worth a listen",
not a confirmed error: each one is double-checked with a second model, then by ear.</p>
<table class="reports"><thead><tr><th>Chapter</th><th>Length</th><th>Checked</th><th>Result</th></tr></thead>
<tbody>{"".join(rep_rows) or "<tr><td colspan=4>No reports yet.</td></tr>"}</tbody></table>
<h2 id="tests">3 · Rule tests <span class="status {"fixed" if passed == len(tests) else "open"}">{passed}/{len(tests)} passing</span></h2>
<p>Run at every build. The scanner must flag the <i>before</i> text and leave the <i>after</i> text alone.</p>
<table class="tests"><thead><tr><th></th><th>From</th><th>Check</th><th>Must flag</th><th>Must not flag</th></tr></thead>
<tbody>{test_rows}</tbody></table>
<h2 id="proposals">4 · Rule proposals</h2>
<div class="prose">{prop_html}</div>""", "Improvements")

    for c in cases:
        before = TRAINING / f"{c['slug']}.before.txt"
        base = before.read_text(encoding="utf-8").splitlines() if before.exists() else []
        variants = sorted(TRAINING.glob(f"{c['slug']}.*.mp3"),
                          key=lambda p: (p.stem.split(".")[-1] != "before", p.stem))
        players = []
        for mp3 in variants:
            v = mp3.stem.split(".")[-1]
            copy(mp3, f"improvements/{mp3.name}")
            txt = mp3.with_suffix(".txt")
            lines = txt.read_text(encoding="utf-8").splitlines() if txt.exists() else []
            changed = [l for l in lines if l.strip() and l not in base and not l.startswith("[pause")]
            shown = changed if v != "before" else []
            diff = "".join(f"<blockquote>{script_html(l)}</blockquote>" for l in shown[:8])
            players.append(f'<div class="variant{" before" if v == "before" else ""}"><h3>{esc(v)}</h3>'
                           f'<audio controls preload="none" src="{mp3.name}"></audio>{diff}'
                           f'<details><summary>Full script</summary><pre>{esc(chr(10).join(lines))}</pre></details></div>')
        sk = owner.get(c["id"])
        page(f"improvements/{c['slug']}.html", f"Case {c['id']}", f"""
<p class="kicker"><a href="../improvements.html">Improvements</a> · Case {c["id"]}
{f' · skill: <a href="../skills/{sk}.html">{sk}</a>' if sk else ""} · <span class="status {c["state"]}">{esc(c["status"])}</span></p>
<div class="prose">{md(c["text"], "../")}</div>
<h2>Listen</h2>
<p class="hint">Each version is rendered with the same voice and settings. Under each fix: the lines that differ from <i>before</i>.</p>
<div class="variants">{"".join(players) or "<p>No audio yet.</p>"}</div>""", "Improvements")


# ---------------------------------------------------------------- books

def load_book(d):
    meta = yaml.safe_load((d / "book.yaml").read_text(encoding="utf-8"))
    chapters = []
    for f in sorted(d.glob("ch[0-9][0-9].md")):
        text = f.read_text(encoding="utf-8")
        mp3 = d / "audio" / f"{f.stem}.mp3"
        chapters.append({"stem": f.stem, "title": meta.get("chapters", {}).get(f.stem, f.stem), "text": text,
                         "words": words(text), "mp3": mp3 if mp3.exists() else None,
                         "dur": duration(mp3) if mp3.exists() else None})
    m4b = next((d / "audio").glob("*.m4b"), None)
    return {"slug": d.name, "dir": d, "meta": meta, "chapters": chapters, "m4b": m4b,
            "cover": d / meta["cover"] if meta.get("cover") and (d / meta["cover"]).exists() else None}


def build_epub(b, dest):
    meta, title = b["meta"], b["meta"]["title"]
    uid = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, REPO_URL + '/' + b['slug'])}"
    css = "body{font-family:serif;line-height:1.5}h1{text-align:center;margin:2em 0 1.5em}hr{border:0;text-align:center}hr:after{content:'* * *'}p{text-indent:1.2em;margin:0}h1+p,hr+p{text-indent:0}"
    items, spine, nav = [], [], []
    with zipfile.ZipFile(dest, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf = lambda name, data: z.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
        zf("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        zf("OEBPS/style.css", css)
        xhtml = lambda t, body: f'<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en"><head><title>{esc(t)}</title><link rel="stylesheet" href="style.css"/></head><body>{body}</body></html>'
        if b["cover"]:
            zf("OEBPS/cover.jpg", b["cover"].read_bytes())
            items.append('<item id="cover-img" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/>')
            zf("OEBPS/cover.xhtml", xhtml("Cover", f'<div style="text-align:center"><img src="cover.jpg" alt="{esc(title)}" style="max-width:100%;max-height:100%"/></div>'))
            items.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
            spine.append('<itemref idref="cover"/>')
        zf("OEBPS/title.xhtml", xhtml(title, f'<h1>{esc(title)}</h1><p style="text-align:center;text-indent:0">{esc(meta.get("author", ""))}</p>'))
        items.append('<item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>')
        spine.append('<itemref idref="title"/>')
        for c in b["chapters"]:
            body = markdown.markdown(c["text"], output_format="xhtml")
            zf(f"OEBPS/{c['stem']}.xhtml", xhtml(c["title"], body))
            items.append(f'<item id="{c["stem"]}" href="{c["stem"]}.xhtml" media-type="application/xhtml+xml"/>')
            spine.append(f'<itemref idref="{c["stem"]}"/>')
            nav.append(f'<li><a href="{c["stem"]}.xhtml">{esc(c["title"])}</a></li>')
        zf("OEBPS/nav.xhtml", xhtml("Contents", f'<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>{"".join(nav)}</ol></nav>'))
        items.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
        modified = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        zf("OEBPS/content.opf", f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="en">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">{uid}</dc:identifier><dc:title>{esc(title)}</dc:title><dc:creator>{esc(meta.get("author", ""))}</dc:creator>
<dc:language>en</dc:language><dc:date>{meta.get("year", "")}</dc:date><meta property="dcterms:modified">{modified}</meta>
<meta name="cover" content="cover-img"/></metadata>
<manifest><item id="css" href="style.css" media-type="text/css"/>{"".join(items)}</manifest>
<spine>{"".join(spine)}</spine></package>''')


def edition_note(b, books):
    """Link between editions: an old edition points forward, the current one lists earlier ones."""
    meta = b["meta"]
    if meta.get("superseded_by"):
        return (f'<p class="spoiler">Earlier edition {meta.get("edition", "")}. {esc(meta.get("note", ""))} '
                f'<a href="../{meta["superseded_by"]}/index.html">Read the current edition →</a></p>')
    older = [o for o in books if o["meta"].get("superseded_by") == b["slug"]]
    if not older:
        return ""
    items = "".join(f'<li><a href="../{o["slug"]}/index.html">Edition {o["meta"].get("edition", "")}</a>: '
                    f'{esc(o["meta"].get("note", ""))}</li>' for o in older)
    return f"<h2>Earlier editions</h2><ul class=making>{items}</ul>"


def build_books(books):
    current = [b for b in books if not b["meta"].get("superseded_by")]
    cards = "".join(f"""<a class="bookcard" href="{b["slug"]}/index.html">
{f'<img src="{b["slug"]}/cover.jpg" alt="">' if b["cover"] else ""}
<div><h2>{esc(b["meta"]["title"])}</h2><p>{esc(b["meta"].get("author", ""))} · {len(b["chapters"])} chapters ·
{sum(c["words"] for c in b["chapters"]):,} words{f' · {mmss(sum(c["dur"] or 0 for c in b["chapters"]))} of audio' if b["m4b"] else ""}</p></div></a>"""
                    for b in current)
    page("books/index.html", "Books", f"<h1>Books</h1><div class=books>{cards}</div>", "Books")

    for b in books:
        s, meta, title = b["slug"], b["meta"], b["meta"]["title"]
        if b["cover"]:
            copy(b["cover"], f"books/{s}/cover.jpg")
        epub_name = re.sub(r"[^\w]+", "-", title).strip("-") + ".epub"
        build_epub(b, OUT / "books" / s / epub_name)
        downloads = []
        if b["m4b"]:
            m4b_name = re.sub(r"[^\w]+", "-", title).strip("-") + ".m4b"
            copy(b["m4b"], f"books/{s}/{m4b_name}")
            downloads.append(f'<a class="dl" href="{m4b_name}" download><b>Audiobook</b><span>.m4b with chapters · {size_mb(b["m4b"])}</span></a>')
        downloads.append(f'<a class="dl" href="{epub_name}" download><b>E-book</b><span>.epub for Kindle, Apple Books, Kobo · {size_mb(OUT / "books" / s / epub_name)}</span></a>')
        rows = []
        for i, c in enumerate(b["chapters"]):
            audio = ""
            if c["mp3"]:
                copy(c["mp3"], f"books/{s}/audio/{c['mp3'].name}")
                audio = f'<audio controls preload="none" src="audio/{c["mp3"].name}"></audio>'
            rows.append(f'<li><div class="ch"><a href="{c["stem"]}.html">{esc(c["title"])}</a>'
                        f'<span>{c["words"]:,} words{" · " + mmss(c["dur"]) if c["dur"] else ""}</span></div>{audio}</li>')
            prev = f'<a href="{b["chapters"][i - 1]["stem"]}.html">← {esc(b["chapters"][i - 1]["title"])}</a>' if i else "<span></span>"
            nxt = f'<a href="{b["chapters"][i + 1]["stem"]}.html">{esc(b["chapters"][i + 1]["title"])} →</a>' if i + 1 < len(b["chapters"]) else "<span></span>"
            player = f'<audio controls preload="none" src="audio/{c["mp3"].name}"></audio>' if c["mp3"] else ""
            page(f"books/{s}/{c['stem']}.html", f"{c['title']} · {title}", f"""
<p class="kicker"><a href="index.html">{esc(title)}</a></p>
<div class="listen">{player}</div>
<article class="chapter">{md(c["text"])}</article>
<nav class="pager">{prev}{nxt}</nav>""", "Books")
        making = "".join(f'<li><a href="making-of/{m}.html">{m.replace("-", " ")}</a></li>'
                         for m in MAKING_OF if (b["dir"] / f"{m}.md").exists())
        for m in MAKING_OF:
            f = b["dir"] / f"{m}.md"
            if f.exists():
                page(f"books/{s}/making-of/{m}.html", f"{m} · {title}", f"""
<p class="kicker"><a href="../index.html">{esc(title)}</a> · making of</p>
<p class="spoiler">Working file from the writing process. Contains spoilers for the whole book.</p>
<div class="prose">{md(f.read_text(encoding="utf-8"), "../../")}</div>""", "Books")
        total = sum(c["dur"] or 0 for c in b["chapters"])
        nar = meta.get("narration", {})
        page(f"books/{s}/index.html", title, f"""
<div class="bookhead">
{f'<img class="cover" src="cover.jpg" alt="Cover of {esc(title)}">' if b["cover"] else ""}
<div><p class="kicker">Book{f" · edition {meta['edition']}" if meta.get("edition") else ""}</p><h1>{esc(title)}</h1>
<p class="lede">by {esc(meta.get("author", ""))} · narrated by Kokoro TTS ({esc(nar.get("narrator", ""))}, speed {nar.get("speed", 1)})</p>
<p class="facts">{len(b["chapters"])} chapters · {sum(c["words"] for c in b["chapters"]):,} words{" · " + mmss(total) + " of audio" if total else ""}</p>
<div class="downloads">{downloads and "".join(downloads)}</div>
<p class="hint">Kindle: send the .epub with Amazon's <a href="https://www.amazon.com/sendtokindle">Send to Kindle</a>.
Phone: put the .m4b in Google Drive or Files and open it in an audiobook player such as BookPlayer.</p>
</div></div>
{edition_note(b, books)}
<h2>Chapters</h2><ol class="chapters">{"".join(rows)}</ol>
<h2>Making of</h2>
<p>The working files behind this book, exactly as the skills left them (spoilers):</p><ul class="making">{making}</ul>""", "Books")


# ---------------------------------------------------------------- top pages

STARTER = ROOT / "site/starter"
KIT = "starter-kit.zip"
SITE_URL = "https://jca374.github.io/fantasy-audiobook-studio/"


def build_starter_kit():
    """Zip the skills, the training notes they refer to and the kit-only files (site/starter/) for download.

    Unzips into the current folder (no top-level directory). Timestamps are fixed, so an unchanged kit
    builds the same bytes."""
    files = [(p, p.relative_to(ROOT).as_posix()) for p in sorted(SKILLS_DIR.rglob("*"))
             if p.is_file() and "__pycache__" not in p.parts]
    files += [(p, f"training/{p.name}") for p in sorted(TRAINING.glob("*")) if p.suffix in (".md", ".yaml")]
    files += [(p, p.relative_to(STARTER).as_posix()) for p in sorted(STARTER.rglob("*")) if p.is_file()]
    OUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT / KIT, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in files:
            info = zipfile.ZipInfo(arc, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (0o755 if src.suffix in (".py", ".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, src.read_bytes())
    return len(files), (OUT / KIT).stat().st_size


def copy_box(label, text):
    return (f'<div class="copybox"><div class="copyhead"><span>{esc(label)}</span>'
            f'<button type="button" class="copybtn">Copy</button></div><pre><code>{esc(text)}</code></pre></div>')


def build_home(skills, books, cases):
    metas = [yaml.safe_load(y.read_text(encoding="utf-8")) or {} for y in sorted(BOOKS.glob("*/book.yaml"))]
    hidden = [m["title"].lower() for m in metas if not m.get("site", True) or not m.get("home", True)]
    entries = [(d, m) for d, m in changelog(16) if not any(t in m.lower() for t in hidden)][:8]  # hidden books stay out of the log too
    log = "".join(f"<li><time>{d}</time> {esc(m)}</li>" for d, m in entries)
    # featured book: the first current one the author hasn't kept off the home page (book.yaml `home: false`)
    b = next((x for x in books if not x["meta"].get("superseded_by") and x["meta"].get("home", True)), None)
    book = ""
    if b:
        total = sum(c["dur"] or 0 for c in b["chapters"])
        book = f"""<a class="feature" href="books/{b["slug"]}/index.html">
{f'<img src="books/{b["slug"]}/cover.jpg" alt="">' if b["cover"] else ""}
<div><p class="kicker">Latest book</p><h2>{esc(b["meta"]["title"])}</h2>
<p>{len(b["chapters"])} chapters · {sum(c["words"] for c in b["chapters"]):,} words{" · " + mmss(total) + " of audio" if total else ""}</p>
<p class="more">Listen, read, or download the .m4b and .epub →</p></div></a>"""
    fixed = sum(c["state"] == "fixed" for c in cases)
    tests = rule_tests()
    video = ""
    if VIDEO.exists():  # rendered locally by site/video/make_video.py
        webm = VIDEO.with_suffix(".webm")
        for f in (VIDEO, webm, VIDEO.with_suffix(".vtt")):
            if f.exists():
                copy(f, f.name)
        # WebM first: some Linux browsers can't decode the MP4's AAC audio
        sources = (f'<source src="{webm.name}" type="video/webm">' if webm.exists() else "") + \
            f'<source src="{VIDEO.name}" type="video/mp4">'
        video = f"""<h2 id="video">How it works, in five minutes</h2>
<video class="explainer" controls preload="metadata">{sources}
<track kind="captions" srclang="en" label="English" src="{VIDEO.with_suffix(".vtt").name}" default></video>"""
    n_files, kit_size = build_starter_kit()
    commands = (f"mkdir my-audiobooks && cd my-audiobooks\n"
                f"curl -LO {SITE_URL}{KIT}\n"
                f"unzip {KIT} && rm {KIT}\n"
                f"claude")
    prompt = (f"Download {SITE_URL}{KIT} into this folder, unzip it here and delete the zip. "
              f"Then read SETUP.md and set everything up for me.")
    kit = f"""<section class="kit" id="get-started">
<h2>Write your own</h2>
<p>Everything here runs in <a href="https://claude.com/claude-code">Claude Code</a> on your own computer. The starter kit
has all {len(skills)} skills, the lessons they learned, and a setup guide Claude can follow (Python, Kokoro, ffmpeg).
No books are included: you start from your own idea.</p>
<div class="downloads"><a class="dl" href="{KIT}" download><b>Download the starter kit</b>
<span>.zip · {n_files} files · {kit_size / 1024:.0f} KB</span></a></div>
<p class="hint">Or paste these commands into a terminal, then ask Claude <em>"Read SETUP.md and set this up for me"</em>:</p>
{copy_box("Terminal", commands)}
<p class="hint">…or open Claude Code in an empty folder and paste this:</p>
{copy_box("Prompt for Claude Code", prompt)}
<p class="hint">When setup is done, ask: <em>"Start a new book with story-seed."</em></p>
</section>
<script>
document.querySelectorAll(".copybtn").forEach(b => b.addEventListener("click", async () => {{
  const text = b.closest(".copybox").querySelector("code").innerText;
  try {{ await navigator.clipboard.writeText(text); b.textContent = "Copied"; }}
  catch (e) {{ b.textContent = "Select and copy"; }}
  setTimeout(() => b.textContent = "Copy", 1800);
}}));
</script>"""
    page("index.html", "Overview", f"""
<section class="hero">
<p class="kicker">A process, documented</p>
<h1>From an idea to a finished audiobook, with Claude Code and a laptop.</h1>
<p class="lede">Short fantasy novels (10–20k words) are planned, drafted, edited and checked by Claude with a set of
<a href="skills/index.html">skills</a>, then narrated by <a href="https://huggingface.co/hexgrad/Kokoro-82M">Kokoro</a>,
a small open TTS model running locally on the CPU, and packaged as a chaptered audiobook. The author makes the creative
calls; everything else is a repeatable pipeline. Every passage that sounded wrong becomes a
<a href="improvements.html">training case</a> that improves the next book.</p>
</section>
{video}
{kit}
<h2>The pipeline</h2>
{pipeline_strip("")}
<p><a class="more" href="pipeline.html">How each stage works, in detail →</a></p>
<div class="cols home">
<section>{book}</section>
<section class="aside">
<h2>By the numbers</h2>
<ul class="stats">
<li><b>{len(skills)}</b> skills, {sum(s["origin"] == "ours" for s in skills)} written for this project</li>
<li><b>{len(cases)}</b> training cases, {fixed} turned into rules</li>
<li><b>{sum(t["ok"] for t in tests)}/{len(tests)}</b> rule tests passing</li>
<li><b>~1 h</b> to narrate a 15k-word book on a laptop CPU</li>
<li><b>−19 LUFS</b> audiobook loudness standard</li></ul>
{f'<h2>Recent changes</h2><ul class="log">{log}</ul>' if log else ""}
</section></div>""", "Overview")


def build_pipeline():
    text = (CONTENT / "pipeline.md").read_text(encoding="utf-8")
    body = md(text)
    # give stage headings ids matching the pipeline strip links ("### 1 · Story bible" -> id="stage-1")
    body = re.sub(r"<h3>(\d+) · ([^<]+)</h3>", lambda m: f'<h3 id="stage-{m.group(1)}">{m.group(1)} · {m.group(2)}</h3>', body)
    page("pipeline.html", "Pipeline", f'{pipeline_strip("")}<div class="prose">{body}</div>', "Pipeline")


def main():
    if "--audio" in sys.argv:
        wav_to_mp3()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "site" / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")
    skills = load_skills()
    cases = load_cases()
    books = [load_book(d) for d in sorted(BOOKS.iterdir()) if on_site(d)]
    build_home(skills, books, cases)
    build_pipeline()
    build_skills(skills, cases)
    build_training(cases, skills)
    build_books(books)
    n = sum(1 for _ in OUT.rglob("*.html"))
    size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file()) / 1e6
    print(f"built {n} pages, {size:.0f} MB -> {OUT}")


if __name__ == "__main__":
    main()
