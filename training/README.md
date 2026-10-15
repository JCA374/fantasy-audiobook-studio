# Narration training

Examples where the audio came out wrong, and how the text conversion was fixed.
The fixes become rules in `.claude/skills/narration-prep/SKILL.md` ("Learned rules"),
and every case here is re-checked whenever those rules change.

## One case = four or five files (flat, numbered)

| File | What |
|---|---|
| `NN-slug.md` | the original manuscript text, plus what sounded wrong and where it came from |
| `NN-slug.before.txt` / `.wav` | the script as the old rules converted it, and its audio |
| `NN-slug.after.txt` / `.wav` | the script with the fix, and its audio |

`cases.md` is the index: one line per case with the problem, the rule learned, and status
(`open` → `fixed` once the author approves the after-audio).

Render a script:

```bash
.venv/bin/python .claude/skills/kokoro-narrate/scripts/narrate.py \
  --script training/NN-slug.after.txt --speed 0.95 -o training/NN-slug.after.wav
```
