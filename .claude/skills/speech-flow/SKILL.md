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
| bare short line | A line of dialogue of six words or fewer, alone in its paragraph with no tag or beat. The listener hears the words but not the feeling, and a short question ends flat (cases 01, 05). Add an **emotion beat**, see below. |
| unclosed-dash | A dash opens an aside, then a new clause runs on. The listener loses the main thread. Close it, or split the sentence. |
| long-sentence (> 35 words) | Hard to follow by ear. Split it where the subject changes. |
| comma-run (≥ 6 commas) | Too many pauses in a row sounds choppy. Keep the run only if the choppiness is intended. |
| semicolon | Kokoro reads it as a comma, so the clauses blur together. Use a full stop instead. |
| interrupter-without-commas | "had by all accounts been": the voice has nowhere to breathe. Put commas around the interrupter. |
| so…that without a breath | "spent so much of their lives arguing about who they were that by the time…": a long *so … that* runs the cause into the result. Put a comma before *that*. The pause matters more here than the grammar rule (case 03). |
| hedge boxed in commas | "not softness, exactly, but attention": three tiny pauses break the contrast apart. Drop the commas around the one-word hedge so the only pause comes before *but*: "not softness exactly, but attention" (case 04). |

**Commas are pauses here, not grammar.** Add a comma where a listener needs a breath (a multi-word interrupter, the turn of a long *so … that*). Remove one where it only chops the rhythm (a one-word hedge, a comma that splits one subject's two verbs). If the two rules seem to conflict, read the sentence aloud and keep the version where the pauses fall on the meaning.

### Emotion beats for short lines (case 05)

The author's rule: when a line is only one or two short sentences, like `"Can I?"`, follow it with a beat that shows the emotion behind it.

```
"You want to appeal it?"
"Can I?" He sat up a little.          <- hope, shown by the body
```

- **Show it through a small physical action**, in under about eight words: *He sat up a little. / She didn't look up. / His hand stopped on the latch.* Avoid adverb tags like "he said hopefully" and named emotions like "he felt hopeful". They tell instead of show, and they sound flat when spoken.
- **Fit the moment.** The beat should carry what the line can't: hope, dread, defiance, relief. If the emotion is already obvious from the line before, a plain tag ("she said") is enough.
- **Pace it.** In a fast back-and-forth, beat about every second or third line (the same rhythm as the dialogue-attribution rule in `writing-for-the-ear.md`). Don't beat every line, or the exchange loses its speed.
- **Skip it** for lines that aren't speech: letters, sign-offs, stamps, signs.

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
4. **Test**: add a before/after pair to `training/rule-tests.yaml` for any new scanner check, then run `python3 .claude/skills/speech-flow/scripts/test_rules.py`. All tests must pass.
5. **Training**: save each fix that taught something new as a case in `training/` (see `training/README.md`). Include before and after audio of the affected paragraphs. Add any recurring pattern to the check table above. If it can be detected mechanically, add it to `scan.py` as well.
