# Status: Second-Hand Dragons (book 3)

**Stage:** COMPLETE 2026-10-19 (re-narrated in af_heart). Audiobook: audio/Second-Hand Dragons.m4b (102.5 min, 13 chapters, cover, -19.4 LUFS) + audio/chNN.mp3; copied to export/Audiobooks/.

**Ch03 revised 2026-10-20** (author: hard to follow who says what; Tansy seemed to live in the back room with the familiars). Now: the house is laid out once (business downstairs, people upstairs; Tansy's small room over the back room), her nightly visit is a routine before bed, every line in the three-way scene is tagged, "smaller than on Thursday" (said on a Thursday) is now "a week ago". Re-narrated and re-packaged.

**Fire and Reckoning logic revised 2026-10-20** (author: the logic for how fire works and how the Reckoning works wasn't clear). `story-bible.md` now holds the author's rule set (rules 1–17: fire, dragons, pledges and the Reckoning) and a reveal ladder. All 13 chapters got light edits so that each rule is shown before the climax uses it. Author's choices: a dragon is fed by a given hearth; the lender keeps the Reckoning price. Fixed contradictions: pledging vs selling (ch2 coal), who gets the money (ch13), the reserve (now Mrs Hobb's to sign, with the shop guaranteed 200 crowns), coal vs asking (ch10), withdrawal (forgiving the debt), Quill (never a pledge), noon (the magistrates' book), and a bought flame vs a bought dragon (ch12). A cold reader test (fresh agent, chapters only) explained every rule correctly; its follow-up flags were fixed (the gift loophole, pinching out the cold flame, Mrs Fennick "couldn't give you away twice", typos). Details in continuity.md `rev3`. Re-narrated (af_heart, changed paragraphs only), listen check clean (the usual this/the and "bot" noise), re-packaged: 107.2 min, 13 chapters, −19.4 LUFS; export/Audiobooks/ updated; verify.py: stages 6–10 PASS.

**Re-narrated 2026-10-19** (af_heart): short questions stressed (case 01) and, where a beat follows, voiced on their own paragraph (case 09). 101.7 min; export/Audiobooks/ updated. Listen check: the same flags as before, nothing new; no stress flags.

Pipeline evidence (`verify.py`, 2026-10-19): stages 0–5 MANUAL (files present); 6 speech flow, 7 audio prep, 8 narrate, 9 listen check, 10 package all **PASS** (content hashes match the current manuscript, scripts, renders and packaged files).

| # | Stage | State |
|---|---|---|
| 0 | Seed | done, `seed.md` |
| 1 | Story bible | done, `story-bible.md` (all proposals approved) |
| 2 | Outline | done, `outline.md` (approved) |
| 3 | Draft | done, 13 chapters |
| 4 | Edit | one revision pass (timeline, numbers, rule clarity, tics; see continuity.md "rev") |
| 5 | Reader test | done (fresh subagent, read cold); findings below, all top five fixed |
| 6 | Speech flow | scan clean except deliberate lines; rule tests 11/11 pass |
| 7 | Audio prep | done, `audio/chNN.txt`; Aldevar has a phoneme override |
| 8 | Narrate | done, af_heart, speed 0.95, 101.7 min. Author 2026-10-19: same voice as The One in the Chair (the first render, published 2026-10-18, used bm_george) |
| 9 | Listen check | done (af_heart). One confirmed pattern: "I want it on the record" heard as "I wanted on the record" (4×), so it was rephrased to "Let the record show that…" in ch03/05/07/10 (training case 08, proposal P3). The rest is small-word noise ("this"/"the") and "bought" as "bot" (American) |
| 10 | Package | done; cover.jpg drawn by `cover.py`; chapter WAVs deleted (rebuild from the cache with kokoro-narrate) |

| Ch | Title | Words |
|----|-------|-------|
| 01 | Pledged | 1637 |
| 02 | Cold Coal | 1393 |
| 03 | A Light Next Door | 1518 |
| 04 | Thursdays | 1284 |
| 05 | The Thermometer | 1507 |
| 06 | Eleven Years | 1308 |
| 07 | Lot Nineteen | 1556 |
| 08 | The First Flame | 1465 |
| 09 | The Widow's Grate | 1609 |
| 10 | Pencil | 1669 |
| 11 | The Reckoning | 1750 |
| 12 | House to House | 1571 |
| 13 | Given | 1382 |
| | **Total** | **19,649** |

## Reader test (2026-10-18), summary

Understood the plot, the rule and every character's want without the bible. Best scenes: "you were very badly priced"
(ch7), the unasked flame (ch8), "Then I suppose I'm useful" (ch9), the widow refusing to buy him (ch11), the fourth bar
(ch13). Top fixes, all applied:
1. The climax seemed to break the rule (sold before he gave): now explicit that possession passes at noon, and whatever fire is left at noon is the Guild's, which is also why he gives everything.
2. "Withdrawn" now has a mechanism (only the ticket holder can withdraw; a pledge with no ticket is no pledge). "You'd have gone cold" changed to plain speech.
3. Mrs Hobb's father kept the shop until after the flood; Quill's unlisted status is set up in ch6.
4. Tics trimmed ("I heard", "on the record", similes); "Aldevar" is now named in ch1, so "Al" makes sense.
5. The skipped last week gets a time stamp at the top of ch11.

Not changed: the ending's tidiness (the warm ending was the author's choice), Strand's quick turn (he has the thermometer and the lamplighter's cold flame as evidence).

## Open questions
- Aldevar pronunciation (AL-dih-var, American override /ˈældɪvˌɑɹ/) by ear.
- Title: *Second-Hand Dragons* (only one dragon) or *Can You Spare a Light?*
- Published to the website 2026-10-18 (bm_george), republished 2026-10-19 (af_heart).
