---
name: narration-prep
description: "Convert finished manuscript chapters into TTS-ready narration scripts for Kokoro: strip markdown, spell out numbers and symbols, apply glossary pronunciations as phoneme markup, add scene-break pauses and optional character-voice tags. Use when preparing a book or chapter for audio, fixing mispronounced names, building the pronunciation glossary, or before running kokoro-narrate."
---

# Narration Prep

> From another project: run these commands through the **voice-text** skill's launcher (`voice.sh <command> voice/<slug>`); there `books/<slug>` = `voice/<slug>`.

Turns `books/<slug>/chNN.md` into `books/<slug>/audio/chNN.txt` (format: see the `kokoro-narrate` skill). You do this conversion yourself, reading and writing the files. The manuscript is never modified; it stays the source of truth. If a chapter is edited later, regenerate its script; unchanged paragraphs stay cached and won't re-render.

## 1. Pronunciation glossary first

`books/<slug>/glossary.md` lists every invented name and word. Kokoro mangles many of them. For example "Ys'tharra" → /hˈaɹə/, which drops the first syllable: apostrophes and unusual vowel clusters are the worst. For each glossary entry:

```bash
.venv/bin/python .claude/skills/narration-prep/scripts/g2p.py "Ys'tharra" "Is tharra" "Iss THAR uh"
```

Use `--say "…"` to render `say.wav` so the user can hear it.

1. Pick the respelling that matches the author's "sounds like" note.
2. Join it into one word: remove the spaces and extra stress marks, keeping a single primary `ˈ` before the stressed syllable.
3. Record it in the glossary table:

```markdown
| Term | Sounds like | Phonemes | Notes |
|------|-------------|----------|-------|
| Ys'tharra | iss-THAR-uh | ɪsθˈɑːɹə | the river goddess |
```

If the author never gave a "sounds like", ask the author. Don't invent one. Names that Kokoro already says correctly get the phonemes column filled with `ok` and no markup.

## 2. Convert each chapter

The mechanical rules below are implemented in `scripts/prep.py` (`.venv/bin/python .claude/skills/narration-prep/scripts/prep.py books/<slug>`). Run it, then read the diff of each script and handle what it can't: italics that carry meaning, numbers that need context, anything the author flagged.

Rules, in order:

1. **Heading** → spoken title paragraph: `Chapter Three. The Drowned Bell.` followed by `[pause 1.0]`.
2. **Strip markdown**: `*italics*`/`**bold**` markers, links, HTML, footnotes. If italics carry meaning (telepathy, a letter, a foreign word), make that clear in words or leave a note for the author; the voice can't do italics.
3. **Scene breaks** (`***`, `* * *`, `#`, `---`) → `[pause 1.5]`.
4. **Numbers and symbols** → words: "1,204" → "twelve hundred and four", "3rd" → "third", "&" → "and", "—" stays (Kokoro pauses on it), "…" → "...".
5. **Abbreviations** → spoken forms: "Mr." → "Mister", "St." → "Saint" or "Street" depending on context.
6. **Glossary names** → wrap **every** occurrence, including possessives, in markup: `[Ys'tharra](/ɪsθˈɑːɹə/)`. For a possessive, put the markup on the name and keep the 's outside: `[Ys'tharra](/ɪsθˈɑːɹə/)'s`.
7. **Long paragraphs** (> ~120 words): split at a natural sentence boundary. This keeps the per-paragraph cache granular.
8. **Character voices**: only if `narration.characters` in `book.yaml` maps characters. Tag a paragraph `[[Name]]` only when it is **pure dialogue** by that character. If a paragraph mixes narration and speech ("Run," Mira said, grabbing his arm), leave it with the narrator; splitting mid-sentence sounds choppy.

## 3. Check

- Grep each script for leftover `*`, `#`, `_`, digits and `[` without a matching `](/`.
- Word count of script ≈ word count of the chapter (± 5 %).
- Hand off to **kokoro-narrate**. Suggest a `--sample` of the most name-dense paragraph first.

## Learned rules

Rules learned from the author's examples in `training/` (see `training/README.md` and `training/cases.md`). They take precedence over the general rules above. When the author reports something that sounds wrong:
1. Save the original text as `training/NN-slug.md` with a note on what sounded wrong and the book/chapter it came from.
2. Write `NN-slug.before.txt` with the current rules and render it; write `NN-slug.after.txt` with the fix and render it (`narrate.py --script … --speed 0.95`). Try several variants if the first fix doesn't sound right.
3. When the author approves, add the rule below, mark the case `fixed` in `cases.md`, and re-check every earlier case's `.after.txt` still follows all the rules.

- **Short questions (case 01).** A quoted question of three words or fewer often gets no main stress from Kokoro (check with `g2p.py`: only `ˌ` marks, no `ˈ`), so it ends flat and sounds cut off. This holds whether the line stands alone or has a tag or beat: `"Why?" It came out sharper…` is still `wˌI?`, because the context doesn't change the question's stress. Put `(+2)` on the word the speaker leans on and double the question mark: `"[Can](+2) I??" He sat up a little.` (`prep.py` does this for the last sentence of any quote; it skips trailing-off `...?` questions and questions containing a glossary name). A beat after the line still helps, since it gives the listener the feeling, but it doesn't replace the markup.
- **Short question before a beat (case 09).** When a marked short question opens a paragraph and an action beat follows, put the question in its own script paragraph and the beat in the next one: `"[Why](+2)??"` / `It came out sharper than she meant.` Voiced alone, it ends more like a question than the same markup inside the paragraph. A tag (`"[How](+2)??" said Quill.`) stays in place. `prep.py` does this; the manuscript is unchanged.
