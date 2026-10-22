---
name: manuscript-review
description: "Review-and-rewrite loop for a book's chapters: an independent reviewer (fresh subagent that never edits) finds issues, the writer fixes them, an objective gate checks word count, clipped dialogue and how much changed, and the loop stops when the gate passes and no must-fix issue is open, or at a hard cap of 3 rounds. Brakes keep it from rewriting the story: locked outline, an issue ledger, a change budget per round. Use after drafting each chapter (fantasy-novella stage 3), for the whole-book loop (stages 4–5), or when the author asks to review, critique, tighten, polish or loop on a chapter."
---

# Manuscript review

Two roles, kept apart:
- **Reviewer:** a fresh `general-purpose` subagent. It reads and reports, and **never edits**.
- **Writer:** you, the main agent. You apply fixes and keep the ledger.

They are kept apart because an agent that reviews its own draft agrees with itself.

The loop must end, and the story must still be the outline's story when it does. Everything below serves those two goals.

## Files
- `books/<slug>/review.md`: the **issue ledger**, one table for the whole book (format below). It is committed with the book.
- `books/<slug>/.review/chNN.rN.md`: a snapshot of each round, written by the gate (git-ignored). r0 is the draft.
- `pipeline.log.jsonl`: gate records (`stage: manuscript-review`). verify.py turns them into stage 4 PASS.

## The gate

```bash
.venv/bin/python .claude/skills/manuscript-review/scripts/gate.py books/<slug> chNN          # log a round
.venv/bin/python .claude/skills/manuscript-review/scripts/gate.py books/<slug> chNN --dry    # check while fixing
.venv/bin/python .claude/skills/manuscript-review/scripts/gate.py books/<slug> chNN --close  # final verdict
```

Hard checks:
- words within ±15% of the outline target
- no clipped-dialogue hits (speech-flow cases 07 and 10):
  - at most 1 spoken line in 20 may be two words or fewer (one is always allowed)
  - at most 1 in 10 may be clipped (two are always allowed)
  - no two terse lines in a row
- **change budget:** at most 25% of the words may change in round 1, and at most 10% in each later round
- at most 3 rounds

It also reports other speech-flow candidates, AI-ism words, open must-fix issues, and **drift** from the draft (a warning above 35%).

## Chapter loop (stage 3, after each chapter is drafted)

```
gate (r0 = draft) → reviewer FULL → writer fixes → gate (r1) → reviewer VERIFY → [fixes → gate (r2) → VERIFY …] → gate --close
```

1. Run the gate once on the draft. This writes r0.
2. **Reviewer, full mode** (prompt below). Append its issues to `review.md` with status `open`. Give `plot` and `rules` issues
   status `queued` straight away (see brakes).
3. **Fix**, in this order:
   - gate failures
   - every `must`
   - `should` items, in round 1 only
   - never `nit` (log them with status `nit`). In the first dry run (*The Worst Liar* ch08) the one regression came from a
     nit fixed anyway: "back door" became "kitchen door" and broke an image carried from ch05 to ch07.

   Mark each row `fixed` or `wontfix: <reason>`. Check with `--dry` before logging the round, and keep inside the change budget.
4. Run the gate. This logs round N.
5. **Reviewer, verify mode.** It checks that the open issues are fixed and that the fixes broke nothing. It may raise *new*
   issues only at `must` severity.
6. **Stop** when the gate passed and no must-fix issue is open: run `--close`, and the chapter is done.
   Otherwise go back to 3, unless this was round 3. At round 3, run `--close` anyway: it logs `capped`. Copy the open
   issues into `status.md` under *Open questions* for the author, and move on. **There is no round 4.**

A clean draft can finish in one round. The usual case is 1–2 rounds.

## Book loop (stages 4–5, once every chapter exists)

1. Run the existing fresh-reader tests in parallel: fiction-workshop Stage 3 (reader test), `world-rules` rule reader test, and a
   developmental read of the whole book. Give each of them the `queued` rows from `review.md` to judge.
2. Structural fixes (plot, rules, who knows what) are allowed **only here**. The outline, bible and `continuity.md` are updated
   to match first, then the chapters. Every chapter that changes goes through the gate again (`--dry`, then one logged round and
   `--close`). The change budget still applies per round. A chapter that needs more than 25% changed means a re-plan:
   ask the author, unless the author said "make all decisions" (book.yaml/status.md). In that case record the decision.
3. Run one re-read by fresh readers. **At most 2 book rounds.** Anything still open goes to `status.md`.

## Brakes (why the loop ends)

