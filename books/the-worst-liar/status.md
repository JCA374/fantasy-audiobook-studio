# Status: The Worst Liar in Pennyford (book 4)

**Stage:** 8 Narrate, in progress (2026-10-21). Manuscript complete and edited. **First publish:** the full text plus ch01 audio (10.9 min, mastered MP3; the one-chapter .m4b was deleted so the site doesn't offer a partial audiobook). Ch02–08 rendering.

Ch01 listen check: 4 flags, none needing a fix. 7:23 "Lucan" heard as "Luke and" (that is LOO-kun, as intended); 10:38 "Nell" heard as "now" (one instance, likely Whisper); two short dialogue paragraphs flagged as slow pace (pauses around short lines).

**Origin:** the author asked (2026-10-21) for a new novel with every decision made automatically, following the pipeline: "when i come back i want a completed novell publisheb. onec the first chapter is convertet to aduio publish it wit the book then publisk the rest when everyting is done." So every choice in seed.md, the bible and the outline is Claude's, made under that instruction (premise 4 from collection.md, "The liar"). All of it is open to change in a second edition.

| # | Stage | State |
|---|---|---|
| 0 | Seed | done, `seed.md` (premise 4, "The liar") |
| 1 | Story bible | done, `story-bible.md` with 16 numbered rules, stress test and reveal ladder; `glossary.md` (all names ordinary English, Kokoro says them right) |
| 2 | Outline | done, `outline.md`, 8 chapters × ~1,900 words |
| 3 | Draft | done, 8 chapters; each checked with speech-flow scan.py and a word-list AI-ism pass while drafting |
| 4 | Edit | developmental and continuity pass (geography of the bridge and toll house; Fairweather's age vs "since I was a girl"; the timeline from the fair to the Moot, rent due before the Moot so the bailiff is held off); world-rules audit (rule 7 made local: a thing goes thin in front of a doubting crowd, slips only when parish-wide belief drops under a hundred); tics trimmed ("the way" ~45 → ~20, "for a moment" 13 → 6, "very"); `continuity.md` filled |
| 5 | Reader test | done twice, fresh subagents with the chapters only (summary below) |
| 6 | Speech flow | scan clean except deliberate lines (scene-break-free comma-before-and false positives; a few punchline short lines) |
| 7 | Audio prep | done, `audio/chNN.txt` |
| 8 | Narrate | af_heart, speed 0.95 (house voice) |
| 9 | Listen check | |
| 10 | Package | cover.jpg drawn by `cover.py` (bridge at dusk, a ghostly toll gate, the Crier's bell) |

| Ch | Title | Words |
|----|-------|-------|
| 01 | Short Weight | 1,950 |
| 02 | The Toll | 2,000 |
| 03 | The Crier | 1,880 |
| 04 | Thin as Glass | 1,730 |
| 05 | The Biggest Liar | 1,660 |
| 06 | The Offer | 1,970 |
| 07 | The Moot | 1,930 |
| 08 | True Weight | 1,960 |
| | **Total** | **about 15,100** |

## Reader test 1 (2026-10-21), summary

A fresh subagent read only the chapters. It understood the plot, every character's want and the stakes, and explained the rules correctly (catching, never-liars, slipping, payments stay paid, bodies out of bounds, one lie ends it, the Ninety-Nine). Best moments: Gran on the stairs ("Liars don't practise, pet"), the mirror scene, Amos's "Thirty-one years", the pies for Luke, "I just gave them a better bridge", the lemon-cake callback, the last cry. Fixes, all applied:
1. **Climax trigger** felt like a switch (a dog's bark). Now Nell uses the rules: she points at a memory the telling left standing (the whole Moot made her Weigher because she "can't fib about a quarter-ounce", planted in ch1) and nobody can explain it; doubt catches; Biscuit is only the last push. Her plan with Gran (try for real, and fail, in front of everyone) is now spelled out.
2. **The Crier's oath** planted in ch2 (sworn by the Reeve, two witnesses) and ch3 (everyone remembers Fairweather sworn); ch8 "false Crier" now follows: Mrs Thorne remembers she never swore him.
3. **Amos's voice** contradiction removed (ch8: "My voice is fine… I'd like to sit down").
4. **Outsider-witness loophole** closed: anyone who has lied catches a telling at the boundary stones; the doubter in Gran's Hollin story was a never-liar (rule 5).
5. **Loose ends:** the toll keeper is Fairweather's real servant (ch1–2, leaves up the Hollin road in ch8); nobody on Ladle Lane owes rent; why he risks the Moot (a story that size needs the whole town at once) and why he doesn't tell Nell banished (ch6). One humiliation beat cut from ch5; Nell's mercy speech now prepared ("the poor little devil").

Not changed: ch3's first half (watching him work the market) stays, since it shows rule 2 in action.

## Reader test 2 (2026-10-21, rule reader test after the climax changed)

A second fresh subagent (chapters only) explained every rule correctly and found the climax obeys them: Nell fails to lie in public (set up by the mirror scene and Gran's plan), the Weigher vote exposes a hole the telling left (planted in ch1), and doubt catches by word of mouth. Biscuit only tips it. Fixes, all applied:
1. Ch2 "it can't change what you've done" contradicted what tellings do (they rewrite past deeds): now "how things are, and how you remember them; whatever you really do while it holds stays done". Ch7 now spells out the lever: his story has no room for the Moot that made her Weigher.
2. Ch8 fine "the toll you never paid" (she paid twice): now "the price of crossing that bridge, for three weeks".
3. Ch3: the Crier is sworn every spring Moot, so 19-year-old Nell saw Amos sworn; she notes the town remembers Fairweather both arriving as a stranger and sworn in, "and nobody seemed to mind that both things were true".
4. Small: a stray quote mark in ch6 (would have split the narration), "kitchen door" → "back door", Gran's "your grandfather" → "since I was widowed" (two grandfathers blurred by ear), "until three weeks ago" → "until this month" for the Crier, one hard-to-parse line in ch7.
Not changed: everything falls at once in ch8 (covered by "what else had he told them?"); the banishment answer in ch6 stays as character motive.

## Open questions (for the author, any time)
- Title: *The Worst Liar in Pennyford* (or shorter: *The Worst Liar*).
- Everything was decided by Claude; any of it can change in a second edition.
