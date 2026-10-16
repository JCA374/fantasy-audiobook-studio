# Rule proposals

Patterns Claude has noticed across two or more training cases or listen-check findings, drafted as a rule,
a scanner check and a test. A proposal becomes a rule only when the author approves it.

| # | Pattern | Seen in | Draft rule | Status |
|---|---|---|---|---|
| P1 | Short lines get both a flat ending (no main stress) and no emotion | cases 01, 05 | Merged: the "bare short line" check covers both; the listen-check stress check confirms it in the audio | approved (merged into case 05) |
| P2 | Paragraphs of one to three words, dialogue **or** narration, standing alone. Kokoro has too little context and may slur them ("A wall." → "A while.") | case 05; case 06 (listen-check, ch06) | Extend the scanner's "bare short line" check to narration paragraphs of ≤ 3 words. Fix by merging into the neighbouring paragraph, or with an emotion beat if it's dialogue. Test: flag `She sat.`, leave `She sat. He did not open a file.` | proposed |
