# Status: The One in the Chair (working title was The Reaper and the Furniture)

**Stage:** COMPLETE 2026-10-14. Audiobook: audio/The One in the Chair.m4b (92 min, 13 chapters, cover, -19.4 LUFS) + audio/chNN.mp3.
Edits later: change chNN.md, regenerate audio/chNN.txt (narration-prep), re-run kokoro-narrate (only changed paragraphs render) and audiobook-assemble.

**Re-narrated 2026-10-19** (second edition, af_heart): short questions stressed and voiced on their own paragraph (training cases 01 and 09), plus the author's ch01 edit ("…where she might find it."). 112.5 min, 14 chapters; copied to export/Audiobooks/ as "The One in the Chair - Second Edition.m4b". Listen check: no stress flags left; 4 old pace/word flags, plus one new borderline pace flag in ch12 ¶60 ("All right," said Mira. "Loud, then.", 2.09 words/s vs 3.0) for the author to hear.

Pipeline evidence (`verify.py`, 2026-10-19; seed predates the seed stage):

| Stage | State | Proof |
|---|---|---|
| 0 seed | MISSING | seed.md |
| 1–5 | MANUAL | bible, glossary, outline, 14 chapters, reader-test summary present |
| 6 speech flow | PASS | last scan of every chapter matches the manuscript |
| 7 audio prep | PASS | every audio/chNN.txt equals prep.py's output for the current manuscript |
| 8 narrate | PASS | rendered from the current scripts, every paragraph cached |
| 9 listen check | PASS | every report made from the current script and audio |
| 10 package | PASS | assembled from the current scripts' renders; MP3s and .m4b unchanged since |

| Ch | Title | Words |
|----|-------|-------|
| 01 | Intake | 1013 |
| 02 | New Evidence | 1245 |
| 03 | The Supervisor | 1322 |
| 04 | The Hearing | 1474 |
| 05 | Lost Correspondence | 1197 |
| 06 | The Boundary Section | 1174 |
| 07 | The Door With No Nameplate | 1422 |
| 08 | A Clean Provenance | 1055 |
| 09 | Sequestered | 1120 |
| 10 | Floor | 1232 |
| 11 | Testimony | 959**Resolved by Claude on the author's instruction (2026-10-14), revisit if desired:**
- Mira's death: one line in ch10, "A wet road, a delivery van, a Tuesday." (bible §9 updated)
- Ch1 light edits for clarity/audio: split two long dash sentences; "doormat-man's cousin" became a sugar bowl
  "that had by all accounts been a very sweet man"; "you people" became "they". Original kept in the session scratchpad.
- Pronunciation: Mira = MEER-uh /mˈiɹə/, Elin = EL-in /ˈɛlɪn/ (glossary.md).
- Author: Jonas (book.yaml).

**Done 2026-10-14:** title "The One in the Chair"; cover.jpg (drawn with Python: `python3 cover.py cover.jpg`);
voice-audition files deleted.

**2026-10-15, speech-flow on ch01:** 9 fixes applied (training cases 02–04: commas, unclosed dashes, cued italics,
split long sentences, "find new evidence", "Can I?" + beat, "who they were, that…", "not softness exactly, but…").
ch01 re-rendered (8 paragraphs), m4b rebuilt (92.1 min, 13 chapters, −19.4 LUFS) and copied to export/.
Next: run speech-flow on ch02–ch13.

**2026-10-16, second edition started** (plan: rewrite-notes.md + story-bible §10).
Stage: rewrite, step 2 of 5. Done: v1 kept (tag `v1-first-edition`, `books/the-one-in-the-chair-v1/`, site shows
"Earlier editions"); bible §3/§4/§10 updated (terms, placement, crossing cost, Hollis, counter clerk); outline.md
rewritten for 14 chapters. Author answers: Hollis OK; crossings revised; cardigan woman planted ch02; placement stays vague. Author then said go ahead with everything.

**2026-10-16, second edition drafted** (14 chapters, ~19.2k words; a little over the 18k target, accepted).
- ch07 "Placement" is new; old ch07–13 became ch08–14. Intake dialogue unchanged.
- Fresh-subagent reader test: fixed Edmund's name leaking into ch09, his age, Crane not suspecting the Keeper, Article Nine wording, the forgery mechanics (line count per entry), the ch04 "drier of the two" line, uncued document text and speakerless lines; added beats to flat "Why?"/"What?" lines and the case 06 fix.
- Still open from the reader test (judgement calls, not changed): Edmund is easy to guess from ch03; Elin's death and the woman's fate stay unstated; where placed objects go stays vague (author's wish).
- Audio: scripts regenerated (narration-prep converter = same splitting as v1, so the cache is reused), full render, listen-check, assemble.
