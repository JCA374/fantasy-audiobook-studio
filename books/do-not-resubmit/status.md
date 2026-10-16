# Status: Do Not Resubmit

**Stage:** COMPLETE 2026-10-16. Audiobook: audio/Do Not Resubmit.m4b (78.9 min, 7 chapters, cover, -19.4 LUFS) + audio/chNN.mp3; copied to export/Audiobooks/.
Edits later: change chNN.md, re-run narration-prep, kokoro-narrate (only changed paragraphs render), listen-check and audiobook-assemble.

**Origin:** a second, separate story grown from chapter 1 of *The One in the Chair*. Only that chapter is reused
(copied from the last commit, with the author's later "find it" ending line). Nothing else from book 1 applies.

| Ch | Title | Words |
|----|-------|-------|
| 01 | Intake | 1057 |
| 02 | The Queue | 2140 |
| 03 | Witness | 2136 |
| 04 | The Archive | 2025 |
| 05 | The Cold Chair | 2054 |
| 06 | The Hearing | 2094 |
| 07 | Passage | 2086 |

**Decisions 2026-10-16** (author: "yes to all, go with your proposals", then "I want a happy ending", then "use the full
pipeline … convert it to an audiobook and publish"): Mira is dead; names Ruth / Agnes Hale / Mr Pell / Dot; af_heart
narrator; ch1 kept as written; Ruth a night-shift nurse; Agnes becomes a hall lamp; both Mira and Ruth granted passage.

**Pipeline run 2026-10-16:**
- Draft ch2–7 (one at a time, each within ±15 % of 2,300 words; ch1 unchanged).
- Edit: own developmental + continuity pass (fixed: Pell's "four years ago" vs the three-year tip; file number made four
  digits; Ruth sitting on the floor in ch7; one weigher stamping instead of two; notes written at night not morning).
- avoid-ai-writing: no tier-1/2 words; trimmed "very" (~25 cut), repeated "nothing in particular", "for a moment".
- prose-mechanics (mechanical audits by script: sentence variance, length, echoes, -ly, tags, starters): split the
  sentences over 40 words; sentence-length sd 7–10.
- Reader test (fresh sub-agent, no bible). Fixed: weighers given fixed labels for the ear; personal appeal "ties the
  two files together" foreshadowed in ch5 (plus "everyone who knew you and died before you did is in there"); Ruth's
  testimony cued "in her mother's words"; shift-swap thread paid off in ch7; ch5 intake beats compressed.
- speech-flow: emotion beats on bare short lines, semicolons → full stops, comma-before-and fixes, long sentences
  split. Pre-speech-flow copies in the session scratchpad only.
- Cover: `python3 cover.py cover.jpg` (house at night, one lit window).

- Narrate: af_heart, speed 0.95, 78.6 min rendered.
- listen-check: 16 flags agreed by both models; 15 judged noise (Whisper writing the file number's "oh" as "zero"/"hundred",
  it/at, sat/sad, short slow paragraphs with deliberate pauses). 1 real: ch02 "Mm," rendered as a bare /m/ (heard "miss"),
  rewritten as "Mira made a noise that meant nothing in particular." and re-rendered; ch02 re-checked clean.
  Not yet confirmed by ear, so no training case was made; worth a listen at ch02 ~3:21 if you want to add one.

**Open (author's taste):** title; whether ch1 (1,057 words) should be expanded to match the others.
