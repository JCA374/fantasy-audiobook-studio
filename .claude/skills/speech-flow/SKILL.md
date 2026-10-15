---
name: speech-flow
description: "Check a manuscript chapter for punctuation and sentence shapes that trip a TTS narrator or a listener: misplaced commas, dashes that never close, italics that vanish in audio, bare short questions, run-on sentences, pronouns pointing too far back, contradictions. Use before narration-prep, when the author says a passage sounds wrong or doesn't flow, or asks for a read-aloud / punctuation / flow check on a chapter or book."
---

# Speech Flow

A listener can't see punctuation, re-read a sentence or notice italics. Kokoro pauses on every comma and dash and reads a sentence's pitch from its punctuation. This skill finds the spots where the written text and the heard text come apart, and fixes them **in the manuscript** (`books/<slug>/chNN.md`), so every later render benefits.

Pipeline position: after editing, **before** `narration-prep`. Narration-prep then only does mechanical conversion.

## 1. Mechanical scan

```bash
python3 .claude/skills/speech-flow/scripts/scan.py books/<slug>/ch01.md   # several chapters OK
```

It prints candidates by paragraph number (¶, heading excluded). They are only candidates. Dismiss any that read fine aloud, such as a deliberate rhythm or an appositive dash tail ("— dark wood, a cushion…").

| Check | Why it matters by ear |
|---|---|
| italics-without-cue | Italic thoughts, stamps and voices become plain narration. "hear it as *I know, love*" is heard as "as I know". Fix it with a cue in words: "hear it say: …", "the stamp read: …". |
| comma-before-and | "She looked up at him, and allowed…": one subject with two verbs shouldn't take a comma, and Kokoro pauses on it in the wrong place. |
| short-question | A question of three words or fewer has no stressed word to rise from, so it ends flat (training case 01). Add a beat or tag after it. |
| unclosed-dash | A dash opens an aside, then a new clause runs on. The listener loses the main thread. Close it, or split the sentence. |
| long-sentence (> 35 words) | Hard to follow by ear. Split it where the subject changes. |
| comma-run (≥ 6 commas) | Too many pauses in a row sounds choppy. Keep the run only if the choppiness is intended. |
| semicolon | Kokoro reads it as a comma, so the clauses blur together. Use a full stop instead. |
| interrupter-without-commas | "had by all accounts been": the voice has nowhere to breathe. Put commas around the interrupter. |

## 2. Listening read-through (the script can't do this)

Read the whole chapter as a listener hearing it once, at narration speed. Look for:
- **Far referents**: "it", "any", "that", "them" pointing more than a sentence back, or across dialogue. Repeat the noun instead.
- **Contradictions that print hides**, for example "None of them ever did, mostly".
- **Garden paths**: a sentence that parses one way until its last words, as in "hear it as I know…".
- **Who is speaking**, using the dialogue rules in `fantasy-novella/references/writing-for-the-ear.md`.
- **Lost emphasis**: a line whose meaning depends on italic stress. Most spoken emphasis ("A *teapot.*") survives without it. Fix a line only when it doesn't.

## 3. Report, then fix

1. Give the author a table: ¶, what's wrong as heard, the current text, and the proposed rewrite. Order it by severity: misheard meaning first, then wrong pauses, then polish. Keep rewrites minimal and in the book's voice. This is punctuation and phrasing, not a line edit.
2. Apply only the fixes the author approves to `chNN.md`. Copy the old version to the scratchpad first.
3. Re-run `narration-prep` on the chapter, then `kokoro-narrate`. Only the changed paragraphs re-render.
4. **Training**: save each fix that taught something new as a case in `training/` (see `training/README.md`). Include before and after audio of the affected paragraphs. Add any recurring pattern to the check table above. If it can be detected mechanically, add it to `scan.py` as well.
