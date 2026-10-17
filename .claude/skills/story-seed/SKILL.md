---
name: story-seed
description: "Grow a one-line book idea into material to work with before the story bible: premise twists, protagonist options, what the magic implies, a pool of set pieces, candidate endings and a theme, cut down to novella size. Use when the user wants to start a new book from a premise, brainstorm or develop a story idea, asks 'what could this story be', or picks one of the premises in books/collection.md. Runs before fantasy-novella Stage 1 and writes books/<slug>/seed.md."
---

# Story Seed

Stage 0 of the pipeline. fiction-workshop's Stage 1 starts with "Core premise/logline?". This skill is how the
author gets to a good answer. It is **divergent first, then convergent**: generate plenty, let the author choose,
then cut to what a 10–20k-word audiobook can hold.

Output: one file, `books/<slug>/seed.md` (flat layout, no subfolders). fantasy-novella Stage 1 reads it and fills
`story-bible.md` from the chosen material only.

## The one rule: keep the author's words apart from yours

`seed.md` records what the author **actually chose or said**, in their words where possible, separately from what
Claude suggested. Suggestions the author hasn't picked stay under *Suggestions not yet chosen*. Ideas they turn down
go under *Rejected*, with the reason. Don't fill gaps the author left open on purpose, and don't promote a
suggestion to a decision because they didn't object. This stops the bible being padded with ideas nobody chose.

## Flow

One step per turn. Stop after each step and let the author pick, combine or throw things out. Their reasons ("too
dark", "I like her") calibrate the next round, so note them. If the author says "go with your proposals", record
that as a decision and move on.

### 1. Premise
Offer the unused premises in `books/collection.md` (skip the ones already written as books), or take a new one.
Pick a slug and create `books/<slug>/seed.md` from the template below.

### 2. Premise ladder: 6–10 twists
Run the What-if ladder and SCAMPER from `../fiction-workshop/references/brainstorming.md` on the premise itself.
Vary the axis: who the protagonist is, whose side we're on, the scale (one street vs one kingdom), the genre blend
(heist, courtroom, cosy mystery, tragedy), what the magic really is. One or two lines each. Include at least one wild
option and one quiet, small one. The author picks one or combines several, and that becomes the **logline**.

### 3. Protagonist: 3–4 candidates
For each: who they are in one line, **want / need / wound / lie**, and why *this* premise hurts *them*
specifically. Run `character-archetypes` Audit mode on the shortlist and flag clichés. Once the author picks one,
sketch the antagonist or opposing force and 1–3 supporting roles by *function* (mirror, obstacle, ally, cost).

### 4. Magic implications
Take the premise's single power and push it out rather than adding more:
- Who profits from it, who gets hurt, who polices it, what is illegal?
- What breaks in daily life (trade, law, family, death) because it exists?
- What is the worst misuse, and the kindest?
Then draft answers to the Sanderson checklist in `../fantasy-novella/references/fantasy-worldbuilding.md`
(cost, hard limit, counter). Offer them as options. Cost is the author's call, and "no personal cost" is a valid answer.

### 5. Set pieces, endings, theme
- **Set-piece pool, 10–15 moments** the story could contain: images and confrontations a listener would remember.
  Mark which ones show the magic's rules early (needed if the climax uses magic).
- **2–3 candidate endings**: happy, bittersweet and dark, or along other lines. For each, say what it costs the
  protagonist. **Ask which ending the author wants before any outline exists.** (Book 2 changed course mid-way with
  "I want a happy ending"; finding that out at Stage 0 is cheaper.)
- **Central question** (the theme as a question the ending answers) and 1–2 recurring motifs that work by ear (a
  sound, a phrase, an object).

### 6. Novella fit check
Cut to the hub's limits: **one** magic system, **2–4 places**, **3–5 characters who matter**, one POV (two at most),
one subplot. Everything cut goes under *Parked*, with a line on why. That keeps ideas around for a later book without
bloating this one. Give each kept place a sensory signature (one smell, one sound, one texture).

### 7. Ear check and hand-off
- Draft names using the Names rules in `fantasy-worldbuilding.md`: distinct first sounds and syllable counts.
  Ask how each is pronounced and start `glossary.md` (`| Term | Sounds like | Phonemes | Notes |`).
- Read the logline aloud in your head. If it takes more than one breath, tighten it.
- Hand off: "Seed done. Next: fantasy-novella Stage 1 (story bible)." Create a `status.md` with stage `0 Seed: done`.

## `seed.md` template

```markdown
# Seed: <working title>

## Premise
- Source: <collection.md premise N / author's new idea>
- Logline (chosen):

## Author said
<!-- decisions in the author's words, dated; this is the authority -->
- YYYY-MM-DD: "…"

## Protagonist
- Name / one line:
- Want / need / wound / lie:
- Opposition:
- Supporting roles (by function):

## Magic implications
- The power:
- Who profits / who is hurt / who polices it:
- Cost / hard limit / counter:

## Places (2–4, with smell / sound / texture)

## Set pieces (kept)

## Ending (chosen) and central question
- Ending:
- Central question:
- Motifs:

## Suggestions not yet chosen
<!-- Claude's options still open; NOT decisions -->

## Rejected
<!-- idea, and the author's reason -->

## Parked
<!-- cut for size; possible material for another book -->
```

## Stopping points

- After every step: wait for the author's picks.
- Don't start the story bible, outline or any prose here. That's fantasy-novella's job.
- If the author already has a full premise, protagonist and ending, skip to step 6 (fit check) or straight to
  fantasy-novella Stage 1.
