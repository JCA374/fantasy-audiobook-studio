---
name: fantasy-novella
description: "Plan and draft a short fantasy novel / novella (10–20k words) destined for audiobook, from idea to finished manuscript. Use when the user wants to start a new book, write a fantasy story, build a fantasy world or magic system, outline or draft chapters, check progress, or asks 'what's next' on a book in books/. Orchestrates the vendored author-toolkit skills (fiction-workshop, story-structure, character-archetypes, prose-mechanics, avoid-ai-writing) and hands off to the audio pipeline."
---

# Fantasy Novella

This is the hub skill for the whole pipeline. It owns the project layout, sizing, fantasy-specific worldbuilding and drafting. For editing it delegates to the vendored skills instead of repeating them.

## Pipeline

| # | Stage | Skill | Output (`books/<slug>/…`) |
|---|---|---|---|
| 0 | Seed (idea → material) | `story-seed` | `seed.md` |
| 1 | Story bible | **this skill** + `fiction-workshop` Stage 1 | `story-bible.md`, `glossary.md` |
| 2 | Structure | `story-structure` (Map mode) | `outline.md` |
| 3 | Draft | **this skill** | `chNN.md` |
| 4 | Edit | `fiction-workshop` personas → `prose-mechanics` → `avoid-ai-writing` | revised `chNN.md` |
| 5 | Reader test | `fiction-workshop` Stage 3 (fresh subagent) | summary in `status.md` |
| 6 | Speech flow | `speech-flow` (punctuation & phrasing for the ear) | revised `chNN.md` |
| 7 | Audio prep | `narration-prep` | `audio/chNN.txt` |
| 8 | Narrate | `kokoro-narrate` | `audio/chNN.wav` |
| 9 | Listen check | `listen-check` (automatic listener: Whisper vs script, pace, stress) | `audio/chNN.listen.json` |
| 10 | Package | `audiobook-assemble` | `audio/chNN.mp3`, `audio/<Title>.m4b` |

**At session start**:
1. List `books/`.
2. Read the active book's `status.md` and `story-bible.md`.
3. Report which stage the book is in and the next step.

**At session end**: update `status.md` with the stage, what was done and any open questions. That file replaces fiction-workshop's `sessions/` notes for this project.

Respect the vendored skills' stopping points. Hand back to the author between stages; don't run straight from bible to finished draft unless asked.

## Project layout

Decisions recorded in the bible (spelling variant, tone, rejected ideas) override this skill's generic advice. `books/collection.md` holds notes shared across the series (premises, house style); per-book facts go in that book's bible.

Keep it flat: one folder per book, one `audio/` folder inside it, nothing else. Don't create extra subfolders.

```
books/collection.md    series premises + house style (British spelling, tone)
books/<slug>/
  status.md            stage, word count per chapter, open questions
  seed.md              Stage 0 ideation from story-seed: chosen premise, options, rejected, parked
  book.yaml            title/author/chapter titles + `narration:` voice settings
  story-bible.md       from fiction-workshop/assets/story-bible-template.md; magic system goes in a
                       "Magic" section (see references/fantasy-worldbuilding.md), not a separate file
  glossary.md          every invented word: | Term | Sounds like | Phonemes | Notes |
  continuity.md        append-only facts established in the draft (chNN | fact)
  outline.md
  ch01.md, ch02.md …   the manuscript, one file per chapter
  audio/               chNN.txt scripts, chNN.wav/.mp3, <Title>.m4b, auditions, hidden .cache/
```

## Stage 1: Story bible (fantasy additions)

If the book has no `seed.md` and the author only has a one-line idea, run `story-seed` first. If `seed.md` exists,
build the bible from its chosen material (*Author said* and the kept sections) and don't re-ask what it already
answers. Never copy *Suggestions not yet chosen* or *Parked* into the bible.

Follow fiction-workshop's Stage 1 questions and template. In addition:
- Load `references/fantasy-worldbuilding.md` and fill the bible's Magic section.
- Start `glossary.md` **as soon as the first name is invented**. Ask the author how each name is pronounced ("sounds like" column) while the decision is fresh; narration-prep needs it later.
- Keep the world small. A novella has room for **one** magic system, **2–4 named locations** and **3–5 characters who matter**. Push back on epic-scale worldbuilding the story won't use.

## Stage 2: Sizing the outline

Target length: ask the author, default **15k words**. Chapters of about 2,000–2,500 words (13–17 min of audio each) → **6–8 chapters**. Then:
- Run `story-structure` Map mode. Its beat percentages apply directly: in a 15k book the Inciting Event lands around 1,800 words (≈ ch1) and the Midpoint around 7,500 (≈ ch4).
- Novella compression: **one** POV (two at most), one main subplot, and the Inciting Event in the first chapter.
- `outline.md` gets one section per chapter with: target words, POV, goal / conflict / turn, the beat it carries, and the closing hook.

## Stage 3: Drafting a chapter

For each chapter, in order. **One chapter per turn** unless the author asks for more.
1. Read `outline.md` (this chapter's section plus the next one), `story-bible.md` (style/voice notes), `continuity.md` and `glossary.md`.
2. Load `references/writing-for-the-ear.md`. These books are heard, not read.
3. Optional: use fiction-workshop's brainstorm → curate step for the chapter's key moments if the author wants to be involved.
4. Write `chNN.md`: an `# Chapter N: Title` heading, then prose. Stay within ±15% of the target word count (check with `wc -w`).
5. Append new facts to `continuity.md` (names, injuries, objects, who knows what, time of day or season) and new terms to `glossary.md`. Mark any missing pronunciations `?` and ask the author.
6. Run `avoid-ai-writing` in **detect** mode on the chapter and fix the clear hits yourself. Generated fiction drifts into AI-isms (tapestries, "a testament to", tidy triplets, every scene ending on a reflective one-liner).
7. Update `status.md` and stop. Report the word count, one line on what happened, and any questions.

## Stage 4–5: Editing

Order matters (it comes from fiction-workshop):
1. developmental pass on the whole book
2. character consult and continuity audit
3. line edit
4. `prose-mechanics` audits
5. final `avoid-ai-writing` pass
6. a **read-aloud pass** using `references/writing-for-the-ear.md` as the checklist
7. reader test

Only then move to audio.
