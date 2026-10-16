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

## How the skills improve

1. **Author reports**: "this sounds wrong" becomes a case with before/after audio; the author picks; the fix becomes a rule.
2. **Automatic listener** (`listen-check` skill): Whisper transcribes every chapter and compares it with the script,
   and also checks pace and stress. Confirmed findings become cases (clip cut with `listen.py --clip`).
3. **Rule tests**: `rule-tests.yaml` holds a before/after pair for every scanner rule. `test_rules.py` must pass
   before publishing, so a new rule can't silently break an old fix.
4. **Rule proposals**: `proposals.md`. When a pattern repeats, Claude drafts the rule; the author approves it.
