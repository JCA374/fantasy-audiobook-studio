# 10 · One- and two-word lines of dialogue

Source: the author, 2026-10-22, about the whole pipeline: "we need to minimize dialog that is one or two words long."

**Measured (2026-10-22):** share of spoken lines that are two words or fewer in total, and share that are clipped (case 07: every sentence three words or fewer).

| Book | ≤2-word lines | clipped |
|---|---|---|
| Second-Hand Dragons | 26/223 = 12% | 18% |
| The One in the Chair | 44/289 = 15% | 24% |
| Do Not Resubmit | 18/153 = 12% | 20% |
| The Worst Liar in Pennyford | 10/168 = 6% | 12% |

Case 07's 1-in-7 rule roughly halved them in book 4, but the author still hears too many.

**Rule (speech-flow *Clipped dialogue*, writing-for-the-ear *Dialogue*):** at most one spoken line in twenty may be two words or fewer, and at most one in ten clipped. Keep a two-word line only when it is a decision, a confession, an interruption or a punchline. A filler line is not fixed by padding it ("Yes, I suppose so, yes."). Fix it with what only this character would say here: a reason, a deflection or a detail. Or fold the exchange into narration ("She said yes before he had finished asking.").

> "Was it you?" … "Yes." … "Why?"
>
> "Was it you?" … "Yes. I signed for her myself." … "Why would you sign for a stranger?"

**Scanner:** `two-word-line share N/M` (shown as ¶0) flags a chapter with at least 12 spoken lines where more than 5% are ≤2 words, and lists their ¶s. `clipped-dialogue share` now fires above 10% (was 15%). The manuscript-review gate makes both hard limits while drafting.

**Status:** rule for new books. The four finished books have not been revised.
