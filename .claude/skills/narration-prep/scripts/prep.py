"""Narration-prep conversion: books/<slug>/chNN.md -> audio/chNN.txt, following the rules in ../SKILL.md
(headings, markdown, scene breaks, glossary phonemes, paragraph splitting, learned rule case 01).

    .venv/bin/python .claude/skills/narration-prep/scripts/prep.py books/<slug> [out_dir]

Paragraph splitting must stay stable: the render cache is keyed on paragraph text, so a changed split
re-renders audio that didn't change. Judgement calls (italics that carry meaning, numbers that need context,
emotion beats) belong in the manuscript, via speech-flow; review the diff of each script after running."""
import re, sys
from pathlib import Path

SPLIT = 120
SENT = re.compile(r"(?:(?<=[.!?…])|(?<=[.!?…][\"”]))\s+(?=[\"“]?[A-Z])")


def glossary(book):
    names = {}
    for line in (book / "glossary.md").read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[2] not in ("ok", "?", "Phonemes", "") and not set(cells[2]) <= set("-"):
            names[cells[0]] = cells[2]
    return names


def words(s):
    return len(s.split())


def split_long(p):
    if words(p) <= SPLIT:
        return [p]
    sents = SENT.split(p)
    out, cur = [], ""
    target = words(p) / ((words(p) + SPLIT - 1) // SPLIT)
    for s in sents:
        if cur and words(cur) >= target:
            out.append(cur); cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


_G2P = []


def stress(text):
    if not _G2P:
        from kokoro import KPipeline
        _G2P.append(KPipeline(lang_code="a", model=False, repo_id="hexgrad/Kokoro-82M"))
    return " ".join(r.phonemes for r in _G2P[0](text))


def short_question(p, names=()):
    """Case 01: a quoted question of <= 3 words with no main stress gets (+2) on its first word and a doubled '?'.
    Applies whether the line stands alone or has a tag or beat: a beat after it doesn't give it a main stress."""
    def fix(m):
        q = m.group(1)
        last = re.split(r"(?<=[.!?…])\s+", q)[-1]
        if (not last.endswith("?") or last.endswith(("??", "...?", "…?")) or words(last) > 3
                or any(re.search(rf"\b{n}\b", last) for n in names) or "ˈ" in stress(f'"{last}"')):
            return m.group(0)
        w = re.match(r"([\w’']+)(.*)", last)
        if not w:
            return m.group(0)
        first, rest = w.groups()
        return f'"{q[:len(q) - len(last)]}[{first}](+2){rest}?"'
    return re.sub(r'"([^"]+)"', fix, p)


def convert(md, names):
    lines = md.read_text().strip().split("\n\n")
    out = []
    for i, par in enumerate(lines):
        par = " ".join(par.split())
        if i == 0 and par.startswith("#"):
            t = par.lstrip("# ").replace(": ", ". ")
            out += [t.rstrip(".") + ".", "[pause 1.0]"]
            continue
        if re.fullmatch(r"(\*\s*){3}|-{3,}|#", par):
            out.append("[pause 1.5]")
            continue
        par = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", par)
        par = par.replace("…", "...")
        par = re.sub(r"\bMr\.", "Mister", par)
        par = short_question(par, names)
        for name, ph in names.items():
            par = re.sub(rf"\b{name}\b", f"[{name}](/{ph}/)", par)
        out += split_long(par)
    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    book = Path(sys.argv[1]); dest = Path(sys.argv[2]) if len(sys.argv) > 2 else book / "audio"
    names = glossary(book if (book / "glossary.md").exists() else Path(sys.argv[3]))
    for md in sorted(book.glob("ch[0-9][0-9].md")):
        (dest / f"{md.stem}.txt").write_text(convert(md, names))
        print(md.stem)
