# How the pipeline works

The goal is a repeatable way to go from an idea to a finished, chaptered audiobook of a short fantasy novel (10–20k words, about 1–2 hours of audio). The whole thing runs in [Claude Code](https://claude.com/claude-code) on a CPU-only laptop. Each stage is handled by a **skill**: a folder in `.claude/skills/` with a `SKILL.md` that tells Claude how to do that job, plus any scripts it needs. The author makes the creative decisions; Claude drafts, checks and runs the tools; the scripts do the mechanical work.

Prefer to watch? There's a [five-minute video](index.html#video) with two narrated hosts walking through every skill, the training loop and one example from chapter 1.

Three rules hold it together:

- **The manuscript is the source of truth.** `books/<slug>/chNN.md` is what gets edited. Narration scripts, audio, the EPUB and this website are all derived from it and can be regenerated.
- **Stop between stages.** Every skill has a stopping point where it hands back to the author. Nothing runs from idea to finished book unattended unless the author asks for it.
- **Everything learned goes back into a skill.** When something sounds wrong, it becomes a training case with before/after audio, and the fix becomes a rule. The next book starts with that rule already in place.

## One folder per book

```
books/collection.md         series premises and house style (British spelling, tone)
books/<slug>/
  status.md                 current stage, words per chapter, open questions
  seed.md                   stage 0 ideas: chosen premise, options, rejected, parked
  book.yaml                 title, author, chapter titles, narration voice settings
  story-bible.md            world, magic, characters, style, decisions
  glossary.md               every invented name: sounds like + phonemes
  continuity.md             append-only facts: "ch08 | the cushion is cold for the first time"
  outline.md                chapter-by-chapter beats
  ch01.md … ch13.md         the manuscript
  cover.py, cover.jpg       the cover, drawn in Python
  audio/                    scripts, renders, mp3s, the .m4b
training/                   "this sounds wrong" examples with before/after audio
site/                       this website's generator
```

The layout is flat on purpose: the author asked for fewer folders, and a flat folder is easier for every skill to find its inputs in.

## Writing

### 0 · Seed
**Skill:** story-seed · **Output:** `seed.md`

The premises in `books/collection.md` are one-liners ("the cartographer", "the debt war"). Before the bible interview can ask for a premise and a hero, there has to be something to choose from. Story-seed generates first and cuts later: 6–10 twists on the premise, 3–4 possible heroes, what the magic does to the world (who profits, who is hurt, what it costs), 10–15 possible scenes, and 2–3 candidate endings. The author picks at each step. Everything is then cut to novella size, and the extra ideas go into a *Parked* list for another book.

`seed.md` keeps the author's words apart from Claude's: *Author said* holds the decisions, while *Suggestions not yet chosen* and *Rejected* hold everything else. The bible is then built from the decisions only.

### 1 · Story bible
**Skills:** fantasy-novella, fiction-workshop · **Output:** `story-bible.md`, `glossary.md`

A question-driven interview fills the bible: premise, world, the one magic system, characters (want, need, wound, lie), places, point of view, tense and tone. Fantasy-novella adds two constraints. The world stays **small**: one magic system, 2–4 named places, 3–5 characters who matter. And the **glossary starts with the first invented name**, with the author's "sounds like" written down while the decision is fresh, because the audio stage will need it.

Decisions the author makes later (who sent the letter, whether the mother moves on) are recorded in a *Decisions* section of the bible, so later sessions don't reopen them.

### 2 · Structure
**Skill:** story-structure (Map mode) · **Output:** `outline.md`

The bible becomes an outline with beats placed by percentage: Inciting Event around 12 %, First Plot Point at 25 %, Midpoint at 50 %, and so on. Each chapter section gets a target word count, its goal / conflict / turn, the beat it carries and its closing hook. The outline also names the **engine**, the reason the plot can't be solved easily, and any open decisions (⚑) for the author.

### 3 · Draft
**Skills:** fantasy-novella, avoid-ai-writing · **Output:** `chNN.md`

One chapter at a time. Before writing, Claude reads the chapter's outline section and the next one, the bible, `continuity.md` and `glossary.md`, plus the *writing for the ear* checklist. After writing, it checks the word count, appends new facts to `continuity.md`, runs avoid-ai-writing in detect mode and fixes clear hits, then updates `status.md`.

### 4 · Edit
**Skills:** fiction-workshop, character-archetypes, prose-mechanics, avoid-ai-writing · **Output:** revised chapters

The order matters: developmental pass on the whole book (does the plot work?) → character and continuity audit → line edit → prose-mechanics audits → a final avoid-ai-writing pass → a read-aloud pass against the *writing for the ear* checklist. Big problems first, so no time goes into polishing sentences that later get cut.

### 5 · Reader test
**Skill:** fiction-workshop (Stage 3) · **Output:** summary in `status.md`

A **fresh subagent** with none of the session's context reads the finished manuscript cold, like a first-time reader, and reports what confused it, what contradicted itself and where it lost interest. On book 1 this found two different characters both called "the archivist", a testimony count that was 36, 35 and 32 in different chapters, and a climax whose legal logic didn't hold. All were fixed before any audio was made.

## Voice

### 6 · Speech flow
**Skill:** speech-flow · **Output:** chapters fixed for the ear

A listener can't see punctuation, can't re-read, and never sees italics. A scanner flags candidates: uncued italics, commas splitting one subject's two verbs, bare short questions, dashes that open an aside and never close it, sentences over 35 words, comma runs, semicolons. Claude then does a listening read-through for what a scanner can't catch: pronouns pointing too far back, contradictions, sentences that sound like they mean one thing until the last word. Fixes are proposed in a table and applied to the manuscript only after the author approves them.

### 7 · Narration prep
**Skill:** narration-prep · **Output:** `audio/chNN.txt`

Each chapter is converted to a script Kokoro can read:

| Manuscript | Script |
|---|---|
| `# Chapter Three: The Supervisor` | `Chapter Three. The Supervisor.` then `[pause 1.0]` |
| `***` scene break | `[pause 1.5]` |
| `*italics*`, `**bold**` | plain text |
| `Mira` | `[Mira](/mˈiɹə/)`: phonemes from the glossary |
| a 200-word paragraph | split at a sentence boundary (keeps the cache granular) |

Pronunciations are tested with `g2p.py`, which shows the phonemes Kokoro would use and can render a test clip. The skill's *Learned rules* section holds rules taught by training cases, such as how to keep a two-word question from ending flat, whether it stands alone or comes with a tag (`"[Why](+2)??" It came out sharper than she meant.`).

### 8 · Narrate
**Skill:** kokoro-narrate · **Output:** `audio/chNN.wav`

[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) is a small open text-to-speech model that runs locally, free, on the CPU. The script is rendered one paragraph at a time, with a configurable pause between paragraphs. Every paragraph's audio is cached under a hash of *voice + speed + text*, so after an edit only the changed paragraphs are re-rendered. A whole book takes about an hour. The voice was chosen by ear from full-chapter auditions: **af_heart** at speed 0.95.

### 9 · Listen check
**Skill:** listen-check · **Output:** `audio/chNN.listen.json`, a list of timestamps to listen to

An automatic first listen. [Whisper](https://github.com/SYSTRAN/faster-whisper), a speech-recognition model, runs locally (about 6× real time, so ~16 minutes per book). It transcribes every chapter, and the transcript is aligned word by word with the script. Words Kokoro skipped, swapped or garbled come back with a timestamp. Two more checks run alongside it: the speaking pace of every paragraph (a paragraph much faster or slower than the rest usually means garbled audio), and the stress of bare short lines and short questions (no stressed word means a flat ending). Each flag is re-checked with a slower, more careful model before the author is asked to listen. Confirmed problems become training cases with the audio clip already cut.

## Package and publish

### 10 · Assemble
**Skill:** audiobook-assemble · **Output:** `audio/chNN.mp3`, `audio/<Title>.m4b`

Each chapter gets a second of silence before and two after, then two-pass loudness normalisation to **−19 LUFS integrated, −3 dBTP** (the ACX audiobook standard), mono 44.1 kHz. The chapters are concatenated into one AAC `.m4b` with chapter markers taken from the real durations, the cover embedded, and title, author and narrator tags. The m4b is what goes on the phone: copied to Google Drive and imported into BookPlayer.

### 11 · This website
**Generator:** `site/build.py` · **Deploy:** GitHub Actions → GitHub Pages

The site is built entirely from the files above: the skill pages from each `SKILL.md`, the book pages from `book.yaml` and the chapters, the improvements from `training/`. The EPUB for Kindle and other e-readers is generated from the same chapters. After any change to text or audio:

```bash
site/publish.sh "what changed"
```

It converts new training audio to MP3, builds the site locally as a check, commits and pushes. GitHub Actions then rebuilds and deploys the site, so the published book, its audio and the process pages always match the repository.

## Making a change after the book is done

1. Edit `chNN.md` (or run speech-flow on it).
2. Regenerate `audio/chNN.txt` with narration-prep.
3. Re-run kokoro-narrate. Only the changed paragraphs re-render, so this takes seconds to minutes.
4. Run listen-check on the chapter.
5. Re-run audiobook-assemble for new MP3s and the m4b.
6. `site/publish.sh "ch01: speech-flow fixes"`.

## Revising a finished book (second editions)

Small fixes go through the change workflow above. A **rewrite** changes the story itself. *The One in the Chair* got one after the first edition was finished: new rules for the afterlife, a mystery with more than one suspect, and a new chapter. A rewrite runs the pipeline again from stage 1, but most stages only touch what changed:

1. **Keep the old edition.** Tag it in git (`v1-first-edition`) and copy it to `books/<slug>-v1/` with `edition` and `superseded_by` in its `book.yaml`. The website lists it under *Earlier editions*.
2. **Rewrite notes.** The author writes down what to keep exactly, what is decided and what is still open. The notes become a making-of page (`rewrite-notes.md`).
3. **Bible and outline first** (stages 1–2). The new rules and the decisions on the open problems go into the story bible. The outline is redone with structure Map mode, and the author approves it before any prose changes.
4. **Rewrite chapter by chapter** (stage 3). Scenes the author froze stay word for word. `continuity.md` gets a *Second edition* section of facts that replace the old ones.
5. **Reader test again** (stage 5). A fresh subagent reads the new edition cold, with questions aimed at the changes: is there more than one suspect, does the new rule feel cheap, do the condition and the ruling agree.
6. **Voice stages as usual** (6–10). The render cache is keyed on each paragraph's text, so only new or edited paragraphs are rendered. A rewrite that keeps two thirds of its sentences costs about a third of a full render.

## The training loop

When the author hears something wrong, they paste the passage and describe what they heard. Claude finds the cause (often visible in the phonemes), writes a *before* script and one or more *after* variants, renders them all, and the author picks by ear. The winning fix becomes a rule in the relevant skill, and every earlier case is re-checked against the new rules. All of it, including the audio, is kept in `training/` and shown on the [Improvements](improvements.html) page.

Three things make this loop partly automatic:

- **The automatic listener** (stage 9) finds problems nobody reported, and turns confirmed ones into cases.
- **Rule tests**: every rule the scanner can check has a before/after test. The tests run before every publish, so a new rule can't silently undo an old fix.
- **Rule proposals**: when the same kind of fix turns up twice, Claude drafts the rule, the check and the test, and the author approves it or not. Whether something *sounds* right stays the author's call.
