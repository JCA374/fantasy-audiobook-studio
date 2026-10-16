---
name: listen-check
description: "Automatic listener for rendered audiobook chapters: transcribes the audio with Whisper (locally, CPU) and compares it with the narration script to find skipped, swapped or garbled words and misheard names, flags paragraphs spoken unusually fast or slow, and finds short lines with no main stress. Use after kokoro-narrate, before audiobook-assemble, when the user asks to check, QA or proof-listen the audio, or wants to find audio problems without listening to everything."
---

# Listen Check

A human can't re-listen to 90 minutes after every change. This skill does a first listen automatically, so the author only has to hear a short list of moments with timestamps.

```bash
.venv/bin/python .claude/skills/listen-check/scripts/listen.py books/<slug>                    # all chapters, ~6x real time
.venv/bin/python .claude/skills/listen-check/scripts/listen.py books/<slug> --chapters ch03    # one chapter
.venv/bin/python .claude/skills/listen-check/scripts/listen.py books/<slug> --reuse         # re-analyse stored transcripts (after tuning)
```

Each chapter gets `audio/chNN.listen.json`, which the website shows, plus a printed report.

| Check | How | What it catches |
|---|---|---|
| **words** | Whisper (`base.en`) transcribes the chapter; the transcript is aligned word by word with `chNN.txt` | Kokoro skipping, swapping or garbling words; names written wrongly in the transcript |
| **pace** | words per second for every paragraph, from the render cache | a paragraph > 30 % faster or slower than the chapter's median: rushed, dragged or garbled audio |
| **stress** | Kokoro's own phonemes for bare short lines (no tag or beat) | lines with no main stress, which end flat (training cases 01 and 05) |

Filtered out as Whisper noise:
- **Numbers** written as digits ("31" for "thirty-one", "50s" for "fifties").
- **Echoes**: a word repeated where Whisper's 30-second windows meet.
- **Small words**: a dropped "the", "a" or "and".
- **Spelling**: British vs American variants (grey/gray, centre/center).
- **Sound-alikes**, compared by Kokoro's phonemes rather than by letters: won/one, route/root, pale/pail.

**Names are compared by sound.** Whisper spells a name it doesn't know the way it sounds ("Elin" → "Ellen", "Mira" → "mere"). A name passes when what Whisper heard is closer to the glossary pronunciation than to Kokoro's own wrong default. That includes possessives like "Mira's".

| Whisper wrote | Verdict | Why |
|---|---|---|
| mere, mirror (Mira) | pass | sounds like MEER-uh |
| Ellen (Elin) | pass | sounds like EL-in |
| Myra (Mira) | flag | that's Kokoro's default, MY-ruh |
| Eline (Elin) | flag | that's the wrong ih-LIN |

**Second opinion, built in.** Every word flag is re-checked automatically. The slower `small.en` model transcribes that paragraph's own clean audio from the render cache, and the flag is kept only if both models agree. Dismissed flags stay in the JSON under `dismissed`, for transparency.

**Limits.** Whisper prefers familiar words and spellings. If it writes "Mira" correctly, Kokoro said something close to "Mira", but not necessarily with the right stress. So a clean report means no gross errors, not perfect pronunciation. Names are still best checked by ear once, when the glossary is made (narration-prep).

## Workflow

1. Run it after `kokoro-narrate`, before `audiobook-assemble`.
2. The report only contains flags both models agree on. Tell the author the remaining flags as **timestamps** to listen to, such as "ch04 3:12: expected 'sequestered', heard 'sequenced'". Don't claim a problem is real until it's confirmed by ear or by both models.
3. **Every confirmed problem becomes a training case** (see `training/README.md`). Cut the clip automatically:
   `listen.py books/<slug> --clip ch04 190 197 -o training/NN-slug.heard.wav`. Then fix it in the right skill: a pronunciation goes to narration-prep's glossary or rules, a phrasing problem to speech-flow.
4. Re-render the paragraph, re-run the check on that chapter, then assemble and publish.

## How the skills improve (shared loop)

- **Author reports** → training case → before/after audio → the author picks → a rule in the right skill.
- **listen-check reports** → confirmed by a second model or by ear → a training case the same way.
- **Rule tests**: every lesson that the speech-flow scanner can detect has a test in `training/rule-tests.yaml`. Run `python3 .claude/skills/speech-flow/scripts/test_rules.py` after changing any rule. All tests must pass before publishing; the website shows the results.
- **Rule proposals**: when two or more cases share a pattern that no rule covers yet, Claude drafts a rule, a scanner check and a test, and adds it to `training/proposals.md` with status `proposed`. It becomes a rule only when the author approves it. Taste ("does this pause feel right?") always stays with the author.
