---
name: world-rules
description: "Make a book's magic and world logic airtight before and while it is written: a numbered rule set stress-tested against the book's law, money and ownership, a reveal ladder (which chapter shows which rule), a rule audit per chapter, a reader test that checks the rules, and a revise step when rules change. Use when building a magic system or world rules, when the author says the logic isn't clear, how does X work, finds a plot hole, loophole or inconsistency, asks for a reveal ladder or rule audit, or when rules change in a finished book. Called by fantasy-novella at stages 1, 2, 3/4 and 5."
---

# World Rules

The hub's Magic section (Sanderson: cost, limit, counter) says what the magic *is*. This skill makes sure every
scene obeys it, and that the reader learns each rule before the climax relies on it.

**Why it exists.** Two of the first three books had their rules fixed after drafting. *The One in the Chair* got new
afterlife rules in its second edition. *Second-Hand Dragons* needed a pass over all 13 chapters (2026-10-20) after the
author said "the logic for how fire works or how the Reckoning works isn't clear". None of its contradictions came
from the magic alone. Each one came where the magic met the book's **law, money or ownership**: pledging vs selling,
who keeps the price, when ownership passes, a bought flame vs a bought dragon. The worked example is in
`references/example-second-hand-dragons.md`. Read it before Build.

Everything goes into the book's existing files: `story-bible.md`, `outline.md`, `continuity.md`, `status.md`.
No new files. Stop after each mode and hand back to the author.

## 1. Build (stage 1, after the bible's Magic section)

Write a `### Rules of the World` section in `story-bible.md`:
- **Numbered rules**, one idea each, a bold one-line statement followed by the detail. Group them under bold topic
  lines (the magic itself / its users or creatures / the institutions: law, trade, guild, family). Number straight
  through the groups so every scene note and audit can cite "rule 6".
- The author's words where they gave them. Claude's fillers are marked *(proposal)*.
- Open with one italic line: the reader never hears the list. It's for the author, so every scene obeys the same rules.

Then run the **stress test**. Put every question to the rules. Answer the ones the bible already settles, and give
the rest to the author as short options (2–3 each, recommendation first). Log each choice in the Decisions Log, marked author or proposal.

1. **Transactions.** What happens to the magic (or the magical thing) when it is given, sold, bought, stolen,
   lent, pledged or mortgaged, inherited, redeemed, and given away after being bought? Is "not paying" the same
   as "giving"? Dragons: pledging is not selling, redeeming is not buying, and a bought dragon given away is warm again.
2. **Chains.** Does the effect pass on (a copy of a copy, a flame lit from a flame)? Does handing it on change it?
   Is there a cure, and what exactly is it? Dragons: cold catches; handing a cold flame on doesn't warm it; put it out and relight it from a given flame.
3. **Ownership and timing.** When exactly does it change hands (signature, payment, a date, noon)? Who owns it in
   between, and what can they still do with it? The climax usually happens in that gap.
4. **Money.** Who gets paid, who keeps the surplus, what is guaranteed, what does the loser get? Every price
   spoken on the page has to agree with these answers.
5. **Each institution in the bible** (law, guild, market, church, family). How does it use, fear, tax or police the
   magic? Where does its law contradict the magic's rule? Pick which one wins, and say why.
6. **Source and upkeep.** What feeds the magic (or the creature)? What happens when the supply stops? Who knows?
   Dragons: a dragon can't live on its own fire; a given hearth kept beside it stops the leak.
7. **Loopholes.** For every character who matters, and for the climax: "why doesn't X just …?" (buy it back, steal
   it, give it away, wait, ask someone else, use the law). Each one gets a rule that closes it, or a reason in
   character, and a line on where the reader learns it.
8. **Exceptions.** Is anything or anyone outside the rules (an old law, a special case, a character the reader
   might think is covered)? Write it down as its own rule. Dragons rule 17: Quill was never a pledge.

Done when every question is answered or explicitly parked, and the rules don't contradict each other.

## 2. Ladder (stage 2, with story-structure Map mode)

Add `### Reveal ladder (what the reader learns where)` under the rules:

```markdown
| Ch | Rules | How |
|----|-------|-----|
| 01 | 8, 11, 12 | Dragon size; Mrs Hobb's terms (forfeit, the Reckoning, highest bid) |
```

Checks:
- Every rule the climax uses appears **at least one chapter earlier, in action** (a scene, not a lecture). Two
  showings are better than one for a listener, who can't flip back.
- No chapter uses a rule before it has been revealed.
- Spread it out: no more than 3–4 new rules a chapter, and none told as a list.
- The closing chapters show the rules "at work" or "paid off", citing their numbers.

Then each chapter's section of `outline.md` gets a line `Rules: 3, 4 (shown: …)`.

## 3. Audit (after each drafted chapter; the whole book at stage 4)

Read the chapter against the rules, the ladder and the bible's Knowledge States table. List every event that
touches a rule, then flag:
- **Contradicts rule N.** Quote the line.
- **Too early.** A rule used before its ladder chapter.
- **Knowledge.** A character acts on something they don't know yet, or ignores something they do.
- **Loophole.** Opens a "why didn't they just …?" that no rule or character reason answers.
- **Numbers.** A price, date or count that disagrees with the rules or with `continuity.md`.

Fix the clear cases yourself. Bring the rest to the author with options. Rule facts the chapter establishes go into
`continuity.md` as usual (`chNN | fact`). At stage 4, run the audit on the whole book in chapter order, after
fiction-workshop's continuity audit.

## 4. Rule reader test (stage 5, alongside fiction-workshop Stage 3)

Use a fresh subagent that gets **the chapters only**: no bible, outline or ladder. Ask it to:
1. explain each rule of the world in its own words, as a reader understood it;
2. say whether the climax obeys those rules, or seems to break one;
3. list every "why didn't they just …?" it thought of;
4. name any moment where it was confused about who owned, knew or could do what.

Compare its answers with the numbered rules. Every rule it explains wrongly or not at all is a finding, as is
every loophole the bible doesn't close. Put the summary in `status.md` with the general reader test. Fix, then run
the test again with a new subagent if the fixes touched the climax.

## 5. Revise (the rules change after drafting)

1. Rewrite the rules in the bible, with `(revised YYYY-MM-DD)` in the heading, and log the author's choices.
2. Add one `rev` row to `continuity.md` listing every fact that changes, and mark the rows it replaces
   `(superseded by revN)`. Don't delete them.
3. Use the ladder to list the chapters that show or use each changed rule. Audit those chapters (mode 3) and fix them.
4. Run the rule reader test again (mode 4).
5. Audio: every edited chapter goes through stages 6–10 again; `verify.py` shows which are STALE.

For a full second edition, follow "Revising a finished book" in `site/content/pipeline.md`; this mode is its rule step.
