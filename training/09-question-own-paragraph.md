# 09 · A short question with a beat still sounds weak

Source: *The One in the Chair*, ch03 (Mira, when the supervisor offers her a favour).

> There was something in the way he asked. Not an order. Mira had been given orders by this man, and they sounded like weather reports. This sounded like a favour.
>
> "Why?" It came out sharper than she meant.

**Heard:** a follow-up to case 01. The beat after "Why?" doesn't give it a main stress (`wˌI?`), so case 01's
markup is needed even with a beat. With the markup (`"[Why](+2)??" It came out…`, now `before`) the author found it
"better but not great".

**Tried** (rendered with the paragraph before and the one after; renders kept out of the repo):
- a third question mark, `"[Why](+2)???"`
- a drawn-out vowel, `"[Why](/wˈIː/)??"`
- the question voiced as its own paragraph, the beat as the next one (now `after`)
- a rewording, `"Why now?"`, which puts the main stress on the last word without markup

**Decision:** the author picked the question on its own paragraph. `prep.py` now does this in the script (the manuscript is
unchanged): a marked short question that opens a paragraph is voiced alone and the beat follows as its own
paragraph. A tag (`"How?" said Quill.`) stays in place, since "said Quill." alone would sound odd.