1. **Story lock.** In the chapter loop the outline beats, the bible's numbered rules and the facts in `continuity.md` are
   fixed. A reviewer issue in category `plot` or `rules` is **never applied** in the chapter loop. It is `queued` for the book loop.
   A `continuity` issue is fixed by making the chapter match `continuity.md`, never the other way round.
2. **Ledger memory.** The reviewer sees `review.md` and may not re-raise a row that is `fixed`, `wontfix` or `nit`. Without
   this, two reviewers can argue over the same sentence forever.
3. **Change budget.** The gate measures the share of words changed per round. A round that goes over budget fails: restore the snapshot
   (`.review/chNN.rN.md`) and apply only the ledger's fixes.
4. **Severity filter.** Round 2 onward only accepts new `must` issues, so the bar for raising an issue goes up each round.
5. **Hard caps.** 3 chapter rounds and 2 book rounds. When a loop hits its cap, the open issues go to the author.
6. **Objective stop.** The loop stops on the gate result and the count of open must-fix issues, never on a reviewer's 1–10 score
   (those scores drift).

## Ledger format (`review.md`)

```markdown
# Review ledger: <Title>

Statuses: open · fixed · wontfix: <reason> · queued (plot/rules → book loop) · nit (logged, not applied)

| ID | Ch | Rd | Cat | Sev | ¶ | Issue | Status |
|---|---|---|---|---|---|---|---|
| ch03-1 | ch03 | 1 | dialogue | must | 20 | "Who?" / "Me." two terse lines; Nell would say why she is asking | fixed |
| ch03-2 | ch03 | 1 | plot | should | 33 | Why doesn't Gran tell the Reeve? | queued |
```

IDs are `chNN-<n>`, numbered across all of the chapter's rounds. `Rd` is the round in which the issue was raised. The gate counts
rows with `Sev = must` and `Status` starting with `open`.

Categories: `plot` `rules` `continuity` `character` `dialogue` `clarity` `ear` `prose` `ai-ism`.

Severity:
- **must**: a listener would be confused, a rule or fact is contradicted, a gate rule is broken, or the line is
  plainly bad (an AI-ism, a filler two-word line).
- **should**: it would be clearly better.
- **nit**: taste.

## Reviewer prompts

Spawn with `Agent` (`subagent_type: general-purpose`). Pass file **paths**, not pasted text, and nothing about how the
chapter was written. The reviewer only reads (it uses Read and Skill, not Edit or Write).

**Full mode (round 1):**

> You are an independent editor reviewing one chapter of a fantasy novella that will be **heard** as an audiobook, not read.
> You did not write it. Do not edit any file. Read: `books/<slug>/chNN.md` (the chapter), the `chNN` section of
> `books/<slug>/outline.md`, the style/voice notes and the "Rules of the World" in `books/<slug>/story-bible.md`,
> `books/<slug>/continuity.md`, `.claude/skills/fantasy-novella/references/writing-for-the-ear.md`, and
> `books/<slug>/review.md` (issues already handled. Don't raise them again). Gate output for this round: <paste>.
> Load the skills avoid-ai-writing (detect mode only), prose-mechanics, and fiction-workshop's line-editor and
> character-consultant personas. Look for:
> - what a listener would miss or mishear
> - dialogue that is filler, especially lines of one to three words that add nothing only this character would say
> - characters who sound alike
> - contradictions with the rules, continuity or outline
> - AI-isms
> - flat or over-tidy scene endings
>
> Return **at most 12 issues**, the most important first, as table rows:
> `| ¶ | category | must/should/nit | "quote" | why, and what kind of fix (not a rewrite) |`.
> Use category `plot` or `rules` for anything that would change what happens. Those are noted, not fixed, at this stage.
> Then give one line on what works and must not be lost in revision.

**Verify mode (round 2+):**

> You are checking a revision of one chapter. Do not edit any file. Read `books/<slug>/chNN.md`, the previous round's
> snapshot `books/<slug>/.review/chNN.r<N-1>.md`, and `books/<slug>/review.md`. For each row of chNN that was `open` last
> round and is now `fixed` or `wontfix`, say if it really is fixed (or the wontfix reason is fair). Then check whether
> the changes broke anything: a new contradiction, a lost line from "what works", worse rhythm. You may add new issues
> **only at must severity**. Gate output: <paste>. Return `| ID or new | verdict / ¶ | category | must | why |` rows,
> or "none" if there is nothing left to fix.

The "what works" line goes into `review.md` under the chapter's rows as `> keep: …`. Revisions must keep it.

## Stopping point

After a chapter's `--close`, update `status.md` with the rounds, the change from draft to the final version (the gate's `drift`)
and anything `queued` or `capped`. Then follow fantasy-novella's stopping rule (one chapter per turn unless the author asked for more).
